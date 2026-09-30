import asyncio
import secrets
from contextlib import asynccontextmanager
from datetime import timedelta, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from pydantic import ValidationError
from .config import settings
from .db import get_db, SessionLocal
from .models import *
from .schemas import *
from .security import passwords, token, current_user, require, authenticate, digest
from .realtime import hub


def record(obj):
    hidden = {"password_hash", "agent_secret_hash", "token_version", "machine_id"}
    values = {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs if c.key not in hidden}
    return {k: str(v) if isinstance(v, Decimal) else v for k, v in values.items()}


def fetch(db, model, id):
    obj = db.get(model, id)
    if obj is None:
        raise HTTPException(404, f"{model.__name__} not found")
    return obj


def customer(db, id):
    u = fetch(db, User, id)
    if u.role != "CUSTOMER" or not u.active:
        raise HTTPException(400, "Select an active customer")
    return u


def bill(session, end):
    seconds = max(0, Decimal(str((end - session.start_time).total_seconds())))
    return (seconds * session.rate / Decimal(3600)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def finalize(db, session, end, cap=False):
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == session.user_id).with_for_update())
    amount = bill(session, end)
    if amount > wallet.balance:
        # Prepaid sessions stop at the exact affordable end time, never create debt.
        end = min(end, session.start_time + timedelta(seconds=float(wallet.balance / session.rate * 3600)))
        amount = min(wallet.balance, bill(session, end))
    wallet.balance -= amount
    session.end_time, session.cost, session.status = end, amount, "COMPLETED"
    db.add(WalletTransaction(user_id=session.user_id, amount=-amount, type="SESSION_PAYMENT", reference="session:" + session.id, session_id=session.id))


async def maintenance():
    while True:
        await asyncio.sleep(2)
        changed = False
        with SessionLocal() as db:
            stale = db.scalars(select(Node).where(Node.status == "ONLINE", Node.last_heartbeat < now() - timedelta(seconds=settings.heartbeat_timeout))).all()
            for node in stale:
                node.status = "OFFLINE"
                changed = True
            for command in db.scalars(select(Command).where(Command.status == "PENDING", Command.created_at < now() - timedelta(seconds=30))).all():
                command.status, command.result = "TIMEOUT", "Agent did not acknowledge within 30 seconds; execution outcome is unknown."
                changed = True
            for session in db.scalars(select(GamingSession).where(GamingSession.status == "ACTIVE").with_for_update(skip_locked=True)).all():
                wallet = db.scalar(select(Wallet).where(Wallet.user_id == session.user_id).with_for_update())
                reservation = db.scalar(select(Reservation).where(Reservation.node_id == session.node_id, Reservation.status == "CONFIRMED", Reservation.user_id != session.user_id, Reservation.start_time <= now(), Reservation.end_time > now()))
                if bill(session, now()) >= wallet.balance or reservation:
                    finalize(db, session, min(now(), reservation.start_time) if reservation else now(), cap=True)
                    db.add(Alert(node_id=session.node_id, type="SESSION_ENDED", message="Prepaid time ended or a reservation began. Staff must ensure the station is available."))
                    changed = True
            db.commit()
        if changed:
            await hub.publish()


@asynccontextmanager
async def lifespan(app):
    with SessionLocal() as db:
        for node in db.scalars(select(Node).where(Node.status == "ONLINE")):
            node.status = "OFFLINE"
        db.commit()
    task = asyncio.create_task(maintenance())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="NexArena API", version="1.0.0", lifespan=lifespan)
from .esports import router as esports_router
app.include_router(esports_router)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type", "X-Agent-Key", "X-Node-Id"])


@app.exception_handler(IntegrityError)
async def conflict(request, exc):
    return JSONResponse(status_code=409, content={"detail": "This operation conflicts with an existing record. Refresh and try again."})


@app.get("/api/health")
def health(db=Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "platform": "NexArena"}


@app.post("/api/auth/login")
def login(body: Login, db=Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not user.active or not passwords.verify(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect")
    return {"access_token": token(user), "token_type": "bearer", "user": record(user)}


@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return record(user)


@app.post("/api/auth/logout")
def logout(user=Depends(current_user), db=Depends(get_db)):
    user.token_version += 1
    db.commit()
    return {"ok": True}


@app.get("/api/users", dependencies=[Depends(require("read"))])
def users(db=Depends(get_db)):
    return [record(x) for x in db.scalars(select(User).order_by(User.name))]


@app.get("/api/users/{id}", dependencies=[Depends(require("read"))])
def user_detail(id: str, db=Depends(get_db)):
    return record(fetch(db, User, id))


@app.post("/api/users", dependencies=[Depends(require("admin"))], status_code=201)
async def add_user(body: UserInput, db=Depends(get_db)):
    u = User(name=body.name, email=body.email.lower(), role=body.role, password_hash=passwords.hash(body.password))
    db.add(u)
    db.flush()
    db.add(Wallet(user_id=u.id))
    db.commit()
    await hub.publish()
    return record(u)


@app.put("/api/users/{id}", dependencies=[Depends(require("admin"))])
async def edit_user(id: str, body: UserUpdate, actor=Depends(current_user), db=Depends(get_db)):
    u = fetch(db, User, id)
    if u.id == actor.id and (body.role != "ADMIN" or not body.active):
        raise HTTPException(400, "You cannot disable or demote your own account")
    for key, value in body.model_dump().items():
        setattr(u, key, value)
    u.token_version += 1
    db.commit()
    await hub.publish()
    return record(u)


@app.get("/api/branches", dependencies=[Depends(require("read"))])
def branches(db=Depends(get_db)):
    return [record(x) for x in db.scalars(select(Branch).order_by(Branch.name))]


@app.post("/api/branches", dependencies=[Depends(require("admin"))], status_code=201)
async def add_branch(body: BranchInput, db=Depends(get_db)):
    obj = Branch(**body.model_dump())
    db.add(obj)
    db.commit()
    await hub.publish()
    return record(obj)


@app.put("/api/branches/{id}", dependencies=[Depends(require("admin"))])
async def edit_branch(id: str, body: BranchInput, db=Depends(get_db)):
    obj = fetch(db, Branch, id)
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    await hub.publish()
    return record(obj)


@app.post("/api/nodes/register")
async def register(body: Register, request: Request, x_agent_key: str = Header(default=""), db=Depends(get_db)):
    if not secrets.compare_digest(x_agent_key, settings.agent_enrollment_key):
        raise HTTPException(401, "Invalid enrollment key")
    fetch(db, Branch, body.branch_id)
    node = db.scalar(select(Node).where(Node.machine_id == body.machine_id))
    if node and node.agent_secret_hash and not secrets.compare_digest(node.agent_secret_hash, digest(body.agent_secret)):
        raise HTTPException(403, "This machine is already enrolled with a different credential")
    if not node:
        node = Node(machine_id=body.machine_id)
        db.add(node)
    for k, v in body.model_dump(exclude={"agent_secret", "machine_id"}).items():
        setattr(node, k, v)
    node.ip_address = request.client.host
    node.agent_secret_hash = digest(body.agent_secret)
    db.commit()
    await hub.publish()
    return {"node_id": node.id}


def agent_node(db, id, secret):
    node = fetch(db, Node, id)
    if not secret or not secrets.compare_digest(node.agent_secret_hash, digest(secret)):
        raise HTTPException(401, "Invalid agent credential")
    return node


def update_telemetry(db, node, telemetry):
    values = telemetry.model_dump()
    for key in ["keyboard", "mouse"]:
        if values[key] is False and node.telemetry.get(key) is True:
            db.add(Alert(node_id=node.id, type="PERIPHERAL_DISCONNECTED", message=f"{key.capitalize()} disconnected from {node.name}"))
    node.telemetry = {**values, "timestamp": now().isoformat()}
    node.status, node.last_heartbeat = "ONLINE", now()


@app.post("/api/nodes/heartbeat")
async def heartbeat(body: Telemetry, x_node_id: str = Header(), x_agent_key: str = Header(), db=Depends(get_db)):
    node = agent_node(db, x_node_id, x_agent_key)
    update_telemetry(db, node, body)
    db.commit()
    await hub.publish("telemetry", {"node_id": node.id})
    return {"ok": True}


@app.get("/api/nodes", dependencies=[Depends(require("read"))])
def nodes(branch_id: str | None = None, db=Depends(get_db)):
    query = select(Node).order_by(Node.name)
    if branch_id:
        query = query.where(Node.branch_id == branch_id)
    return [record(x) for x in db.scalars(query)]


@app.get("/api/nodes/{id}", dependencies=[Depends(require("read"))])
def node_detail(id: str, db=Depends(get_db)):
    return record(fetch(db, Node, id))


@app.get("/api/nodes/{id}/telemetry", dependencies=[Depends(require("read"))])
def telemetry(id: str, db=Depends(get_db)):
    return fetch(db, Node, id).telemetry


@app.put("/api/nodes/{id}", dependencies=[Depends(require("admin"))])
async def edit_node(id: str, body: NodeUpdate, db=Depends(get_db)):
    node = db.scalar(select(Node).where(Node.id == id).with_for_update())
    if not node:
        raise HTTPException(404, "Station not found")
    fetch(db, Branch, body.branch_id)
    if body.branch_id != node.branch_id:
        if db.scalar(select(GamingSession).where(GamingSession.node_id == id, GamingSession.status == "ACTIVE")) or db.scalar(select(Reservation).where(Reservation.node_id == id, Reservation.status == "CONFIRMED", Reservation.end_time > now())):
            raise HTTPException(409, "Finish active sessions and cancel future reservations before moving this station")
    node.name, node.branch_id = body.name, body.branch_id
    db.commit()
    await hub.publish()
    return record(node)


@app.get("/api/sessions", dependencies=[Depends(require("read"))])
def sessions(branch_id: str | None = None, db=Depends(get_db)):
    q = select(GamingSession).join(Node)
    if branch_id:
        q = q.where(Node.branch_id == branch_id)
    return [{**record(s), "current_cost": bill(s, now()) if s.status == "ACTIVE" else s.cost} for s in db.scalars(q.order_by(GamingSession.start_time.desc()))]


@app.get("/api/sessions/active", dependencies=[Depends(require("read"))])
def active_sessions(db=Depends(get_db)):
    return [record(x) for x in db.scalars(select(GamingSession).where(GamingSession.status == "ACTIVE"))]


@app.post("/api/sessions/start", dependencies=[Depends(require("operate"))], status_code=201)
async def start_session(body: SessionStart, db=Depends(get_db)):
    customer(db, body.user_id)
    node = db.scalar(select(Node).where(Node.id == body.node_id).with_for_update())
    if not node or node.status != "ONLINE" or not node.last_heartbeat or node.last_heartbeat < now() - timedelta(seconds=settings.heartbeat_timeout):
        raise HTTPException(409, "The station is currently offline")
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == body.user_id).with_for_update())
    if not wallet or wallet.balance < body.rate / 60:
        raise HTTPException(409, "Insufficient balance: add at least one minute of credit")
    active = db.scalar(select(GamingSession).where(GamingSession.status == "ACTIVE", or_(GamingSession.node_id == node.id, GamingSession.user_id == body.user_id)))
    if active:
        raise HTTPException(409, "This station or customer already has an active session")
    reserved = db.scalar(select(Reservation).where(Reservation.node_id == node.id, Reservation.status == "CONFIRMED", Reservation.start_time <= now(), Reservation.end_time > now(), Reservation.user_id != body.user_id))
    if reserved:
        raise HTTPException(409, "This station is reserved for another customer")
    obj = GamingSession(**body.model_dump())
    db.add(obj)
    db.commit()
    await hub.publish("session_start")
    return record(obj)


@app.post("/api/sessions/{id}/stop", dependencies=[Depends(require("operate"))])
async def stop_session(id: str, db=Depends(get_db)):
    obj = db.scalar(select(GamingSession).where(GamingSession.id == id).with_for_update())
    if not obj:
        raise HTTPException(404, "Session not found")
    if obj.status != "ACTIVE":
        raise HTTPException(409, "This session has already been billed")
    finalize(db, obj, now())
    db.commit()
    await hub.publish("session_end")
    return record(obj)


@app.get("/api/users/{id}/wallet", dependencies=[Depends(require("read"))])
def wallet(id: str, db=Depends(get_db)):
    return record(fetch(db, Wallet, id))


@app.get("/api/users/{id}/wallet/transactions", dependencies=[Depends(require("read"))])
def transactions(id: str, db=Depends(get_db)):
    return [record(x) for x in db.scalars(select(WalletTransaction).where(WalletTransaction.user_id == id).order_by(WalletTransaction.created_at.desc()))]


@app.post("/api/users/{id}/wallet/topup", dependencies=[Depends(require("admin"))])
async def topup(id: str, body: TopUp, db=Depends(get_db)):
    customer(db, id)
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == id).with_for_update())
    reference = "topup:" + body.reference
    old = db.scalar(select(WalletTransaction).where(WalletTransaction.reference == reference))
    if old:
        if old.user_id != id or old.amount != body.amount:
            raise HTTPException(409, "The payment reference was already used")
        return record(wallet)
    wallet.balance += body.amount
    db.add(WalletTransaction(user_id=id, amount=body.amount, type="TOP_UP", reference=reference))
    db.commit()
    await hub.publish("wallet")
    return record(wallet)


@app.get("/api/membership-plans", dependencies=[Depends(require("read"))])
def plans(db=Depends(get_db)):
    return [record(x) for x in db.scalars(select(MembershipPlan).order_by(MembershipPlan.price))]


@app.post("/api/membership-plans", dependencies=[Depends(require("admin"))], status_code=201)
async def add_plan(body: PlanInput, db=Depends(get_db)):
    obj = MembershipPlan(**body.model_dump())
    db.add(obj)
    db.commit()
    await hub.publish()
    return record(obj)


@app.put("/api/membership-plans/{id}", dependencies=[Depends(require("admin"))])
async def edit_plan(id: str, body: PlanInput, db=Depends(get_db)):
    obj = fetch(db, MembershipPlan, id)
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    await hub.publish()
    return record(obj)


@app.get("/api/memberships", dependencies=[Depends(require("read"))])
def memberships(db=Depends(get_db)):
    return [{**record(x), "status": "ACTIVE" if x.expiration_date > now() else "EXPIRED"} for x in db.scalars(select(UserMembership))]


@app.post("/api/users/{id}/membership", dependencies=[Depends(require("admin"))])
async def assign_membership(id: str, body: MembershipInput, db=Depends(get_db)):
    customer(db, id)
    plan = fetch(db, MembershipPlan, body.plan_id)
    if not plan.active:
        raise HTTPException(409, "This membership plan is disabled")
    obj = db.get(UserMembership, id) or UserMembership(user_id=id)
    obj.plan_id, obj.start_date, obj.expiration_date, obj.status = plan.id, now(), now() + timedelta(days=plan.duration_days), "ACTIVE"
    db.add(obj)
    db.commit()
    await hub.publish()
    return record(obj)


@app.get("/api/reservations", dependencies=[Depends(require("read"))])
def reservations(branch_id: str | None = None, date: str | None = None, db=Depends(get_db)):
    q = select(Reservation)
    if branch_id:
        q = q.where(Reservation.branch_id == branch_id)
    if date:
        try:
            start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(422, "Date must be YYYY-MM-DD")
        q = q.where(Reservation.start_time < start + timedelta(days=1), Reservation.end_time > start)
    return [record(x) for x in db.scalars(q.order_by(Reservation.start_time))]


@app.get("/api/availability", dependencies=[Depends(require("read"))])
def availability(start_time: AwareDatetime, end_time: AwareDatetime, branch_id: str | None = None, db=Depends(get_db)):
    if end_time <= start_time:
        raise HTTPException(422, "End must be after start")
    occupied = select(Reservation.node_id).where(Reservation.status == "CONFIRMED", Reservation.start_time < end_time, Reservation.end_time > start_time)
    q = select(Node).where(Node.id.not_in(occupied))
    if branch_id:
        q = q.where(Node.branch_id == branch_id)
    return [record(x) for x in db.scalars(q)]


@app.post("/api/reservations", dependencies=[Depends(require("operate"))], status_code=201)
async def reserve(body: ReservationInput, db=Depends(get_db)):
    if body.end_time <= body.start_time or body.start_time < now():
        raise HTTPException(422, "Choose a future start and an end after the start")
    customer(db, body.user_id)
    node = db.scalar(select(Node).where(Node.id == body.node_id).with_for_update())
    if not node:
        raise HTTPException(404, "Station not found")
    existing = db.scalar(select(Reservation).where(Reservation.node_id == node.id, Reservation.status == "CONFIRMED", Reservation.start_time < body.end_time, Reservation.end_time > body.start_time))
    if existing:
        raise HTTPException(409, "This station is already reserved during that period")
    obj = Reservation(**body.model_dump(), branch_id=node.branch_id)
    db.add(obj)
    db.commit()
    await hub.publish("reservation")
    return record(obj)


@app.delete("/api/reservations/{id}", dependencies=[Depends(require("operate"))])
async def cancel_reservation(id: str, db=Depends(get_db)):
    obj = fetch(db, Reservation, id)
    obj.status = "CANCELLED"
    db.commit()
    await hub.publish("reservation")
    return record(obj)


@app.get("/api/games", dependencies=[Depends(require("read"))])
def games(db=Depends(get_db)):
    return [{**record(x), "node_ids": list(db.scalars(select(NodeGame.node_id).where(NodeGame.game_id == x.id)))} for x in db.scalars(select(Game).order_by(Game.name))]


@app.post("/api/games", dependencies=[Depends(require("admin"))], status_code=201)
async def add_game(body: GameInput, db=Depends(get_db)):
    obj = Game(**body.model_dump())
    db.add(obj)
    db.commit()
    await hub.publish()
    return record(obj)


@app.put("/api/games/{id}", dependencies=[Depends(require("admin"))])
async def edit_game(id: str, body: GameInput, db=Depends(get_db)):
    obj = fetch(db, Game, id)
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    await hub.publish()
    return record(obj)


@app.delete("/api/games/{id}", dependencies=[Depends(require("admin"))])
async def disable_game(id: str, db=Depends(get_db)):
    obj = fetch(db, Game, id)
    obj.active = False
    db.commit()
    await hub.publish()
    return record(obj)


@app.put("/api/nodes/{id}/games/{game_id}", dependencies=[Depends(require("admin"))])
async def associate_game(id: str, game_id: str, db=Depends(get_db)):
    fetch(db, Node, id)
    fetch(db, Game, game_id)
    if not db.get(NodeGame, (id, game_id)):
        db.add(NodeGame(node_id=id, game_id=game_id))
        db.commit()
    await hub.publish()
    return {"ok": True}


async def send_command(id, kind, actor, db, game_id=None):
    node = fetch(db, Node, id)
    if node.status != "ONLINE" or id not in hub.agents:
        raise HTTPException(409, "Unable to send command. Agent is offline.")
    payload = {"type": "command", "command": kind}
    if game_id:
        game = fetch(db, Game, game_id)
        if not game.active or not db.get(NodeGame, (id, game_id)):
            raise HTTPException(409, "Game is disabled or not assigned to this station")
        payload.update(game_id=game.id, executable_path=game.executable_path)
    command = Command(node_id=id, actor_id=actor.id, type=kind)
    db.add(command)
    db.commit()
    payload["command_id"] = command.id
    if not await hub.command(id, payload):
        command.status, command.result = "FAILED", "Agent connection was lost"
        db.commit()
    await hub.publish("command")
    return record(command)


@app.post("/api/nodes/{id}/lock")
async def lock(id: str, actor=Depends(require("remote")), db=Depends(get_db)):
    return await send_command(id, "LOCK_SCREEN", actor, db)


@app.post("/api/nodes/{id}/unlock")
async def unlock(id: str, actor=Depends(require("remote")), db=Depends(get_db)):
    raise HTTPException(409, "Windows requires the user to unlock locally with their credentials")


@app.post("/api/nodes/{id}/shutdown")
async def shutdown(id: str, actor=Depends(require("admin")), db=Depends(get_db)):
    return await send_command(id, "SHUTDOWN", actor, db)


@app.post("/api/nodes/{id}/launch-game")
async def launch(id: str, body: LaunchInput, actor=Depends(require("remote")), db=Depends(get_db)):
    return await send_command(id, "LAUNCH_GAME", actor, db, body.game_id)


@app.get("/api/commands", dependencies=[Depends(require("read"))])
def commands(db=Depends(get_db)):
    return [record(x) for x in db.scalars(select(Command).order_by(Command.created_at.desc()).limit(100))]


@app.get("/api/alerts", dependencies=[Depends(require("read"))])
def alerts(branch_id: str | None = None, db=Depends(get_db)):
    q = select(Alert).join(Node)
    if branch_id:
        q = q.where(Node.branch_id == branch_id)
    return [record(x) for x in db.scalars(q.order_by(Alert.created_at.desc()).limit(200))]


@app.get("/api/nodes/{id}/alerts", dependencies=[Depends(require("read"))])
def node_alerts(id: str, db=Depends(get_db)):
    return [record(x) for x in db.scalars(select(Alert).where(Alert.node_id == id).order_by(Alert.created_at.desc()).limit(100))]


@app.put("/api/alerts/{id}", dependencies=[Depends(require("operate"))])
async def resolve_alert(id: str, db=Depends(get_db)):
    obj = fetch(db, Alert, id)
    obj.read = obj.resolved = True
    db.commit()
    await hub.publish()
    return record(obj)


@app.websocket("/ws/dashboard")
async def dashboard_ws(ws: WebSocket):
    await ws.accept()
    try:
        auth = await asyncio.wait_for(ws.receive_json(), 10)
        value = auth.get("token", "")
        with SessionLocal() as db:
            user = authenticate(value, db)
            role = db.get(Role, user.role)
            if not role or not ("*" in role.permissions or "read" in role.permissions):
                await ws.close(code=1008)
                return
        hub.dashboards.add(ws)
        await ws.send_json({"event": "connected"})
        while True:
            await asyncio.wait_for(ws.receive_text(), 45)
            with SessionLocal() as db:
                authenticate(value, db)
    except (WebSocketDisconnect, HTTPException, asyncio.TimeoutError, ValueError):
        pass
    finally:
        hub.dashboards.discard(ws)
        try:
            await ws.close()
        except (RuntimeError, WebSocketDisconnect):
            pass


@app.websocket("/ws/agent/{id}")
async def agent_ws(ws: WebSocket, id: str):
    await ws.accept()
    enrolled = False
    try:
        auth = await asyncio.wait_for(ws.receive_json(), 10)
        with SessionLocal() as db:
            node = agent_node(db, id, auth.get("secret", ""))
            node.status, node.last_heartbeat = "ONLINE", now()
            db.commit()
        previous = hub.agents.get(id)
        if previous:
            await previous.close(code=1012)
        hub.agents[id] = ws
        enrolled = True
        await hub.publish("node_online")
        while True:
            data = await asyncio.wait_for(ws.receive_json(), settings.heartbeat_timeout)
            with SessionLocal() as db:
                node = fetch(db, Node, id)
                if data.get("type") == "telemetry":
                    update_telemetry(db, node, Telemetry.model_validate(data.get("data", {})))
                elif data.get("type") == "heartbeat":
                    node.status, node.last_heartbeat = "ONLINE", now()
                elif data.get("type") == "command_result":
                    command = db.get(Command, data.get("command_id"))
                    if command and command.node_id == id and command.status in ("PENDING", "TIMEOUT"):
                        command.status = "SUCCEEDED" if data.get("success") is True else "FAILED"
                        command.result = str(data.get("message", ""))[:1000]
                db.commit()
            await hub.publish(data.get("type", "refresh"), {"node_id": id})
    except (WebSocketDisconnect, HTTPException, asyncio.TimeoutError, ValueError, ValidationError):
        pass
    finally:
        if enrolled and hub.agents.get(id) is ws:
            hub.agents.pop(id, None)
            with SessionLocal() as db:
                node = db.get(Node, id)
                if node:
                    node.status = "OFFLINE"
                    db.commit()
            await hub.publish("node_offline")
        try:
            await ws.close()
        except (RuntimeError, WebSocketDisconnect):
            pass
