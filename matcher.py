import re
import math
import os
import google.generativeai as genai
import database

# Configure Gemini if API key is present
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Simple TF-IDF Vectorizer in Pure Python for matching
def tokenize(text):
    if not text:
        return []
    # Lowercase, keep words, split by whitespace and commas
    text = text.lower()
    words = re.findall(r'\b[a-z0-9\-]+\b', text)
    # Filter short words and common stopwords
    stopwords = {"and", "the", "for", "with", "a", "of", "to", "in", "on", "at", "an", "is", "are", "by"}
    return [w for w in words if w not in stopwords]

def calculate_cosine_similarity(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    
    sum1 = sum([val**2 for val in vec1.values()])
    sum2 = sum([val**2 for val in vec2.values()])
    
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    
    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

def get_tf_idf_vectors(profiles):
    # Prepare documents
    docs = []
    for p in profiles:
        # We separate profiles into multiple text blocks for fine-grained weighting
        interests_text = p.get('interests', '')
        needs_text = p.get('tech_needs', '') + " " + p.get('looking_for', '')
        bio_text = p.get('bio', '') + " " + p.get('job_title', '')
        
        docs.append({
            'id': p['id'],
            'interests': tokenize(interests_text),
            'needs': tokenize(needs_text),
            'bio': tokenize(bio_text)
        })
        
    # Build vocabs & IDF for each category
    def compute_category_tfidf(category):
        # Count document frequency
        df = {}
        total_docs = len(docs)
        for doc in docs:
            unique_words = set(doc[category])
            for word in unique_words:
                df[word] = df.get(word, 0) + 1
                
        # Calculate IDF
        idf = {}
        for word, count in df.items():
            idf[word] = math.log((total_docs + 1) / (count + 0.5)) + 1
            
        # Calculate TF-IDF vectors
        vectors = {}
        for doc in docs:
            tf = {}
            for word in doc[category]:
                tf[word] = tf.get(word, 0) + 1
            
            # Multiply TF by IDF
            tfidf = {}
            for word, count in tf.items():
                tfidf[word] = count * idf[word]
            vectors[doc['id']] = tfidf
            
        return vectors

    interests_vectors = compute_category_tfidf('interests')
    needs_vectors = compute_category_tfidf('needs')
    bio_vectors = compute_category_tfidf('bio')
    
    return interests_vectors, needs_vectors, bio_vectors

def compute_profile_matches(active_profile_id, event_id=None):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # Get the active profile
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (active_profile_id,))
    active_row = cursor.fetchone()
    if not active_row:
        conn.close()
        return []
    active_profile = dict(active_row)
    
    # Get candidate profiles based on event membership
    if event_id:
        # Only match against other attendees of the same event
        cursor.execute("""
            SELECT p.* FROM profiles p
            JOIN event_members em ON p.id = em.profile_id
            WHERE em.event_id = ? AND p.id != ?
        """, (event_id, active_profile_id))
    else:
        # No event filter — match against all profiles
        cursor.execute("SELECT * FROM profiles WHERE id != ?", (active_profile_id,))
    
    other_profiles = [dict(row) for row in cursor.fetchall()]
    
    if not other_profiles:
        conn.close()
        return []
    
    # Build the full list for TF-IDF computation (active + others)
    all_profiles = [active_profile] + other_profiles

    # Get vectors
    int_vecs, need_vecs, bio_vecs = get_tf_idf_vectors(all_profiles)
    
    # Get historical feedback to adjust weights
    # We query all rated matches where the active profile was involved
    cursor.execute("""
    SELECT profile_a_id, profile_b_id, feedback_score 
    FROM matches 
    WHERE (profile_a_id = ? OR profile_b_id = ?) AND feedback_score IS NOT NULL
    """, (active_profile_id, active_profile_id))
    feedbacks = cursor.fetchall()
    
    # Default category weights
    w_interests = 0.5
    w_needs = 0.3
    w_bio = 0.2
    
    # Simple adaptation feedback loop:
    # If the user has rated matches with higher interests similarity positively, we increase w_interests.
    # If they rated matches with higher needs similarity positively, we increase w_needs.
    if feedbacks:
        interests_feedback_sum = 0
        needs_feedback_sum = 0
        feedback_count = 0
        
        for fb in feedbacks:
            other_id = fb['profile_b_id'] if fb['profile_a_id'] == active_profile_id else fb['profile_a_id']
            score = fb['feedback_score'] # 1 to 5 scale
            normalized_score = (score - 3) / 2.0 # range -1.0 to 1.0
            
            # Calculate similarities for this historical pair
            int_sim = calculate_cosine_similarity(int_vecs[active_profile_id], int_vecs[other_id])
            need_sim = calculate_cosine_similarity(need_vecs[active_profile_id], need_vecs[other_id])
            
            interests_feedback_sum += normalized_score * int_sim
            needs_feedback_sum += normalized_score * need_sim
            feedback_count += 1
            
        if feedback_count > 0:
            # Adjust weights based on correlation of feedback with features
            # E.g. if positive feedback correlates with interest similarity, boost interest weight
            w_interests += interests_feedback_sum * 0.1
            w_needs += needs_feedback_sum * 0.1
            
            # Ensure weights are positive and sum to 1
            w_interests = max(0.1, min(0.8, w_interests))
            w_needs = max(0.1, min(0.8, w_needs))
            total_w = w_interests + w_needs
            # Scale to leave some room for bio weight
            w_interests = (w_interests / total_w) * 0.8
            w_needs = (w_needs / total_w) * 0.8
            w_bio = 1.0 - w_interests - w_needs
            
    matches_list = []
    
    for other in other_profiles:
        other_id = other['id']
        
        # Calculate individual similarity components
        sim_interests = calculate_cosine_similarity(int_vecs[active_profile_id], int_vecs[other_id])
        sim_needs = calculate_cosine_similarity(need_vecs[active_profile_id], need_vecs[other_id])
        sim_bio = calculate_cosine_similarity(bio_vecs[active_profile_id], bio_vecs[other_id])
        
        # Weighted overall score
        raw_score = (sim_interests * w_interests) + (sim_needs * w_needs) + (sim_bio * w_bio)
        
        # Map score to percentage (0% to 100%)
        # Add a small base similarity so the range is friendly (e.g. 45% to 98%)
        percentage_score = min(99.0, max(30.0, 45.0 + (raw_score * 54.0)))
        
        # Check if we already have an icebreaker or feedback for this pair
        cursor.execute("""
        SELECT icebreaker_a_to_b, icebreaker_b_to_a, feedback_score, feedback_notes
        FROM matches
        WHERE (profile_a_id = ? AND profile_b_id = ?) OR (profile_a_id = ? AND profile_b_id = ?)
        """, (active_profile_id, other_id, other_id, active_profile_id))
        match_row = cursor.fetchone()
        
        icebreaker = ""
        feedback_score = None
        feedback_notes = None
        
        if match_row:
            feedback_score = match_row['feedback_score']
            feedback_notes = match_row['feedback_notes']
            
            # Determine correct perspective for icebreaker
            cursor.execute("SELECT profile_a_id FROM matches WHERE (profile_a_id = ? AND profile_b_id = ?)", (active_profile_id, other_id))
            is_a_to_b = cursor.fetchone() is not None
            
            if is_a_to_b:
                icebreaker = match_row['icebreaker_a_to_b']
            else:
                icebreaker = match_row['icebreaker_b_to_a']
                
            # If user previously rated this match poorly (e.g. 1 or 2 stars), penalize score in dynamic ranking
            if feedback_score is not None:
                if feedback_score <= 2:
                    percentage_score = max(20.0, percentage_score - 25.0)
                elif feedback_score >= 4:
                    percentage_score = min(100.0, percentage_score + 10.0)

        # Generate icebreaker if it doesn't exist
        if not icebreaker:
            icebreaker_a_to_b, icebreaker_b_to_a = generate_icebreakers(active_profile, other)
            # Save new match details
            database.save_match(active_profile_id, other_id, raw_score, icebreaker_a_to_b, icebreaker_b_to_a)
            icebreaker = icebreaker_a_to_b if active_profile_id < other_id else icebreaker_b_to_a

        matches_list.append({
            'profile': other,
            'match_score': round(percentage_score, 1),
            'icebreaker': icebreaker,
            'feedback_score': feedback_score,
            'feedback_notes': feedback_notes
        })
        
    # Sort matches by score descending
    matches_list.sort(key=lambda x: x['match_score'], reverse=True)
    conn.close()
    return matches_list

def generate_icebreakers(profile_a, profile_b):
    """
    Generates icebreakers for both perspectives: A to B, and B to A.
    Returns (icebreaker_a_to_b, icebreaker_b_to_a).
    """
    if GEMINI_API_KEY:
        try:
            # Model selection
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt_template = (
                "You are an AI Event Networking Assistant. You are creating a personalized, professional, "
                "yet conversational networking icebreaker message that Attendee A can send to Attendee B at a conference. "
                "Keep it concise (2-3 sentences max) and contextual, focusing on shared interests, technological synergy, "
                "or how Attendee A's needs align with Attendee B's profile. "
                "Format: Direct message from A to B. Do not use quotes or introductory text like 'Here is the icebreaker:'.\n\n"
                "Attendee A:\n"
                "Name: {name_a}\n"
                "Role: {job_a} at {company_a}\n"
                "Bio: {bio_a}\n"
                "Interests: {interests_a}\n"
                "Needs/Looking For: {needs_a} / {looking_a}\n\n"
                "Attendee B:\n"
                "Name: {name_b}\n"
                "Role: {job_b} at {company_b}\n"
                "Bio: {bio_b}\n"
                "Interests: {interests_b}\n"
                "Needs/Looking For: {needs_b} / {looking_b}\n"
            )
            
            # Generate A to B
            response_a = model.generate_content(prompt_template.format(
                name_a=profile_a['name'], job_a=profile_a['job_title'], company_a=profile_a['company'],
                bio_a=profile_a['bio'], interests_a=profile_a['interests'], needs_a=profile_a['tech_needs'], looking_a=profile_a['looking_for'],
                name_b=profile_b['name'], job_b=profile_b['job_title'], company_b=profile_b['company'],
                bio_b=profile_b['bio'], interests_b=profile_b['interests'], needs_b=profile_b['tech_needs'], looking_b=profile_b['looking_for']
            ))
            
            # Generate B to A
            response_b = model.generate_content(prompt_template.format(
                name_a=profile_b['name'], job_a=profile_b['job_title'], company_a=profile_b['company'],
                bio_a=profile_b['bio'], interests_a=profile_b['interests'], needs_a=profile_b['tech_needs'], looking_a=profile_b['looking_for'],
                name_b=profile_a['name'], job_b=profile_a['job_title'], company_b=profile_a['company'],
                bio_b=profile_a['bio'], interests_b=profile_a['interests'], needs_b=profile_a['tech_needs'], looking_b=profile_a['looking_for']
            ))
            
            return response_a.text.strip(), response_b.text.strip()
        except Exception as e:
            # Fall back to simulated generator on error
            pass

    # High-quality Simulated Icebreaker Generator
    return (
        create_simulated_icebreaker(profile_a, profile_b),
        create_simulated_icebreaker(profile_b, profile_a)
    )

def create_simulated_icebreaker(p_from, p_to):
    # Find overlapping words in interests and needs to personalize
    from_interests = set(tokenize(p_from['interests']))
    to_interests = set(tokenize(p_to['interests']))
    to_needs = set(tokenize(p_to['tech_needs']))
    from_needs = set(tokenize(p_from['tech_needs']))
    
    shared_interests = from_interests & to_interests
    need_alignment = from_needs & to_interests
    solutions_alignment = from_interests & to_needs
    
    greeting = f"Hi {p_to['name'].split()[0]},"
    
    # Construct message template based on intersection of interests
    if shared_interests:
        keyword = list(shared_interests)[0].title()
        msg = (
            f"{greeting} I saw in your profile that you're interested in {keyword}, which is also a core focus of mine. "
            f"I'd love to swap insights on how you're approaching this in your work at {p_to['company']}. "
            f"Are you free for a quick 10-minute chat in the networking lounge?"
        )
    elif need_alignment:
        keyword = list(need_alignment)[0].title()
        msg = (
            f"{greeting} I noticed you work with {p_to['company']} and focus on {p_to['interests'].split(',')[0]}. "
            f"At {p_from['company']}, we are currently looking for solutions in {keyword}. "
            f"I'd love to connect to hear your perspective and see if we might collaborate."
        )
    elif solutions_alignment:
        keyword = list(solutions_alignment)[0].title()
        msg = (
            f"{greeting} Your profile caught my eye because you mentioned needing resources/expertise in {keyword}. "
            f"We've been focusing heavily on this area at {p_from['company']}, and I think we have some highly relevant experience. "
            f"Let's grab a coffee at the event café to discuss!"
        )
    else:
        # Generic professional outreach based on job titles
        msg = (
            f"{greeting} I'm attending the conference to connect with peers in the AI space. "
            f"Your work as a {p_to['job_title']} at {p_to['company']} looks fascinating, particularly regarding {p_to['interests'].split(',')[0]}. "
            f"I'd love to introduce myself and learn about what you're building."
        )
        
    return msg

def generate_followup_email(profile_from, profile_to, meeting):
    """
    Generates a personalized follow-up email draft.
    """
    venue = meeting.get('venue_location', 'the conference lounge')
    time_slot = meeting.get('time_slot', 'our scheduled slot')
    notes = meeting.get('notes', '')
    
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = (
                "You are an AI Event Networking Assistant. Draft a professional post-event follow-up email "
                "from Person A to Person B after a successful brief meeting at a conference.\n"
                "The email should be warm, refer to their meeting at the conference, incorporate details "
                "of their roles and interests, and propose a next step (like a follow-up Zoom call).\n"
                "Keep the email to a standard, concise layout (Subject, Body, Sign-off). Do not include extraneous system text.\n\n"
                f"Person A: {profile_from['name']}, {profile_from['job_title']} at {profile_from['company']}\n"
                f"Person B: {profile_to['name']}, {profile_to['job_title']} at {profile_to['company']}\n"
                f"Meeting context: Met at {venue} during {time_slot}. {f'Discussion topics included: {notes}' if notes else ''}"
            )
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            pass
            
    # Simulated follow-up email
    subject = f"Great connecting at the conference! - {profile_from['name']} ({profile_from['company']})"
    body = (
        f"Hi {profile_to['name'].split()[0]},\n\n"
        f"It was fantastic meeting you briefly at {venue} earlier today during {time_slot}.\n\n"
        f"I really enjoyed our discussion, especially hearing about your work at {profile_to['company']} "
        f"and your thoughts on {profile_to['interests'].split(',')[0]}. It seems there is a lot of synergy "
        f"between what you're doing and our initiatives at {profile_from['company']}.\n\n"
        f"As discussed, I would love to schedule a follow-up 30-minute call next week to dive deeper into potential "
        f"collaborations and explore how we can support each other.\n\n"
        f"Let me know if you have any availability next Tuesday or Wednesday morning.\n\n"
        f"Best regards,\n\n"
        f"{profile_from['name']}\n"
        f"{profile_from['job_title']}\n"
        f"{profile_from['company']}"
    )
    
    return f"Subject: {subject}\n\n{body}"

def suggest_groups_for_profile(profile_id):
    """
    Recommends groups based on profile interests.
    """
    profile = database.get_profile(profile_id)
    if not profile:
        return []
        
    p_interests = tokenize(profile['interests'])
    p_needs = tokenize(profile['tech_needs'])
    p_profile_tokens = set(p_interests + p_needs)
    
    groups = database.get_groups()
    scored_groups = []
    
    for g in groups:
        # Tokenize group name, topic, and description
        g_text = g['name'] + " " + g['topic'] + " " + g.get('description', '')
        g_tokens = set(tokenize(g_text))
        
        # Calculate overlap
        overlap = len(p_profile_tokens & g_tokens)
        
        # Simple score
        scored_groups.append({
            'group': g,
            'score': overlap
        })
        
    # Sort groups
    scored_groups.sort(key=lambda x: x['score'], reverse=True)
    return [item['group'] for item in scored_groups]
