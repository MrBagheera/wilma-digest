import argparse
import os
import sys
from datetime import date
from pathlib import Path

import yaml
from dotenv import load_dotenv

from wilma_digest.wilma import WilmaClient
from wilma_digest.summarizer import summarize_messages
from wilma_digest.telegram import send_message


def load_task(path: str) -> dict:
    with open(path) as f:
        task = yaml.safe_load(f)
    if not isinstance(task, dict):
        raise ValueError(f"{path}: task file must be a YAML mapping")
    if "wilma_url" not in task:
        raise ValueError(f"{path}: missing required field 'wilma_url'")
    return task


def run_task(task: dict, resend_last: int | None, skip_telegram: bool) -> None:
    wilma_url = task["wilma_url"]
    prefix = task.get("credentials_prefix", "").strip()
    children_filter: list[str] | None = task.get("children")
    language: str = task.get("language", "English")
    prompt_template: str | None = task.get("prompt")

    # Resolve credentials from env using optional prefix
    def env(name: str) -> str | None:
        if prefix:
            value = os.getenv(f"{prefix}_{name}")
            if value:
                return value
        return os.getenv(name)

    email = env("WILMA_EMAIL")
    password = env("WILMA_PASSWORD")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    missing = []
    if not email:
        missing.append(f"{'_'.join(filter(None, [prefix, 'WILMA_EMAIL']))}")
    if not password:
        missing.append(f"{'_'.join(filter(None, [prefix, 'WILMA_PASSWORD']))}")
    if not api_key:
        missing.append("ANTHROPIC_API_KEY")
    if not skip_telegram:
        if not os.getenv("TELEGRAM_BOT_TOKEN"):
            missing.append("TELEGRAM_BOT_TOKEN")
        if not os.getenv("TELEGRAM_CHAT_ID"):
            missing.append("TELEGRAM_CHAT_ID")
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    print(f"[{wilma_url}] Logging in as {email}...")
    client = WilmaClient(email, password, wilma_url)
    client.login()

    students = client.get_students()
    if not students:
        raise RuntimeError("No students found after login.")
    print(f"[{wilma_url}] Found students: {[s['name'] for s in students]}")

    if children_filter:
        students = [s for s in students if s["name"] in children_filter]
        if not students:
            raise RuntimeError(
                f"None of the specified children {children_filter} were found"
            )

    all_messages = []
    for student in students:
        if resend_last is not None:
            msgs = client.get_last_messages(student["id"], resend_last)
            print(f"  {student['name']}: fetching last {resend_last} message(s)")
        else:
            msgs = client.get_unread_messages(student["id"])
            print(f"  {student['name']}: {len(msgs)} unread message(s)")
        for msg in msgs:
            msg.body = client.get_message_body(student["id"], msg.id)
            msg.student_name = student["name"]
        all_messages.extend(msgs)

    if not all_messages:
        print(f"[{wilma_url}] No messages. Nothing sent.")
        return

    all_messages.sort(key=lambda m: m.sent_ts)

    print(f"[{wilma_url}] Summarising {len(all_messages)} message(s) with Claude...")
    digest = summarize_messages(
        [
            {
                "student": m.student_name,
                "subject": m.subject,
                "sender": m.sender,
                "sent_label": m.sent_label,
                "body": m.body,
            }
            for m in all_messages
        ],
        api_key=api_key,
        language=language,
        prompt_template=prompt_template,
    )

    header = f"*Wilma Digest — {date.today().strftime('%-d.%-m.%Y')}*\n\n"
    full_text = header + digest

    if skip_telegram:
        print(full_text)
    else:
        bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
        chat_id = os.environ["TELEGRAM_CHAT_ID"]
        send_message(bot_token, chat_id, full_text)
        print(f"[{wilma_url}] Sent digest for {len(all_messages)} message(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Wilma message digest")
    parser.add_argument(
        "task_files", metavar="TASK_FILE", nargs="+",
        help="YAML task file(s) defining Wilma instance and options",
    )
    parser.add_argument(
        "--resend-last", metavar="N", type=int, default=None,
        help="Ignore unread status and digest the last N messages per student",
    )
    parser.add_argument(
        "--skip-telegram", action="store_true",
        help="Print digest to stdout instead of sending via Telegram",
    )
    args = parser.parse_args()

    load_dotenv()

    errors = []
    for path in args.task_files:
        try:
            task = load_task(path)
            run_task(task, args.resend_last, args.skip_telegram)
        except Exception as e:
            print(f"ERROR [{path}]: {e}", file=sys.stderr)
            errors.append(path)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
