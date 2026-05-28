from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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

CURRENT_USER_ID = 1


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


class LoginRequest(BaseModel):
    email: str
    password: str


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
def dashboard():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------- AUTH ----------------

@app.post("/api/login")
def login(req: LoginRequest):
    global CURRENT_USER_ID

    profiles = database.get_profiles()

    if not profiles:
        raise HTTPException(status_code=404, detail="No profiles found")

    CURRENT_USER_ID = profiles[0]["id"]

    return {
        "status": "success",
        "current_user_id": CURRENT_USER_ID
    }


@app.get("/api/session")
def get_session():
    return {"current_user_id": CURRENT_USER_ID}


# ---------------- PROFILES ----------------

@app.get("/api/profiles")
def get_profiles(active: Optional[bool] = False):
    if active:
        return database.get_profiles(active_id=CURRENT_USER_ID)
    return database.get_profiles()


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: int):
    profile = database.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.post("/api/profiles")
def create_profile(profile: ProfileCreate):
    global CURRENT_USER_ID

    new_id = database.create_profile(
        name=profile.name,
        company=profile.company,
        job_title=profile.job_title,
        bio=profile.bio,
        interests=profile.interests,
        tech_needs=profile.tech_needs,
        looking_for=profile.looking_for
    )

    CURRENT_USER_ID = new_id

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


@app.get("/api/profiles/{profile_id}/group-suggestions")
def get_group_suggestions(profile_id: int):
    return matcher.suggest_groups_for_profile(profile_id)


# ---------------- FOLLOWUP ----------------

@app.post("/api/followup")
def generate_followup(req: FollowUpRequest):
    return {
        "followup_email": matcher.generate_followup_email(
            req.profile_from_id,
            req.profile_to_id,
            req.meeting_id
        )
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)