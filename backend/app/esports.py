"""Local arena rankings; independent from publisher matchmaking ratings."""
from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from .db import get_db
from .models import EsportsTeam, PlayerProfile, PlayerRanking, RankedResult, User, Game, now
from .schemas import TeamInput, PlayerProfileInput, RankedResultInput
from .security import require
from .realtime import hub

router = APIRouter(prefix="/api", tags=["Tunisian esports"])


def serialize(obj):
    return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}


def get(db, model, id):
    obj = db.get(model, id)
    if not obj:
        raise HTTPException(404, f"{model.__name__} not found")
    return obj


def tier(rating):
    for threshold, label in [(1400, "Elite"), (1300, "Diamond"), (1200, "Platinum"), (1100, "Gold"), (1000, "Silver"), (900, "Bronze")]:
        if rating >= threshold:
            return label
    return "Rookie"


def apply_result(db, game_id, winner_id, loser_id, actor_id, reference, is_demo=False, played_at=None):
    # All writes for a game serialize on the game row, including first-time entries.
    # This also makes replayed references safe under concurrent requests.
    game = db.scalar(select(Game).where(Game.id == game_id).with_for_update())
    if not game:
        raise HTTPException(404, "Game not found")
    previous = db.scalar(select(RankedResult).where(RankedResult.reference == reference))
    if previous:
        if (previous.game_id, previous.winner_id, previous.loser_id) != (game_id, winner_id, loser_id):
            raise HTTPException(409, "This result reference was already used for a different result")
        return previous
    if not game.active:
        raise HTTPException(409, "Ranked results cannot be added to a disabled game")
    if winner_id == loser_id:
        raise HTTPException(422, "Choose two different players")
    rankings = []
    for id in (winner_id, loser_id):
        get(db, PlayerProfile, id)
        user = get(db, User, id)
        if not user.active or user.role != "CUSTOMER":
            raise HTTPException(409, "Both players must be active customers")
        ranking = db.get(PlayerRanking, (id, game_id))
        if not ranking:
            ranking = PlayerRanking(user_id=id, game_id=game_id, rating=1000, peak_rating=1000, wins=0, losses=0, streak=0)
            db.add(ranking)
        rankings.append(ranking)
    winner, loser = rankings
    exponent = max(-20, min(20, (loser.rating - winner.rating) / 400))
    expected = 1 / (1 + 10 ** exponent)
    delta = min(loser.rating, max(1, int(Decimal(str(32 * (1 - expected))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))))
    winner.rating += delta
    loser.rating -= delta
    winner.wins += 1
    loser.losses += 1
    winner.streak = max(0, winner.streak) + 1
    loser.streak = min(0, loser.streak) - 1
    for ranking in rankings:
        ranking.peak_rating = max(ranking.peak_rating, ranking.rating)
        ranking.updated_at = played_at or now()
    result = RankedResult(game_id=game_id, winner_id=winner_id, loser_id=loser_id, actor_id=actor_id, reference=reference, rating_delta=delta, winner_rating=winner.rating, loser_rating=loser.rating, is_demo=is_demo, created_at=played_at or now())
    db.add(result)
    db.flush()
    return result


@router.get("/teams", dependencies=[Depends(require("read"))])
def teams(db=Depends(get_db)):
    return [{**serialize(t), "member_count": db.scalar(select(func.count()).select_from(PlayerProfile).where(PlayerProfile.team_id == t.id))} for t in db.scalars(select(EsportsTeam).order_by(EsportsTeam.tag))]


@router.post("/teams", dependencies=[Depends(require("admin"))], status_code=201)
async def create_team(body: TeamInput, db=Depends(get_db)):
    team = EsportsTeam(**body.model_dump())
    db.add(team)
    db.commit()
    await hub.publish("esports")
    return serialize(team)


@router.put("/teams/{id}", dependencies=[Depends(require("admin"))])
async def update_team(id: str, body: TeamInput, db=Depends(get_db)):
    team = get(db, EsportsTeam, id)
    for key, value in body.model_dump().items():
        setattr(team, key, value)
    db.commit()
    await hub.publish("esports")
    return serialize(team)


@router.get("/players", dependencies=[Depends(require("read"))])
def players(db=Depends(get_db)):
    return [{**serialize(p), "name": u.name, "active": u.active, "team_tag": team.tag if team else None} for p, u, team in db.execute(select(PlayerProfile, User, EsportsTeam).join(User, User.id == PlayerProfile.user_id).outerjoin(EsportsTeam, EsportsTeam.id == PlayerProfile.team_id).order_by(PlayerProfile.handle))]


@router.put("/players/{user_id}", dependencies=[Depends(require("admin"))])
async def update_player(user_id: str, body: PlayerProfileInput, db=Depends(get_db)):
    user = get(db, User, user_id)
    if user.role != "CUSTOMER":
        raise HTTPException(422, "Only customers can have competitive player profiles")
    if body.team_id:
        get(db, EsportsTeam, body.team_id)
    profile = db.get(PlayerProfile, user_id) or PlayerProfile(user_id=user_id)
    for key, value in body.model_dump().items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    await hub.publish("esports")
    return serialize(profile)


@router.get("/rankings", dependencies=[Depends(require("read"))])
def rankings(game_id: str, team_id: str | None = None, search: str = "", db=Depends(get_db)):
    game = get(db, Game, game_id)
    query = select(PlayerRanking, PlayerProfile, User, EsportsTeam).join(PlayerProfile, PlayerProfile.user_id == PlayerRanking.user_id).join(User, User.id == PlayerRanking.user_id).outerjoin(EsportsTeam, EsportsTeam.id == PlayerProfile.team_id).where(PlayerRanking.game_id == game_id, User.active.is_(True), User.role == "CUSTOMER").order_by(PlayerRanking.rating.desc(), PlayerRanking.wins.desc(), PlayerRanking.losses, PlayerProfile.handle)
    entries = []
    last_key, position = None, 0
    for i, (r, p, u, team) in enumerate(db.execute(query), 1):
        key = (r.rating, r.wins, r.losses)
        if key != last_key:
            position, last_key = i, key
        if team_id and p.team_id != team_id:
            continue
        if search and search.lower() not in (p.handle + " " + u.name).lower():
            continue
        entries.append({**serialize(r), "position": position, "handle": p.handle, "name": u.name, "city": p.city, "team_id": p.team_id, "team_tag": team.tag if team else None, "team_color": team.color if team else "#8395ab", "is_demo": p.is_demo, "tier": tier(r.rating), "win_rate": round(100*r.wins/(r.wins+r.losses), 1) if r.wins+r.losses else 0})
    return {"game_id": game.id, "game_name": game.name, "system": "NexArena Elo", "starting_rating": 1000, "k_factor": 32, "entries": entries}


@router.get("/ranked-results", dependencies=[Depends(require("read"))])
def results(game_id: str, db=Depends(get_db)):
    get(db, Game, game_id)
    rows = db.scalars(select(RankedResult).where(RankedResult.game_id == game_id).order_by(RankedResult.created_at.desc(), RankedResult.id).limit(30))
    return [{**serialize(r), "winner_handle": get(db, PlayerProfile, r.winner_id).handle, "loser_handle": get(db, PlayerProfile, r.loser_id).handle} for r in rows]


@router.post("/ranked-results", status_code=201)
async def record_result(body: RankedResultInput, actor=Depends(require("admin")), db=Depends(get_db)):
    result = apply_result(db, body.game_id, body.winner_id, body.loser_id, actor.id, body.reference)
    db.commit()
    await hub.publish("esports", {"game_id": body.game_id})
    return serialize(result)
