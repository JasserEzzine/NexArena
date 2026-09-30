# Phase 1 verification

Verified locally on Windows with PostgreSQL 17.6, Python 3.14.4, Node 22.12.0, and .NET SDK 8.0.418. Final real-agent launch verification: 2026-09-30.

## Executed checks

| Check | Result |
|---|---|
| PostgreSQL database initialization | Passed, real local PostgreSQL |
| Alembic initial migration | Passed; frozen schema DDL with reservation exclusion constraint |
| Seed data and repeat-safe initialization | Passed |
| FastAPI startup and OpenAPI generation | Passed |
| PostgreSQL API integration suite | **10 passed** |
| React production build / TypeScript compile | Passed |
| Playwright browser suite | **2 passed**, desktop, tablet and mobile-width overflow checks |
| C# release build | Passed, 0 warnings / 0 errors |
| C# command safety suite | **9 passed** |
| Docker Compose configuration validation | Passed |
| Docker runtime / container image builds | Not verified: installed Docker Desktop engine did not start |

The Python test runner emits one upstream Starlette warning about future replacement of its `httpx` TestClient transport. It does not affect the passing tests.

## Flows verified

API tests exercise administrator login, rejected credentials, JWT revocation, staff permissions, unauthorized requests, agent enrollment, heartbeat, persisted telemetry, peripheral transition alerts, alert resolution, decimal session billing, wallet deductions, duplicate billing prevention, wallet top-up idempotency, concurrent top-ups, prepaid credit exhaustion, membership assignment, branch filtering, game configuration/assignment/disable, reservation availability/cancel/overlap/concurrency, WebSocket telemetry events, lock/shutdown/launch command routing, result acknowledgments, agent reconnect, and stale heartbeat detection.

Tests use a unique temporary PostgreSQL schema with an explicit migration version-table schema. An initial isolation issue was found, corrected, and all fixtures from that initial run were removed from the demo database. The final suite verifies that its node table actually exists in the isolated schema before running.

Browser tests exercise administrator and staff login, all dashboard pages, station details, a real wallet top-up write, membership forms, logout, live WebSocket connection indication, hidden admin-only controls for staff, and desktop/tablet/mobile layout checks. No browser runtime errors were recorded. Screenshots are in `docs/screenshots/`.

## Real C# agent evidence

PC-01 was enrolled against the local backend and displayed ONLINE in the React dashboard. Actual measurements included CPU load, RAM utilization, GPU temperature, keyboard presence, and mouse presence. CPU temperature and fan RPM were unavailable on this machine and remained `null`/`—`.

A harmless local C# executable was temporarily allowlisted and assigned to PC-01. A launch request traveled from REST through WebSocket to the real agent, which started the executable. The executable wrote a UTC timestamp to disk; the API recorded the agent's SUCCEEDED acknowledgment. This verifies actual executable launch, not a simulated agent result. It does **not** claim that Counter-Strike, VALORANT, or Rocket League are installed or individually tested.

A shutdown request delivered to the real agent was correctly rejected because `EnableShutdown` was false. The local agent was restored to its original **monitoring-only** configuration afterward. No actual Windows shutdown or screen lock was executed on the developer's computer.

## Remaining acceptance boundaries

- Docker image execution needs a functioning Docker Linux engine. Compose syntax/configuration was validated only.
- Physical Windows lock, enabled shutdown, and real installed-game behavior still need acceptance on a dedicated gaming station. The native implementations build and command routing is tested.
- Peripheral removal alerts were verified with protocol fixtures; physically unplugging devices and virtual-device edge cases need testing on the target PCs.
- Sensor availability varies with hardware, drivers, and permissions.
- CI configuration is included but has not run on GitHub until the repository is pushed and Actions executes it.
- The source was pushed to the public [JasserEzzine/NexArena](https://github.com/JasserEzzine/NexArena) repository on 2026-09-30. A demo video script is included; no video was recorded.

These boundaries are intentionally separate from implemented features; they should not be described as completed physical or deployment acceptance tests.
