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

**SAM files location:** All SAM-related files are in the `sam/` directory:
- `template.yaml` — CloudFormation/SAM template
- `samconfig.toml` — deployment configuration
- `lambda_handler.py` — Lambda entry point
- `Makefile` — build/deploy automation

**Deployment:**

1. Load environment variables (including the command to run):
   ```bash
   export $(cat .env | xargs)
   export WILMA_DIGEST_CMD="wilma-digest task1.yaml task2.yaml"
   ```

2. Build and deploy using Make:
   ```bash
   cd sam
   make deploy   # Builds and deploys to AWS
   ```

3. First-time deployment prompts:
   - Stack name: `wilma-digest`
   - Region: `eu-north-1` (Stockholm - closest to Finland)
   - Confirm IAM role creation: Yes
   - Allow Lambda without authorization: Yes
   - Save arguments to config: Yes

**Testing:**
```bash
cd sam

# Set up environment
export $(cat ../.env | xargs)
export WILMA_DIGEST_CMD="wilma-digest task1.yaml task2.yaml"

# Test locally before deploying (requires make build first)
make build
sam local invoke WilmaDigestFunction
```

**Teardown:**
```bash
cd sam

# Remove all AWS resources
sam delete --stack-name wilma-digest

# Clean local build artifacts
make clean
```

**Configuration:**
- `WILMA_DIGEST_CMD`: The command to run, e.g. `"wilma-digest task1.yaml task2.yaml --max-messages 10"`
- Schedule: Runs every hour 7:00-22:00 on weekdays (Mon-Fri); edit `sam/template.yaml` to modify
- Task files: Place in project root; they will be packaged with the Lambda

### Option 2: macOS launchd (Local)

Run the digest locally on macOS using launchd for scheduled execution.

**Benefits:**
- No cloud account needed
- Runs on your Mac automatically
- Simple setup

**Requirements:**
- macOS
- Project cloned locally with `uv sync` completed

**Setup:**

1. Copy the example plist and customize it:
   ```bash
   cp com.wilma-digest.example.plist com.wilma-digest.plist
   ```

2. Edit `com.wilma-digest.plist` and update:
   - `ProgramArguments`: Add your task files after `wilma-digest`
   - `WorkingDirectory`: Path to your project directory
   - `StandardOutPath` / `StandardErrorPath`: Log file paths
   - Path to `uv` binary (find with `which uv`)

   Example `ProgramArguments` section:
   ```xml
   <key>ProgramArguments</key>
   <array>
       <string>/Users/yourname/.local/bin/uv</string>
       <string>run</string>
       <string>wilma-digest</string>
       <string>task1.yaml</string>
       <string>task2.yaml</string>
   </array>
   ```

3. Install the launch agent:
   ```bash
   cp com.wilma-digest.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.wilma-digest.plist
   ```

**Schedule:**
- Default: Daily at 19:00
- Edit the `StartCalendarInterval` section in the plist to change

**Managing the service:**
```bash
# Check if running
launchctl list | grep wilma-digest

# Stop the service
launchctl unload ~/Library/LaunchAgents/com.wilma-digest.plist

# Start after making changes
launchctl load ~/Library/LaunchAgents/com.wilma-digest.plist

# Run manually (for testing)
launchctl start com.wilma-digest
```

**Logs:**
- `wilma-digest.log` — standard output
- `wilma-digest-error.log` — errors

**Uninstall:**
```bash
launchctl unload ~/Library/LaunchAgents/com.wilma-digest.plist
rm ~/Library/LaunchAgents/com.wilma-digest.plist
```

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
