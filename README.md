# MeetYourTribe 🤝

**AI-Powered Conference Networking Hub**

MeetYourTribe is an intelligent event networking platform that uses AI-driven matching algorithms to connect conference attendees based on shared interests, technology needs, and professional synergy. It features smart profile matching, real-time meeting scheduling, topic-based networking groups, and AI-generated icebreakers and follow-up emails.

---

## ✨ Features

- **Smart Matching** — TF-IDF cosine similarity engine ranks attendees by interests, tech needs, and bio alignment. Matches are scoped to the event you've joined.
- **Event Management** — Create or join events from a dropdown. Matches are filtered to show only people attending the same event.
- **AI Icebreakers** — Auto-generated personalized conversation starters powered by Google Gemini (falls back to a template engine if no API key is set).
- **Meeting Scheduler** — Send and accept/decline meeting invitations with time slots and venue locations.
- **Feedback Loop** — Rate match quality (1–5 stars). Ratings dynamically adjust matching weights for future recommendations.
- **Networking Groups** — Create or join topic-based discussion circles. Groups are recommended based on profile interests.
- **Follow-up Hub** — Generate professional post-event follow-up email drafts for confirmed connections.
- **Cookie-based Multi-session** — Multiple users can be logged in simultaneously across different browser windows/incognito tabs.

---

## 🛠️ Tech Stack

| Layer      | Technology                                                 |
| ---------- | ---------------------------------------------------------- |
| Backend    | [FastAPI](https://fastapi.tiangolo.com/) (Python)          |
| Frontend   | Vanilla HTML / CSS / JavaScript                            |
| Database   | SQLite (`conference.db`, auto-created on first run)        |
| AI Engine  | [Google Gemini](https://ai.google.dev/) (optional)         |
| Matching   | Custom TF-IDF + Cosine Similarity (pure Python, no sklearn)|
| Server     | [Uvicorn](https://www.uvicorn.org/) ASGI server            |

---

## 📁 Project Structure

```
MeetYourTribe/
├── main.py              # FastAPI app — routes, models, API endpoints
├── database.py          # SQLite schema, CRUD operations, seed data
├── matcher.py           # TF-IDF matching engine, icebreaker & follow-up generation
├── requirements.txt     # Python dependencies
├── conference.db        # SQLite database (auto-created on first run)
├── profiles_data.csv    # Auto-exported CSV of all profiles
├── static/
│   ├── index.html       # Main dashboard UI
│   ├── landing.html     # Landing / home page
│   ├── login.html       # Login page
│   ├── signup.html      # Sign-up page
│   ├── app.js           # Frontend logic — API calls, rendering, event handlers
│   ├── css/
│   │   ├── style.css    # Dashboard styles (dark theme, glassmorphism)
│   │   ├── auth.css     # Login & signup page styles
│   │   └── landing.css  # Landing page styles
│   └── assets/
│       ├── logo.png     # App logo
│       └── hero.png     # Landing page hero image
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+ recommended

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/MeetYourTribe.git
cd MeetYourTribe

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
python main.py
```

The server starts at **http://127.0.0.1:8000**.

| URL              | Description             |
| ---------------- | ----------------------- |
| `/`              | Landing page            |
| `/signup`        | Create a new account    |
| `/login`         | Login to existing account|
| `/dashboard`     | Main app dashboard      |

> The database (`conference.db`) is auto-created with 8 seed profiles on the first run. Delete the file and restart to reset all data.

### (Optional) Enable AI-Powered Features

Set a Google Gemini API key to unlock AI-generated icebreakers and follow-up emails:

```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# macOS/Linux
export GEMINI_API_KEY=your_api_key_here
```

Without the key, the app uses high-quality template-based generators as a fallback.

---

## 📖 How to Use

### 1. Sign Up & Login
Create an account with your name, company, job title, bio, interests, tech needs, and what you're looking for. Login from a different browser/incognito window to simulate another user.

### 2. Join an Event
From the dashboard header, either:
- **Select an existing event** from the dropdown and click **"Join Selected Event"**
- **Select "+ My Event Is Not Listed"** to create a new event with a name and location

### 3. View Smart Matches
The **Smart Matches** tab shows AI-ranked attendees from your current event. Each match card displays:
- Match percentage (TF-IDF similarity score)
- Common focus areas
- Action buttons to schedule a meeting or view AI icebreakers

### 4. Schedule Meetings
Click **"Meet"** on a match card to send a meeting invitation with a time slot and venue.

### 5. Rate Matches
Use the star rating system on match cards. Ratings feed back into the matching algorithm to improve future recommendations.

### 6. Networking Groups
Switch to the **Networking Groups** tab to create or join topic-based circles. Groups are recommended based on your profile's interests.

### 7. Follow-up Hub
After a meeting is **accepted**, the **Follow-up Hub** tab lets you generate a personalized post-event email draft.

---

## 🔌 API Reference

### Authentication
| Method | Endpoint            | Description          |
| ------ | ------------------- | -------------------- |
| POST   | `/api/signup`       | Create new account   |
| POST   | `/api/login`        | Login (sets cookie)  |
| POST   | `/api/logout`       | Logout (clears cookie)|
| GET    | `/api/session`      | Get current user ID  |

### Events
| Method | Endpoint            | Description                    |
| ------ | ------------------- | ------------------------------ |
| GET    | `/api/events`       | List all events                |
| POST   | `/api/events/join`  | Join/create an event           |

### Profiles
| Method | Endpoint                              | Description                          |
| ------ | ------------------------------------- | ------------------------------------ |
| GET    | `/api/profiles`                       | List all profiles                    |
| GET    | `/api/profiles/{id}`                  | Get a single profile                 |
| POST   | `/api/profiles`                       | Create a profile                     |
| PUT    | `/api/profiles/{id}`                  | Update a profile                     |
| GET    | `/api/profiles/{id}/matches?event_id=`| Get smart matches (filtered by event)|
| GET    | `/api/profiles/{id}/groups`           | Get groups the user belongs to       |
| GET    | `/api/profiles/{id}/group-suggestions`| AI-recommended groups                |

### Meetings
| Method | Endpoint                          | Description              |
| ------ | --------------------------------- | ------------------------ |
| POST   | `/api/meetings`                   | Schedule a meeting       |
| GET    | `/api/meetings/{profile_id}`      | Get user's meetings      |
| POST   | `/api/meetings/{id}/respond`      | Accept/decline a meeting |

### Groups
| Method | Endpoint                 | Description       |
| ------ | ------------------------ | ----------------- |
| GET    | `/api/groups`            | List all groups   |
| POST   | `/api/groups`            | Create a group    |
| POST   | `/api/groups/{id}/join`  | Join a group      |
| POST   | `/api/groups/{id}/leave` | Leave a group     |

### Other
| Method | Endpoint           | Description                       |
| ------ | ------------------ | --------------------------------- |
| POST   | `/api/followup`    | Generate AI follow-up email       |
| GET    | `/api/export/csv`  | Download all profiles as CSV      |

---

## 🧠 Matching Algorithm

The matching engine uses a weighted **TF-IDF + Cosine Similarity** approach across three profile dimensions:

| Dimension    | Default Weight | Description                              |
| ------------ | -------------- | ---------------------------------------- |
| Interests    | 0.50           | Keyword overlap in stated interests      |
| Tech Needs   | 0.30           | Alignment of tech needs + looking-for     |
| Bio          | 0.20           | Contextual similarity from bio + job title|

**Adaptive feedback loop**: When users rate matches (1–5 stars), the system correlates ratings with similarity dimensions and adjusts weights dynamically. High-rated matches with strong interest overlap increase the interest weight; poor ratings reduce it.

---

## 📄 License

This project is for educational and demonstration purposes.
