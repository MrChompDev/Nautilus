# Glossary

Nautilus names everything like a ship at sea. Decode table:

| Name | Meaning | Role |
| :--- | :--- | :--- |
| **Nautilus** | The chambered nautilus — a drifting vessel | The OS / desktop shell itself |
| **Core** | Ship's core systems | Shell code + design system (`core/`) |
| **Surfline** | The line where waves break | Web browser — your line onto the open web |
| **Abyssal** | Of the deep ocean | The IDE — where you dive into code |
| **Kraken** | Legendary sea monster | Agentic AI engine ([Kraken AI](Kraken-AI.md)) |
| **Riptide** | Strong offshore current | Audio hub — sound flowing through |
| **Cinema** | *(plain)* | Local media center |
| **Logbook** | A ship's record of journeys | Markdown notes app |
| **Mariner** | One who navigates the sea | Calculator with nautical units |
| **Current** | Ocean current | System telemetry — what's flowing through the machine |
| **Harbor** | Safe place to dock | File manager |
| **Tide** | Rising/falling sea level | Terminal |
| **Anchor** | What holds the ship steady | Settings / control center |
| **Reef** | Coral formation near shore | Messenger — close-quarters communication |

## Model personas (training assets)

The AI training data under `models/data/` uses sea-monster persona codenames:

| Persona | Domain corpus |
| :--- | :--- |
| **Kraken** | Code examples |
| **Leviathan** | General/large-scale model work |
| **Megalodon** | Model configuration/weights experiments |
| **Charybdis** | Mixed corpus + visual descriptions (whirlpool = data ingestion) |

## Design-language terms

- **Glass surfaces** — translucent bars (v2: warm-sand `rgba(212,200,176,200)`;
  v1 was navy glass over an ocean wallpaper).
- **Tokens** — named values from `core/theme.py`; see
  [Design System](Design-System.md).
