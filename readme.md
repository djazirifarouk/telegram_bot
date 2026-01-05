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

{% include_relative bot_setup_guide.md %}