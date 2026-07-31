from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
from typing import List
from datetime import datetime, timezone
import logging
import uuid
import os

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# MongoDB
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# FastAPI app
app = FastAPI(
    title="Portfolio API",
    version="1.0.0"
)

# Router
api_router = APIRouter(prefix="/api")


# Models
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
@api_router.get("/")
async def root():
    return {
        "message": "Portfolio API Running"
    }

@api_router.get("/personal-info", response_model=PersonalInfo)
async def get_personal_info():

    data = await db.personal_info.find_one({}, {"_id": 0})

    if data is None:
        return {
            "name": "Your Name",
            "title": "Full Stack Developer",
            "bio": "Welcome to my portfolio.",
            "experience": "0 Years",
            "resume": "#",
            "email": "you@example.com",
            "phone": "+91 9876543210",
            "location": "India",
            "social": {
                "github": "https://github.com/yourname",
                "linkedin": "https://linkedin.com/in/yourname",
                "twitter": "https://twitter.com/yourname"
            }
        }

    return data

# ==============================
# Routes
# ==============================

@api_router.get("/")
async def root():
    return {
        "message": "Portfolio API Running"
    }


# ------------------------------
# Personal Information
# ------------------------------
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
            email="you@example.com",
            phone="+91 9876543210",
            location="India",
            social=SocialLinks(
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


# ------------------------------
# Projects
# ------------------------------

@api_router.get("/projects", response_model=List[Project])
async def get_projects():

    return await db.projects.find({}, {"_id": 0}).to_list(100)


@api_router.post("/projects", response_model=Project)
async def create_project(project: Project):

    await db.projects.insert_one(project.model_dump())

    logger.info(f"Project created: {project.title}")

    return project


# ------------------------------
# Skills
# ------------------------------
from typing import List

@api_router.get("/skills", response_model=List[SkillCategory])
async def get_skills():
    return await db.skills.find({}, {"_id": 0}).to_list(100)


@api_router.post("/skills", response_model=SkillCategory)
async def create_skill(skill: SkillCategory):
    await db.skills.insert_one(skill.model_dump())
    return skill

 #------------------------
 # Testimonials 
#-------------------------
@api_router.get("/testimonials", response_model=List[Testimonial])
async def get_testimonials():

    return await db.testimonials.find({}, {"_id": 0}).to_list(100)

@api_router.post("/testimonials", response_model=Testimonial)
async def create_testimonial(testimonial: Testimonial):

    await db.testimonials.insert_one(testimonial.model_dump())

    logger.info(f"Testimonial added by {testimonial.name}")

    return testimonial

# ------------------------------
# Contact
# ------------------------------

@api_router.post("/contact")
async def send_contact(message: ContactMessage):

    await db.contacts.insert_one(message.model_dump())

    logger.info(f"New contact message from {message.name}")

    return {
        "success": True,
        "message": "Message sent successfully"
    }


# ------------------------------
# Status Check
# ------------------------------

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(payload: StatusCheckCreate):

    status = StatusCheck(**payload.model_dump())

    document = status.model_dump()
    document["timestamp"] = document["timestamp"].isoformat()

    await db.status_checks.insert_one(document)

    logger.info(f"Status check created for {status.client_name}")

    return status


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():

    results = await db.status_checks.find(
        {},
        {"_id": 0}
    ).to_list(1000)

    for item in results:
        if isinstance(item["timestamp"], str):
            item["timestamp"] = datetime.fromisoformat(item["timestamp"])

    return results


# ==============================
# Register Router
# ==============================

app.include_router(api_router)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("MongoDB connection closed")