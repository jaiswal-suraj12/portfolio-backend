from fastapi import FastAPI, APIRouter
from urllib.parse import quote_plus
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
from typing import List
from datetime import datetime, timezone
import uuid
import logging
import os

# ===============================
# Load Environment Variables
# ===============================

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# ===============================
# Logging
# ===============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# ===============================
# MongoDB
# ===============================
username = quote_plus(os.getenv("MONGO_USER"))
password = quote_plus(os.getenv("MONGO_PASSWORD"))

MONGO_URL = os.getenv("MONGO_URL")
print(MONGO_URL)
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ===============================
# FastAPI App
# ===============================

app = FastAPI(
    title="Portfolio API",
    version="1.0.0"
)

api_router = APIRouter(prefix="/api")

# ===============================
# Models
# ===============================

class Social(BaseModel):
    github: str
    linkedin: str
    twitter: str


class PersonalInfo(BaseModel):
    name: str
    title: str
    bio: str
    experience: str
    resume: str
    photo: str
    email: str
    phone: str
    location: str
    social: Social


class Project(BaseModel):
    title: str
    description: str
    image: str
    technologies: List[str]
    featured: bool = False


class Technology(BaseModel):
    name: str
    level: int


class SkillCategory(BaseModel):
    category: str
    technologies: List[Technology]


class ContactMessage(BaseModel):
    name: str
    email: str
    subject: str
    message: str


class Testimonial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    position: str
    avatar: str
    text: str


class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class StatusCheckCreate(BaseModel):
    client_name: str

class Social(BaseModel):
    github: str
    linkedin: str
    twitter: str


class PersonalInfo(BaseModel):
    name: str
    title: str
    bio: str
    experience: str
    resume: str
    photo:str
    email: str
    phone: str
    location: str

    social: Social

class Project(BaseModel):
    title: str
    description: str
    image: str
    technologies: List[str]
    featured: bool = False


class Technology(BaseModel):
    name: str
    level: int


class SkillCategory(BaseModel):
    category: str
    technologies: list[Technology]

class ContactMessage(BaseModel):
    name: str
    email: str
    subject: str
    message: str

class Testimonial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    position: str
    avatar: str
    text: str
# Routes
# ==========================================
# Root API
# ==========================================

@api_router.get("/")
async def root():
    return {
        "message": "Portfolio API Running Successfully 🚀"
    }


# ==========================================
# Personal Information
# ==========================================

@api_router.get("/personal-info", response_model=PersonalInfo)
async def get_personal_info():

    data = await db.personal_info.find_one({}, {"_id": 0})

    if data is None:
        return PersonalInfo(
            name="Your Name",
            title="Full Stack Developer",
            bio="Welcome to my portfolio.",
            experience="0 Years",
            resume="#",
            photo="/profile.jpg",
            email="you@example.com",
            phone="+91 9876543210",
            location="India",
            social=Social(
                github="https://github.com/yourname",
                linkedin="https://linkedin.com/in/yourname",
                twitter="https://twitter.com/yourname"
            )
        )

    return PersonalInfo(**data)


@api_router.post("/personal-info", response_model=PersonalInfo)
async def create_personal_info(info: PersonalInfo):

    await db.personal_info.delete_many({})
    await db.personal_info.insert_one(info.model_dump())

    logger.info("Personal information updated")

    return info


# ==========================================
# Projects
# ==========================================

@api_router.get("/projects", response_model=List[Project])
async def get_projects():

    projects = await db.projects.find({}, {"_id": 0}).to_list(100)

    return projects


@api_router.post("/projects", response_model=Project)
async def create_project(project: Project):

    await db.projects.insert_one(project.model_dump())

    logger.info(f"Project added: {project.title}")

    return project


# ==========================================
# Skills
# ==========================================

@api_router.get("/skills", response_model=List[SkillCategory])
async def get_skills():

    skills = await db.skills.find({}, {"_id": 0}).to_list(100)

    return skills


@api_router.post("/skills", response_model=SkillCategory)
async def create_skill(skill: SkillCategory):

    await db.skills.insert_one(skill.model_dump())

    logger.info(f"Skill category added: {skill.category}")

    return skill
 # ==========================================
# Testimonials
# ==========================================

@api_router.get("/testimonials", response_model=List[Testimonial])
async def get_testimonials():

    testimonials = await db.testimonials.find({}, {"_id": 0}).to_list(100)

    return testimonials


@api_router.post("/testimonials", response_model=Testimonial)
async def create_testimonial(testimonial: Testimonial):

    await db.testimonials.insert_one(testimonial.model_dump())

    logger.info(f"New testimonial added by {testimonial.name}")

    return testimonial


# ==========================================
# Contact
# ==========================================

@api_router.post("/contact")
async def send_contact(message: ContactMessage):

    await db.contacts.insert_one(message.model_dump())

    logger.info(f"Contact message from {message.name}")

    return {
        "success": True,
        "message": "Message sent successfully"
    }


# ==========================================
# Status Check
# ==========================================

@api_router.post("/status", response_model=StatusCheck)
async def create_status(payload: StatusCheckCreate):

    status = StatusCheck(**payload.model_dump())

    document = status.model_dump()
    document["timestamp"] = document["timestamp"].isoformat()

    await db.status_checks.insert_one(document)

    return status


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status():

    results = await db.status_checks.find(
        {},
        {"_id": 0}
    ).to_list(100)

    for item in results:
        if isinstance(item["timestamp"], str):
            item["timestamp"] = datetime.fromisoformat(item["timestamp"])

    return results


# ==========================================
# Register Router
# ==========================================

app.include_router(api_router)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Shutdown Event
# ==========================================

@app.on_event("shutdown")
async def shutdown_db():

    client.close()

    logger.info("MongoDB connection closed")