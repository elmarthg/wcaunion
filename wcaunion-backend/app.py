# app.py
from typing import Optional
import os
import smtplib
from email.message import EmailMessage
import logging

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models import Base, ContactSubmission, GetInvolvedSubmission

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Database setup ----------
DATABASE_URL = "sqlite:///./union.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables on startup
Base.metadata.create_all(bind=engine)

# ---------- FastAPI app ----------
app = FastAPI(
    title="Weingart Workers Union Backend",
    description="API for contact + get involved forms.",
)

# CORS: allow your frontend origin(s)
origins = [
    "http://localhost:5500",   # VS Code Live Server / Python http.server
    "http://127.0.0.1:5500",
    "http://127.0.0.1:5501",
    "https://wcaunion.org",    # later: your real domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Email helper ----------

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")  # your Gmail address
SMTP_PASS = os.getenv("SMTP_PASS")  # your app password

# default recipients: fall back to SMTP_USER if not set
CONTACT_RECIPIENT = os.getenv("CONTACT_RECIPIENT", SMTP_USER or "")
GI_RECIPIENT = os.getenv("GI_RECIPIENT", SMTP_USER or "")


def send_notification_email(subject: str, body: str, to_email: str):
    """
    Basic email sender. If SMTP settings are missing, it logs a warning but
    does not crash the API.
    """
    if not (SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASS and to_email):
        logger.warning("Email not sent: SMTP config incomplete.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        logger.info("Notification email sent to %s", to_email)
    except Exception as e:
        logger.exception("Failed to send notification email: %s", e)


# ---------- Pydantic models ----------

class ContactIn(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = None
    program: Optional[str] = None
    message: str


class ContactOut(BaseModel):
    id: int
    message: str


class GetInvolvedIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: Optional[str] = None
    program: Optional[str] = None
    interest_level: Optional[str] = None
    concerns: Optional[str] = None


class GetInvolvedOut(BaseModel):
    id: int
    message: str


# ---------- Endpoints ----------

@app.post("/api/contact", response_model=ContactOut)
def create_contact_submission(
    payload: ContactIn,
    db: Session = Depends(get_db),
):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    submission = ContactSubmission(
        name=payload.name.strip(),
        email=payload.email.strip(),
        role=(payload.role or "").strip() or None,
        program=(payload.program or "").strip() or None,
        message=payload.message.strip(),
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Build email body
    subject = f"[WCA Union] New contact from {submission.name}"
    body_lines = [
        f"Name: {submission.name}",
        f"Email: {submission.email}",
        f"Role: {submission.role or '(not provided)'}",
        f"Program: {submission.program or '(not provided)'}",
        "",
        "Message:",
        submission.message,
    ]
    body = "\n".join(body_lines)

    # Send notification email (best-effort, errors just logged)
    send_notification_email(subject, body, CONTACT_RECIPIENT)

    return ContactOut(
        id=submission.id,
        message="Thanks for reaching out. An organizer will follow up.",
    )


@app.post("/api/get-involved", response_model=GetInvolvedOut)
def create_get_involved_submission(
    payload: GetInvolvedIn,
    db: Session = Depends(get_db),
):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    submission = GetInvolvedSubmission(
        name=payload.name.strip(),
        email=payload.email.strip(),
        phone=(payload.phone or "").strip() or None,
        role=(payload.role or "").strip() or None,
        program=(payload.program or "").strip() or None,
        interest_level=(payload.interest_level or "").strip() or None,
        concerns=(payload.concerns or "").strip() or None,
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Build email body
    subject = f"[WCA Union] New Get Involved submission from {submission.name}"
    body_lines = [
        f"Name: {submission.name}",
        f"Email: {submission.email}",
        f"Phone: {submission.phone or '(not provided)'}",
        f"Role: {submission.role or '(not provided)'}",
        f"Program: {submission.program or '(not provided)'}",
        f"Interest level: {submission.interest_level or '(not provided)'}",
        "",
        "Concerns / notes:",
        submission.concerns or "(none provided)",
    ]
    body = "\n".join(body_lines)

    # Send notification email
    send_notification_email(subject, body, GI_RECIPIENT)

    return GetInvolvedOut(
        id=submission.id,
        message="Thanks for signing up to be involved. An organizer will reach out.",
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
