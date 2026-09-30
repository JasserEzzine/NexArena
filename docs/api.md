# API and realtime protocol

Interactive OpenAPI: `http://localhost:8000/docs` (JSON: `/openapi.json`). Monetary request values may be decimal strings; monetary responses use strings. Dates require timezone offsets. Errors use `detail`; validation errors include Pydantic's structured details. Authenticated routes require `Authorization: Bearer <token>`.

| Area | Routes |
|---|---|
| Auth | `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout` |
| Users | `GET/POST /api/users`, `GET/PUT /api/users/{id}` |
| Branches | `GET/POST /api/branches`, `PUT /api/branches/{id}` |
| Stations | `POST /api/nodes/register`, `POST /api/nodes/heartbeat`, `GET /api/nodes`, `GET/PUT /api/nodes/{id}` |
| Telemetry | `GET /api/nodes/{id}/telemetry`, `GET /api/nodes/{id}/alerts` |
| Sessions | `GET /api/sessions`, `GET /api/sessions/active`, `POST /api/sessions/start`, `POST /api/sessions/{id}/stop` |
| Wallets | `GET /api/users/{id}/wallet`, `POST /api/users/{id}/wallet/topup`, `GET /api/users/{id}/wallet/transactions` |
| Memberships | `GET/POST /api/membership-plans`, `PUT /api/membership-plans/{id}`, `GET /api/memberships`, `POST /api/users/{id}/membership` |
| Reservations | `GET/POST /api/reservations`, `DELETE /api/reservations/{id}`, `GET /api/availability` |
| Games | `GET/POST /api/games`, `PUT/DELETE /api/games/{id}`, `PUT /api/nodes/{id}/games/{game_id}` |
| Commands | `POST /api/nodes/{id}/lock`, `/unlock`, `/shutdown`, `/launch-game`; `GET /api/commands` |
| Alerts | `GET /api/alerts`, `PUT /api/alerts/{id}` (acknowledge and resolve) |
| Health | `GET /api/health` |

`branch_id` filters nodes, sessions, reservations, alerts and availability. Reservations also support `date=YYYY-MM-DD` (UTC day on the API). Availability requires `start_time` and `end_time`; it returns stations without a confirmed reservation overlap, not a guarantee of current network status or an unoccupied desktop. The UI shows active-session occupancy separately.

## Examples

Login:

```json
{"email":"admin@nexarena.local","password":"YOUR_LOCAL_DEMO_PASSWORD"}
```

Start session:

```json
{"node_id":"UUID","user_id":"UUID","rate":"3.000"}
```

Top-up:

```json
{"amount":"20.000","reference":"UNIQUE-PAYMENT-REFERENCE"}
```

Game launch:

```json
{"game_id":"UUID"}
```

## Dashboard WebSocket

Connect `/ws/dashboard`, then within 10 seconds send:

```json
{"token":"JWT"}
```

Server events use `{"event":"telemetry","data":{"node_id":"UUID"}}`. Events include `connected`, `refresh`, `node_online`, `node_offline`, `heartbeat`, `telemetry`, `session_start`, `session_end`, `wallet`, `reservation`, `command`, and `command_result`. Re-fetch relevant REST state on an event. Send a text `ping` every 20 seconds to keep the connection and auth check alive.

## Agent registration and WebSocket

Register at `/api/nodes/register` with header `X-Agent-Key: ENROLLMENT_KEY`:

```json
{"machine_id":"unique-stable-id","hostname":"PC-01","name":"PC-01","branch_id":"UUID","os":"Windows 11","agent_version":"1.0.0","agent_secret":"RANDOM-LOCAL-SECRET-AT-LEAST-32-CHARACTERS"}
```

Response: `{"node_id":"UUID"}`. Re-enrollment requires the same local secret. Connect `/ws/agent/{node_id}` and send `{"secret":"LOCAL_SECRET"}` within 10 seconds.

```json
{"type":"heartbeat"}
```

```json
{"type":"telemetry","data":{"cpu":42,"ram":61,"cpu_temperature":58,"gpu_temperature":64,"fan_rpm":1800,"keyboard":true,"mouse":true}}
```

Sensor values may be `null` when unavailable. REST fallback `/api/nodes/heartbeat` accepts the same telemetry object (without the wrapper) with `X-Node-Id` and `X-Agent-Key` containing the per-machine secret, not the enrollment key.

Server command:

```json
{"type":"command","command_id":"UUID","command":"LAUNCH_GAME","game_id":"UUID","executable_path":"C:\\Games\\game.exe"}
```

Agent acknowledgment:

```json
{"type":"command_result","command_id":"UUID","success":true,"message":"Game process started"}
```

Allowed commands are `LOCK_SCREEN`, `SHUTDOWN`, and `LAUNCH_GAME`. The `/unlock` endpoint explicitly returns 409 explaining that Windows requires local credentials.
