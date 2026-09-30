# Three-minute Phase 1 walkthrough

Before recording: start PostgreSQL, migrate, seed, start API and dashboard, and connect a Windows agent. Use a dedicated gaming PC for lock/shutdown demonstrations. Install one permitted game (or a harmless locally configured demonstration executable), assign it in the catalog, and configure the identical local allowlist entry. Never claim a seeded station is live before its agent connects.

| Time | Show |
|---|---|
| 0:00–0:20 | Sign in with `admin@nexarena.local`; introduce NexArena and the command center. |
| 0:20–0:45 | Show branches, real PC-01 status, current CPU/RAM readings, and sensor availability in station details. |
| 0:45–1:15 | Open a player's wallet, top up, start a session, show its running timer, then end and display the ledger deduction. |
| 1:15–1:40 | Show membership plans, assign a plan, create a reservation, and demonstrate an overlapping slot being rejected. |
| 1:40–2:10 | Open Game library, show station assignment, launch the allowlisted installed executable, and show the returned command result. |
| 2:10–2:35 | On the dedicated station, lock Windows and show the acknowledgment. Explain local credential-based unlocking. Demonstrate a detectable mouse/keyboard disconnect if hardware supports it. |
| 2:35–3:00 | Show alert resolution, staff's restricted controls, API docs, and the repository's test results. |

Use the password generated as `DEMO_PASSWORD` in `.env`; do not show `.env`, enrollment credentials, or JWTs in the video. Sample memberships use internal assignment, not a real payment gateway. Where a physical device action has not been tested, state that clearly rather than substituting fabricated telemetry or a false success message.
