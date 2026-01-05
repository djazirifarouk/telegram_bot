import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Supabase Configuration
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# Validate required environment variables
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables!")

# Application Constants
EDITABLE_FIELDS = {
    "first_name": "First Name",
    "last_name": "Last Name",
    "email": "Personal Email",
    "whatsapp": "WhatsApp",
    "application_plan": "Application Plan",
    "roles": "Roles",
    "education": "Education",
    "skills": "Skills",
    "languages": "Languages",
    "certificates": "Certificates",
}

APPLICATION_PLAN_OPTIONS = ["casual", "normal", "intense"]

LANGUAGE_PROFICIENCY_OPTIONS = [
    "A0 Starter",
    "A1 Beginner",
    "A2 Elementary",
    "B1 Intermediate",
    "B2 Upper Intermediate",
    "C1 Advanced",
    "C2 Mastery"
]

# Data structure definitions for nested fields
NESTED_FIELD_STRUCTURES = {
    "roles": {
        "fields": ["title", "company", "location", "start", "end", "current", "description"],
        "labels": {
            "title": "Title",
            "company": "Company",
            "location": "Location",
            "start": "Start Date (YYYY-MM)",
            "end": "End Date (YYYY-MM)",
            "current": "Currently Working",
            "description": "Description"
        },
        "types": {
            "current": "boolean",
            "start": "date",
            "end": "date"
        },
        "optional": ["end", "start"]
    },
    "education": {
        "fields": ["degree", "field", "school", "start", "end"],
        "labels": {
            "degree": "Degree",
            "field": "Field of Study",
            "school": "School/University",
            "start": "Start Date (YYYY-MM)",
            "end": "End Date (YYYY-MM)"
        },
        "types": {
            "start": "date",
            "end": "date"
        },
        "optional": ["end", "start"]
    },
    "certificates": {
        "fields": ["name", "number", "start", "end"],
        "labels": {
            "name": "Course Name",
            "number": "Certificate Number",
            "start": "Start Date (YYYY-MM)",
            "end": "End Date (YYYY-MM)"
        },
        "types": {
            "start": "date",
            "end": "date"
        },
        "optional": ["number", "end", "start"]
    },
    "languages": {
        "fields": ["language", "proficiency"],
        "labels": {
            "language": "Language",
            "proficiency": "Proficiency Level"
        },
        "types": {
            "proficiency": "select"
        },
        "optional": []
    }
}