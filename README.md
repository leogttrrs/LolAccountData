# LoL Personal Match History Pipeline

An end-to-end modular Data Engineering platform (ETL) developed in Python. This project extracts, transforms, and stores your personal League of Legends match history — enriching each game with performance stats and classifying your results by a custom performance tier.

## About the Project

This project was built to practice Data Engineering skills using a real-world API. The pipeline pulls your last 100 Ranked Solo/Duo and 100 Arena matches from the Riot Games API, runs pandas transformations to compute KDA, CS/min, and a performance flag, and loads everything into a PostgreSQL cloud database (Neon) for analytical SQL queries.

## Architecture & Data Flow

The architecture follows a modular ETL approach, where each phase is independent and can be run standalone or orchestrated centrally via `main.py`.

- **Extract:** Three sequential API calls to the Riot Games API — Riot ID → PUUID → Match IDs → Match Details. Rate limiting and 429 retries are handled automatically.
- **Transform:** Raw match JSON processed with `pandas`. Transformations include:
  - Exploding the participants array to isolate your own row from each match
  - Filtering remakes (early surrenders and games under 5 minutes)
  - Datetime parsing, patch extraction, and game duration conversion
  - **Feature Engineering:** KDA score, CS/min, and a `performance_flag` (`GREAT` / `GOOD` / `POOR`) with separate logic per queue type — win-based for Ranked, placement-based for Arena
- **Load:** Cleaned DataFrame upserted into a **PostgreSQL** cloud database (Neon) via SQLAlchemy, with `ON CONFLICT DO NOTHING` to make every run idempotent. An audit log is written to `pipeline_runs` after every execution.

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3 |
| Data Manipulation | Pandas + NumPy |
| Database | PostgreSQL (Neon) + SQLAlchemy |
| HTTP Requests | Requests |
| Environment | python-dotenv |

## Project Structure

```
/LolAccountData
├── ETLs/
│   ├── extract.py       # API calls: Riot ID → PUUID → match IDs → match details
│   ├── transform.py     # pandas transformations, feature engineering
│   └── load.py          # upsert to PostgreSQL, pipeline audit log
├── main.py              # orchestrator: runs extract → transform → load
├── requirements.txt
├── .env.example
└── README.md
```

## Target Tables

**`match_history`** — one row per match, upserted by `match_id`:

| Column | Type | Description |
|---|---|---|
| `match_id` | varchar (PK) | Riot match identifier |
| `queue_type` | varchar | `RANKED` or `ARENA` |
| `champion_name` | varchar | Champion played |
| `kills` / `deaths` / `assists` | int | Raw KDA stats |
| `kda_score` | float | `(kills + assists) / max(deaths, 1)` |
| `damage_dealt` | int | Total damage dealt to champions |
| `vision_score` | int | Vision score (Ranked only) |
| `cs_per_min` | float | Minions + jungle CS per minute (Ranked only) |
| `game_duration_min` | float | Game length in minutes |
| `win` | boolean | Match result |
| `placement` | int | Final placement (Arena only, 1–8) |
| `performance_flag` | varchar | `GREAT`, `GOOD`, or `POOR` |
| `played_at` | timestamp | Match start time |
| `patch` | varchar | Game patch (e.g. `16.7`) |

**`pipeline_runs`** — audit log, one row per execution:

| Column | Description |
|---|---|
| `run_id` | UUID |
| `started_at` / `finished_at` | Timestamps |
| `matches_processed` | Total matches fetched |
| `rows_inserted` | New rows added to `match_history` |
| `status` | `SUCCESS` or `FAILED` |
| `error_message` | Populated on failure |

---

## Setup

### 1. Clone the repository and install dependencies

```bash
git clone https://github.com/leogttrrs/LolAccountData.git
cd LolAcoountData
pip install -r requirements.txt
```

### 2. Get a Riot API Key

1. Go to [developer.riotgames.com](https://developer.riotgames.com) and log in with your League of Legends account
2. On the dashboard, copy your **Development API Key**

> Development keys expire every 24 hours. Regenerate yours on the same page whenever it expires. If you want a permanent key, apply for a **Personal API Key** on the Riot developer portal.

### 3. Get a Neon PostgreSQL database

1. Go to [neon.tech](https://neon.tech) and create a free account
2. Create a new project — Neon will provision a PostgreSQL database instantly
3. On the project dashboard, copy the **Connection String** (it looks like `postgresql://user:password@host.neon.tech/dbname`)

> The pipeline creates both tables automatically on the first run — no manual SQL setup needed.

### 4. Configure environment variables

Copy `.env.example` and rename it to `.env`, then fill in your credentials:

```env
RIOT_API_KEY=RGAPI-your-key-here
GAME_NAME=your summoner name
TAG_LINE=your tag (without the # symbol)
REGION=br1
ROUTING=americas
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname
```

> `REGION` is your server (e.g. `br1`, `na1`, `euw1`). `ROUTING` is the cluster used by match-v5 — BR1, NA1, and LAN all use `americas`. EUW/EUNE use `europe`. KR/JP use `asia`.

---

## How to Run

**Option A — Run everything orchestrated (recommended):**

```bash
python main.py
```

Runs the full extract → transform → load pipeline and logs the result to `pipeline_runs`.

**Option B — Run each phase individually** (useful for debugging):

```bash
python ETLs/extract.py
python ETLs/transform.py
python ETLs/load.py
```

Results will automatically populate the `match_history` table in your Neon PostgreSQL database. Re-running the pipeline is safe — duplicate matches are silently skipped.