# Reef Messenger

**A local-first messenger** with an offline thread that always works, plus
optional IMAP/SMTP mail accounts.

- **Launch:** `python3 apps/Reef/main.py` or `Ctrl+Alt+Z`
- **Memory target:** ~40 MB
- **Engine:** pure Python stdlib (no Qt) — `apps/Reef/engine.py`

## Overview

Reef is built around a **Local Thread** — you can compose, store, and browse
messages entirely offline with no account and no network. Optional IMAP/SMTP
accounts add real mail sync on top. The engine is a pure-stdlib mail + store
layer; the GUI is a clean three-pane reader.

## Features

- **Offline-first** — the Local Thread works with zero configuration.
- **3-pane layout** — folder list | message list | message viewer.
- **Mail accounts** — label / email / password / hosts, stored locally in
  `~/.reef/accounts.json`. IMAP inbox sync with auto-dedupe by message ID;
  SMTP outbound via STARTTLS; Sent folder records outbound mail.
- **Background workers** — `RefreshWorker` + `SendWorker` `QThread`s keep IMAP
  and SMTP off the UI thread.
- **Dialogs** — Compose and Account dialogs; Reply from the viewer.

## Engine

`engine.py` (pure stdlib):
- `MailStore` — JSON persistence in `~/.reef/` (`accounts.json`,
  `messages.json`).
- `Account` / `Message` dataclasses.
- `fetch_inbox` via `imaplib` (RFC822 parse, newest N).
- `send_mail` via `smtplib` + STARTTLS.
- `append_local` for the offline thread.

## Data

| Location | Contents |
| :--- | :--- |
| `~/.reef/accounts.json` | IMAP/SMTP account config |
| `~/.reef/messages.json` | Local thread + synced messages |

Your credentials are stored in plain JSON locally — no cloud, no servers
besides the mail hosts you configure yourself.
