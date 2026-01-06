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
    "cv_url": "CV Document",
    "picture_url": "Profile Picture",
    "recommendation_url": "Recommendation Letters",
    "achievements": "Achievements",
    "authorized_countries": "Authorized Countries",  # ✅ CORRECT
    "visa": "Visa Status",
    "relocate": "Willing to Relocate",
    "experience": "Years of Experience",
    "employment_type": "Employment Type",
    "search_accuracy": "Search Accuracy",
    "country_preference": "Country Preferences",  # ✅ FIXED - removed 's'
    "socials": "Social Media Links",
    "apply_role": "Applying For Role",
    "general": "General Information",
    "skills": "Skills",
    "roles": "Roles",
    "education": "Education",
    "languages": "Languages",
    "certificates": "Certificates",
}

# New constants
YES_NO_OPTIONS = ["Yes", "No"]

EMPLOYMENT_TYPE_OPTIONS = ["On-site", "Remote", "Hybrid"]

SEARCH_ACCURACY_OPTIONS = [
    "Broad Match",
    "Exact Match",
    ">=50%",
    ">=60%",
    ">=70%",
    ">=80%",
    ">=90%"
]

CURRENCY_OPTIONS = ["USD", "EUR", "TND"]

# List of countries for autocomplete
COUNTRIES_LIST = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia",
    "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
    "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina",
    "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia",
    "Cameroon", "Canada", "Cape Verde", "Central African Republic", "Chad", "Chile", "China",
    "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt",
    "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland",
    "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala",
    "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India",
    "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan",
    "Jordan", "Kazakhstan", "Kenya", "Kiribati", "North Korea", "South Korea", "Kuwait",
    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein",
    "Lithuania", "Luxembourg", "Macedonia", "Madagascar", "Malawi", "Malaysia", "Maldives",
    "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia",
    "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia",
    "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Norway",
    "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines",
    "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe",
    "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia",
    "Slovenia", "Solomon Islands", "Somalia", "South Africa", "Spain", "Sri Lanka", "Sudan",
    "Suriname", "Swaziland", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania",
    "Thailand", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan",
    "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
    "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia",
    "Zimbabwe"
]

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