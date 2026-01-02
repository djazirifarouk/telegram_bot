# Telegram Bot - Applicant Management

This Telegram bot allows you to manage applicants, track payments, subscriptions, and store files (CV, profile pictures, recommendation letters) using **Supabase**. It’s fully containerized with Docker and can be run automatically on system startup.

---

## Features

- List all pending, completed, or archived applicants.
- Retrieve detailed applicant information with attached files.
- Mark payments as done or pending.
- Set or extend subscription expiration.
- Archive or restore applicants.
- Display organized applicant info: personal, address, work experience, education, certificates, languages, skills, country preferences, payment, and subscription.
- Automatically download and send applicant files (CV, profile picture, recommendation letters) in Telegram.

---

## Commands

| Command | Description |
|---------|-------------|
| `/all_pending_applicants` | List all applicants with pending payments. |
| `/all_done_applicants` | List all applicants whose payment is done. |
| `/all_archived_applicants` | List all archived applicants. |
| `/find_applicant <alias_email>` | Show full details of a specific applicant with files. |
| `/mark_payment_done <alias_email>` | Mark an applicant’s payment as done. |
| `/mark_payment_pending <alias_email>` | Revert payment to pending. |
| `/set_subscription <alias_email> <YYYY-MM-DD>` | Set subscription expiration date. |
| `/extend_subscription <alias_email> <days>` | Extend subscription by a number of days. |
| `/archive_applicant <alias_email>` | Move an applicant to the archive table. |
| `/restore_applicant <alias_email>` | Restore an archived applicant back to the main table. |
| `/applicant_stats` | Show counts of pending, done, and archived applicants. |

---

## Requirements

- Python 3.11+
- Docker & Docker Compose
- Supabase project with:
  - `applications` table
  - `applications_archive` table
  - Storage buckets: `pictures`, `cv`, `letters`
- Telegram Bot Token from BotFather

---

## Setup

1. Clone the repository:

```bash
git clone <repo-url>
cd telegram-bot
```

2. Create a .env file with your credentials:
```bash
TELEGRAM_TOKEN=your_telegram_bot_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
```

3. Build and start the bot using Docker Compose:
```bash
docker compose up -d --build
```