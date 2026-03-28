import argparse
import os
import sys
from datetime import date

from dotenv import load_dotenv

from wilma_digest.wilma import WilmaClient
from wilma_digest.summarizer import summarize_messages
from wilma_digest.telegram import send_message


def main() -> None:
    parser = argparse.ArgumentParser(description="Wilma message digest")
    parser.add_argument(
        "--resend-last", metavar="N", type=int, default=None,
        help="Ignore unread status and digest the last N messages per student",
    )
    args = parser.parse_args()

    load_dotenv()

    required = ["WILMA_EMAIL", "WILMA_PASSWORD", "ANTHROPIC_API_KEY",
                "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    email = os.environ["WILMA_EMAIL"]
    password = os.environ["WILMA_PASSWORD"]
    api_key = os.environ["ANTHROPIC_API_KEY"]
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    print(f"Logging in as {email}...")
    client = WilmaClient(email, password)
    client.login()

    students = client.get_students()
    if not students:
        print("No students found after login.", file=sys.stderr)
        sys.exit(1)
    print(f"Found students: {[s['name'] for s in students]}")

    all_messages = []
    for student in students:
        if args.resend_last is not None:
            msgs = client.get_last_messages(student["id"], args.resend_last)
            print(f"  {student['name']}: fetching last {args.resend_last} message(s)")
        else:
            msgs = client.get_unread_messages(student["id"])
            print(f"  {student['name']}: {len(msgs)} unread message(s)")
        for msg in msgs:
            msg.body = client.get_message_body(student["id"], msg.id)
            msg.student_name = student["name"]
        all_messages.extend(msgs)

    if not all_messages:
        print("No messages. Nothing sent.")
        return

    all_messages.sort(key=lambda m: m.sent_ts)

    print(f"Summarising {len(all_messages)} message(s) with Claude...")
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
    )

    header = f"*Дайджест Wilma — {date.today().strftime('%-d.%-m.%Y')}*\n\n"
    send_message(bot_token, chat_id, header + digest)
    print(f"Sent digest for {len(all_messages)} unread message(s).")


if __name__ == "__main__":
    main()
