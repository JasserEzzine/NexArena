import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, JSON, Index, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def now():
    return datetime.now(timezone.utc)


def uid():
    return str(uuid.uuid4())


class Role(Base):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(30), primary_key=True)
    permissions: Mapped[list] = mapped_column(JSON, default=list)


class Branch(Base):
    __tablename__ = "branches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    address: Mapped[str] = mapped_column(String(300), default="")


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(ForeignKey("roles.name"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Node(Base):
    __tablename__ = "nodes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    machine_id: Mapped[str] = mapped_column(String(100), unique=True)
    hostname: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(120))
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id"), index=True)
    ip_address: Mapped[str] = mapped_column(String(100), default="")
    os: Mapped[str] = mapped_column(String(200), default="")
    agent_version: Mapped[str] = mapped_column(String(30), default="")
    agent_secret_hash: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(20), default="OFFLINE")
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    telemetry: Mapped[dict] = mapped_column(JSON, default=dict)


class Wallet(Base):
    __tablename__ = "wallets"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    __table_args__ = (CheckConstraint("balance >= 0"),)


class GamingSession(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    node_id: Mapped[str] = mapped_column(ForeignKey("nodes.id"), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (Index("one_active_session_per_node", "node_id", unique=True, postgresql_where=text("status = 'ACTIVE'")), Index("one_active_session_per_user", "user_id", unique=True, postgresql_where=text("status = 'ACTIVE'")), CheckConstraint("rate > 0"))


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    type: Mapped[str] = mapped_column(String(30))
    reference: Mapped[str] = mapped_column(String(150), unique=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("sessions.id"), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MembershipPlan(Base):
    __tablename__ = "membership_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    duration_days: Mapped[int] = mapped_column(Integer, default=30)
    benefits: Mapped[str] = mapped_column(String(1000), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserMembership(Base):
    __tablename__ = "user_memberships"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("membership_plans.id"))
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expiration_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")


class Reservation(Base):
    __tablename__ = "reservations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    node_id: Mapped[str] = mapped_column(ForeignKey("nodes.id"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id"), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="CONFIRMED")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (CheckConstraint("end_time > start_time"),)


class Game(Base):
    __tablename__ = "games"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(1000), default="")
    genre: Mapped[str] = mapped_column(String(100), default="")
    version: Mapped[str] = mapped_column(String(50), default="")
    executable_path: Mapped[str] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[str] = mapped_column(String(500), default="")


class NodeGame(Base):
    __tablename__ = "node_games"
    node_id: Mapped[str] = mapped_column(ForeignKey("nodes.id"), primary_key=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), primary_key=True)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    node_id: Mapped[str] = mapped_column(ForeignKey("nodes.id"), index=True)
    type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(30), default="WARNING")
    message: Mapped[str] = mapped_column(String(500))
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Command(Base):
    __tablename__ = "commands"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    node_id: Mapped[str] = mapped_column(ForeignKey("nodes.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    result: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EsportsTeam(Base):
    __tablename__ = "esports_teams"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    tag: Mapped[str] = mapped_column(String(12), unique=True)
    city: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(1000), default="")
    color: Mapped[str] = mapped_column(String(7), default="#34d5c4")
    website: Mapped[str] = mapped_column(String(300), default="")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class PlayerProfile(Base):
    __tablename__ = "player_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    handle: Mapped[str] = mapped_column(String(40), unique=True)
    city: Mapped[str] = mapped_column(String(80))
    team_id: Mapped[str | None] = mapped_column(ForeignKey("esports_teams.id"), nullable=True, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class PlayerRanking(Base):
    __tablename__ = "player_rankings"
    user_id: Mapped[str] = mapped_column(ForeignKey("player_profiles.user_id"), primary_key=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, default=1000)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    peak_rating: Mapped[int] = mapped_column(Integer, default=1000)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint("rating >= 0 AND wins >= 0 AND losses >= 0", name="nonnegative_ranking"),)


class RankedResult(Base):
    __tablename__ = "ranked_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    reference: Mapped[str] = mapped_column(String(100), unique=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), index=True)
    winner_id: Mapped[str] = mapped_column(ForeignKey("player_profiles.user_id"))
    loser_id: Mapped[str] = mapped_column(ForeignKey("player_profiles.user_id"))
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    rating_delta: Mapped[int] = mapped_column(Integer)
    winner_rating: Mapped[int] = mapped_column(Integer)
    loser_rating: Mapped[int] = mapped_column(Integer)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint("winner_id <> loser_id", name="distinct_ranked_players"),)
