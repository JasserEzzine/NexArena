# Tunisian esports showcase

NexArena includes game artwork, a Tunisian team directory, competitive player profiles, and a separate **NexArena Elo ladder for every game**. This is a local arena ranking system. It does not fetch or impersonate official League of Legends, VALORANT, CS2, or Rocket League matchmaking ranks.

## Load the data

On an existing installation:

```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m app.seed_tunisia
```

Restart the API afterward. For new installations, `python -m app.seed` now includes this showcase automatically. The additional seed is additive and repeat-safe: it does not replace users, reset wallet balances, duplicate results, change configured executables, overwrite existing cover images, or manufacture online stations/telemetry.

The sample contains four games (including League of Legends), four teams, 16 fictional competitive profiles, 512 sample ranked results, 32 completed demo sessions, memberships, ledger-backed demo wallets, upcoming bookings, and 12 total seed stations across Tunis, Sousse, Sfax, and Kairouan. Reservations that conflict with an existing booking are skipped. Nodes remain offline until actual agents connect.

## Team references and sample data

[GnG Esports](https://www.gngesports.gg/) and [JSK Esports](https://www.linkedin.com/company/jsk-esports) are used as Tunisian team references. Their sample roster assignments are fictional and explicitly labeled; no official player affiliation, match record, current roster, endorsement, or national ranking is claimed. Carthage Wolves and Sahel Phoenix are fictional community teams. Team badges use original generic shields and initials rather than unofficial reproductions of official logos.

Game artwork comes from publisher-hosted Riot and Steam assets and is stored locally in `frontend/public/images/games`. See [asset credits](../frontend/public/images/CREDITS.txt) for each source and rights holder. Custom games can use an HTTPS cover URL or a local `/images/` path; the UI falls back to a gamepad if the image fails.

## Ranking rules

- Each player starts at **1,000 Elo for each game**, on their first recorded result.
- Admin records a winner and a distinct opponent through Player rankings → Record result.
- This models local head-to-head player challenges, including custom challenges within team games; it is not a 5v5 team-match or publisher API integration.
- Expected winner score: `1 / (1 + 10^((opponent_rating - winner_rating) / 400))`.
- Rating transfer: `round-half-up(32 × (1 − expected_score))`, minimum 1, capped by the loser's remaining rating so ratings never become negative.
- Both ratings, win/loss totals, current streaks and peak ratings update in one PostgreSQL transaction.
- The game row serializes concurrent results. Unique result references provide replay protection and reject conflicting reuse.
- Sort order: Elo descending, wins descending, losses ascending. Equal performance keys share a rank; handles provide stable ordering.
- Arena tiers: Rookie <900, Bronze 900+, Silver 1,000+, Gold 1,100+, Platinum 1,200+, Diamond 1,300+, Elite 1,400+. These are NexArena tiers, not official game ranks.
- Team changes do not reset player ratings. Archived/disabled customers are excluded from current ladders.
- Results for a disabled game cannot be added. Existing history remains readable.
- Demo ratings are calculated from the same result logic as real submissions; no arbitrary rating totals are inserted.

## API

| Route | Access | Purpose |
|---|---|---|
| `GET /api/teams` | Staff/admin | Team directory and player counts |
| `POST /api/teams`, `PUT /api/teams/{id}` | Admin | Team management |
| `GET /api/players` | Staff/admin | Competitive profiles |
| `PUT /api/players/{user_id}` | Admin | Create/edit a customer profile and team assignment |
| `GET /api/rankings?game_id=...` | Staff/admin | Per-game ladder; optional team_id and search |
| `GET /api/ranked-results?game_id=...` | Staff/admin | Latest 30 results |
| `POST /api/ranked-results` | Admin | Record an atomic rating update with game_id, winner_id, loser_id, reference |

`esports` WebSocket events refresh open ladders and team pages. The UI also refreshes every 15 seconds as a recovery path. The global branch filter applies to operational stations and sessions; the competitive ladder spans the Tunisian community and has its own team filter.

Browser tests record one additional VALORANT result between sample players in the local demo database. API tests run in an isolated PostgreSQL schema and verify game isolation, atomic/concurrent idempotency, permissions, validation, team assignments, seed repeat-safety, balanced wallet ledgers, and sample result totals.
