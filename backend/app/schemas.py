from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, AwareDatetime, ConfigDict


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Input):
    email: str
    password: str


class UserInput(Input):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=200)
    password: str = Field(min_length=10, max_length=128)
    role: Literal["ADMIN", "STAFF", "CUSTOMER"] = "CUSTOMER"


class UserUpdate(Input):
    name: str = Field(min_length=1, max_length=120)
    role: Literal["ADMIN", "STAFF", "CUSTOMER"]
    active: bool = True


class BranchInput(Input):
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(default="", max_length=300)


class Register(Input):
    machine_id: str = Field(min_length=1, max_length=100)
    hostname: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=120)
    branch_id: str
    os: str = Field(default="", max_length=200)
    agent_version: str = Field(default="1.0.0", max_length=30)
    agent_secret: str = Field(min_length=32, max_length=128)


class Telemetry(Input):
    cpu: float | None = Field(default=None, ge=0, le=100)
    ram: float | None = Field(default=None, ge=0, le=100)
    cpu_temperature: float | None = Field(default=None, ge=-50, le=150)
    gpu_temperature: float | None = Field(default=None, ge=-50, le=150)
    fan_rpm: float | None = Field(default=None, ge=0, le=50000)
    keyboard: bool | None = None
    mouse: bool | None = None


class NodeUpdate(Input):
    name: str = Field(min_length=1, max_length=120)
    branch_id: str


class SessionStart(Input):
    node_id: str
    user_id: str
    rate: Decimal = Field(default=Decimal("3.000"), gt=0, le=1000, decimal_places=3)


class TopUp(Input):
    amount: Decimal = Field(gt=0, le=100000, decimal_places=3)
    reference: str = Field(min_length=8, max_length=100)


class PlanInput(Input):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    price: Decimal = Field(ge=0, le=100000, decimal_places=3)
    duration_days: int = Field(default=30, ge=1, le=3650)
    benefits: str = Field(default="", max_length=1000)
    active: bool = True


class MembershipInput(Input):
    plan_id: str


class ReservationInput(Input):
    user_id: str
    node_id: str
    start_time: AwareDatetime
    end_time: AwareDatetime


class GameInput(Input):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    genre: str = Field(default="", max_length=100)
    version: str = Field(default="", max_length=50)
    executable_path: str = Field(min_length=1, max_length=500)
    active: bool = True
    image_url: str = Field(default="", max_length=500, pattern=r"^(https://[^\s]+|/images/[^\s]+)?$")


class LaunchInput(Input):
    game_id: str


class TeamInput(Input):
    name: str = Field(min_length=2, max_length=120)
    tag: str = Field(pattern=r"^[A-Z0-9]{2,12}$")
    city: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=1000)
    color: str = Field(default="#34d5c4", pattern=r"^#[0-9a-fA-F]{6}$")
    website: str = Field(default="", max_length=300, pattern=r"^(https://[^\s]+)?$")


class PlayerProfileInput(Input):
    handle: str = Field(min_length=2, max_length=40, pattern=r"^[\w.-]+$")
    city: str = Field(min_length=2, max_length=80)
    team_id: str | None = None


class RankedResultInput(Input):
    game_id: str
    winner_id: str
    loser_id: str
    reference: str = Field(min_length=8, max_length=100)
