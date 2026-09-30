"""Frozen initial NexArena schema; independent of future ORM changes."""
from alembic import op

revision = "001"
down_revision = None

def upgrade():
    op.execute('CREATE TABLE branches (\n\tid VARCHAR(36) NOT NULL, \n\tname VARCHAR(120) NOT NULL, \n\taddress VARCHAR(300) NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (name)\n)')
    op.execute('CREATE TABLE games (\n\tid VARCHAR(36) NOT NULL, \n\tname VARCHAR(120) NOT NULL, \n\tdescription VARCHAR(1000) NOT NULL, \n\tgenre VARCHAR(100) NOT NULL, \n\tversion VARCHAR(50) NOT NULL, \n\texecutable_path VARCHAR(500) NOT NULL, \n\tactive BOOLEAN NOT NULL, \n\tPRIMARY KEY (id)\n)')
    op.execute('CREATE TABLE membership_plans (\n\tid VARCHAR(36) NOT NULL, \n\tname VARCHAR(100) NOT NULL, \n\tdescription VARCHAR(500) NOT NULL, \n\tprice NUMERIC(12, 3) NOT NULL, \n\tduration_days INTEGER NOT NULL, \n\tbenefits VARCHAR(1000) NOT NULL, \n\tactive BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (name)\n)')
    op.execute('CREATE TABLE roles (\n\tname VARCHAR(30) NOT NULL, \n\tpermissions JSON NOT NULL, \n\tPRIMARY KEY (name)\n)')
    op.execute('CREATE TABLE nodes (\n\tid VARCHAR(36) NOT NULL, \n\tmachine_id VARCHAR(100) NOT NULL, \n\thostname VARCHAR(120) NOT NULL, \n\tname VARCHAR(120) NOT NULL, \n\tbranch_id VARCHAR(36) NOT NULL, \n\tip_address VARCHAR(100) NOT NULL, \n\tos VARCHAR(200) NOT NULL, \n\tagent_version VARCHAR(30) NOT NULL, \n\tagent_secret_hash VARCHAR(128) NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\tlast_heartbeat TIMESTAMP WITH TIME ZONE, \n\ttelemetry JSON NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (machine_id), \n\tFOREIGN KEY(branch_id) REFERENCES branches (id)\n)')
    op.execute('CREATE INDEX ix_nodes_branch_id ON nodes (branch_id)')
    op.execute('CREATE TABLE users (\n\tid VARCHAR(36) NOT NULL, \n\tname VARCHAR(120) NOT NULL, \n\temail VARCHAR(200) NOT NULL, \n\tpassword_hash VARCHAR(300) NOT NULL, \n\trole VARCHAR(30) NOT NULL, \n\tactive BOOLEAN NOT NULL, \n\ttoken_version INTEGER NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (email), \n\tFOREIGN KEY(role) REFERENCES roles (name)\n)')
    op.execute('CREATE TABLE alerts (\n\tid VARCHAR(36) NOT NULL, \n\tnode_id VARCHAR(36) NOT NULL, \n\ttype VARCHAR(50) NOT NULL, \n\tseverity VARCHAR(30) NOT NULL, \n\tmessage VARCHAR(500) NOT NULL, \n\tread BOOLEAN NOT NULL, \n\tresolved BOOLEAN NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(node_id) REFERENCES nodes (id)\n)')
    op.execute('CREATE INDEX ix_alerts_node_id ON alerts (node_id)')
    op.execute('CREATE TABLE commands (\n\tid VARCHAR(36) NOT NULL, \n\tnode_id VARCHAR(36) NOT NULL, \n\tactor_id VARCHAR(36) NOT NULL, \n\ttype VARCHAR(30) NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\tresult VARCHAR(1000) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(node_id) REFERENCES nodes (id), \n\tFOREIGN KEY(actor_id) REFERENCES users (id)\n)')
    op.execute('CREATE INDEX ix_commands_node_id ON commands (node_id)')
    op.execute('CREATE TABLE node_games (\n\tnode_id VARCHAR(36) NOT NULL, \n\tgame_id VARCHAR(36) NOT NULL, \n\tPRIMARY KEY (node_id, game_id), \n\tFOREIGN KEY(node_id) REFERENCES nodes (id), \n\tFOREIGN KEY(game_id) REFERENCES games (id)\n)')
    op.execute('CREATE TABLE reservations (\n\tid VARCHAR(36) NOT NULL, \n\tuser_id VARCHAR(36) NOT NULL, \n\tnode_id VARCHAR(36) NOT NULL, \n\tbranch_id VARCHAR(36) NOT NULL, \n\tstart_time TIMESTAMP WITH TIME ZONE NOT NULL, \n\tend_time TIMESTAMP WITH TIME ZONE NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (end_time > start_time), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tFOREIGN KEY(node_id) REFERENCES nodes (id), \n\tFOREIGN KEY(branch_id) REFERENCES branches (id)\n)')
    op.execute('CREATE INDEX ix_reservations_branch_id ON reservations (branch_id)')
    op.execute('CREATE INDEX ix_reservations_node_id ON reservations (node_id)')
    op.execute('CREATE TABLE sessions (\n\tid VARCHAR(36) NOT NULL, \n\tuser_id VARCHAR(36) NOT NULL, \n\tnode_id VARCHAR(36) NOT NULL, \n\tstart_time TIMESTAMP WITH TIME ZONE NOT NULL, \n\tend_time TIMESTAMP WITH TIME ZONE, \n\trate NUMERIC(12, 3) NOT NULL, \n\tcost NUMERIC(12, 3) NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (rate > 0), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tFOREIGN KEY(node_id) REFERENCES nodes (id)\n)')
    op.execute('CREATE INDEX ix_sessions_node_id ON sessions (node_id)')
    op.execute('CREATE INDEX ix_sessions_user_id ON sessions (user_id)')
    op.execute("CREATE UNIQUE INDEX one_active_session_per_node ON sessions (node_id) WHERE status = 'ACTIVE'")
    op.execute("CREATE UNIQUE INDEX one_active_session_per_user ON sessions (user_id) WHERE status = 'ACTIVE'")
    op.execute('CREATE TABLE user_memberships (\n\tuser_id VARCHAR(36) NOT NULL, \n\tplan_id VARCHAR(36) NOT NULL, \n\tstart_date TIMESTAMP WITH TIME ZONE NOT NULL, \n\texpiration_date TIMESTAMP WITH TIME ZONE NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\tPRIMARY KEY (user_id), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tFOREIGN KEY(plan_id) REFERENCES membership_plans (id)\n)')
    op.execute('CREATE TABLE wallets (\n\tuser_id VARCHAR(36) NOT NULL, \n\tbalance NUMERIC(12, 3) NOT NULL, \n\tPRIMARY KEY (user_id), \n\tCHECK (balance >= 0), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)')
    op.execute('CREATE TABLE wallet_transactions (\n\tid VARCHAR(36) NOT NULL, \n\tuser_id VARCHAR(36) NOT NULL, \n\tamount NUMERIC(12, 3) NOT NULL, \n\ttype VARCHAR(30) NOT NULL, \n\treference VARCHAR(150) NOT NULL, \n\tsession_id VARCHAR(36), \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tUNIQUE (reference), \n\tUNIQUE (session_id), \n\tFOREIGN KEY(session_id) REFERENCES sessions (id)\n)')
    op.execute('CREATE INDEX ix_wallet_transactions_user_id ON wallet_transactions (user_id)')
    op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')
    op.execute("ALTER TABLE reservations ADD CONSTRAINT no_overlapping_reservations EXCLUDE USING gist (node_id WITH =, tstzrange(start_time, end_time, '[)') WITH &&) WHERE (status = 'CONFIRMED')")


def downgrade():
    op.drop_table('wallet_transactions')
    op.drop_table('wallets')
    op.drop_table('user_memberships')
    op.drop_table('sessions')
    op.drop_table('reservations')
    op.drop_table('node_games')
    op.drop_table('commands')
    op.drop_table('alerts')
    op.drop_table('users')
    op.drop_table('nodes')
    op.drop_table('roles')
    op.drop_table('membership_plans')
    op.drop_table('games')
    op.drop_table('branches')
