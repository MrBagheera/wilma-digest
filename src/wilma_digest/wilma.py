import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

BASE_URL = "https://espoo.inschool.fi"


@dataclass
class Message:
    id: str
    subject: str
    sender: str
    sent_ts: int        # Unix timestamp (seconds)
    sent_label: str     # Human-readable date as shown in Wilma
    body: str = ""
    student_name: str = ""


class WilmaClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

    def login(self) -> None:
        # Fetch fresh SESSIONID (JWT) from the login page
        r = self.session.get(f"{BASE_URL}/login")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        form = soup.find("form")
        if not form:
            raise RuntimeError("Could not find login form")

        data = {
            inp["name"]: inp.get("value", "")
            for inp in form.find_all("input")
            if inp.get("name")
        }
        data["Login"] = self.email
        data["Password"] = self.password

        r = self.session.post(f"{BASE_URL}/login", data=data, allow_redirects=True)
        r.raise_for_status()

        if r.url.rstrip("/").endswith("/login"):
            raise RuntimeError("Login failed — check WILMA_EMAIL / WILMA_PASSWORD")

    def get_students(self) -> list[dict]:
        r = self.session.get(f"{BASE_URL}/")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        students = []
        seen: set[str] = set()
        # Student links appear in the user-menu dropdown as /!{id} (no trailing path)
        for a in soup.find_all("a", href=re.compile(r"^/!\d+/?$")):
            sid = re.search(r"/!(\d+)", a["href"]).group(1)
            name = a.get_text(strip=True)
            if sid not in seen and name:
                seen.add(sid)
                students.append({"id": sid, "name": name})
        return students

    def _parse_message_list(self, items: list[dict]) -> list[Message]:
        from datetime import datetime
        messages = []
        for item in items:
            ts_str = item.get("TimeStamp", "")
            try:
                sent_ts = int(datetime.strptime(ts_str, "%Y-%m-%d %H:%M").timestamp())
            except ValueError:
                sent_ts = 0
            messages.append(Message(
                id=str(item["Id"]),
                subject=item.get("Subject", ""),
                sender=item.get("Sender", ""),
                sent_ts=sent_ts,
                sent_label=ts_str,
            ))
        return messages

    def get_unread_messages(self, student_id: str) -> list[Message]:
        """Return all unread messages (Status==1) via the JSON list API."""
        r = self.session.get(f"{BASE_URL}/!{student_id}/messages/list")
        r.raise_for_status()
        data = r.json()

        unread = [item for item in data.get("Messages", []) if item.get("Status") == 1]
        return self._parse_message_list(unread)

    def get_last_messages(self, student_id: str, n: int) -> list[Message]:
        """Return the N most recent messages regardless of read status."""
        r = self.session.get(f"{BASE_URL}/!{student_id}/messages/list")
        r.raise_for_status()
        data = r.json()
        return self._parse_message_list(data.get("Messages", [])[:n])

    def get_message_body(self, student_id: str, message_id: str) -> str:
        r = self.session.get(f"{BASE_URL}/!{student_id}/messages/{message_id}")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        main = soup.find("main")
        if not main:
            return ""

        # Remove modal dialogs and the header table (sender/recipient/date)
        for el in main.find_all(True, class_=re.compile(r"modal|dialog")):
            el.decompose()
        for el in main.find_all("table"):
            el.decompose()
        # Remove hidden inputs
        for el in main.find_all("input"):
            el.decompose()

        return main.get_text(separator="\n", strip=True)
