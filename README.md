# MusicDigger ⛏

A social music platform where every post — a **DIG** — is a song paired with
the user's opinion. You can't just drop a link: you have to say why it matters.

Holberton School portfolio project.

---

## The idea

Music discovery today is locked inside opaque algorithms, and sharing songs
happens without context — a link in a group chat, no opinion, no conversation.

MusicDigger puts the opinion at the center. Users post DIGs, the community
reacts with upvotes and ReDigs, and a recommendation engine surfaces tracks
based on what people with similar taste have dug.

---

## Features

- **DIGs** — post a song with a mandatory opinion. Metadata is fetched
  automatically from Spotify, with YouTube as a fallback and manual entry as a
  last resort.
- **Trending** — public ranking, score = upvotes + 2 × ReDigs. Filterable by
  period and genre.
- **DigsCover** — recommends *tracks from the catalog*, not existing posts, so
  users can be the first to dig a song. Uses collaborative filtering.
- **Social** — follow curators, personal feed, public profiles.
- **Direct messages** — 1-to-1 conversations, with DIGs shareable in chat.
- **Search** — users, artists, albums, tracks, genres.

---

## Stack

| Layer | Tech |
| --- | --- |
| Back-end | Flask (Blueprints) + SQLAlchemy |
| Auth | Flask-JWT-Extended |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Front-end | Jinja2 + Tailwind CSS + Vanilla JS |
| External APIs | Spotify (primary), YouTube Data API (fallback) |

Architecture follows MVC with an added service layer: blueprints stay thin,
business logic lives in `app/services/`.

---

## Getting started

**Requirements:** Python 3.11+

```bash
git clone https://github.com/SedraR78/MusicDigger.git
cd MusicDigger

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy the environment template and fill it in:

```bash
cp .env.example .env
```

SECRET_KEY=
JWT_SECRET_KEY=
DATABASE_URL=sqlite:///musicdigger.db
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
YOUTUBE_API_KEY=


Generate the two secret keys:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Get Spotify credentials at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
(free, Client Credentials flow — no user login required).
YouTube key at [console.cloud.google.com](https://console.cloud.google.com)
(enable *YouTube Data API v3*).

Create the database and load demo data:

```bash
flask --app "app:create_app" db upgrade
python seed_big.py
```

The seed calls Spotify once per track, so it takes a few minutes. It is safe
to re-run — users and digs that already exist are skipped.

Run it:

```bash
flask --app "app:create_app" run --port 5006 --debug
```

Open http://127.0.0.1:5006 — log in with any seeded account
(`alex@musicdigger.test`, password `password123`).

---

## Pages

| Route | What it does |
| --- | --- |
| `/trending` | public ranking, filterable by period and genre |
| `/digscover` | recommendations — works without an account, personalized with one |
| `/feed` | digs from the people you follow |
| `/u/<username>` | public profile |
| `/artist/<name>` | every dig posted about an artist |
| `/people` | directory of diggers |
| `/messages` | 1-to-1 conversations, with DIGs shareable in chat |
| `/about` | what the project is and why |

---

## Project structure

app/
├── models/ # SQLAlchemy models (14 tables)
├── routes/ # Blueprints — thin controllers
├── services/ # Business logic, external APIs
├── templates/ # Jinja2 pages and components
└── static/js/ # Vanilla JS, Fetch API
migrations/ # Alembic migrations
seed_big.py # Demo data


---

## API

30 endpoints across 7 blueprints. All responses are JSON; protected routes
expect `Authorization: Bearer <token>`.

| Prefix | What it covers |
| --- | --- |
| `/api/auth` | register, login, refresh, profile, onboarding, account deletion |
| `/api/digs` | search, create, trending, feed, CRUD |
| `/api/digs/<id>` | upvote, redig, comments |
| `/api/users` | profiles, follow, followers |
| `/api/digscover` | recommendations, random dig |
| `/api/search` | global search and suggestions |
| `/api/conversations`, `/api/messages` | direct messaging |

Errors are uniform: `{"error": "...", "code": 400}`

---

## Some decisions worth explaining

**Triple fallback on song lookup.** Spotify first for clean metadata, YouTube
when the track isn't there (remixes, freestyles, mixtapes), manual entry if
both fail. Posting a DIG can never fail.

**The client never sends song metadata.** Only a source and an external ID —
the server fetches title, artist and cover itself. Users can't falsify a track.

**DigsCover recommends tracks, not DIGs.** Recommending existing posts would
only ever surface songs someone already posted. Recommending catalog tracks
means discovery produces content.

**Collaborative filtering over genre matching.** Spotify no longer exposes
genres through its API, so the main signal became behavioral: people who dug
the same songs as you also dug these. No external dependency, and it improves
as the platform is used.

**Denormalized counters.** Trending sorts the whole table by score, so upvote
and redig counts are stored on each DIG. A single `toggle()` method is the only
code allowed to modify them, keeping them in sync.

**Accounts are anonymized, not deleted.** Personal data is wiped and login
disabled, but posts and messages stay under "RetiredDigger" — otherwise other
users' conversations would lose chunks.

---

## Known limitations

- No automated test suite yet — endpoints validated manually, including error
  cases. Highest-priority technical debt.
- Rate limiting stored in memory, resets on restart. Redis in production.
- DigsCover scores up to 300 candidates in Python; SQL-side scoring would be
  needed at scale.
- Genres come from a local 611-artist mapping plus community tagging.
  Importing a MusicBrainz dump is the next step.
- Messages use polling, not WebSockets.
- The onboarding endpoint is implemented but has no dedicated UI yet.

---

## Author

Sedra Ramarosaona — [GitHub](https://github.com/SedraR78)
