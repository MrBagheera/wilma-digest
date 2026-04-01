# wilma-digest

Fetches unread messages from a [Wilma](https://www.visma.fi/wilma/) school portal, summarises them using Claude AI, and delivers the digest via Telegram.

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- An Anthropic API key
- A Telegram bot (see below)

## Installation

```bash
uv sync
```

## Configuration

### `.env` file

Create a `.env` file in the project root (see `.env.example`):

```env
# Wilma credentials (default, used when no credentials_prefix is set in task file)
WILMA_EMAIL=your_email@example.com
WILMA_PASSWORD=your_wilma_password

# Claude API key — https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-...

# Telegram bot
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI...
TELEGRAM_CHAT_ID=your_chat_id
```

If you have multiple Wilma portals with different credentials, add prefixed variants:

```env
ESPOO_WILMA_EMAIL=alice@example.com
ESPOO_WILMA_PASSWORD=secret1

OMNIA_WILMA_EMAIL=bob@example.com
OMNIA_WILMA_PASSWORD=secret2
```

### Task files

Each task is a YAML file that describes one Wilma instance to process:

```yaml
# Required
wilma_url: https://espoo.inschool.fi

# Optional: prefix for credential env vars (e.g. ESPOO_WILMA_EMAIL / ESPOO_WILMA_PASSWORD)
# credentials_prefix: ESPOO

# Optional: only process these children (exact name match); processes all if omitted
# children:
#   - Alice Smith

# Optional: digest language (default: English)
language: Russian

# Optional: max messages per digest batch (default: 5; overrides --max-messages for this task)
# max_messages: 10

# Optional: custom summarisation prompt; use {language} and {messages_text} as placeholders
# prompt: |
#   Summarise these school messages in {language}. Be concise.
#   {messages_text}
```

## Usage

```bash
# Process one or more task files
uv run wilma-digest task.yaml
uv run wilma-digest espoo.yaml omnia.yaml

# Re-digest the last N messages per student (ignores unread status)
uv run wilma-digest task.yaml --resend-last 3

# Print digest to stdout instead of sending via Telegram
uv run wilma-digest task.yaml --skip-telegram

# Limit digest size (default: 5 messages per digest; larger batches are split into multiple digests)
uv run wilma-digest task.yaml --max-messages 10
```

## Deployment Options

### Option 1: AWS Lambda (Recommended)

Deploy to AWS Lambda using AWS SAM (Serverless Application Model) for automatic, scheduled execution in the cloud.

**Benefits:**
- No local machine needed
- Automatic scheduling (hourly 7-22 on weekdays)
- Infrastructure as code (version controlled)
- ~$0.00/month (AWS free tier)

**Requirements:**
- AWS account
- AWS CLI configured with credentials
- AWS SAM CLI: `brew install aws-sam-cli`

**Deployment:**

1. Load environment variables:
   ```bash
   export $(cat .env | xargs)
   ```

2. Build the Lambda package:
   ```bash
   sam build
   ```

3. Deploy to AWS (first time):
   ```bash
   sam deploy --guided
   ```
   
   Accept the defaults when prompted:
   - Stack name: `wilma-digest`
   - Region: `eu-north-1` (Stockholm - closest to Finland)
   - Confirm IAM role creation: Yes
   - Allow Lambda without authorization: Yes
   - Save arguments to config: Yes

4. Subsequent updates:
   ```bash
   sam build && sam deploy
   ```

**Testing:**
```bash
# Test locally before deploying
sam local invoke WilmaDigestFunction

# View logs in AWS
sam logs -n WilmaDigestFunction --stack-name wilma-digest --tail
```

**Teardown:**
```bash
# Remove all AWS resources
sam delete --stack-name wilma-digest
```

**Configuration:**
- Schedule: Runs every hour 7:00-22:00 on weekdays (Mon-Fri)
- Task files: Edit `lambda_handler.py` to change which task files are processed
- Schedule: Edit `template.yaml` to modify the cron expression

### Option 2: macOS launchd (Local)

A launchd plist is included to run the digest locally on macOS daily at 19:00.

1. Edit `com.wilma-digest.plist` — update the task file paths in `ProgramArguments` to match your setup.
2. Install:

```bash
cp com.wilma-digest.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.wilma-digest.plist
```

Logs are written to `wilma-digest.log` and `wilma-digest-error.log` in the project directory.

## Setting up a Telegram bot

### 1. Create the bot

1. Open Telegram and start a chat with [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts (choose a name and username).
3. BotFather will give you a **bot token** — copy it to `TELEGRAM_BOT_TOKEN` in `.env`.

### 2. Get your chat ID

The bot needs to know where to send messages. The easiest way:

1. Start a chat with your new bot (search for its username and press **Start**).
   — or add it to a group if you want group delivery.
2. Send any message to the bot (or the group).
3. Open this URL in a browser, replacing `<TOKEN>` with your bot token:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
4. Find the `"chat"` object in the response. The `"id"` field is your chat ID:
   ```json
   {"chat": {"id": 123456789, "type": "private", ...}}
   ```
   For a group the ID will be a negative number, e.g. `-987654321`.
5. Copy the value to `TELEGRAM_CHAT_ID` in `.env`.

### Troubleshooting

- **No updates returned** — send another message to the bot first, then retry the URL.
- **Bot not sending** — make sure you pressed **Start** in the bot chat; bots cannot initiate conversations.
- **Group delivery** — add the bot to the group, send a message that mentions it (or any message), then check `getUpdates`.
