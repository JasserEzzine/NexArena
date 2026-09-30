import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from sqlalchemy import select
from app.config import settings
from app.db import SessionLocal
from app.models import GamingSession, Wallet, Node, now
from app.main import bill


def player(client, headers):
    unique = uuid.uuid4().hex
    r = client.post("/api/users", headers=headers, json={"name":"Integration player", "email":unique+"@test.local", "password":"test-password-2026", "role":"CUSTOMER"})
    assert r.status_code == 201, r.text
    id = r.json()["id"]
    client.post(f"/api/users/{id}/wallet/topup", headers=headers, json={"amount":"25.000", "reference":unique})
    return id


def heartbeat(client, enrolled, **extra):
    id, secret = enrolled
    return client.post("/api/nodes/heartbeat", headers={"X-Node-Id":id, "X-Agent-Key":secret}, json={"cpu":42, "ram":61, "keyboard":True, "mouse":True, **extra})


def test_login_logout_and_permissions(client, admin, staff):
    assert client.get("/api/nodes").status_code == 401
    assert client.post("/api/auth/login", json={"email":"admin@nexarena.local", "password":"wrong"}).status_code == 401
    assert client.get("/api/auth/me", headers=admin).json()["role"] == "ADMIN"
    assert client.get("/api/nodes", headers=staff).status_code == 200
    assert client.post("/api/branches", headers=staff, json={"name":"Forbidden"}).status_code == 403
    assert client.post("/api/membership-plans", headers=staff, json={"name":"Forbidden", "price":0}).status_code == 403
    client.post("/api/auth/logout", headers=staff)
    assert client.get("/api/auth/me", headers=staff).status_code == 401


def test_registration_telemetry_and_alerts(client, admin, enrolled):
    id, secret = enrolled
    assert client.post("/api/nodes/register", json={"machine_id":"unauthorized", "hostname":"x", "name":"x", "branch_id":"x", "agent_secret":secret}).status_code == 401
    assert heartbeat(client,enrolled).status_code == 200
    node = client.get(f"/api/nodes/{id}", headers=admin).json()
    assert node["status"] == "ONLINE"
    assert node["telemetry"]["cpu"] == 42
    assert "agent_secret_hash" not in node
    assert node["last_heartbeat"]
    heartbeat(client,enrolled,mouse=False)
    heartbeat(client,enrolled,mouse=False)
    alerts = client.get(f"/api/nodes/{id}/alerts",headers=admin).json()
    assert len(alerts) == 1 and "Mouse disconnected" in alerts[0]["message"]
    assert client.put('/api/alerts/'+alerts[0]['id'],headers=admin).json()['resolved']
    assert heartbeat(client,enrolled,cpu=101).status_code == 422


def test_session_billing_wallet_and_duplicate_guards(client, admin, staff, enrolled):
    id, _ = enrolled
    user_id = player(client,admin)
    heartbeat(client,enrolled)
    body={"node_id":id,"user_id":user_id,"rate":"3.000"}
    r=client.post('/api/sessions/start',headers=staff,json=body)
    assert r.status_code==201,r.text
    session_id=r.json()['id']
    assert client.post('/api/sessions/start',headers=staff,json=body).status_code==409
    with SessionLocal() as db:
        session=db.get(GamingSession,session_id)
        session.start_time=now()-timedelta(hours=1,minutes=30)
        assert bill(session,session.start_time+timedelta(hours=1,minutes=30))==Decimal('4.500')
        db.commit()
    result=client.post(f'/api/sessions/{session_id}/stop',headers=staff)
    assert result.status_code==200,result.text
    assert abs(Decimal(result.json()['cost'])-Decimal('4.500'))<Decimal('.010')
    balance=Decimal(client.get(f'/api/users/{user_id}/wallet',headers=admin).json()['balance'])
    assert abs(balance-Decimal('20.500'))<Decimal('.010')
    assert client.post(f'/api/sessions/{session_id}/stop',headers=admin).status_code==409
    transactions=client.get(f'/api/users/{user_id}/wallet/transactions',headers=admin).json()
    assert len([t for t in transactions if t['type']=='SESSION_PAYMENT'])==1
    assert client.post('/api/sessions/missing/stop',headers=admin).status_code==404


def test_wallet_topup_idempotency_and_insufficient_balance(client,admin,staff,enrolled):
    id=player(client,admin)
    body={"amount":"10.123","reference":uuid.uuid4().hex}
    assert client.post(f'/api/users/{id}/wallet/topup',headers=staff,json=body).status_code==403
    first=client.post(f'/api/users/{id}/wallet/topup',headers=admin,json=body).json()
    second=client.post(f'/api/users/{id}/wallet/topup',headers=admin,json=body).json()
    assert first==second and Decimal(second['balance'])==Decimal('35.123')
    assert client.post(f'/api/users/{id}/wallet/topup',headers=admin,json={**body,'amount':'99'}).status_code==409
    with SessionLocal() as db:
        db.get(Wallet,id).balance=0
        db.commit()
    heartbeat(client,enrolled)
    assert client.post('/api/sessions/start',headers=admin,json={'user_id':id,'node_id':enrolled[0]}).status_code==409


def test_memberships_branch_filters_and_games(client,admin,enrolled):
    user=player(client,admin)
    plan=client.post('/api/membership-plans',headers=admin,json={'name':'Test '+uuid.uuid4().hex,'price':'50','benefits':'Priority;Events'}).json()
    r=client.post(f'/api/users/{user}/membership',headers=admin,json={'plan_id':plan['id']})
    assert r.status_code==200 and r.json()['status']=='ACTIVE'
    branches=client.get('/api/branches',headers=admin).json()
    nodes=client.get('/api/nodes',headers=admin,params={'branch_id':branches[0]['id']}).json()
    assert all(n['branch_id']==branches[0]['id'] for n in nodes)
    g=client.post('/api/games',headers=admin,json={'name':'Test game','executable_path':'C:\\Games\\test.exe'}).json()
    assert client.put(f"/api/nodes/{enrolled[0]}/games/{g['id']}",headers=admin).status_code==200
    assert client.delete('/api/games/'+g['id'],headers=admin).json()['active'] is False


def test_reservations_overlap_cancel_and_availability(client,admin,enrolled):
    user=player(client,admin)
    start=now()+timedelta(days=1)
    body={'user_id':user,'node_id':enrolled[0],'start_time':start.isoformat(),'end_time':(start+timedelta(hours=2)).isoformat()}
    r=client.post('/api/reservations',headers=admin,json=body)
    assert r.status_code==201,r.text
    assert client.post('/api/reservations',headers=admin,json={**body,'start_time':(start+timedelta(hours=1)).isoformat()}).status_code==409
    available=client.get('/api/availability',headers=admin,params={'start_time':body['start_time'],'end_time':body['end_time']}).json()
    assert enrolled[0] not in [n['id'] for n in available]
    assert client.post('/api/reservations',headers=admin,json={**body,'end_time':body['start_time']}).status_code==422
    assert client.delete('/api/reservations/'+r.json()['id'],headers=admin).json()['status']=='CANCELLED'
    assert client.post('/api/reservations',headers=admin,json=body).status_code==201


def test_websocket_commands_results_and_reconnect(client,admin,staff,enrolled):
    id,secret=enrolled
    with client.websocket_connect('/ws/dashboard') as dashboard:
        dashboard.send_json({'token':admin['Authorization'][7:]})
        assert dashboard.receive_json()['event']=='connected'
        with client.websocket_connect('/ws/agent/'+id) as agent:
            agent.send_json({'secret':secret})
            assert dashboard.receive_json()['event']=='node_online'
            agent.send_json({'type':'telemetry','data':{'cpu':37,'ram':52,'keyboard':True,'mouse':True}})
            assert dashboard.receive_json()['event']=='telemetry'
            assert client.get('/api/nodes/'+id+'/telemetry',headers=admin).json()['cpu']==37
            for kind in ['lock','shutdown']:
                r=client.post(f'/api/nodes/{id}/{kind}',headers=admin)
                assert r.status_code==200
                received=agent.receive_json()
                assert received['command']=='LOCK_SCREEN' if kind=='lock' else received['command']=='SHUTDOWN'
                agent.send_json({'type':'command_result','command_id':received['command_id'],'success':False,'message':'Test fixture: no OS action executed'})
                # Consume events until acknowledgment is committed.
                while dashboard.receive_json()['event']!='command_result':
                    pass
                commands=client.get('/api/commands',headers=admin).json()
                assert next(c for c in commands if c['id']==received['command_id'])['status']=='FAILED'
            assert client.post(f'/api/nodes/{id}/shutdown',headers=staff).status_code==403
            assert client.post(f'/api/nodes/{id}/unlock',headers=admin).status_code==409
            game=client.get('/api/games',headers=admin).json()[0]
            client.put(f"/api/nodes/{id}/games/{game['id']}",headers=admin)
            r=client.post(f'/api/nodes/{id}/launch-game',headers=admin,json={'game_id':game['id']})
            assert r.status_code==200,r.text
            assert agent.receive_json()['command']=='LAUNCH_GAME'
        # Wait for disconnect event, skipping preceding refreshes.
        while dashboard.receive_json()['event']!='node_offline':
            pass
        assert client.get('/api/nodes/'+id,headers=admin).json()['status']=='OFFLINE'
        assert client.post(f'/api/nodes/{id}/lock',headers=admin).status_code==409
        with client.websocket_connect('/ws/agent/'+id) as agent:
            agent.send_json({'secret':secret})
            assert dashboard.receive_json()['event']=='node_online'


def test_stale_heartbeat_detection(client,admin,enrolled):
    heartbeat(client,enrolled)
    with SessionLocal() as db:
        db.get(Node,enrolled[0]).last_heartbeat=now()-timedelta(seconds=settings.heartbeat_timeout+5)
        db.commit()
    time.sleep(2.5)
    assert client.get('/api/nodes/'+enrolled[0],headers=admin).json()['status']=='OFFLINE'


def test_concurrent_reservations(client,admin,enrolled):
    user=player(client,admin)
    start=now()+timedelta(days=2)
    body={'user_id':user,'node_id':enrolled[0],'start_time':start.isoformat(),'end_time':(start+timedelta(hours=1)).isoformat()}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(client.post,'/api/reservations',headers=admin,json=body) for _ in range(2)]
    assert sorted(f.result().status_code for f in futures)==[201,409]


def test_prepaid_expiration_and_concurrent_topups(client,admin,enrolled):
    id=player(client,admin)
    body={"amount":"1.000","reference":uuid.uuid4().hex}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(client.post,f'/api/users/{id}/wallet/topup',headers=admin,json=body) for _ in range(2)]
    assert all(f.result().status_code==200 for f in futures)
    assert client.get(f'/api/users/{id}/wallet',headers=admin).json()['balance']=='26.000'
    heartbeat(client,enrolled)
    r=client.post('/api/sessions/start',headers=admin,json={'node_id':enrolled[0],'user_id':id,'rate':'3'})
    assert r.status_code==201
    with SessionLocal() as db:
        session=db.get(GamingSession,r.json()['id'])
        session.start_time=now()-timedelta(hours=10)
        db.commit()
    time.sleep(2.5)
    assert client.get(f'/api/users/{id}/wallet',headers=admin).json()['balance']=='0.000'
    result=next(s for s in client.get('/api/sessions',headers=admin).json() if s['id']==r.json()['id'])
    assert result['status']=='COMPLETED' and result['cost']=='26.000'
    assert client.post('/api/sessions/'+r.json()['id']+'/stop',headers=admin).status_code==409
