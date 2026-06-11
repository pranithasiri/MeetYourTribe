import sqlite3
import os
import csv

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conference.db")
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles_data.csv")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Profiles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        password TEXT,
        company TEXT,
        job_title TEXT,
        bio TEXT,
        interests TEXT, -- Comma-separated
        tech_needs TEXT, -- Comma-separated
        looking_for TEXT,
        avatar_url TEXT
    )
    """)
    # Create Events Table
    cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    location TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

    # Create Event Members Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_members (
        event_id INTEGER,
        profile_id INTEGER,
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (event_id, profile_id),
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
    )
    """)
    # Create Matches Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_a_id INTEGER,
        profile_b_id INTEGER,
        score REAL,
        icebreaker_a_to_b TEXT,
        icebreaker_b_to_a TEXT,
        feedback_score INTEGER DEFAULT NULL, -- 1 to 5 rating
        feedback_notes TEXT,
        FOREIGN KEY (profile_a_id) REFERENCES profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (profile_b_id) REFERENCES profiles(id) ON DELETE CASCADE,
        UNIQUE(profile_a_id, profile_b_id)
    )
    """)
    
    # Create Meetings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inviter_id INTEGER,
        invitee_id INTEGER,
        time_slot TEXT, -- e.g., "14:00 - 14:15"
        venue_location TEXT, -- e.g., "Networking Lounge A", "Booth 12"
        status TEXT DEFAULT 'pending', -- pending, accepted, declined
        notes TEXT,
        FOREIGN KEY (inviter_id) REFERENCES profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (invitee_id) REFERENCES profiles(id) ON DELETE CASCADE
    )
    """)
    
    # Create Groups Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        topic TEXT NOT NULL,
        description TEXT,
        created_by INTEGER,
        FOREIGN KEY (created_by) REFERENCES profiles(id)
    )
    """)
    
    # Create Group Members Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS group_members (
        group_id INTEGER,
        profile_id INTEGER,
        PRIMARY KEY (group_id, profile_id),
        FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
        FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
    )
    """)

    # Create Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (receiver_id) REFERENCES profiles(id) ON DELETE CASCADE
    )
    """)

    # Seed mock data if profiles is empty
    cursor.execute("SELECT COUNT(*) FROM profiles")
    if cursor.fetchone()[0] == 0:
        seed_profiles = [
            (
                "Dr. Elena Rostova",
                "elena.rostova@deepmind.example.com",
                "password123",
                "DeepMind Technologies",
                "Principal Research Scientist",
                "Working on Large Language Model alignment, RLHF, and agentic workflows. Former researcher at OpenAI and MIT AI Lab.",
                "LLM Alignment, Agentic Workflows, Reinforcement Learning, Cognitive Architecture",
                "High-performance GPU cluster access, Rust deployment frameworks",
                "Collaborators on multi-agent collaboration frameworks and ethicists working on AI safety.",
                "https://api.dicebear.com/7.x/adventurer/svg?seed=Elena"
            ),
            (
                "Aravind Reddy",
                "aravind.reddy@apexventures.example.com",
                "password123",
                "Apex Ventures",
                "General Partner",
                "Investing in seed and early-stage generative AI startups. Passionate about developer tools and vertical SaaS applications using LLMs.",
                "Venture Capital, Seed Investing, Developer Tools, Vertical AI, SaaS scaling",
                "High-quality startup pitch decks, Tech founders in stealth mode",
                "Stealth-mode founders building core AI infrastructure or developer tools who need initial funding and strategic growth planning.",
                "https://api.dicebear.com/7.x/adventurer/svg?seed=Aravind"
            ),
            (
                "Sarah Jenkins",
                "sarah.jenkins@medtech.example.com",
                "password123",
                "MedTech Solutions Inc.",
                "Director of AI Strategy & Clinical Products",
                "Driving AI integration into digital healthcare. Focused on clinical decision support, HIPAA-compliant patient report summarization, and medical imaging analysis.",
                "Healthcare AI, HIPAA Compliance, Medical Imaging, Patient Summarization, Digital Health",
                "Privacy-preserving AI architectures, Medical NLP models, Federated learning engines",
                "AI engineers with experience in health-tech, data compliance officers, and medical researchers.",
                "https://api.dicebear.com/7.x/adventurer/svg?seed=Sarah"
            ),
            (
                "Hiroshi Tanaka",
                "hiroshi.tanaka@canvasflow.example.com",
                "password123",
                "CanvasFlow AI",
                "Lead Frontend & UX Architect",
                "Building interactive playgrounds and visual design systems for prompt engineering, model tuning, and multi-modal canvas layouts.",
                "UX Design, Prompt Engineering UI, WebGL, Canvas API, Frontend Architecture",
                "Lightweight client-side model runners, Vector search visualization tools",
                "Product designers and backend AI engineers building LLM-integrated canvas interfaces.",
                "https://api.dicebear.com/7.x/adventurer/svg?seed=Hiroshi"
            ),
            (
                "Liam O'Connor",
                "liam.oconnor@agenticlabs.example.com",
                "password123",
                "Agentic Labs",
                "Co-Founder & CTO",
                "Building a developer platform for autonomous AI software engineers. Focused on code synthesis, repository editing, and local execution sandboxes.",
                "Autonomous Agents, Code Synthesis, Development Sandboxes, DevOps Automation",
                "Reliable API integrations, Sandboxed execution microservices, LLM code fine-tuning",
                "Talented software developers interested in agentic frameworks, and potential enterprise beta-testers.",
                "https://api.dicebear.com/7.x/adventurer/svg?seed=Liam"
            ),
            (
                "Emily Chen",
                "emily.chen@orbitscale.example.com",
                "password123",
                "OrbitScale Cloud",
                "Principal Solutions Architect",
                "Specializing in distributed computing, multi-GPU model serving, vLLM optimization, and green computing strategies for massive AI inference clusters.",
                "vLLM Optimization, Cloud Infrastructure, Multi-GPU Serving, Green AI, Distributed Computing",
                "Hardware acceleration chips, Model quantization libraries, Kubernetes orchestration",
                "Startups and enterprises struggling to scale their LLM inference performance while keeping cost and carbon footprint down.",
                "https://api.dicebear.com/7.x/adventurer/svg?seed=Emily"
            ),
            (
                "Marcus Vance",
                "marcus.vance@vancepartners.example.com",
                "password123",
                "Vance & Partners Legal",
                "Managing Partner - Tech & AI Policy",
                "Advising tech giants and fast-growing startups on AI regulations, copyright compliance in dataset curation, and data privacy compliance.",
                "AI Regulation, Copyright Compliance, Data Privacy, EU AI Act, Intellectual Property",
                "Auditing tools for training datasets, Bias detection engines",
                "Founders and Chief Compliance Officers seeking legal frameworks for generative AI models and dataset licensing advice.",
                "https://api.dicebear.com/7.x/adventurer/svg?seed=Marcus"
            ),
            (
                "Priya Sharma",
                "priya.sharma@omniretail.example.com",
                "password123",
                "OmniRetail Global",
                "Senior Director of Engineering",
                "Integrating AI capabilities into customer support automation, catalog search systems, and personalization models for multi-million user retail apps.",
                "E-Commerce AI, Customer Support Bots, Personalization Engines, Search Recommenders",
                "RAG architectures, Hybrid semantic search, Guardrails for customer-facing chatbots",
                "Providers of advanced recommendation algorithms, reliable vector databases, and RAG guardrail solutions.",
                "https://api.dicebear.com/7.x/adventurer/svg?seed=Priya"
            )
        ]
        
        cursor.executemany("""
        INSERT INTO profiles (name, email, password, company, job_title, bio, interests, tech_needs, looking_for, avatar_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_profiles)
        
        # Seed initial groups
        seed_groups = [
            ("LLM Alignment & Safety", "LLM Alignment, AI Regulation", "Discussion on RLHF, RLAIF, and complying with global AI acts.", 1),
            ("Scaling Autonomous Agents", "Agentic Workflows, Autonomous Agents", "Focus on building stable, self-healing developer agents and sandboxing.", 5),
            ("AI Inference at Scale", "vLLM Optimization, Cloud Infrastructure", "Techniques for low-latency serving, model quantization, and serverless hosting.", 6)
        ]
        
        cursor.executemany("""
        INSERT INTO groups (name, topic, description, created_by)
        VALUES (?, ?, ?, ?)
        """, seed_groups)
        
        # Seed group memberships
        cursor.execute("INSERT INTO group_members (group_id, profile_id) VALUES (1, 1)") # Elena in Alignment
        cursor.execute("INSERT INTO group_members (group_id, profile_id) VALUES (1, 7)") # Marcus in Alignment
        cursor.execute("INSERT INTO group_members (group_id, profile_id) VALUES (2, 1)") # Elena in Agents
        cursor.execute("INSERT INTO group_members (group_id, profile_id) VALUES (2, 5)") # Liam in Agents
        cursor.execute("INSERT INTO group_members (group_id, profile_id) VALUES (3, 6)") # Emily in Inference
        cursor.execute("INSERT INTO group_members (group_id, profile_id) VALUES (3, 8)") # Priya in Inference

    conn.commit()
    conn.close()
    
    # Export seed profiles to CSV on startup
    export_profiles_csv()

# Helper DB Functions

def get_profiles(active_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if active_id:
        # Exclude active profile from listing, or order it
        cursor.execute("SELECT * FROM profiles WHERE id != ?", (active_id,))
    else:
        cursor.execute("SELECT * FROM profiles")
    profiles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return profiles

def get_profile(profile_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_profile_by_email(email):
    """Fetch a profile by email address for login validation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_profile(name, company, job_title, bio, interests, tech_needs, looking_for, email=None, password=None, avatar_url=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if not avatar_url:
        avatar_url = f"https://api.dicebear.com/7.x/adventurer/svg?seed={name.replace(' ', '')}"
    cursor.execute("""
    INSERT INTO profiles (name, email, password, company, job_title, bio, interests, tech_needs, looking_for, avatar_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, email, password, company, job_title, bio, interests, tech_needs, looking_for, avatar_url))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

       
    
    # Auto-export to CSV on every new profile creation
    export_profiles_csv()
    
    return new_id

def update_profile(profile_id, name, company, job_title, bio, interests, tech_needs, looking_for):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE profiles
    SET name = ?, company = ?, job_title = ?, bio = ?, interests = ?, tech_needs = ?, looking_for = ?
    WHERE id = ?
    """, (name, company, job_title, bio, interests, tech_needs, looking_for, profile_id))
    conn.commit()
    conn.close()
    
    # Auto-export to CSV on profile update
    export_profiles_csv()
    
    return True

def get_cached_matches(profile_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT m.*, p.name, p.company, p.job_title, p.bio, p.interests, p.tech_needs, p.looking_for, p.avatar_url
    FROM matches m
    JOIN profiles p ON (m.profile_b_id = p.id AND m.profile_a_id = ?) 
                    OR (m.profile_a_id = p.id AND m.profile_b_id = ?)
    """, (profile_id, profile_id))
    matches = []
    for row in cursor.fetchall():
        match_dict = dict(row)
        # Fix perspective: we want profile_b to be the "other" person
        if match_dict['profile_a_id'] == profile_id:
            match_dict['other_profile_id'] = match_dict['profile_b_id']
            match_dict['icebreaker'] = match_dict['icebreaker_a_to_b']
        else:
            match_dict['other_profile_id'] = match_dict['profile_a_id']
            match_dict['icebreaker'] = match_dict['icebreaker_b_to_a']
        matches.append(match_dict)
    conn.close()
    return matches

def save_match(profile_a_id, profile_b_id, score, icebreaker_a_to_b, icebreaker_b_to_a):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Sort IDs so profile_a_id < profile_b_id to maintain uniqueness
    id1, id2 = min(profile_a_id, profile_b_id), max(profile_a_id, profile_b_id)
    if id1 != profile_a_id:
        icebreaker_a_to_b, icebreaker_b_to_a = icebreaker_b_to_a, icebreaker_a_to_b
        
    cursor.execute("""
    INSERT INTO matches (profile_a_id, profile_b_id, score, icebreaker_a_to_b, icebreaker_b_to_a)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(profile_a_id, profile_b_id) DO UPDATE SET
        score = excluded.score,
        icebreaker_a_to_b = excluded.icebreaker_a_to_b,
        icebreaker_b_to_a = excluded.icebreaker_b_to_a
    """, (id1, id2, score, icebreaker_a_to_b, icebreaker_b_to_a))
    conn.commit()
    conn.close()

def save_feedback(profile_id, other_id, score, notes=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    id1, id2 = min(profile_id, other_id), max(profile_id, other_id)
    cursor.execute("""
    UPDATE matches
    SET feedback_score = ?, feedback_notes = ?
    WHERE profile_a_id = ? AND profile_b_id = ?
    """, (score, notes, id1, id2))
    conn.commit()
    conn.close()
    return True

def create_meeting(inviter_id, invitee_id, time_slot, venue_location, notes=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO meetings (inviter_id, invitee_id, time_slot, venue_location, status, notes)
    VALUES (?, ?, ?, ?, 'pending', ?)
    """, (inviter_id, invitee_id, time_slot, venue_location, notes))
    meeting_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return meeting_id

def get_meetings(profile_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT m.*, 
           p1.name as inviter_name, p1.company as inviter_company, p1.avatar_url as inviter_avatar,
           p2.name as invitee_name, p2.company as invitee_company, p2.avatar_url as invitee_avatar
    FROM meetings m
    JOIN profiles p1 ON m.inviter_id = p1.id
    JOIN profiles p2 ON m.invitee_id = p2.id
    WHERE m.inviter_id = ? OR m.invitee_id = ?
    """, (profile_id, profile_id))
    meetings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return meetings

def get_meeting(meeting_id):
    """Fetch a single meeting by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT m.*, 
           p1.name as inviter_name, p1.company as inviter_company, p1.avatar_url as inviter_avatar,
           p2.name as invitee_name, p2.company as invitee_company, p2.avatar_url as invitee_avatar
    FROM meetings m
    JOIN profiles p1 ON m.inviter_id = p1.id
    JOIN profiles p2 ON m.invitee_id = p2.id
    WHERE m.id = ?
    """, (meeting_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def respond_meeting(meeting_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE meetings
    SET status = ?
    WHERE id = ?
    """, (status, meeting_id))
    conn.commit()
    conn.close()
    return True

def get_events():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM events
        ORDER BY name
    """)

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]

def join_event(profile_id, event_name, location=""):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM events WHERE name = ?",
        (event_name,)
    )

    event = cursor.fetchone()

    if event:
        event_id = event["id"]
    else:
        cursor.execute(
            """
            INSERT INTO events (name, location)
            VALUES (?, ?)
            """,
            (event_name, location)
        )

    event_id = cursor.lastrowid

    cursor.execute("""
        INSERT OR IGNORE INTO event_members
        (event_id, profile_id)
        VALUES (?, ?)
    """, (event_id, profile_id))

    conn.commit()
    conn.close()

    return event_id
def get_user_events(profile_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.*
        FROM events e
        JOIN event_members em
        ON e.id = em.event_id
        WHERE em.profile_id = ?
    """, (profile_id,))

    events = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return events

def get_profiles_in_event(event_id, exclude_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    if exclude_id:
        cursor.execute("""
            SELECT p.*
            FROM profiles p
            JOIN event_members em
            ON p.id = em.profile_id
            WHERE em.event_id = ?
            AND p.id != ?
        """, (event_id, exclude_id))
    else:
        cursor.execute("""
            SELECT p.*
            FROM profiles p
            JOIN event_members em
            ON p.id = em.profile_id
            WHERE em.event_id = ?
        """, (event_id,))

    profiles = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return profiles

def get_groups():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT g.*, COUNT(gm.profile_id) as member_count, p.name as creator_name
    FROM groups g
    LEFT JOIN group_members gm ON g.id = gm.group_id
    LEFT JOIN profiles p ON g.created_by = p.id
    GROUP BY g.id
    """)
    groups = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return groups

def create_group(name, topic, description, created_by):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO groups (name, topic, description, created_by)
    VALUES (?, ?, ?, ?)
    """, (name, topic, description, created_by))
    group_id = cursor.lastrowid
    # Creator automatically joins
    cursor.execute("""
    INSERT OR IGNORE INTO group_members (group_id, profile_id)
    VALUES (?, ?)
    """, (group_id, created_by))
    conn.commit()
    conn.close()
    return group_id

def join_group(group_id, profile_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO group_members (group_id, profile_id)
    VALUES (?, ?)
    """, (group_id, profile_id))
    conn.commit()
    conn.close()
    return True

def leave_group(group_id, profile_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    DELETE FROM group_members
    WHERE group_id = ? AND profile_id = ?
    """, (group_id, profile_id))
    conn.commit()
    conn.close()
    return True

def get_group_members(group_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.*
    FROM group_members gm
    JOIN profiles p ON gm.profile_id = p.id
    WHERE gm.group_id = ?
    """, (group_id,))
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return members

def get_user_groups(profile_id):
    """Return list of group IDs that a profile belongs to."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT group_id FROM group_members WHERE profile_id = ?
    """, (profile_id,))
    group_ids = [row['group_id'] for row in cursor.fetchall()]
    conn.close()
    return group_ids

def get_messages(user_id, other_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM messages 
    WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
    ORDER BY timestamp ASC
    """, (user_id, other_id, other_id, user_id))
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

def save_message(sender_id, receiver_id, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO messages (sender_id, receiver_id, message)
    VALUES (?, ?, ?)
    """, (sender_id, receiver_id, message))
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def export_profiles_csv():
    """Export all profiles to a CSV file for persistent storage."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, company, job_title, bio, interests, tech_needs, looking_for, avatar_url FROM profiles")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return
    
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'email', 'company', 'job_title', 'bio', 'interests', 'tech_needs', 'looking_for', 'avatar_url'])
        for row in rows:
            writer.writerow([row['id'], row['name'], row['email'], row['company'], row['job_title'],
                           row['bio'], row['interests'], row['tech_needs'], row['looking_for'], row['avatar_url']])

# Automatically initialize DB when module is imported or run directly
init_db()


