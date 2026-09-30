"""Additive, repeat-safe Tunisian showcase. Player rosters/results are fictional."""
import random
import uuid
from datetime import timedelta
from decimal import Decimal
from sqlalchemy import select
from .db import SessionLocal
from .models import *
from .security import passwords
from .config import settings
from .esports import apply_result


def demo_id(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "nexarena:tunisia-demo:v1:" + label))


def seed_tunisia():
    if len(settings.demo_password) < 10:
        raise RuntimeError("Set DEMO_PASSWORD before adding demo customers")
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.role == "ADMIN"))
        if not admin:
            raise RuntimeError("Run python -m app.seed first")
        game_specs = [
            ("Counter-Strike 2", "Tactical FPS", "Steam", "Precision, teamwork, and one more round. The arena's tactical classic.", r"C:\Games\Counter-Strike Global Offensive\game\bin\win64\cs2.exe", "counter-strike-2.jpg"),
            ("VALORANT", "Tactical FPS", "Riot", "Five agents. One objective. Find your next clutch with the Tunisian community.", r"C:\Riot Games\VALORANT\live\VALORANT.exe", "valorant.jpg"),
            ("League of Legends", "MOBA", "Riot", "From the first wave to the final Nexus. Meet your next duo on the Rift.", r"C:\Riot Games\League of Legends\LeagueClient.exe", "league-of-legends.jpg"),
            ("Rocket League", "Car football", "Epic", "Aerials, overtime, and impossible saves. Bring your squad to the pitch.", r"C:\Games\rocketleague\Binaries\Win64\RocketLeague.exe", "rocket-league.jpg"),
        ]
        games = []
        for name, genre, version, description, path, image in game_specs:
            game = db.scalar(select(Game).where(Game.name == name))
            if not game:
                game = Game(name=name, genre=genre, version=version, description=description, executable_path=path)
                db.add(game)
            if not game.image_url:
                game.image_url = "/images/games/" + image
            games.append(game)
        teams = []
        for name, tag, city, color, website, description in [
            ("GnG Esports", "GNG", "Tunis", "#ba9afa", "https://www.gngesports.gg/", "Gamers and Geeks. A Tunisian esports name, featured here with a fictional showcase roster."),
            ("JSK Esports", "JSK", "Kairouan", "#66d7a3", "https://tn.linkedin.com/company/jsk-esports", "Kairouan on the map. A Tunisian esports name, featured here with a fictional showcase roster."),
            ("Carthage Wolves", "CW", "Tunis", "#f5ba6a", "", "A fictional Tunis-based community squad for the NexArena demo."),
            ("Sahel Phoenix", "SPX", "Sousse", "#6bcdf0", "", "A fictional coastal community squad for the NexArena demo."),
        ]:
            team = db.scalar(select(EsportsTeam).where(EsportsTeam.tag == tag))
            if not team:
                team = EsportsTeam(name=name, tag=tag, city=city, color=color, website=website, description=description, is_demo=True)
                db.add(team)
            teams.append(team)
        db.flush()
        branches = list(db.scalars(select(Branch).order_by(Branch.name)))
        for name, address in [("Sfax Gaming House", "Route de Gremda, Sfax"), ("Kairouan Gaming House", "Centre-ville, Kairouan")]:
            branch = db.scalar(select(Branch).where(Branch.name == name))
            if not branch:
                branch = Branch(name=name, address=address)
                db.add(branch)
                db.flush()
            branches.append(branch)
        for i in range(5, 13):
            machine = f"demo-pc-{i:02}"
            if not db.scalar(select(Node).where(Node.machine_id == machine)):
                db.add(Node(machine_id=machine, hostname=f"PC-{i:02}", name=f"PC-{i:02}", branch_id=branches[(i-5) % len(branches)].id, os="Windows 11 · awaiting agent"))
        db.flush()
        nodes = list(db.scalars(select(Node).where(Node.machine_id.like("demo-pc-%")).order_by(Node.name)))
        for node in nodes:
            for game in games:
                if not db.get(NodeGame, (node.id, game.id)):
                    db.add(NodeGame(node_id=node.id, game_id=game.id))
        roster = [
            ("Aziz Ben Salem", "Azix", "Tunis"), ("Nour Ben Youssef", "Noura", "Ariana"),
            ("Youssef Gharbi", "Ghoul", "Bizerte"), ("Rania Trabelsi", "Ranya", "Tunis"),
            ("Ahmed Bouazizi", "Kair0", "Kairouan"), ("Mariem Saidi", "Mira", "Kairouan"),
            ("Oussama Jabri", "Ouss", "Sfax"), ("Wassim Chouchane", "Wass", "Monastir"),
            ("Fares Hamdi", "Fenix", "Tunis"), ("Ines Mansouri", "Iness", "La Marsa"),
            ("Seif Ben Amor", "SeifX", "Ben Arous"), ("Malek Dridi", "Malek", "Nabeul"),
            ("Bilel Chaabane", "Bilou", "Sousse"), ("Emna Jaziri", "Emna", "Sousse"),
            ("Khalil Messaoudi", "Khalix", "Mahdia"), ("Sarra Ben Salah", "Sora", "Monastir"),
        ]
        profiles = []
        demo_hash = passwords.hash(settings.demo_password)
        plans = list(db.scalars(select(MembershipPlan).where(MembershipPlan.active.is_(True)).order_by(MembershipPlan.price)))
        for i, (name, handle, city) in enumerate(roster):
            email = handle.lower() + "@demo.nexarena.local"
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                user = User(name=name, email=email, role="CUSTOMER", password_hash=demo_hash)
                db.add(user)
                db.flush()
                opening = Decimal(40 + i*3)
                db.add(Wallet(user_id=user.id, balance=opening))
                db.add(WalletTransaction(user_id=user.id, amount=opening, type="TOP_UP", reference="tunisia-demo:opening:" + user.id, created_at=now()-timedelta(days=10)))
            profile = db.get(PlayerProfile, user.id)
            if not profile:
                profile = PlayerProfile(user_id=user.id, handle=handle, city=city, team_id=teams[i//4].id, is_demo=True)
                db.add(profile)
            profiles.append(profile)
            if plans and not db.get(UserMembership, user.id):
                db.add(UserMembership(user_id=user.id, plan_id=plans[i % len(plans)].id, start_date=now()-timedelta(days=i%10), expiration_date=now()+timedelta(days=20+i%10)))
            db.flush()
            for j in range(2):
                session_id = demo_id(f"session:{i}:{j}")
                if db.get(GamingSession, session_id):
                    continue
                node = nodes[(i+j) % len(nodes)]
                end = now() - timedelta(hours=3+i*3+j, minutes=10)
                minutes = 45+(i*13+j*25) % 100
                cost = (Decimal(minutes) / 60 * 3).quantize(Decimal(".001"))
                wallet = db.get(Wallet, user.id)
                if wallet.balance < cost:
                    continue
                db.add(GamingSession(id=session_id, user_id=user.id, node_id=node.id, start_time=end-timedelta(minutes=minutes), end_time=end, rate=Decimal("3"), cost=cost, status="COMPLETED", is_demo=True))
                db.flush()
                wallet.balance -= cost
                db.add(WalletTransaction(user_id=user.id, amount=-cost, type="SESSION_PAYMENT", reference="tunisia-demo:session:"+session_id, session_id=session_id, created_at=end))
            reservation_id = demo_id(f"reservation:{i}")
            if not db.get(Reservation, reservation_id):
                node = nodes[i % len(nodes)]
                start = now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=2+(i//len(nodes))*3)
                overlap = db.scalar(select(Reservation).where(Reservation.node_id==node.id, Reservation.status=="CONFIRMED", Reservation.start_time<start+timedelta(hours=2), Reservation.end_time>start))
                if not overlap:
                    db.add(Reservation(id=reservation_id, user_id=user.id, node_id=node.id, branch_id=node.branch_id, start_time=start, end_time=start+timedelta(hours=2), is_demo=True))
        db.flush()
        rng = random.Random(2026)
        # Every demo rating is derived from this reproducible result ledger.
        for game_index, game in enumerate(games):
            for match in range(128):
                a, b = rng.sample(range(len(profiles)), 2)
                skill_a = ((a*7+game_index*5) % 17) + rng.random()*9
                skill_b = ((b*7+game_index*5) % 17) + rng.random()*9
                winner, loser = (a,b) if skill_a > skill_b else (b,a)
                reference = f"tunisia-demo:result:{game.id}:{match}"
                if db.scalar(select(RankedResult).where(RankedResult.reference==reference)):
                    continue
                apply_result(db, game.id, profiles[winner].user_id, profiles[loser].user_id, admin.id, reference, is_demo=True, played_at=now()-timedelta(hours=128-match, minutes=game_index*10))
        db.commit()
        print("Tunisian showcase ready: 4 games, 4 teams, 16 fictional player profiles, 512 sample ranked results. Existing records preserved; station telemetry unchanged.")


if __name__ == "__main__":
    seed_tunisia()
