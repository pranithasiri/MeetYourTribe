from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import database
import matcher

app = FastAPI(
    title="Event Management AI Conference Networking MeetYourTribeAPI",
    description="Backend API for managing conference networking, matching, and schedules.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- HELPER: Get current user from cookie ----------

def get_current_user_id(request: Request) -> int:
    """Read the logged-in user ID from the browser cookie.
    Each browser/incognito window has its own independent cookie,
    so multiple users can be logged in simultaneously."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    try:
        return int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid session")


# ---------------- MODELS ----------------

class ProfileCreate(BaseModel):
    name: str
    company: str
    job_title: str
    bio: str
    interests: str
    tech_needs: str
    looking_for: str


class ProfileUpdate(ProfileCreate):
    pass


class SignupRequest(BaseModel):
    name: str
    company: str
    job_title: str
    bio: str
    interests: str
    tech_needs: str
    looking_for: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str

class JoinEventRequest(BaseModel):
    profile_id: int
    event_name: str
    location: str = ""

class MeetingCreate(BaseModel):
    inviter_id: int
    invitee_id: int
    time_slot: str
    venue_location: str
    notes: Optional[str] = None


class FeedbackCreate(BaseModel):
    profile_id: int
    other_id: int
    score: int
    notes: Optional[str] = None


class GroupCreate(BaseModel):
    name: str
    topic: str
    description: str
    created_by: int


class GroupMemberAction(BaseModel):
    profile_id: int


class FollowUpRequest(BaseModel):
    profile_from_id: int
    profile_to_id: int
    meeting_id: int


# ---------------- FRONTEND ROUTES ----------------

@app.get("/")
def landing():
    return FileResponse("static/landing.html")


@app.get("/login")
def login_page():
    return FileResponse("static/login.html")


@app.get("/signup")
def signup_page():
    return FileResponse("static/signup.html")


@app.get("/dashboard")
def dashboard(request: Request):
    # If not logged in, redirect to login page
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")
    return FileResponse("static/index.html")



app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------- AUTH (cookie-based per-browser sessions) ----------------

@app.post("/api/login")
def login(req: LoginRequest, response: Response):
    profile = database.get_profile_by_email(req.email)

    if not profile:
        raise HTTPException(status_code=401, detail="No account found with that email")

    if profile.get("password") != req.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    # Set cookie for THIS browser — other browsers/incognito keep their own cookie
    response.set_cookie(
        key="user_id",
        value=str(profile["id"]),
        httponly=False,   # allow JS to read for client-side logic
        samesite="lax",
        max_age=86400     # 24 hours
    )

    return {
        "status": "success",
        "current_user_id": profile["id"],
        "name": profile["name"]
    }

@app.post("/api/events/join")
def join_event(req: JoinEventRequest):

    event_id = database.join_event(
        req.profile_id,
        req.event_name,
        req.location
    )

    return {
        "success": True,
        "event_id": event_id
    }

@app.post("/api/signup")
def signup(req: SignupRequest, response: Response):
    # Check if email already exists
    existing = database.get_profile_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    new_id = database.create_profile(
        name=req.name,
        company=req.company,
        job_title=req.job_title,
        bio=req.bio,
        interests=req.interests,
        tech_needs=req.tech_needs,
        looking_for=req.looking_for,
        email=req.email,
        password=req.password
    )

    # Set cookie for THIS browser
    response.set_cookie(
        key="user_id",
        value=str(new_id),
        httponly=False,
        samesite="lax",
        max_age=86400
    )

    return {
        "status": "success",
        "profile_id": new_id
    }


@app.get("/api/session")
def get_session(request: Request):
    """Returns the current user ID from this browser's cookie."""
    uid = get_current_user_id(request)
    return {"current_user_id": uid}

@app.get("/api/events")
def get_all_events():
    return database.get_events()


@app.post("/api/act-as/{profile_id}")
def act_as(profile_id: int, response: Response):
    """Switch to another profile (for demo/testing purposes)."""
    profile = database.get_profile(profile_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    response.set_cookie(
        key="user_id",
        value=str(profile_id),
        httponly=False,
        samesite="lax",
        max_age=86400
    )

    return {
        "status": "success",
        "current_user_id": profile_id
    }


@app.post("/api/logout")
def logout(response: Response):
    """Clear the session cookie and log out."""
    response.delete_cookie(key="user_id")
    return {"status": "success"}


# ---------------- PROFILES ----------------

@app.get("/api/profiles")
def get_profiles(request: Request, active: Optional[bool] = False):
    if active:
        uid = get_current_user_id(request)
        return database.get_profiles(active_id=uid)
    return database.get_profiles()


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: int):
    profile = database.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.post("/api/profiles")
def create_profile(profile: ProfileCreate, response: Response):
    new_id = database.create_profile(
        name=profile.name,
        company=profile.company,
        job_title=profile.job_title,
        bio=profile.bio,
        interests=profile.interests,
        tech_needs=profile.tech_needs,
        looking_for=profile.looking_for
    )

    # Auto-login the new profile
    response.set_cookie(
        key="user_id",
        value=str(new_id),
        httponly=False,
        samesite="lax",
        max_age=86400
    )

    return {
        "status": "success",
        "profile_id": new_id
    }


@app.put("/api/profiles/{profile_id}")
def update_profile(profile_id: int, profile: ProfileUpdate):
    existing = database.get_profile(profile_id)

    if not existing:
        raise HTTPException(status_code=404, detail="Profile not found")

    database.update_profile(
        profile_id=profile_id,
        name=profile.name,
        company=profile.company,
        job_title=profile.job_title,
        bio=profile.bio,
        interests=profile.interests,
        tech_needs=profile.tech_needs,
        looking_for=profile.looking_for
    )

    return {"status": "success"}


@app.get("/api/profiles/{profile_id}/matches")
def get_matches(profile_id: int):
    return matcher.compute_profile_matches(profile_id)


@app.get("/api/profiles/{profile_id}/groups")
def get_user_groups(profile_id: int):
    """Return list of group IDs that a user belongs to."""
    return database.get_user_groups(profile_id)


# ---------------- FEEDBACK ----------------

@app.post("/api/feedback")
def submit_feedback(fb: FeedbackCreate):
    database.save_feedback(
        profile_id=fb.profile_id,
        other_id=fb.other_id,
        score=fb.score,
        notes=fb.notes
    )
    return {"status": "success"}


# ---------------- MEETINGS ----------------

@app.post("/api/meetings")
def schedule_meeting(meeting: MeetingCreate):
    meeting_id = database.create_meeting(
        inviter_id=meeting.inviter_id,
        invitee_id=meeting.invitee_id,
        time_slot=meeting.time_slot,
        venue_location=meeting.venue_location,
        notes=meeting.notes
    )

    return {"status": "success", "meeting_id": meeting_id}


@app.get("/api/meetings/{profile_id}")
def get_meetings(profile_id: int):
    return database.get_meetings(profile_id)

@app.post("/api/meetings/{meeting_id}/respond")
def respond_to_meeting(meeting_id: int, payload: dict):
    status = payload.get("status")

    if status not in ["accepted", "declined"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    database.respond_meeting(meeting_id, status)

    return {
        "status": "success",
        "meeting_id": meeting_id
    }


# ---------------- GROUPS ----------------

@app.get("/api/groups")
def get_groups():
    return database.get_groups()


@app.post("/api/groups")
def create_group(group: GroupCreate):
    group_id = database.create_group(
        name=group.name,
        topic=group.topic,
        description=group.description,
        created_by=group.created_by
    )
    return {"status": "success", "group_id": group_id}


@app.post("/api/groups/{group_id}/join")
def join_group(group_id: int, payload: GroupMemberAction):
    database.join_group(group_id, payload.profile_id)
    return {"status": "success", "group_id": group_id}


@app.post("/api/groups/{group_id}/leave")
def leave_group(group_id: int, payload: GroupMemberAction):
    database.leave_group(group_id, payload.profile_id)
    return {"status": "success", "group_id": group_id}


@app.get("/api/profiles/{profile_id}/group-suggestions")
def get_group_suggestions(profile_id: int):
    return matcher.suggest_groups_for_profile(profile_id)


# ---------------- FOLLOWUP ----------------

@app.post("/api/followup")
def generate_followup(req: FollowUpRequest):
    # Fetch actual profile and meeting objects (not just IDs)
    profile_from = database.get_profile(req.profile_from_id)
    profile_to = database.get_profile(req.profile_to_id)
    meeting = database.get_meeting(req.meeting_id)

    if not profile_from or not profile_to:
        raise HTTPException(status_code=404, detail="Profile not found")
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {
        "followup_email": matcher.generate_followup_email(
            profile_from,
            profile_to,
            meeting
        )
    }


# ---------------- CSV EXPORT ----------------

@app.get("/api/export/csv")
def export_csv():
    """Download all profile data as a CSV file."""
    database.export_profiles_csv()
    return FileResponse(
        database.CSV_PATH,
        media_type="text/csv",
        filename="profiles_data.csv"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)