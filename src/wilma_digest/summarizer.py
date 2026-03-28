import anthropic

DEFAULT_PROMPT_TEMPLATE = """\
You are helping a parent by summarizing school messages from a school portal.
The messages below may be in a foreign language. Summarize each one in {language}.

Rules:
- Output {language} only — do not quote or reproduce the original language text
- Group messages by student; use the full student name (including institution) as the section header
- For each message: bold the subject, name the sender, include the sent date, and give a 2-4 sentence summary
- Highlight any action items or important dates

Messages:
{messages_text}"""


def summarize_messages(
    messages: list[dict],
    api_key: str,
    language: str = "English",
    prompt_template: str | None = None,
) -> str:
    """
    Translate and summarize a list of Wilma messages into a digest.

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

    template = prompt_template if prompt_template is not None else DEFAULT_PROMPT_TEMPLATE
    prompt = template.format(language=language, messages_text=messages_text)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
