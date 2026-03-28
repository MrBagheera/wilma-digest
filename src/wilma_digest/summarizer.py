import anthropic


def summarize_messages(messages: list[dict], api_key: str) -> str:
    """
    Translate and summarize a list of Wilma messages into an English digest.

    Each message dict: {student, subject, sender, sent_label, body}
    Returns a formatted string ready to send via Telegram.
    """
    if not messages:
        return "No new messages today."

    client = anthropic.Anthropic(api_key=api_key)

    messages_text = ""
    for i, msg in enumerate(messages, 1):
        messages_text += f"""
--- Message {i} ---
Student: {msg['student']}
From: {msg['sender']}
Subject: {msg['subject']}
Sent: {msg['sent_label']}
Body:
{msg['body']}
"""

    prompt = f"""You are helping a parent by summarizing school messages from Wilma, a Finnish school portal.
The messages below are in Finnish. Summarize each one in Russian.

Rules:
- Output Russian only — do not quote or reproduce any Finnish text
- Group messages by student (child's name as a header)
- For each message: bold the subject, name the sender, and give a 2-4 sentence summary
- Highlight any action items or important dates

Messages:
{messages_text}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
