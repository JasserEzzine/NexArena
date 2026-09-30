import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type FormEvent,
} from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronRight,
  Crown,
  Flame,
  Gamepad2,
  MapPin,
  Plus,
  Search,
  Shield,
  Swords,
  Trophy,
  Users,
  X,
} from "lucide-react";
import { api } from "./api";
import type {
  Game,
  Leaderboard,
  Player,
  RankedResult,
  Team,
  User,
} from "./types";

type Context = { games: Game[]; users: User[]; admin: boolean };
type FormKind =
  | { kind: "team"; team?: Team }
  | { kind: "player"; player?: Player }
  | { kind: "result" };

export function TunisiaFlag() {
  return (
    <span className="tunisia-flag" role="img" aria-label="Tunisia">
      <span>☪</span>
    </span>
  );
}

function CompetitionForm({
  form,
  teams,
  players,
  users,
  gameId,
  close,
  saved,
}: {
  form: FormKind;
  teams: Team[];
  players: Player[];
  users: User[];
  gameId: string;
  close: () => void;
  saved: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [reference] = useState(() => crypto.randomUUID());
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const values = Object.fromEntries(
      new FormData(event.currentTarget),
    ) as Record<string, string>;
    try {
      if (form.kind === "team")
        await api(
          "/teams" + (form.team ? "/" + form.team.id : ""),
          form.team ? "PUT" : "POST",
          values,
        );
      if (form.kind === "player") {
        const { user_id, ...body } = values;
        await api("/players/" + user_id, "PUT", {
          ...body,
          team_id: body.team_id || null,
        });
      }
      if (form.kind === "result")
        await api("/ranked-results", "POST", {
          ...values,
          game_id: gameId,
          reference,
        });
      saved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="modal-backdrop">
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={
          form.kind === "result"
            ? "Record ranked result"
            : form.kind === "team"
              ? "Team details"
              : "Player profile"
        }
      >
        <div className="panel-head">
          <h2>
            {form.kind === "result"
              ? "Record ranked result"
              : form.kind === "team"
                ? "Team details"
                : "Player profile"}
          </h2>
          <button
            className="icon-button"
            aria-label="Close form"
            onClick={close}
            disabled={busy}
          >
            <X size={20} />
          </button>
        </div>
        <form onSubmit={submit}>
          {form.kind === "team" && (
            <>
              <label>
                Team name
                <input
                  name="name"
                  defaultValue={form.team?.name}
                  required
                  maxLength={120}
                />
              </label>
              <div className="form-two">
                <label>
                  Tag
                  <input
                    name="tag"
                    defaultValue={form.team?.tag}
                    required
                    pattern="[A-Z0-9]{2,12}"
                    placeholder="GNG"
                  />
                </label>
                <label>
                  City
                  <input name="city" defaultValue={form.team?.city} required />
                </label>
              </div>
              <label>
                Description
                <input
                  name="description"
                  defaultValue={form.team?.description}
                />
              </label>
              <div className="form-two">
                <label>
                  Team color
                  <input
                    name="color"
                    type="color"
                    defaultValue={form.team?.color || "#34d5c4"}
                  />
                </label>
                <label>
                  Website · optional
                  <input
                    name="website"
                    type="url"
                    defaultValue={form.team?.website}
                    placeholder="https://…"
                  />
                </label>
              </div>
            </>
          )}
          {form.kind === "player" && (
            <>
              <label>
                Customer
                <select
                  name="user_id"
                  defaultValue={form.player?.user_id || ""}
                  required
                >
                  <option value="" disabled>
                    Select customer
                  </option>
                  {users
                    .filter(
                      (u) =>
                        u.role === "CUSTOMER" &&
                        u.active &&
                        (!form.player || u.id === form.player.user_id),
                    )
                    .map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.name}
                      </option>
                    ))}
                </select>
              </label>
              <label>
                Player handle
                <input
                  name="handle"
                  defaultValue={form.player?.handle}
                  required
                  minLength={2}
                  maxLength={40}
                  pattern="[\w.-]+"
                />
              </label>
              <label>
                City
                <input name="city" defaultValue={form.player?.city} required />
              </label>
              <label>
                Team
                <select
                  name="team_id"
                  defaultValue={form.player?.team_id || ""}
                >
                  <option value="">Free agent</option>
                  {teams.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </label>
            </>
          )}
          {form.kind === "result" && (
            <>
              <p className="muted form-explainer">
                Record a verified head-to-head arena result. Both players’ Elo,
                win/loss records, and streaks update together. For team games,
                this ladder tracks local player challenges, not official 5v5
                matchmaking.
              </p>
              {[
                ["winner_id", "Winner"],
                ["loser_id", "Opponent"],
              ].map(([key, label]) => (
                <label key={key}>
                  {label}
                  <select
                    name={key}
                    aria-label={label}
                    required
                    defaultValue=""
                  >
                    <option value="" disabled>
                      Select player
                    </option>
                    {players
                      .filter((p) => p.active)
                      .map((p) => (
                        <option key={p.user_id} value={p.user_id}>
                          {p.handle} · {p.team_tag || "Free agent"}
                        </option>
                      ))}
                  </select>
                </label>
              ))}
            </>
          )}
          {error && (
            <div className="error" role="alert">
              {error}
            </div>
          )}
          <div className="modal-actions">
            <button
              type="button"
              className="button secondary"
              onClick={close}
              disabled={busy}
            >
              Cancel
            </button>
            <button className="button primary" disabled={busy}>
              {busy
                ? "Saving…"
                : form.kind === "result"
                  ? "Confirm result"
                  : "Save changes"}
              <Check size={16} />
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default function Esports({
  mode,
  games,
  users,
  admin,
}: Context & { mode: "teams" | "rankings" }) {
  const [params, setParams] = useSearchParams();
  const [teams, setTeams] = useState<Team[]>([]);
  const [players, setPlayers] = useState<Player[]>([]);
  const [board, setBoard] = useState<Leaderboard | null>(null);
  const [results, setResults] = useState<RankedResult[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [teamId, setTeamId] = useState("");
  const [form, setForm] = useState<FormKind | null>(null);
  const [notice, setNotice] = useState("");
  const requestVersion = useRef(0);
  useEffect(() => {
    setTeamId("");
    setSearch("");
    setForm(null);
  }, [mode]);
  const selectedGame =
    games.find((g) => g.id === params.get("game")) ||
    games.find((g) => g.name === "League of Legends") ||
    games[0];
  const gameId = selectedGame?.id || "";
  const load = useCallback(async () => {
    const version = ++requestVersion.current;
    if (!gameId) {
      setLoading(false);
      return;
    }
    try {
      const [t, p, b, r] = await Promise.all([
        api<Team[]>("/teams"),
        api<Player[]>("/players"),
        api<Leaderboard>("/rankings?game_id=" + gameId),
        api<RankedResult[]>("/ranked-results?game_id=" + gameId),
      ]);
      if (version !== requestVersion.current) return;
      setTeams(t);
      setPlayers(p);
      setBoard(b);
      setResults(r);
      setError("");
    } catch (e) {
      if (version === requestVersion.current) setError((e as Error).message);
    } finally {
      if (version === requestVersion.current) setLoading(false);
    }
  }, [gameId]);
  useEffect(() => {
    setLoading(true);
    setBoard(null);
    setResults([]);
    void load();
    const interval = setInterval(() => void load(), 15000);
    window.addEventListener("arena-esports", load);
    return () => {
      clearInterval(interval);
      window.removeEventListener("arena-esports", load);
    };
  }, [load]);
  useEffect(() => {
    if (notice) {
      const timer = setTimeout(() => setNotice(""), 4000);
      return () => clearTimeout(timer);
    }
  }, [notice]);
  const entries = (board?.entries || []).filter(
    (p) =>
      (!teamId || p.team_id === teamId) &&
      `${p.handle} ${p.name}`.toLowerCase().includes(search.toLowerCase()),
  );
  const selectedTeam = teams.find((t) => t.id === teamId);
  const podium = entries.slice(0, 3);
  const demo = players.some((p) => p.is_demo);
  const saved = () => {
    setForm(null);
    void load();
    setNotice("Saved. The arena rankings are up to date.");
  };
  return (
    <div className="esports-page">
      <section
        className={"esports-hero " + (mode === "teams" ? "teams-hero" : "")}
        style={
          selectedGame?.image_url && mode === "rankings"
            ? ({
                "--game-image": `url("${selectedGame.image_url.replaceAll('"', "%22")}")`,
              } as CSSProperties)
            : undefined
        }
      >
        <div>
          <div className="esports-kicker">
            <TunisiaFlag />
            TUNISIA / COMMUNITY ESPORTS
          </div>
          <h2>
            {mode === "teams" ? (
              <>
                Homegrown talent.
                <br />
                <span>One Tunisian scene.</span>
              </>
            ) : (
              <>
                Every game.
                <br />
                <span>A new climb.</span>
              </>
            )}
          </h2>
          <p>
            {mode === "teams"
              ? "Discover the teams and players bringing the arena to life."
              : "Your arena. Your rivals. Your place on the leaderboard."}
          </p>
          <div className="esports-hero-chips">
            <span>
              <Users size={14} />
              {players.length} players
            </span>
            <span>
              <Shield size={14} />
              {teams.length} teams
            </span>
            <span>
              <Gamepad2 size={14} />
              {games.filter((g) => g.active).length} games
            </span>
          </div>
        </div>
        <div className="esports-hero-symbol" aria-hidden="true">
          {mode === "teams" ? (
            <Shield size={130} strokeWidth={0.8} />
          ) : (
            <Trophy size={130} strokeWidth={0.8} />
          )}
        </div>
      </section>
      {demo && (
        <div className="demo-note">
          <span className="demo-chip">SHOWCASE DATA</span>
          <p>
            Fictional players, team assignments, and results. GNG and JSK are
            featured as Tunisian team references; no official roster or
            affiliation is claimed.
          </p>
        </div>
      )}
      {error && (
        <div className="error" role="alert">
          {error}
          <button onClick={() => void load()}>Retry</button>
        </div>
      )}
      {mode === "teams" ? (
        <>
          <div className="section-title">
            <div>
              <h2>
                The Tunisian lineup{" "}
                <span className="count">{teams.length}</span>
              </h2>
              <p>Local identity. Competitive spirit.</p>
            </div>
            {admin && (
              <button
                className="button primary"
                onClick={() => setForm({ kind: "team" })}
              >
                <Plus size={16} />
                Add team
              </button>
            )}
          </div>
          <div className="team-grid">
            {teams.map((team) => {
              const roster = players.filter((p) => p.team_id === team.id);
              return (
                <article
                  className="team-card"
                  key={team.id}
                  style={{ "--team-color": team.color } as CSSProperties}
                >
                  <div className="team-card-top">
                    <div className="team-monogram">
                      <Shield size={58} strokeWidth={1} />
                      <strong>{team.tag}</strong>
                    </div>
                    <span className="team-country">
                      <TunisiaFlag />
                      TUNISIA
                    </span>
                  </div>
                  <div className="team-card-body">
                    <div className="eyebrow">
                      {team.city.toUpperCase()} / ESPORTS
                    </div>
                    <h2>{team.name}</h2>
                    <p>{team.description}</p>
                    <div className="team-roster-preview">
                      <div className="roster-avatars">
                        {roster.slice(0, 4).map((p) => (
                          <span key={p.user_id} title={p.handle}>
                            {p.handle.slice(0, 2)}
                          </span>
                        ))}
                      </div>
                      <span>
                        {roster.length} players{" "}
                        <small>
                          {team.is_demo ? "Demo roster" : "Arena roster"}
                        </small>
                      </span>
                    </div>
                    <div className="team-card-actions">
                      <button
                        className="button secondary"
                        onClick={() => {
                          setTeamId(team.id);
                          document
                            .getElementById("roster-directory")
                            ?.scrollIntoView({ behavior: "smooth" });
                        }}
                      >
                        View roster
                        <ArrowRight size={14} />
                      </button>
                      {admin && (
                        <button
                          className="text-button"
                          onClick={() => setForm({ kind: "team", team })}
                        >
                          Edit team
                        </button>
                      )}
                      {team.website && (
                        <a
                          href={team.website}
                          target="_blank"
                          rel="noreferrer"
                          className="icon-button"
                          aria-label={`${team.name} website`}
                        >
                          <ArrowUpRight size={17} />
                        </a>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
          <section className="panel" id="roster-directory">
            <div className="panel-head">
              <h2>
                {selectedTeam
                  ? selectedTeam.name + " roster"
                  : "Player directory"}
              </h2>
              {admin && (
                <button
                  className="button secondary small"
                  onClick={() => setForm({ kind: "player" })}
                >
                  <Plus size={14} />
                  Add player profile
                </button>
              )}
            </div>
            <div className="competition-filters">
              <div className="search">
                <Search size={16} />
                <input
                  aria-label="Search players"
                  placeholder="Search players…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <select
                aria-label="Filter team"
                value={teamId}
                onChange={(e) => setTeamId(e.target.value)}
              >
                <option value="">All teams</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Player</th>
                    <th>Team</th>
                    <th>Hometown</th>
                    <th>Profile</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {players
                    .filter(
                      (p) =>
                        (!teamId || p.team_id === teamId) &&
                        `${p.handle} ${p.name}`
                          .toLowerCase()
                          .includes(search.toLowerCase()),
                    )
                    .map((p) => (
                      <tr key={p.user_id}>
                        <td>
                          <b>{p.handle}</b>
                          <small>{p.name}</small>
                        </td>
                        <td>
                          <span className="team-tag">
                            {p.team_tag || "Free agent"}
                          </span>
                        </td>
                        <td>{p.city}</td>
                        <td>
                          {p.is_demo ? (
                            <span className="demo-chip">Demo</span>
                          ) : (
                            <span className="muted">Arena player</span>
                          )}
                        </td>
                        <td>
                          {admin && (
                            <button
                              className="text-button"
                              onClick={() =>
                                setForm({ kind: "player", player: p })
                              }
                            >
                              Edit profile
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
            {!players.length && !loading && (
              <div className="empty">
                Add a customer, then create their player profile.
              </div>
            )}
          </section>
        </>
      ) : (
        <>
          <div className="game-tabs" role="group" aria-label="Ranking game">
            {games
              .filter((g) => g.active)
              .map((g) => (
                <button
                  key={g.id}
                  aria-pressed={g.id === gameId}
                  className={g.id === gameId ? "selected" : ""}
                  onClick={() => setParams({ game: g.id })}
                >
                  {g.image_url ? (
                    <img src={g.image_url} alt="" />
                  ) : (
                    <Gamepad2 size={20} />
                  )}
                  <span>{g.name}</span>
                  {g.id === gameId && <span className="dot green" />}
                </button>
              ))}
          </div>
          <div className="section-title ranking-title">
            <div>
              <div className="eyebrow">LOCAL ARENA LADDER</div>
              <h2>
                {selectedGame?.name || "Choose a game"}{" "}
                <span className="count">{board?.entries.length || 0}</span>
              </h2>
              <p>
                NexArena Elo · 1,000 starting rating · K-factor 32 · independent
                of official game ranks
              </p>
            </div>
            {admin && (
              <button
                className="button primary"
                disabled={
                  !gameId || !selectedGame?.active || players.length < 2
                }
                onClick={() => setForm({ kind: "result" })}
              >
                <Plus size={16} />
                Record result
              </button>
            )}
          </div>
          {!loading && podium.length > 0 && (
            <div className="podium">
              {podium.map((p, i) => (
                <article
                  key={p.user_id}
                  className={"podium-card podium-" + i}
                  style={{ "--team-color": p.team_color } as CSSProperties}
                >
                  <span className="podium-position">#{p.position}</span>
                  {i === 0 ? (
                    <Crown className="podium-crown" size={22} />
                  ) : (
                    <Trophy className="podium-crown" size={19} />
                  )}
                  <div className="player-emblem">
                    {p.handle.slice(0, 2).toUpperCase()}
                  </div>
                  <span className="eyebrow">{p.team_tag || "FREE AGENT"}</span>
                  <h3>{p.handle}</h3>
                  <span className="podium-city">
                    <MapPin size={11} />
                    {p.city}
                  </span>
                  <strong className="podium-rating">
                    {p.rating}
                    <small>ELO</small>
                  </strong>
                  <span className={"rank-tier tier-" + p.tier.toLowerCase()}>
                    {p.tier}
                  </span>
                  <div className="podium-footer">
                    <span>
                      {p.wins}W <i>/</i> {p.losses}L
                    </span>
                    <span>{p.win_rate}% win rate</span>
                  </div>
                </article>
              ))}
            </div>
          )}
          <section className="panel leaderboard">
            <div className="competition-filters">
              <div className="search">
                <Search size={16} />
                <input
                  aria-label="Search rankings"
                  placeholder="Find a player…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <select
                aria-label="Ranking team"
                value={teamId}
                onChange={(e) => setTeamId(e.target.value)}
              >
                <option value="">All teams</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
              <span className="muted">{entries.length} ranked players</span>
            </div>
            {loading ? (
              <div className="empty">Loading the ladder…</div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Player</th>
                      <th>Team</th>
                      <th>Arena tier</th>
                      <th>Elo</th>
                      <th>W / L</th>
                      <th>Win rate</th>
                      <th>Streak</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((p) => (
                      <tr key={p.user_id}>
                        <td>
                          <span
                            className={
                              "rank-number " +
                              (p.position <= 3 ? "top-rank" : "")
                            }
                          >
                            #{p.position}
                          </span>
                        </td>
                        <td>
                          <div className="ranked-player">
                            <span
                              className="ranked-avatar"
                              style={
                                {
                                  "--team-color": p.team_color,
                                } as CSSProperties
                              }
                            >
                              {p.handle.slice(0, 2)}
                            </span>
                            <div>
                              <b>{p.handle}</b>
                              <small>
                                {p.city}
                                {p.is_demo ? " · Demo" : ""}
                              </small>
                            </div>
                          </div>
                        </td>
                        <td>
                          <span
                            className="team-tag"
                            style={{ color: p.team_color }}
                          >
                            {p.team_tag || "FA"}
                          </span>
                        </td>
                        <td>
                          <span
                            className={"rank-tier tier-" + p.tier.toLowerCase()}
                          >
                            {p.tier}
                          </span>
                        </td>
                        <td>
                          <b className="elo-value">{p.rating}</b>
                        </td>
                        <td>
                          {p.wins} <span className="muted">/ {p.losses}</span>
                        </td>
                        <td>
                          <div className="win-rate">
                            <span>{p.win_rate}%</span>
                            <i>
                              <em style={{ width: p.win_rate + "%" }} />
                            </i>
                          </div>
                        </td>
                        <td>
                          {p.streak > 0 ? (
                            <span className="win-streak">
                              <Flame size={13} />
                              {p.streak}W
                            </span>
                          ) : (
                            <span className="muted">{Math.abs(p.streak)}L</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!entries.length && (
                  <div className="empty">
                    No ranked players for this selection. Record a result to
                    start a ladder.
                  </div>
                )}
              </div>
            )}
          </section>
          <section className="panel">
            <div className="panel-head">
              <h2>Recent results</h2>
              <span className="muted text-xs">
                {selectedGame?.name} · latest 30
              </span>
            </div>
            <div className="rank-results">
              {results.slice(0, 8).map((r) => (
                <div key={r.id}>
                  <span className="result-icon">
                    <Swords size={17} />
                  </span>
                  <div>
                    <b>{r.winner_handle}</b>
                    <span className="muted"> defeated </span>
                    <b>{r.loser_handle}</b>
                    <small>
                      {new Date(r.created_at).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}{" "}
                      {r.is_demo && "· Sample result"}
                    </small>
                  </div>
                  <span className="result-delta">
                    +{r.rating_delta}
                    <small>ELO</small>
                  </span>
                </div>
              ))}
              {!results.length && !loading && (
                <div className="empty">
                  No results recorded for this game yet.
                </div>
              )}
            </div>
          </section>
        </>
      )}
      {loading && mode === "teams" && (
        <div className="empty">Loading the Tunisian scene…</div>
      )}
      {form && (
        <CompetitionForm
          form={form}
          teams={teams}
          players={players}
          users={users}
          gameId={gameId}
          close={() => setForm(null)}
          saved={saved}
        />
      )}
      {notice && (
        <div className="toast" role="status">
          <Check size={18} />
          {notice}
          <button
            aria-label="Dismiss notification"
            onClick={() => setNotice("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}

export function CommunityPreview({ games }: { games: Game[] }) {
  const [teams, setTeams] = useState<Team[]>([]);
  const [board, setBoard] = useState<Leaderboard | null>(null);
  const game = games.find((g) => g.name === "League of Legends");
  useEffect(() => {
    if (!game) return;
    let cancelled = false;
    Promise.all([
      api<Team[]>("/teams"),
      api<Leaderboard>("/rankings?game_id=" + game.id),
    ])
      .then(([t, b]) => {
        if (!cancelled) {
          setTeams(t);
          setBoard(b);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [game?.id]);
  if (!teams.length) return null;
  return (
    <section className="community-preview">
      <div className="community-intro">
        <div className="esports-kicker">
          <TunisiaFlag />
          MADE FOR THE TUNISIAN SCENE
        </div>
        <h2>Local talent. Next-level competition.</h2>
        <p>Meet the teams. Follow the climb. Find your next rival.</p>
        <Link to="/teams" className="text-button">
          Explore Tunisian teams
          <ArrowRight size={15} />
        </Link>
      </div>
      <div className="community-team-tags">
        {teams.map((t) => (
          <Link
            to="/teams"
            key={t.id}
            style={{ "--team-color": t.color } as CSSProperties}
          >
            <Shield size={17} />
            <b>{t.tag}</b>
            <small>{t.city}</small>
          </Link>
        ))}
      </div>
      <Link to={"/rankings?game=" + game?.id} className="community-leader">
        <Trophy size={24} />
        <div>
          <span className="eyebrow">LEAGUE OF LEGENDS · DEMO LADDER</span>
          <strong>{board?.entries[0]?.handle || "The next champion"}</strong>
          <small>{board?.entries[0]?.rating || 1000} NexArena Elo</small>
        </div>
        <ChevronRight size={19} />
      </Link>
    </section>
  );
}
