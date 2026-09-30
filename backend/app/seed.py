from datetime import timedelta
from sqlalchemy import select
from .db import SessionLocal
from .models import *
from .security import passwords
from .config import settings


def seed():
    if len(settings.demo_password) < 10:
        raise RuntimeError("Set DEMO_PASSWORD (at least 10 characters) before seeding")
    with SessionLocal() as db:
        if db.scalar(select(User)):
            print("Database already seeded; no changes made.")
            return
        db.add_all([Role(name="ADMIN", permissions=["*"]), Role(name="STAFF", permissions=["read", "operate", "remote"]), Role(name="CUSTOMER", permissions=[])])
        db.flush()
        branches = [Branch(name="Tunis Gaming House", address="Les Berges du Lac, Tunis"), Branch(name="Sousse Gaming House", address="Sahloul, Sousse")]
        db.add_all(branches)
        people = [User(name=n, email=e, role=r, password_hash=passwords.hash(settings.demo_password)) for n, e, r in [("Arena Admin", "admin@nexarena.local", "ADMIN"), ("Arena Staff", "staff@nexarena.local", "STAFF"), ("Mohamed Naili", "mohamed@nexarena.local", "CUSTOMER"), ("Yasmine Ben Ali", "yasmine@nexarena.local", "CUSTOMER"), ("Amine Trabelsi", "amine@nexarena.local", "CUSTOMER")]]
        db.add_all(people)
        db.flush()
        for u in people:
            balance = Decimal("25.000") if u.role == "CUSTOMER" else Decimal(0)
            db.add(Wallet(user_id=u.id, balance=balance))
            if balance:
                db.add(WalletTransaction(user_id=u.id, amount=balance, type="TOP_UP", reference="seed:" + u.id))
        nodes = [Node(machine_id=f"demo-pc-{i:02}", hostname=f"PC-{i:02}", name=f"PC-{i:02}", branch_id=branches[0 if i < 4 else 1].id, os="Windows 11 · awaiting agent") for i in range(1, 5)]
        db.add_all(nodes)
        plans = [MembershipPlan(name=n, price=p, duration_days=30, description=d, benefits=b) for n, p, d, b in [("Free", 0, "Your next game starts here", "Standard station access;Community events"), ("Gamer", 50, "For the regulars", "Priority reservations;Member events;Community access"), ("Premium", 100, "The complete arena experience", "VIP station requests;Priority support;Member events")]]
        db.add_all(plans)
        games = [Game(name="Counter-Strike 2", genre="Tactical FPS", version="Steam", description="Every round counts.", executable_path=r"C:\Games\Counter-Strike Global Offensive\game\bin\win64\cs2.exe"), Game(name="VALORANT", genre="Tactical FPS", version="Riot", description="Defy the limits.", executable_path=r"C:\Riot Games\VALORANT\live\VALORANT.exe"), Game(name="Rocket League", genre="Sports", version="Epic", description="Take your shot.", executable_path=r"C:\Games\rocketleague\Binaries\Win64\RocketLeague.exe")]
        db.add_all(games)
        db.flush()
        db.add(UserMembership(user_id=people[2].id, plan_id=plans[1].id, start_date=now(), expiration_date=now() + timedelta(days=30)))
        db.add(Reservation(user_id=people[2].id, node_id=nodes[0].id, branch_id=nodes[0].branch_id, start_time=now() + timedelta(hours=2), end_time=now() + timedelta(hours=3)))
        for node in nodes:
            for game in games:
                db.add(NodeGame(node_id=node.id, game_id=game.id))
        db.commit()
        print("NexArena seeded. Stations remain offline until real agents connect.")


if __name__ == "__main__":
    seed()
