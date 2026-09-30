import uuid
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select, func
from app.db import SessionLocal
from app.models import EsportsTeam, PlayerProfile, PlayerRanking, RankedResult, Wallet, Game, Node, GamingSession, Reservation, WalletTransaction
from app.seed_tunisia import seed_tunisia


def make_player(client, admin):
    unique = uuid.uuid4().hex
    user = client.post('/api/users', headers=admin, json={'name':'Ranking test','email':unique+'@rank.test','password':'test-password-2026'}).json()
    r = client.put('/api/players/'+user['id'], headers=admin, json={'handle':unique[:12], 'city':'Tunis'})
    assert r.status_code == 200, r.text
    return user['id']


def make_game(client, admin):
    return client.post('/api/games', headers=admin, json={'name':'Rank '+uuid.uuid4().hex, 'executable_path':'C:\\Games\\rank.exe'}).json()['id']


def test_elo_game_isolation_and_idempotency(client, admin):
    a,b = make_player(client,admin),make_player(client,admin)
    game,other = make_game(client,admin),make_game(client,admin)
    body={'game_id':game,'winner_id':a,'loser_id':b,'reference':uuid.uuid4().hex}
    r=client.post('/api/ranked-results',headers=admin,json=body)
    assert r.status_code==201,r.text
    assert r.json()['rating_delta']==16
    assert r.json()['winner_rating']==1016 and r.json()['loser_rating']==984
    repeated=client.post('/api/ranked-results',headers=admin,json=body)
    assert repeated.json()['id']==r.json()['id']
    board=client.get('/api/rankings',headers=admin,params={'game_id':game}).json()['entries']
    assert [(p['rating'],p['wins'],p['losses'],p['position']) for p in board]==[(1016,1,0,1),(984,0,1,2)]
    assert board[0]['streak']==1 and board[1]['streak']==-1
    assert client.get('/api/rankings',headers=admin,params={'game_id':other}).json()['entries']==[]
    assert client.post('/api/ranked-results',headers=admin,json={**body,'winner_id':b,'loser_id':a}).status_code==409


def test_ranked_permissions_validation_and_concurrency(client, admin, staff):
    a,b = make_player(client,admin),make_player(client,admin)
    game = make_game(client,admin)
    body={'game_id':game,'winner_id':a,'loser_id':b,'reference':uuid.uuid4().hex}
    assert client.get('/api/rankings',params={'game_id':game}).status_code==401
    assert client.post('/api/ranked-results',headers=staff,json=body).status_code==403
    assert client.put('/api/players/'+a,headers=staff,json={'handle':'blocked','city':'Tunis'}).status_code==403
    assert client.post('/api/ranked-results',headers=admin,json={**body,'loser_id':a}).status_code==422
    assert client.post('/api/ranked-results',headers=admin,json={**body,'loser_id':'missing'}).status_code==404
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:client.post('/api/ranked-results',headers=admin,json=body),range(2)))
    assert all(r.status_code==201 for r in responses)
    assert responses[0].json()['id']==responses[1].json()['id']
    results=client.get('/api/ranked-results',headers=staff,params={'game_id':game}).json()
    assert len(results)==1
    client.delete('/api/games/'+game,headers=admin)
    assert client.post('/api/ranked-results',headers=admin,json={**body,'reference':uuid.uuid4().hex}).status_code==409


def test_team_profiles_and_validation(client, admin, staff):
    tag='T'+uuid.uuid4().hex[:6].upper()
    body={'name':'Test '+tag,'tag':tag,'city':'Sousse','color':'#64c6a8','website':'https://example.com'}
    assert client.post('/api/teams',headers=staff,json=body).status_code==403
    team=client.post('/api/teams',headers=admin,json=body).json()
    player=make_player(client,admin)
    r=client.put('/api/players/'+player,headers=admin,json={'handle':tag+'player','city':'Sousse','team_id':team['id']})
    assert r.status_code==200
    listed=next(t for t in client.get('/api/teams',headers=staff).json() if t['id']==team['id'])
    assert listed['member_count']==1
    assert client.put('/api/teams/'+team['id'],headers=admin,json={**body,'color':'red;display:none'}).status_code==422
    assert client.put('/api/teams/'+team['id'],headers=admin,json={**body,'website':'javascript:alert(1)'}).status_code==422
    assert client.put('/api/players/'+player,headers=admin,json={'handle':tag+'player','city':'Sfax','team_id':None}).json()['team_id'] is None


def test_tunisian_seed_is_additive_repeat_safe_and_balanced(client, admin):
    seed_tunisia()
    def snapshot():
        with SessionLocal() as db:
            return {
                'counts': [db.scalar(select(func.count()).select_from(m)) for m in (EsportsTeam,PlayerProfile,RankedResult,GamingSession,Reservation)],
                'wallets': [(w.user_id,str(w.balance)) for w in db.scalars(select(Wallet).order_by(Wallet.user_id))],
                'nodes': [(n.id,n.status,n.telemetry) for n in db.scalars(select(Node).order_by(Node.id))],
                'ranks': [(r.user_id,r.game_id,r.rating,r.wins,r.losses) for r in db.scalars(select(PlayerRanking).order_by(PlayerRanking.user_id,PlayerRanking.game_id))],
            }
    before=snapshot()
    seed_tunisia()
    assert snapshot()==before
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(RankedResult).where(RankedResult.is_demo.is_(True)))==512
        profiles=list(db.scalars(select(PlayerProfile).where(PlayerProfile.is_demo.is_(True))))
        assert len(profiles)==16
        for p in profiles:
            balance=db.get(Wallet,p.user_id).balance
            ledger=db.scalar(select(func.sum(WalletTransaction.amount)).where(WalletTransaction.user_id==p.user_id))
            assert balance==ledger
        league=db.scalar(select(Game).where(Game.name=='League of Legends'))
        assert league.image_url=='/images/games/league-of-legends.jpg'
        ranks=list(db.scalars(select(PlayerRanking).where(PlayerRanking.game_id==league.id)))
        assert len(ranks)==16
        assert sum(r.rating for r in ranks)==16000
        assert sum(r.wins for r in ranks)==128==sum(r.losses for r in ranks)
    teams=client.get('/api/teams',headers=admin).json()
    assert {'GNG','JSK'}.issubset({t['tag'] for t in teams})
