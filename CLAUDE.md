# CLAUDE.md

## Project Overview

`wilma-digest` is a Python utility that fetches unread messages from the Finnish Wilma school portal, summarizes them in Russian using Claude AI, and delivers the digest via Telegram. It is scheduled to run daily at 19:00 via macOS launchd.

### Stack

- **Language:** Python >=3.11
- **Package manager / build:** `uv`, `hatchling`
- **HTTP / scraping:** `requests`, `beautifulsoup4`, `lxml`
- **AI summarization:** `anthropic` SDK (Claude Haiku)
- **Config:** `python-dotenv` (`.env` file)
- **Delivery:** Telegram Bot API

### Structure

- `pyproject.toml` — project metadata and dependencies
- `uv.lock` — locked dependency versions
- `src/wilma_digest/` — all source code
  - `main.py` — CLI entry point (`wilma-digest` command)
  - `wilma.py` — Wilma portal client (login, fetch messages)
  - `summarizer.py` — Claude-based digest summarizer
  - `telegram.py` — Telegram message sender
- `com.wilma-digest.plist` — macOS launchd schedule (daily at 19:00)
- `.env` — runtime secrets (not committed); see `.env.example` for required variables

### Documentation

**Required environment variables** (set in `.env`):
```
WILMA_EMAIL, WILMA_PASSWORD   # Wilma portal credentials
ANTHROPIC_API_KEY             # Claude API key
TELEGRAM_BOT_TOKEN            # Telegram bot token
TELEGRAM_CHAT_ID              # Target Telegram chat ID
```

**Run:**
```bash
uv run wilma-digest            # fetch & send unread messages
uv run wilma-digest --resend-last 5   # resend last 5 messages per student
```

**Install launchd schedule (macOS):**
```bash
cp com.wilma-digest.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.wilma-digest.plist
```

No tests are present in the project.

---

## User-Provided Instructions

_Add your project-specific instructions here._
