"""Game artwork, Tunisian teams, player profiles and per-game arena ratings."""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"


def upgrade():
    op.add_column("games", sa.Column("image_url", sa.String(500), nullable=False, server_default=""))
    for table in ("sessions", "reservations"):
        op.add_column(table, sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table("esports_teams",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), unique=True, nullable=False),
        sa.Column("tag", sa.String(12), unique=True, nullable=False),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("color", sa.String(7), nullable=False),
        sa.Column("website", sa.String(300), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False))
    op.create_table("player_profiles",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("handle", sa.String(40), unique=True, nullable=False),
        sa.Column("city", sa.String(80), nullable=False),
        sa.Column("team_id", sa.String(36), sa.ForeignKey("esports_teams.id"), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False))
    op.create_index("ix_player_profiles_team_id", "player_profiles", ["team_id"])
    op.create_table("player_rankings",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("player_profiles.user_id"), primary_key=True),
        sa.Column("game_id", sa.String(36), sa.ForeignKey("games.id"), primary_key=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("wins", sa.Integer(), nullable=False),
        sa.Column("losses", sa.Integer(), nullable=False),
        sa.Column("streak", sa.Integer(), nullable=False),
        sa.Column("peak_rating", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("rating >= 0 AND wins >= 0 AND losses >= 0", name="nonnegative_ranking"))
    op.create_table("ranked_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("reference", sa.String(100), unique=True, nullable=False),
        sa.Column("game_id", sa.String(36), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("winner_id", sa.String(36), sa.ForeignKey("player_profiles.user_id"), nullable=False),
        sa.Column("loser_id", sa.String(36), sa.ForeignKey("player_profiles.user_id"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating_delta", sa.Integer(), nullable=False),
        sa.Column("winner_rating", sa.Integer(), nullable=False),
        sa.Column("loser_rating", sa.Integer(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("winner_id <> loser_id", name="distinct_ranked_players"))
    op.create_index("ix_ranked_results_game_id", "ranked_results", ["game_id"])


def downgrade():
    op.drop_table("ranked_results")
    op.drop_table("player_rankings")
    op.drop_table("player_profiles")
    op.drop_table("esports_teams")
    op.drop_column("games", "image_url")
    for table in ("sessions", "reservations"):
        op.drop_column(table, "is_demo")
