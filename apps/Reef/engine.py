"""Reef engine — local-first mail + chat. Pure stdlib, never touches Qt.

Design: everything the user does works offline against a local JSON store.
IMAP/SMTP accounts are optional additions layered on top (imaplib/smtplib).
"""

from __future__ import annotations

import email
import email.utils
import hashlib
import imaplib
import json
import os
import smtplib
import time
from dataclasses import dataclass
from email.header import decode_header, make_header
from email.message import Message as EmailMessage


@dataclass
class Account:
    label: str
    email: str
    password: str
    imap_host: str = ""
    smtp_host: str = ""
    smtp_port: int = 587

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "email": self.email,
            "password": self.password,
            "imap_host": self.imap_host,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Account:
        return cls(
            label=d.get("label", "Mail"),
            email=d.get("email", ""),
            password=d.get("password", ""),
            imap_host=d.get("imap_host", ""),
            smtp_host=d.get("smtp_host", ""),
            smtp_port=int(d.get("smtp_port", 587)),
        )


@dataclass
class Message:
    id: str
    account: str
    folder: str
    subject: str
    sender: str = ""
    recipient: str = ""
    date: str = ""
    body: str = ""
    read: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "account": self.account,
            "folder": self.folder,
            "subject": self.subject,
            "sender": self.sender,
            "recipient": self.recipient,
            "date": self.date,
            "body": self.body,
            "read": self.read,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Message:
        return cls(
            id=d["id"],
            account=d.get("account", ""),
            folder=d.get("folder", ""),
            subject=d.get("subject", ""),
            sender=d.get("sender", ""),
            recipient=d.get("recipient", ""),
            date=d.get("date", ""),
            body=d.get("body", ""),
            read=d.get("read", False),
        )


def _decode(s) -> str:
    if not s:
        return ""
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return str(s)


def _extract_body(msg: EmailMessage) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
                except Exception:
                    continue
            if ctype == "text/html":
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
                except Exception:
                    continue
        return ""
    try:
        payload = msg.get_payload(decode=True)
        if not payload:
            return msg.get_payload() or ""
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    except Exception:
        return str(msg.get_payload() or "")


def fetch_inbox(account: Account, limit: int = 50) -> list[Message]:
    """Fetch the newest `limit` messages from the account's INBOX via IMAP."""
    server = imaplib.IMAP4_SSL(account.imap_host)
    server.login(account.email, account.password)
    server.select("INBOX", readonly=True)
    typ, data = server.search(None, "ALL")
    uids = data[0].split()[-limit:]
    messages: list[Message] = []
    for raw_uid in uids:
        try:
            typ, msg_data = server.fetch(raw_uid, "(RFC822)")
            if not msg_data or msg_data[0] is None:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            mid = hashlib.sha1(raw_uid + b":" + account.email.encode()).hexdigest()[:16]
            subject = _decode(msg.get("Subject"))
            sender = _decode(msg.get("From"))
            recipient = _decode(msg.get("To"))
            date = _decode(msg.get("Date")) or time.strftime("%a, %d %b %Y %H:%M")
            messages.append(
                Message(
                    id=mid,
                    account=account.label,
                    folder="inbox",
                    subject=subject or "(no subject)",
                    sender=sender,
                    recipient=recipient,
                    date=date,
                    body=_extract_body(msg),
                )
            )
        except Exception:
            continue
    server.logout()
    return messages


def send_mail(account: Account, to: str, subject: str, body: str) -> None:
    """Send a message through SMTP."""
    from email.mime.text import MIMEText

    mime = MIMEText(body, "plain", "utf-8")
    mime["Subject"] = subject
    mime["From"] = account.email
    mime["To"] = to
    mime["Date"] = email.utils.formatdate(localtime=True)

    server = smtplib.SMTP(account.smtp_host, account.smtp_port, timeout=30)
    server.starttls()
    server.login(account.email, account.password)
    server.sendmail(account.email, [to], mime.as_string())
    server.quit()


class MailStore:
    """JSON-backed persistence under ~/.reef (or a custom base dir)."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or os.path.join(os.path.expanduser("~"), ".reef")
        os.makedirs(self.base_dir, exist_ok=True)
        self.accounts_path = os.path.join(self.base_dir, "accounts.json")
        self.messages_path = os.path.join(self.base_dir, "messages.json")

    # ── accounts ──
    def load_accounts(self) -> list[Account]:
        try:
            with open(self.accounts_path, encoding="utf-8") as f:
                data = json.load(f)
            return [Account.from_dict(d) for d in data]
        except (OSError, json.JSONDecodeError):
            return []

    def save_accounts(self, accounts: list[Account]) -> None:
        with open(self.accounts_path, "w", encoding="utf-8") as f:
            json.dump([a.to_dict() for a in accounts], f, indent=2)

    # ── messages ──
    def load_messages(self) -> list[Message]:
        try:
            with open(self.messages_path, encoding="utf-8") as f:
                data = json.load(f)
            return [Message.from_dict(d) for d in data]
        except (OSError, json.JSONDecodeError):
            return []

    def save_messages(self, messages: list[Message]) -> None:
        with open(self.messages_path, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in messages], f, indent=2)

    def upsert_messages(self, new: list[Message]) -> list[Message]:
        """Merge new messages into the store, keyed by id. Returns the full list."""
        existing = {m.id: m for m in self.load_messages()}
        for m in new:
            if m.id not in existing:
                existing[m.id] = m
        merged = list(existing.values())
        merged.sort(key=lambda m: m.date or "")
        self.save_messages(merged)
        return merged

    # ── local chat thread (offline-first) ──
    def append_local(self, sender: str, body: str) -> Message:
        msg = Message(
            id=hashlib.sha1(f"local:{time.time()}:{sender}".encode()).hexdigest()[:16],
            account="Local",
            folder="local",
            subject=sender,
            sender=sender,
            recipient="Local",
            date=time.strftime("%a, %d %b %Y %H:%M"),
            body=body,
            read=True,
        )
        self.upsert_messages([msg])
        return msg
