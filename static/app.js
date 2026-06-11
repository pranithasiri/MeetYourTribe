// Global Application State
const state = {
    currentUserId: null,
    currentUserProfile: null,
    allProfiles: [],
    matches: [],
    meetings: [],
    groups: [],
    userGroupIds: [],
    activeTab: 'matches'
};

// API Endpoint Wrapper
const API = {
    async getSession() {
        const res = await fetch('/api/session');
        return res.json();
    },
    async getProfiles(activeOnly = false) {
        const res = await fetch(`/api/profiles${activeOnly ? '?active=true' : ''}`);
        return res.json();
    },
    async getProfile(userId) {
        const res = await fetch(`/api/profiles/${userId}`);
        return res.json();
    },
    async saveProfile(profileData, userId = null) {
        const url = userId ? `/api/profiles/${userId}` : '/api/profiles';
        const method = userId ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });
        return res.json();
    },
    async actAs(profileId) {
        const res = await fetch(`/api/act-as/${profileId}`, {
            method: 'POST'
        });
        return res.json();
    },
    async getMatches(userId, eventId = null) {
        let url = `/api/profiles/${userId}/matches`;
        if (eventId) url += `?event_id=${eventId}`;
        const res = await fetch(url);
        return res.json();
    },
    async submitFeedback(feedbackData) {
        const res = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(feedbackData)
        });
        return res.json();
    },
    async scheduleMeeting(meetingData) {
        const res = await fetch('/api/meetings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(meetingData)
        });
        return res.json();
    },
    async getMeetings(userId) {
        const res = await fetch(`/api/meetings/${userId}`);
        return res.json();
    },
    async respondMeeting(meetingId, status) {
        const res = await fetch(`/api/meetings/${meetingId}/respond`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        return res.json();
    },
    async getGroups() {
        const res = await fetch('/api/groups');
        return res.json();
    },
    async getGroupSuggestions(userId) {
        const res = await fetch(`/api/profiles/${userId}/group-suggestions`);
        return res.json();
    },
    async createGroup(groupData) {
        const res = await fetch('/api/groups', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(groupData)
        });
        return res.json();
    },
    async joinGroup(groupId, userId) {
        const res = await fetch(`/api/groups/${groupId}/join`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_id: userId })
        });
        return res.json();
    },
    async leaveGroup(groupId, userId) {
        const res = await fetch(`/api/groups/${groupId}/leave`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_id: userId })
        });
        return res.json();
    },
    async getUserGroups(userId) {
        const res = await fetch(`/api/profiles/${userId}/groups`);
        return res.json();
    },
    async generateFollowup(fromId, toId, meetingId) {
        const res = await fetch('/api/followup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                profile_from_id: fromId,
                profile_to_id: toId,
                meeting_id: meetingId
            })
        });
        return res.json();
    }
};

// Toast Notification Helper
function showToast(message, type = 'info') {
    const toast = document.getElementById('notification-toast');
    toast.textContent = message;
    toast.className = `toast active ${type}`;
    
    // Create check or cross icon based on type
    const icon = type === 'success' ? '✓ ' : type === 'error' ? '⚠ ' : 'ℹ ';
    toast.innerHTML = `<span style="margin-right: 0.5rem; font-weight: 700;">${icon}</span> ${message}`;

    setTimeout(() => {
        toast.classList.remove('active');
    }, 4000);
}

// Helper to create badges from comma-separated string
function renderBadges(containerId, csvString, classes = 'tag') {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    if (!csvString) {
        container.innerHTML = '<span class="text-muted">None specified</span>';
        return;
    }
    
    const items = csvString.split(',').map(i => i.trim()).filter(Boolean);
    items.forEach(item => {
        const span = document.createElement('span');
        span.className = classes;
        span.textContent = item;
        container.appendChild(span);
    });
}

// Modal Helpers
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function openJoinEventModal() {
    openModal('event-modal');
}
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// ==========================================================================
// CORE DATA CONTROLLERS & RENDERING
// ==========================================================================

// 1. Initialize session
async function initSession() {
    try {
        const sessionData = await API.getSession();
        state.currentUserId = sessionData.current_user_id;
        
        await refreshUserData();
    } catch (err) {
        showToast('Error connecting to backend database server', 'error');
        console.error(err);
    }
}

// Refresh currently acted user data
async function refreshUserData() {
    try {
        state.currentUserProfile = await API.getProfile(state.currentUserId);
        
        // Update user panel in sidebar
        document.getElementById('user-name').textContent = state.currentUserProfile.name;
        document.getElementById('user-title').textContent = state.currentUserProfile.job_title;
        document.getElementById('user-company').textContent = state.currentUserProfile.company;
        document.getElementById('user-bio').textContent = `"${state.currentUserProfile.bio}"`;
        document.getElementById('user-avatar').src = state.currentUserProfile.avatar_url;
        
        renderBadges('user-interests-tags', state.currentUserProfile.interests);
        renderBadges('user-needs-tags', state.currentUserProfile.tech_needs, 'tag');
        
        // No dropdown switcher to update
        
        // Trigger parallel reloads of active tab content
        await loadEvents();
        await loadSidebarMeetings();
        await refreshActiveTab();
    } catch (err) {
        showToast('Failed to load profile data', 'error');
    }
}


async function loadEvents() {

    const response = await fetch('/api/events');

    const events = await response.json();

    const select =
        document.getElementById('eventSelect');

    select.innerHTML = '';

    events.forEach(event => {

        const option =
            document.createElement('option');

        option.value = event.id;
        option.textContent =
    `${event.name} — ${event.location || 'Location TBD'}`;  

        select.appendChild(option);
    });

    const addOption =
        document.createElement('option');

    addOption.value = 'new_event';
    addOption.textContent = '+ My Event Is Not Listed';

    select.appendChild(addOption);
}
// Load meeting list in the sidebar
async function loadSidebarMeetings() {
    const list = document.getElementById('meetings-list');
    const countBadge = document.getElementById('meetings-count');
    
    state.meetings = await API.getMeetings(state.currentUserId);
    countBadge.textContent = state.meetings.length;
    
    if (state.meetings.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <p>No meetings scheduled yet.</p>
            </div>
        `;
        return;
    }
    
    list.innerHTML = '';
    state.meetings.forEach(m => {
        const isInviter = m.inviter_id === state.currentUserId;
        const otherName = isInviter ? m.invitee_name : m.inviter_name;
        const otherCompany = isInviter ? m.invitee_company : m.inviter_company;
        const otherAvatar = isInviter ? m.invitee_avatar : m.inviter_avatar;
        
        const item = document.createElement('div');
        item.className = `meeting-item status-${m.status}`;
        
        const acceptDeclineBtns = (!isInviter && m.status === 'pending') ? `
            <div class="meeting-actions">
                <button class="btn btn-primary btn-accept" data-id="${m.id}">Accept</button>
                <button class="btn btn-secondary btn-decline" data-id="${m.id}">Decline</button>
            </div>
        ` : '';
        
        item.innerHTML = `
            <div class="meeting-status-label">${m.status}</div>
            <div class="meeting-time-badge">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                ${m.time_slot}
            </div>
            <div class="meeting-item-header">
                <img class="meeting-avatar" src="${otherAvatar}" alt="${otherName}">
                <div class="meeting-user-info">
                    <h4>${otherName}</h4>
                    <p>${otherCompany}</p>
                </div>
            </div>
            <div class="meeting-location">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                </svg>
                ${m.venue_location}
            </div>
            ${m.notes ? `<p class="bio-text" style="font-size: 0.75rem; margin-top: 0.35rem;">"${m.notes}"</p>` : ''}
            ${acceptDeclineBtns}
        `;
        
        list.appendChild(item);
    });
}

async function joinSelectedEvent() {

    const select =
        document.getElementById('eventSelect');

    if (select.value === 'new_event') {
        openModal('event-modal');
        return;
    }

    const eventId = select.value;
    // Extract just the event name (before the " — " separator)
    const fullText = select.options[select.selectedIndex].text;
    const eventName = fullText.split(' \u2014 ')[0].trim();

    const response =
        await fetch('/api/events/join', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                profile_id: state.currentUserId,
                event_name: eventName
            })
        });

    const result =
        await response.json();

    console.log(result);

    showToast(
        `Joined ${eventName}`,
        'success'
    );

    // Reload matches filtered to this event
    await loadSmartMatches();
}

async function createNewEvent() {

    const eventName =
        document.getElementById(
            'newEventName'
        ).value;
    const location =
    document.getElementById(
        'newEventLocation'
    ).value;
    if (!eventName.trim()) {
        return;
    }

    await fetch('/api/events/join', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            profile_id: state.currentUserId,
            event_name: eventName,
            location: location
        })
    });

    await loadEvents();

    const select =
        document.getElementById('eventSelect');

    // Select the newly created event in the dropdown
    for (let i = 0; i < select.options.length; i++) {
        // Match by event name prefix (before the " — " separator)
        const optText = select.options[i].text;
        if (optText.split(' \u2014 ')[0].trim() === eventName.trim()) {
            select.selectedIndex = i;
            break;
        }
    }

    document.getElementById('newEventName').value = '';
    document.getElementById('newEventLocation').value = '';
    closeModal('event-modal');

    showToast(
        'Event added successfully!',
        'success'
    );
}


// Refresh the current tab data
async function refreshActiveTab() {
    const tabPanes = document.querySelectorAll('.tab-pane');
    tabPanes.forEach(pane => pane.classList.remove('active'));
    
    const activePane = document.getElementById(`tab-${state.activeTab}`);
    activePane.classList.add('active');
    
    if (state.activeTab === 'matches') {
        await loadSmartMatches();
    } else if (state.activeTab === 'groups') {
        await loadGroups();
    } else if (state.activeTab === 'followup') {
        await loadFollowUpHub();
    }
}

// 2. Tab Content Loader: Smart Matches
async function loadSmartMatches() {
    const grid = document.getElementById('matches-grid');
    grid.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p>Analyzing profiles and calculating similarity scores...</p>
        </div>
    `;
    
    try {
        // Get the currently selected event from dropdown
        const eventSelect = document.getElementById('eventSelect');
        const selectedEventId = (eventSelect && eventSelect.value && eventSelect.value !== 'new_event')
            ? parseInt(eventSelect.value)
            : null;

        state.matches = await API.getMatches(state.currentUserId, selectedEventId);
        
        if (state.matches.length === 0) {
            const emptyMsg = selectedEventId
                ? `<h3>No other attendees in this event yet</h3>
                   <p>Be the first! Invite more people to join this event to see smart matches.</p>`
                : `<h3>Join an event to see matches</h3>
                   <p>Select an event from the dropdown above and click "Join Selected Event" to find people attending the same event.</p>`;
            grid.innerHTML = `<div class="empty-state">${emptyMsg}</div>`;
            return;
        }
        
        grid.innerHTML = '';
        state.matches.forEach(m => {
            const prof = m.profile;
            const card = document.createElement('article');
            card.className = 'match-card';
            
            // Calculate Dash Offset for similarity circle
            // Circle circumference = 2 * PI * r = 2 * 3.14159 * 32 = ~201
            const scoreVal = m.match_score;
            const radius = 32;
            const circum = 2 * Math.PI * radius;
            const offset = circum - (scoreVal / 100) * circum;
            
            // Find intersection details for display
            const myInterests = state.currentUserProfile.interests.split(',').map(x => x.trim().toLowerCase());
            const otherInterests = prof.interests.split(',').map(x => x.trim().toLowerCase());
            const matchedInterests = myInterests.filter(x => otherInterests.includes(x)).map(x => {
                // Return styled word
                return prof.interests.split(',').map(t => t.trim()).find(t => t.toLowerCase() === x) || x;
            });
            
            const synergyHTML = matchedInterests.length > 0 ? `
                <div class="match-synergies">
                    <div class="synergy-row">
                        <span class="synergy-label">Common Focus</span>
                        <div class="synergy-values">
                            ${matchedInterests.map(val => `<span class="tag" style="border-color: rgba(139, 92, 246, 0.3); color:#c084fc; background:rgba(139, 92, 246, 0.08);">${val}</span>`).join('')}
                        </div>
                    </div>
                </div>
            ` : `
                <div class="match-synergies">
                    <div class="synergy-row">
                        <span class="synergy-label">Synergy</span>
                        <span class="text-secondary" style="font-size: 0.8rem;">Complementary technological alignment</span>
                    </div>
                </div>
            `;

            // Star rating display logic
            let starRatingHTML = '';
            if (m.feedback_score !== null) {
                starRatingHTML = `
                    <div class="feedback-submitted-badge">
                        <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                        </svg>
                        Rated ${m.feedback_score}/5
                    </div>
                `;
            } else {
                starRatingHTML = `
                    <span class="feedback-label">Rate match quality:</span>
                    <div class="feedback-stars" data-other-id="${prof.id}">
                        <button class="star-btn" data-star="1" aria-label="1 Star">★</button>
                        <button class="star-btn" data-star="2" aria-label="2 Stars">★</button>
                        <button class="star-btn" data-star="3" aria-label="3 Stars">★</button>
                        <button class="star-btn" data-star="4" aria-label="4 Stars">★</button>
                        <button class="star-btn" data-star="5" aria-label="5 Stars">★</button>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="match-card-main">
                    <!-- CIRCLE CHART -->
                    <div class="match-score-circle">
                        <svg class="match-score-svg" viewBox="0 0 76 76">
                            <circle class="match-score-track" cx="38" cy="38" r="${radius}"></circle>
                            <circle class="match-score-fill" cx="38" cy="38" r="${radius}" 
                                    style="stroke-dasharray: ${circum}; stroke-dashoffset: ${offset};"></circle>
                        </svg>
                        <div class="match-score-text">
                            <span class="match-score-num">${scoreVal}%</span>
                            <span class="match-score-label">Match</span>
                        </div>
                    </div>
                    
                    <!-- USER DETAILS -->
                    <div class="match-details-box">
                        <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom: 0.25rem;">
                            <img class="match-avatar" src="${prof.avatar_url}" alt="${prof.name}" style="width: 44px; height: 44px;">
                            <div>
                                <h3>${prof.name}</h3>
                                <p class="matching-job">${prof.job_title} at <span class="company-tag">${prof.company}</span></p>
                            </div>
                        </div>
                        <p class="matching-bio">"${prof.bio}"</p>
                        ${synergyHTML}
                    </div>
                    
                    <!-- ACTIONS -->
                    <div class="match-actions-box">
                        <button class="btn btn-primary btn-schedule-meeting" data-id="${prof.id}" data-name="${prof.name}" data-job="${prof.job_title} at ${prof.company}" data-avatar="${prof.avatar_url}">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                <line x1="3" y1="10" x2="21" y2="10"></line>
                            </svg>
                            Meet
                        </button>
                        <button class="btn btn-secondary btn-toggle-icebreaker" data-id="${prof.id}">
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                            </svg>
                            AI Icebreaker
                        </button>
                    </div>
                </div>
                
                <!-- ICEBREAKER DRAWER -->
                <div id="icebreaker-drawer-${prof.id}" class="icebreaker-drawer" style="display: none;">
                    <div class="icebreaker-header">
                        <div class="icebreaker-title">
                            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3">
                                <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                                <polyline points="2 17 12 22 22 17"></polyline>
                                <polyline points="2 12 12 17 22 12"></polyline>
                            </svg>
                            Suggested AI Icebreaker Starter
                        </div>
                        <button class="btn-text btn-copy-icebreaker" data-text="${encodeURIComponent(m.icebreaker)}" style="font-size:0.75rem; padding:0;">
                            Copy Message
                        </button>
                    </div>
                    <p class="icebreaker-msg">${m.icebreaker}</p>
                </div>
                
                <!-- FEEDBACK LOOP -->
                <div class="feedback-box">
                    ${starRatingHTML}
                </div>
            `;
            
            grid.appendChild(card);
        });
        
    } catch (err) {
        grid.innerHTML = `<div class="empty-state"><p>Error generating matches. Please refresh the page.</p></div>`;
    }
}



// 3. Tab Content Loader: Groups
async function loadGroups() {
    const recommendedList = document.getElementById('recommended-groups-list');
    const allList = document.getElementById('all-groups-list');
    
    recommendedList.innerHTML = `<div class="spinner" style="margin: 2rem auto;"></div>`;
    allList.innerHTML = `<div class="spinner" style="margin: 2rem auto;"></div>`;
    
    try {
        // Fetch user's current group memberships
        state.userGroupIds = await API.getUserGroups(state.currentUserId);
        
        const recommendations = await API.getGroupSuggestions(state.currentUserId);
        const allGroups = await API.getGroups();
        
        // Load Recommended
        recommendedList.innerHTML = '';
        if (recommendations.length === 0) {
            recommendedList.innerHTML = '<p class="text-muted">No custom recommendations. Populate interests to matching groups.</p>';
        } else {
            // Pick top 2 suggested groups
            recommendations.slice(0, 2).forEach(g => {
                recommendedList.appendChild(createGroupCard(g, true));
            });
        }
        
        // Load All Groups
        allList.innerHTML = '';
        if (allGroups.length === 0) {
            allList.innerHTML = '<p class="text-muted">No groups created yet. Be the first to start a group!</p>';
        } else {
            allGroups.forEach(g => {
                allList.appendChild(createGroupCard(g, false));
            });
        }
        
    } catch (err) {
        recommendedList.innerHTML = '<p class="text-muted">Error loading groups</p>';
        allList.innerHTML = '<p class="text-muted">Error loading groups</p>';
    }
}

function createGroupCard(group, isRecommended = false) {
    const card = document.createElement('div');
    card.className = 'group-card';
    if (isRecommended) {
        card.style.borderColor = 'var(--accent-secondary)';
        card.style.backgroundImage = 'linear-gradient(180deg, rgba(6, 182, 212, 0.05) 0%, rgba(0, 0, 0, 0) 100%)';
    }
    
    // Check if current user is inside this group
    const isJoined = state.userGroupIds.includes(group.id);
    
    const buttonHTML = isJoined
        ? `<button class="btn btn-secondary btn-leave-group" data-id="${group.id}">Leave Group Circle</button>`
        : `<button class="btn btn-secondary btn-join-group" data-id="${group.id}">Join Group Circle</button>`;
    
    card.innerHTML = `
        <div class="group-card-header">
            <h4>${group.name}</h4>
            <div class="group-member-count">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                </svg>
                ${group.member_count} joined
            </div>
        </div>
        <p class="group-topic-label">Topic: ${group.topic}</p>
        <p class="group-desc">${group.description}</p>
        <p class="group-creator">Created by: ${group.creator_name || 'System'}</p>
        ${buttonHTML}
    `;
    
    return card;
}

// 4. Tab Content Loader: Follow-up Hub
async function loadFollowUpHub() {
    const list = document.getElementById('followup-list');
    list.innerHTML = `<div class="spinner" style="margin: 2rem auto;"></div>`;
    
    try {
        state.meetings = await API.getMeetings(state.currentUserId);
        
        // Filter meetings to only display scheduled/accepted ones
        const connectedMeetings = state.meetings.filter(m => m.status === 'accepted');
        
        if (connectedMeetings.length === 0) {
            list.innerHTML = `
                <div class="empty-state" style="background: var(--bg-surface); border: 1px solid var(--border-color); border-radius:14px; padding: 3rem 1.5rem;">
                    <h3>No confirmed connections found</h3>
                    <p>Once you schedule a meeting and it is marked as <strong>accepted</strong>, you can generate personalized follow-up email drafts here.</p>
                </div>
            `;
            return;
        }
        
        list.innerHTML = '';
        connectedMeetings.forEach(m => {
            const isInviter = m.inviter_id === state.currentUserId;
            const otherId = isInviter ? m.invitee_id : m.inviter_id;
            const otherName = isInviter ? m.invitee_name : m.inviter_name;
            const otherCompany = isInviter ? m.invitee_company : m.inviter_company;
            
            const card = document.createElement('div');
            card.className = 'followup-card';
            card.id = `followup-card-${m.id}`;
            
            card.innerHTML = `
                <div class="followup-card-header">
                    <div class="followup-user-info">
                        <div class="followup-user-details">
                            <h3>Connect with ${otherName}</h3>
                            <p>${otherCompany}</p>
                        </div>
                    </div>
                    <div class="followup-meeting-meta">
                        Met at: <strong>${m.venue_location}</strong> (${m.time_slot})
                    </div>
                    <button class="btn btn-primary btn-trigger-followup" data-meeting-id="${m.id}" data-other-id="${otherId}">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5">
                            <polygon points="12 2 2 22 12 17 22 22 12 2"></polygon>
                        </svg>
                        Draft AI Follow-up
                    </button>
                </div>
                <div id="followup-draft-container-${m.id}" style="display: none;"></div>
            `;
            
            list.appendChild(card);
        });
        
    } catch (err) {
        list.innerHTML = '<p class="text-muted">Error loading follow-up sessions</p>';
    }
}

// Renders the follow-up draft inside its container
function renderFollowUpDraft(meetingId, draftText) {
    const container = document.getElementById(`followup-draft-container-${meetingId}`);
    container.innerHTML = `
        <div class="followup-draft-area">
            <div class="followup-actions">
                <button class="btn btn-secondary btn-copy-followup" data-text="${encodeURIComponent(draftText)}">
                    Copy to Clipboard
                </button>
            </div>
            <textarea class="followup-textarea" rows="12">${draftText}</textarea>
        </div>
    `;
    container.style.display = 'block';
}

// ==========================================================================
// INTERACTIVE EVENT LISTENERS & TRIGGERS
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
     
    document
    .getElementById('eventSelect')
    .addEventListener('change', async function () {

        if (this.value === 'new_event') {

            document.getElementById('newEventName').value = '';
            document.getElementById('newEventLocation').value = '';

            openModal('event-modal');
        } else if (state.activeTab === 'matches') {
            // Reload matches for the newly selected event
            await loadSmartMatches();
        }
    });
    // 2. Tab Navigation clicks
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
            const target = e.currentTarget;
            target.classList.add('active');
            state.activeTab = target.dataset.tab;
            await refreshActiveTab();
        });
    });

    // 3. Close Modals Click Handler
    document.querySelectorAll('[data-close]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            closeModal(e.target.dataset.close);
        });
    });
    
    // Close on background modal overlay click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });

    // 4. Edit Profile Button Click
    document.getElementById('btn-edit-profile').addEventListener('click', () => {
        const prof = state.currentUserProfile;
        document.getElementById('profile-modal-title').textContent = 'Edit Profile';
        document.getElementById('form-profile-id').value = prof.id;
        document.getElementById('form-name').value = prof.name;
        document.getElementById('form-company').value = prof.company;
        document.getElementById('form-title').value = prof.job_title;
        document.getElementById('form-bio').value = prof.bio;
        document.getElementById('form-interests').value = prof.interests;
        document.getElementById('form-needs').value = prof.tech_needs;
        document.getElementById('form-looking').value = prof.looking_for;
        
        openModal('profile-modal');
    });

    // 6. Submit Profile Form Handler (New/Edit)
    document.getElementById('profile-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const profileId = document.getElementById('form-profile-id').value;
        const profileData = {
            name: document.getElementById('form-name').value,
            company: document.getElementById('form-company').value,
            job_title: document.getElementById('form-title').value,
            bio: document.getElementById('form-bio').value,
            interests: document.getElementById('form-interests').value,
            tech_needs: document.getElementById('form-needs').value,
            looking_for: document.getElementById('form-looking').value
        };
        
        try {
            if (profileId) {
                // Update
                await API.saveProfile(profileData, profileId);
                showToast('Profile updated successfully!', 'success');
            } else {
                // Create
                const res = await API.saveProfile(profileData);
                state.currentUserId = res.profile_id;
                showToast('Profile created successfully!', 'success');
            }
            
            closeModal('profile-modal');
            await refreshUserData();
        } catch (err) {
            showToast('Failed to save profile. Make sure fields are filled.', 'error');
        }
    });

    // 7. Click Delegation for matches and schedules inside containers
    
    // Toggle Icebreaker Starter Drawer
    document.getElementById('matches-grid').addEventListener('click', (e) => {
        const toggleBtn = e.target.closest('.btn-toggle-icebreaker');
        if (toggleBtn) {
            const otherId = toggleBtn.dataset.id;
            const drawer = document.getElementById(`icebreaker-drawer-${otherId}`);
            if (drawer.style.display === 'none') {
                drawer.style.display = 'block';
            } else {
                drawer.style.display = 'none';
            }
        }
    });
    
    // Copy Icebreaker to clipboard
    document.getElementById('matches-grid').addEventListener('click', (e) => {
        const copyBtn = e.target.closest('.btn-copy-icebreaker');
        if (copyBtn) {
            const rawMsg = decodeURIComponent(copyBtn.dataset.text);
            navigator.clipboard.writeText(rawMsg);
            showToast('Icebreaker copied to clipboard!', 'success');
        }
    });

    // Open Schedule Meeting Modal
    document.getElementById('matches-grid').addEventListener('click', (e) => {
        const scheduleBtn = e.target.closest('.btn-schedule-meeting');
        if (scheduleBtn) {
            const id = scheduleBtn.dataset.id;
            const name = scheduleBtn.dataset.name;
            const job = scheduleBtn.dataset.job;
            const avatar = scheduleBtn.dataset.avatar;
            
            document.getElementById('schedule-invitee-id').value = id;
            document.getElementById('schedule-invitee-avatar').src = avatar;
            document.getElementById('schedule-invitee-name').textContent = name;
            document.getElementById('schedule-invitee-job').textContent = job;
            document.getElementById('schedule-notes').value = '';
            
            openModal('schedule-modal');
        }
    });

    // Submit Schedule Meeting Form
    document.getElementById('schedule-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const inviteeId = parseInt(document.getElementById('schedule-invitee-id').value);
        const meetingData = {
            inviter_id: state.currentUserId,
            invitee_id: inviteeId,
            time_slot: document.getElementById('schedule-time').value,
            venue_location: document.getElementById('schedule-location').value,
            notes: document.getElementById('schedule-notes').value
        };
        
        try {
            await API.scheduleMeeting(meetingData);
            showToast('Meeting invitation sent successfully!', 'success');
            closeModal('schedule-modal');
            await loadSidebarMeetings();
        } catch (err) {
            showToast('Could not schedule meeting.', 'error');
        }
    });

    // Respond to Meeting Invitations (Accept/Decline in sidebar)
    document.getElementById('meetings-list').addEventListener('click', async (e) => {
        const acceptBtn = e.target.closest('.btn-accept');
        const declineBtn = e.target.closest('.btn-decline');
        
        if (acceptBtn) {
            const id = acceptBtn.dataset.id;
            await API.respondMeeting(id, 'accepted');
            showToast('Meeting invitation accepted!', 'success');
            await loadSidebarMeetings();
            if (state.activeTab === 'followup') {
                await loadFollowUpHub();
            }
        } else if (declineBtn) {
            const id = declineBtn.dataset.id;
            await API.respondMeeting(id, 'declined');
            showToast('Meeting invitation declined.', 'info');
            await loadSidebarMeetings();
        }
    });

    // Feedback Rating Interaction (Star rating system)
    document.getElementById('matches-grid').addEventListener('click', async (e) => {
        const starBtn = e.target.closest('.star-btn');
        if (starBtn) {
            const parent = starBtn.closest('.feedback-stars');
            const otherId = parseInt(parent.getAttribute('data-other-id'));
            const score = parseInt(starBtn.dataset.star);
            
            try {
                await API.submitFeedback({
                    profile_id: state.currentUserId,
                    other_id: otherId,
                    score: score,
                    notes: `Rated match quality ${score}/5 stars`
                });
                
                showToast(`Feedback saved! Ranking weights updated.`, 'success');
                // Re-evaluate matches to show feedback score status and update alignment
                await loadSmartMatches();
            } catch (err) {
                showToast('Failed to record feedback rating', 'error');
            }
        }
    });

    // 8. Topic-based Groups Actions

    // Open Group Modal
    document.getElementById('btn-create-group').addEventListener('click', () => {
        document.getElementById('group-form').reset();
        openModal('group-modal');
    });

    // Submit Group Form
    document.getElementById('group-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const groupData = {
            name: document.getElementById('group-name').value,
            topic: document.getElementById('group-topic').value,
            description: document.getElementById('group-desc').value,
            created_by: state.currentUserId
        };
        
        try {
            await API.createGroup(groupData);
            showToast('Group circle created successfully!', 'success');
            closeModal('group-modal');
            await loadGroups();
        } catch (err) {
            showToast('Failed to create group', 'error');
        }
    });

    // Join Group Click Handler
    document.getElementById('tab-groups').addEventListener('click', async (e) => {
        const joinBtn = e.target.closest('.btn-join-group');
        if (joinBtn) {
            const groupId = parseInt(joinBtn.dataset.id);
            try {
                await API.joinGroup(groupId, state.currentUserId);
                showToast('Successfully joined group circle!', 'success');
                
                // Reload groups to get updated member count and button state
                await loadGroups();
            } catch (err) {
                showToast('Failed to join group', 'error');
            }
        }
    });

    // Leave Group Click Handler
    document.getElementById('tab-groups').addEventListener('click', async (e) => {
        const leaveBtn = e.target.closest('.btn-leave-group');
        if (leaveBtn) {
            const groupId = parseInt(leaveBtn.dataset.id);
            try {
                await API.leaveGroup(groupId, state.currentUserId);
                showToast('Left group circle.', 'info');
                
                // Reload groups to get updated member count and button state
                await loadGroups();
            } catch (err) {
                showToast('Failed to leave group', 'error');
            }
        }
    });

    // 9. Follow-up Hub Actions

    // Generate Follow-up Click Handler
    document.getElementById('followup-list').addEventListener('click', async (e) => {
        const draftBtn = e.target.closest('.btn-trigger-followup');
        if (draftBtn) {
            const meetingId = parseInt(draftBtn.dataset.meetingId);
            const otherId = parseInt(draftBtn.dataset.otherId);
            
            // Set loading text
            draftBtn.disabled = true;
            draftBtn.textContent = 'Drafting email...';
            
            try {
                const res = await API.generateFollowup(state.currentUserId, otherId, meetingId);
                renderFollowUpDraft(meetingId, res.followup_email);
                
                draftBtn.textContent = 'Re-draft Email';
                draftBtn.disabled = false;
            } catch (err) {
                showToast('Error drafting follow-up email', 'error');
                draftBtn.disabled = false;
                draftBtn.textContent = 'Draft AI Follow-up';
            }
        }
    });

    // Copy follow-up draft to clipboard
    document.getElementById('followup-list').addEventListener('click', (e) => {
        const copyBtn = e.target.closest('.btn-copy-followup');
        if (copyBtn) {
            const rawEmail = decodeURIComponent(copyBtn.dataset.text);
            navigator.clipboard.writeText(rawEmail);
            showToast('Follow-up email copied to clipboard!', 'success');
        }
    });

    // Trigger initial load
    initSession();
});
