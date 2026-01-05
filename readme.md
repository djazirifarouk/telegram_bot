# Telegram Applicant Management Bot

A comprehensive bot for managing job applicants with features for viewing, editing, payment tracking, and subscription management.

## Features
- 📋 View applicants (pending, done, archived)
- ✏️ Edit applicant information
- 💰 Payment management
- 📅 Subscription management
- 🗄️ Archive management
- 📊 Statistics

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env` file with your credentials:
   ```
   TELEGRAM_TOKEN=your_telegram_token
   TELEGRAM_CHAT_ID=your_admin_chat_id
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```
4. Run the bot:
   ```bash
   python main.py
   ```

## Project Structure
See the codebase for detailed structure.


# Telegram Applicant Bot - Setup Guide

## 📁 Project Structure

```
telegram_applicant_bot/
├── .env                          # Environment variables (DON'T commit!)
├── .gitignore                    # Files to ignore in git
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
├── main.py                       # Entry point - starts the bot
│
├── config/                       # Configuration
│   ├── __init__.py
│   └── settings.py              # All constants and config
│
├── database/                     # Database layer
│   ├── __init__.py
│   ├── supabase_client.py       # Supabase connection
│   └── queries.py               # All database operations
│
├── utils/                        # Utility functions
│   ├── __init__.py
│   ├── helpers.py               # Helper functions
│   └── state_manager.py         # User state management
│
└── bot/                          # Bot logic
    ├── __init__.py
    ├── handlers/                 # Command and callback handlers
    │   ├── __init__.py
    │   ├── start.py             # Main menu & start command
    │   ├── view.py              # View applicants
    │   ├── edit.py              # Edit applicants
    │   ├── payment.py           # Payment management
    │   ├── subscription.py      # Subscription management
    │   ├── archive.py           # Archive management
    │   ├── stats.py             # Statistics
    │   └── text_handler.py      # Text input processing
    ├── keyboards/                # Keyboard layouts
    │   ├── __init__.py
    │   └── menus.py             # All inline keyboards
    ├── validators/               # Input validation
    │   ├── __init__.py
    │   └── input_validators.py  # Validation functions
    └── formatters/               # Display formatting
        ├── __init__.py
        └── display.py           # Data formatting
```

## 🚀 Quick Start

### 1. Create the folder structure:
```bash
mkdir -p telegram_applicant_bot/{config,database,utils,bot/{handlers,keyboards,validators,formatters}}
cd telegram_applicant_bot
```

### 2. Create all __init__.py files:
```bash
touch config/__init__.py
touch database/__init__.py
touch utils/__init__.py
touch bot/__init__.py
touch bot/handlers/__init__.py
touch bot/keyboards/__init__.py
touch bot/validators/__init__.py
touch bot/formatters/__init__.py
```

### 3. Create your .env file:
```env
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_admin_chat_id
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 4. Install dependencies:
```bash
pip install -r requirements.txt
```

### 5. Run the bot:
```bash
python main.py
```

## 🏗️ Architecture Overview

### **Separation of Concerns**

1. **config/** - All configuration in one place
   - Easy to modify constants
   - Centralized settings

2. **database/** - Database operations isolated
   - All Supabase queries in `queries.py`
   - Easy to test and mock
   - Single source of truth for data operations

3. **utils/** - Reusable utilities
   - Helper functions
   - State management
   - No business logic

4. **bot/handlers/** - Feature-based handlers
   - Each file handles one feature area
   - Easy to find and modify code
   - Clear responsibilities

5. **bot/keyboards/** - UI layouts separated
   - All keyboards in one place
   - Reusable components
   - Easy to modify UI

6. **bot/validators/** - Input validation
   - All validation logic centralized
   - Easy to add new validators
   - Reusable across handlers

7. **bot/formatters/** - Display formatting
   - Consistent data presentation
   - Easy to modify output format

## 🎯 Key Benefits

### **Easy to Debug**
- Each file has a single responsibility
- Clear function names
- Logging in each module
- Easy to trace issues

### **Easy to Add Features**
1. Create new handler file in `bot/handlers/`
2. Add keyboard layouts in `bot/keyboards/menus.py`
3. Add database queries in `database/queries.py`
4. Register handler in `bot/handlers/__init__.py`

### **Easy to Test**
- Each module is independent
- Database layer can be mocked
- Validators are pure functions
- Clear inputs and outputs

### **Easy to Maintain**
- Find code quickly by feature
- Modify one thing without breaking others
- Clear dependencies
- Good naming conventions

## 📝 How to Add a New Feature

**Example: Adding "Bulk Export" feature**

1. **Create handler** (`bot/handlers/export.py`):
```python
async def show_export_menu(update, context):
    # Your logic here
    pass

def register_export_handlers(application):
    application.add_handler(CallbackQueryHandler(show_export_menu, pattern="^export$"))
```

2. **Add keyboard** (`bot/keyboards/menus.py`):
```python
def get_export_menu():
    keyboard = [
        [InlineKeyboardButton("Export CSV", callback_data="export_csv")],
        [InlineKeyboardButton("Export PDF", callback_data="export_pdf")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)
```

3. **Add database query** (`database/queries.py`):
```python
async def get_all_applicants_for_export():
    result = await asyncio.to_thread(
        lambda: supabase.table("applications").select("*").execute()
    )
    return result.data
```

4. **Register in main** (`bot/handlers/__init__.py`):
```python
from .export import register_export_handlers

def register_all_handlers(application):
    # ... other handlers ...
    register_export_handlers(application)
```

5. **Add to main menu** (`bot/keyboards/menus.py`):
```python
def get_main_menu():
    keyboard = [
        # ... existing buttons ...
        [InlineKeyboardButton("📤 Export Data", callback_data="export")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

## 🐛 Debugging Tips

### Check logs:
```python
logger.info(f"User {user_id} triggered {action}")
logger.error(f"Error in function: {e}")
```

### Test database queries separately:
```python
# In Python console
from database.queries import get_applicant
import asyncio

applicant = asyncio.run(get_applicant("alias_email", "test@example.com"))
print(applicant)
```

### Check user state:
```python
from utils.state_manager import state_manager
state = state_manager.get_state(user_id)
print(state)
```

## 📦 Git Setup

```bash
git init
git add .
git commit -m "Initial commit: Structured bot architecture"
git branch -M main
git remote add origin your-repo-url
git push -u origin main
```

## 🔒 Security Notes

1. **Never commit .env file**
2. **Use .gitignore properly**
3. **Keep tokens secret**
4. **Validate all user input**
5. **Log errors, not sensitive data**

## 📚 Further Improvements

1. **Add unit tests** in `tests/` folder
2. **Add Docker support** with Dockerfile
3. **Add CI/CD** with GitHub Actions
4. **Add monitoring** with logging handlers
5. **Add rate limiting** for API calls
6. **Add caching** for frequently accessed data

---

**Ready to start!** Just copy the code from the artifacts into the appropriate files and run `python main.py` 🚀