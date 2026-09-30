import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  Activity,
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  Bell,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronRight,
  Clock3,
  CreditCard,
  Crown,
  Gamepad2,
  LayoutDashboard,
  LogOut,
  MapPin,
  Monitor,
  MoreHorizontal,
  Plus,
  Power,
  Radio,
  Search,
  ShieldCheck,
  Users,
  Wallet,
  X,
  Zap,
  LockKeyhole,
  Cpu,
  MemoryStick,
  Thermometer,
  Fan,
  Keyboard,
  Mouse,
  RefreshCw,
} from "lucide-react";
import { api } from "./api";
import type {
  Alert,
  Branch,
  Command,
  Data,
  Game,
  Membership,
  Node,
  Plan,
  Reservation,
  Session,
  Transaction,
  User,
} from "./types";

const empty: Data = {
  branches: [],
  nodes: [],
  users: [],
  sessions: [],
  plans: [],
  memberships: [],
  reservations: [],
  games: [],
  alerts: [],
  commands: [],
};
const navigation = [
  ["/", "Overview", LayoutDashboard],
  ["/stations", "Gaming stations", Monitor],
  ["/sessions", "Sessions", Clock3],
  ["/reservations", "Reservations", CalendarDays],
  ["/wallets", "Wallets", Wallet],
  ["/memberships", "Memberships", Crown],
  ["/games", "Game library", Gamepad2],
  ["/alerts", "Alerts", Bell],
  ["/users", "People", Users],
  ["/branches", "Branches", MapPin],
] as const;
const money = (value: string | number) => Number(value).toFixed(3);
const stamp = (value: string | null) =>
  value
    ? new Date(value).toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Never connected";
const duration = (s: Session, time: number) => {
  const n = Math.max(
    0,
    Math.floor(
      ((s.end_time ? new Date(s.end_time).getTime() : time) -
        new Date(s.start_time).getTime()) /
        1000,
    ),
  );
  return [Math.floor(n / 3600), Math.floor((n % 3600) / 60), n % 60]
    .map((x) => String(x).padStart(2, "0"))
    .join(":");
};
const cost = (s: Session, time: number) =>
  s.status === "ACTIVE"
    ? Math.max(
        0,
        ((time - new Date(s.start_time).getTime()) / 3600000) * Number(s.rate),
      )
    : Number(s.cost);
type Field = {
  key: string;
  label: string;
  type?: string;
  value?: string | number;
  options?: { id: string; name: string }[];
  required?: boolean;
  min?: string;
  step?: string;
};
type Dialog = {
  title: string;
  subtitle?: string;
  fields: Field[];
  submit: (v: Record<string, string>) => Promise<unknown>;
  action?: string;
};

function Brand() {
  return (
    <div className="brand">
      <span className="brand-icon">N</span>
      <span>
        Nex<span className="text-white">Arena</span>
        <small>OPERATIONS PLATFORM</small>
      </span>
    </div>
  );
}
function Badge({
  children,
  tone = "",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return (
    <span className={"badge " + tone}>
      <i />
      {children}
    </span>
  );
}
function Empty({ children = "Nothing here yet." }: { children?: ReactNode }) {
  return (
    <div className="empty">
      <Activity size={26} />
      <p>{children}</p>
    </div>
  );
}
function Panel({
  title,
  eyebrow,
  action,
  children,
  className = "",
}: {
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={"panel " + className}>
      {title && (
        <div className="panel-head">
          <div>
            {eyebrow && <span className="eyebrow">{eyebrow}</span>}
            <h2>{title}</h2>
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

function FormDialog({
  dialog,
  close,
  done,
}: {
  dialog: Dialog;
  close: () => void;
  done: () => void;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await dialog.submit(
        Object.fromEntries(new FormData(e.currentTarget)) as Record<
          string,
          string
        >,
      );
      done();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !busy) close();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [close, busy]);
  return (
    <div className="modal-backdrop">
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={dialog.title}
      >
        <div className="panel-head">
          <h2>{dialog.title}</h2>
          <button
            className="icon-button"
            aria-label="Close dialog"
            onClick={close}
            disabled={busy}
          >
            <X size={20} />
          </button>
        </div>
        {dialog.subtitle && <p className="muted mb-5">{dialog.subtitle}</p>}
        <form onSubmit={submit}>
          {dialog.fields.map((f, i) => (
            <label key={f.key}>
              {f.label}
              {f.options ? (
                <select
                  name={f.key}
                  defaultValue={f.value || ""}
                  required={f.required !== false}
                >
                  <option value="" disabled>
                    Select {f.label.toLowerCase()}
                  </option>
                  {f.options.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.name}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  autoFocus={i === 0}
                  name={f.key}
                  type={f.type || "text"}
                  defaultValue={f.value}
                  required={f.required !== false}
                  min={f.min}
                  step={f.step}
                />
              )}
            </label>
          ))}
          {error && (
            <div role="alert" className="error">
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
              {busy ? "Working…" : dialog.action || "Save changes"}
              <ArrowRight size={16} />
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function Login({ signedIn }: { signedIn: (u: User) => void }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const values = Object.fromEntries(new FormData(e.currentTarget));
    try {
      const result = await api<{ access_token: string; user: User }>(
        "/auth/login",
        "POST",
        values,
      );
      if (!["ADMIN", "STAFF"].includes(result.user.role))
        throw new Error(
          "This dashboard is for arena administrators and staff.",
        );
      sessionStorage.setItem("token", result.access_token);
      signedIn(result.user);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login">
      <div className="login-story">
        <Brand />
        <div>
          <span className="eyebrow cyan">
            THE NEXT LEVEL OF ARENA MANAGEMENT
          </span>
          <h1>
            Great games.
            <br />
            Seamless
            <br />
            <span>operations.</span>
          </h1>
          <p>
            Every station. Every session. Every player.
            <br />
            Your entire arena, connected in one place.
          </p>
          <div className="login-lines">
            <Monitor />
            <span>Built for the way you play.</span>
            <div />
          </div>
        </div>
        <small>NEXARENA / ESPORTS OPERATIONS</small>
      </div>
      <div className="login-form">
        <div className="login-form-inner">
          <Badge tone="cyan">ARENA CONTROL</Badge>
          <h2>Welcome back.</h2>
          <p className="muted">Sign in to your operations workspace.</p>
          <form onSubmit={submit}>
            <label>
              Email address
              <input
                name="email"
                type="email"
                placeholder="you@nexarena.local"
                autoComplete="username"
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />
            </label>
            {error && (
              <div className="error" role="alert">
                {error}
              </div>
            )}
            <button className="button primary" disabled={busy}>
              {busy ? "Signing in…" : "Enter your arena"}
              <ArrowRight size={18} />
            </button>
          </form>
          <p className="login-note">
            <ShieldCheck size={16} />
            Secure access for administrators and staff
          </p>
        </div>
        <small>YOUR ARENA. YOUR ADVANTAGE.</small>
      </div>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    if (sessionStorage.getItem("token"))
      api<User>("/auth/me")
        .then(setUser)
        .catch(() => sessionStorage.removeItem("token"))
        .finally(() => setChecking(false));
    else setChecking(false);
    const clear = () => {
      sessionStorage.removeItem("token");
      setUser(null);
    };
    window.addEventListener("signed-out", clear);
    return () => window.removeEventListener("signed-out", clear);
  }, []);
  if (checking)
    return (
      <div className="boot">
        <Brand />
        <p>Connecting to your arena…</p>
      </div>
    );
  if (!user) return <Login signedIn={setUser} />;
  return (
    <Workspace
      user={user}
      logout={() => {
        sessionStorage.removeItem("token");
        setUser(null);
      }}
    />
  );
}

function Workspace({ user, logout }: { user: User; logout: () => void }) {
  const [data, setData] = useState<Data>(empty);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [branch, setBranch] = useState("");
  const [live, setLive] = useState(false);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("ALL");
  const [list, setList] = useState(false);
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const [detail, setDetail] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const [time, setTime] = useState(Date.now());
  const [customerId, setCustomerId] = useState("");
  const [balance, setBalance] = useState("0");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [walletLoading, setWalletLoading] = useState(false);
  const [day, setDay] = useState(new Date().toISOString().slice(0, 10));
  const navigate = useNavigate();
  const location = useLocation();
  const admin = user.role === "ADMIN";
  const load = useCallback(async () => {
    try {
      const [
        branches,
        nodes,
        users,
        sessions,
        plans,
        memberships,
        reservations,
        games,
        alerts,
        commands,
      ] = await Promise.all([
        api<Branch[]>("/branches"),
        api<Node[]>("/nodes"),
        api<User[]>("/users"),
        api<Session[]>("/sessions"),
        api<Plan[]>("/membership-plans"),
        api<Membership[]>("/memberships"),
        api<Reservation[]>("/reservations"),
        api<Game[]>("/games"),
        api<Alert[]>("/alerts"),
        api<Command[]>("/commands"),
      ]);
      setData({
        branches,
        nodes,
        users,
        sessions,
        plans,
        memberships,
        reservations,
        games,
        alerts,
        commands,
      });
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
    const interval = setInterval(() => setTime(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [load]);
  useEffect(() => {
    let stopped = false;
    let ws: WebSocket;
    let retry: ReturnType<typeof setTimeout>;
    let refresh: ReturnType<typeof setTimeout>;
    let delay = 1000;
    const connect = () => {
      ws = new WebSocket(
        `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/dashboard`,
      );
      ws.onopen = () => {
        ws.send(JSON.stringify({ token: sessionStorage.getItem("token") }));
      };
      ws.onmessage = () => {
        setLive(true);
        delay = 1000;
        clearTimeout(refresh);
        refresh = setTimeout(() => void load(), 150);
      };
      ws.onclose = () => {
        setLive(false);
        if (!stopped) {
          retry = setTimeout(connect, delay);
          delay = Math.min(delay * 2, 15000);
        }
      };
      ws.onerror = () => ws.close();
    };
    connect();
    const heartbeat = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) ws.send("ping");
    }, 20000);
    const fallback = setInterval(() => void load(), 30000);
    return () => {
      stopped = true;
      clearTimeout(retry);
      clearTimeout(refresh);
      clearInterval(heartbeat);
      clearInterval(fallback);
      ws?.close();
    };
  }, [load]);
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(""), 5000);
      return () => clearTimeout(t);
    }
  }, [toast]);
  const customers = data.users.filter((u) => u.role === "CUSTOMER" && u.active);
  useEffect(() => {
    if (!customerId && customers[0]) setCustomerId(customers[0].id);
  }, [customers, customerId]);
  useEffect(() => {
    if (!customerId) return;
    let current = true;
    setWalletLoading(true);
    Promise.all([
      api<{ balance: string }>(`/users/${customerId}/wallet`),
      api<Transaction[]>(`/users/${customerId}/wallet/transactions`),
    ])
      .then(([w, t]) => {
        if (current) {
          setBalance(w.balance);
          setTransactions(t);
        }
      })
      .catch((e) => {
        if (current) setError(e.message);
      })
      .finally(() => {
        if (current) setWalletLoading(false);
      });
    return () => {
      current = false;
    };
  }, [customerId, data]);
  const nodes = data.nodes.filter((n) => !branch || n.branch_id === branch);
  const sessions = data.sessions.filter((s) =>
    nodes.some((n) => n.id === s.node_id),
  );
  const active = sessions.filter((s) => s.status === "ACTIVE");
  const alerts = data.alerts.filter((a) =>
    nodes.some((n) => n.id === a.node_id),
  );
  const unresolved = alerts.filter((a) => !a.resolved);
  const reservations = data.reservations.filter(
    (r) => !branch || r.branch_id === branch,
  );
  const uname = (id: string) =>
    data.users.find((x) => x.id === id)?.name || "Unknown customer";
  const nname = (id: string) =>
    data.nodes.find((x) => x.id === id)?.name || "Station";
  const bname = (id: string) =>
    data.branches.find((x) => x.id === id)?.name || "Branch";
  const act = async (path: string, method = "POST", body?: unknown) => {
    try {
      await api(path, method, body);
      await load();
      setToast("Changes saved");
    } catch (e) {
      setToast((e as Error).message);
    }
  };
  const confirm = (
    title: string,
    subtitle: string,
    submit: () => Promise<unknown>,
    action = "Confirm",
  ) => setDialog({ title, subtitle, fields: [], submit, action });
  const start = (nodeId?: string) =>
    setDialog({
      title: "Start a gaming session",
      subtitle:
        "Billing uses the hourly rate below and the customer’s prepaid wallet.",
      action: "Start session",
      fields: [
        {
          key: "node_id",
          label: "Station",
          value: nodeId,
          options: nodes.filter(
            (n) =>
              n.status === "ONLINE" && !active.some((s) => s.node_id === n.id),
          ),
        },
        { key: "user_id", label: "Customer", options: customers },
        {
          key: "rate",
          label: "Hourly rate · TND",
          type: "number",
          value: "3.000",
          min: "0.001",
          step: "0.001",
        },
      ],
      submit: (v) => api("/sessions/start", "POST", v),
    });
  const reserve = () =>
    setDialog({
      title: "Reserve a station",
      subtitle:
        "Times use your local timezone. Overlapping reservations are prevented.",
      action: "Create reservation",
      fields: [
        { key: "node_id", label: "Station", options: nodes },
        { key: "user_id", label: "Customer", options: customers },
        { key: "start_time", label: "Start time", type: "datetime-local" },
        { key: "end_time", label: "End time", type: "datetime-local" },
      ],
      submit: (v) =>
        api("/reservations", "POST", {
          ...v,
          start_time: new Date(v.start_time).toISOString(),
          end_time: new Date(v.end_time).toISOString(),
        }),
    });
  const command = (node: Node, kind: string) =>
    confirm(
      `${kind === "lock" ? "Lock" : "Shut down"} ${node.name}?`,
      kind === "lock"
        ? "The player will need their Windows credentials to unlock the station."
        : "Windows will shut down in 30 seconds after the agent accepts this command. Unsaved work may be lost.",
      () => api(`/nodes/${node.id}/${kind}`),
      "Send command",
    );
  const launch = (game: Game, nodeId?: string) =>
    setDialog({
      title: `Launch ${game.name}`,
      subtitle:
        "The game must be installed and allowlisted in the station’s agent configuration.",
      action: "Send launch command",
      fields: [
        {
          key: "node_id",
          label: "Station",
          value: nodeId,
          options: nodes.filter(
            (n) => n.status === "ONLINE" && game.node_ids.includes(n.id),
          ),
        },
      ],
      submit: (v) =>
        api(`/nodes/${v.node_id}/launch-game`, "POST", { game_id: game.id }),
    });
  const editPlan = (p?: Plan) =>
    setDialog({
      title: p ? "Edit membership plan" : "Create membership plan",
      fields: [
        { key: "name", label: "Plan name", value: p?.name },
        { key: "description", label: "Description", value: p?.description },
        {
          key: "price",
          label: "Price · TND",
          value: p?.price || "0",
          type: "number",
          min: "0",
          step: "0.001",
        },
        {
          key: "duration_days",
          label: "Duration · days",
          value: p?.duration_days || 30,
          type: "number",
          min: "1",
        },
        {
          key: "benefits",
          label: "Benefits · separate with semicolons",
          value: p?.benefits,
        },
        {
          key: "active",
          label: "Status",
          value: p?.active === false ? "false" : "true",
          options: [
            { id: "true", name: "Active" },
            { id: "false", name: "Disabled" },
          ],
        },
      ],
      submit: (v) =>
        api("/membership-plans" + (p ? "/" + p.id : ""), p ? "PUT" : "POST", {
          ...v,
          duration_days: Number(v.duration_days),
          active: v.active === "true",
        }),
    });
  const editGame = (g?: Game) =>
    setDialog({
      title: g ? "Edit game" : "Add a game",
      fields: [
        { key: "name", label: "Name", value: g?.name },
        { key: "description", label: "Description", value: g?.description },
        { key: "genre", label: "Genre", value: g?.genre },
        { key: "version", label: "Version", value: g?.version },
        {
          key: "executable_path",
          label: "Windows executable path",
          value: g?.executable_path,
        },
        {
          key: "active",
          label: "Status",
          value: g?.active === false ? "false" : "true",
          options: [
            { id: "true", name: "Active" },
            { id: "false", name: "Disabled" },
          ],
        },
      ],
      submit: (v) =>
        api("/games" + (g ? "/" + g.id : ""), g ? "PUT" : "POST", {
          ...v,
          active: v.active === "true",
        }),
    });
  const editBranch = (b?: Branch) =>
    setDialog({
      title: b ? "Edit branch" : "Add a branch",
      fields: [
        { key: "name", label: "Branch name", value: b?.name },
        { key: "address", label: "Address", value: b?.address },
      ],
      submit: (v) =>
        api("/branches" + (b ? "/" + b.id : ""), b ? "PUT" : "POST", v),
    });
  const heading =
    navigation.find((n) => n[0] === location.pathname)?.[1] || "Overview";
  const metric = (
    label: string,
    value: ReactNode,
    icon: ReactNode,
    note: string,
    tone = "",
  ) => (
    <div className={"metric " + tone}>
      <div className="metric-label">
        {label}
        <span>{icon}</span>
      </div>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
  const stationCard = (node: Node) => {
    const s = active.find((s) => s.node_id === node.id);
    const online = node.status === "ONLINE";
    return (
      <article
        className={
          "station " + (s ? "in-session" : "") + (!online ? " offline" : "")
        }
        key={node.id}
      >
        <div className="station-top">
          <span className="station-icon">
            <Monitor size={23} />
          </span>
          <Badge tone={online ? (s ? "purple" : "green") : ""}>
            {online ? (s ? "In session" : "Available") : "Offline"}
          </Badge>
          <button
            className="icon-button"
            aria-label={`View ${node.name}`}
            onClick={() => setDetail(node.id)}
          >
            <MoreHorizontal size={20} />
          </button>
        </div>
        <button className="station-title" onClick={() => setDetail(node.id)}>
          {node.name}
          <ArrowUpRight size={17} />
        </button>
        <p className="station-location">
          {bname(node.branch_id).replace(" Gaming House", "")} <span>·</span>{" "}
          {node.os.toLowerCase().includes("windows")
            ? "Windows"
            : "Gaming station"}
        </p>
        <div className="telemetry-bars">
          {(["cpu", "ram"] as const).map((key) => (
            <div key={key}>
              <div>
                <span>{key.toUpperCase()}</span>
                <b>
                  {online && node.telemetry[key] != null
                    ? Math.round(node.telemetry[key]!) + "%"
                    : "—"}
                </b>
              </div>
              <div className="track">
                <i
                  style={{
                    width: (online ? node.telemetry[key] || 0 : 0) + "%",
                  }}
                />
              </div>
            </div>
          ))}
        </div>
        <div className="station-session">
          {s ? (
            <>
              <span className="avatar tiny">
                {uname(s.user_id).slice(0, 1)}
              </span>
              <div>
                <b>{uname(s.user_id)}</b>
                <small>
                  {duration(s, time)} <span>·</span> {money(cost(s, time))} TND
                </small>
              </div>
              <span className="pulse" />
            </>
          ) : (
            <>
              <Clock3 size={17} />
              <span>
                {online
                  ? "Ready for the next player"
                  : "Waiting for agent connection"}
              </span>
            </>
          )}
        </div>
        <div className="station-actions">
          <button onClick={() => setDetail(node.id)}>
            Station details
            <ChevronRight size={14} />
          </button>
          {online && (
            <button
              aria-label={`Lock ${node.name}`}
              onClick={() => command(node, "lock")}
            >
              <LockKeyhole size={14} />
            </button>
          )}
        </div>
      </article>
    );
  };
  const sessionTable = (items: Session[]) => (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Station / player</th>
            <th>Started</th>
            <th>Duration</th>
            <th>Rate / hr</th>
            <th>Total · TND</th>
            <th>Status</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {items.map((s) => (
            <tr key={s.id}>
              <td>
                <b>{nname(s.node_id)}</b>
                <small>{uname(s.user_id)}</small>
              </td>
              <td>{stamp(s.start_time)}</td>
              <td className="mono">{duration(s, time)}</td>
              <td>{money(s.rate)}</td>
              <td className="text-white">{money(cost(s, time))}</td>
              <td>
                <Badge tone={s.status === "ACTIVE" ? "purple" : ""}>
                  {s.status === "ACTIVE" ? "Live" : "Completed"}
                </Badge>
              </td>
              <td>
                {s.status === "ACTIVE" && (
                  <button
                    className="button small secondary"
                    onClick={() =>
                      confirm(
                        "End session & bill wallet?",
                        `${nname(s.node_id)} · ${uname(s.user_id)}. The final cost is calculated when you confirm.`,
                        () => api(`/sessions/${s.id}/stop`, "POST"),
                        "End & bill",
                      )
                    }
                  >
                    End session
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!items.length && (
        <Empty>
          No sessions to show. Start a session on a connected station.
        </Empty>
      )}
    </div>
  );
  const reservationsTable = (items: Reservation[]) => (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Player</th>
            <th>Station</th>
            <th>Time slot</th>
            <th>Status</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {items.map((r) => (
            <tr key={r.id}>
              <td>
                <b>{uname(r.user_id)}</b>
              </td>
              <td>{nname(r.node_id)}</td>
              <td>
                {stamp(r.start_time)}
                <small>to {stamp(r.end_time)}</small>
              </td>
              <td>
                <Badge tone={r.status === "CONFIRMED" ? "cyan" : ""}>
                  {r.status.toLowerCase()}
                </Badge>
              </td>
              <td>
                {r.status === "CONFIRMED" && (
                  <button
                    className="text-button"
                    onClick={() =>
                      confirm(
                        "Cancel this reservation?",
                        `${uname(r.user_id)} · ${nname(r.node_id)}`,
                        () => api(`/reservations/${r.id}`, "DELETE"),
                        "Cancel reservation",
                      )
                    }
                  >
                    Cancel
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!items.length && <Empty>No reservations for this selection.</Empty>}
    </div>
  );
  const selected = data.nodes.find((n) => n.id === detail);
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Brand />
        <div className="workspace-tag">
          <span className="arena-symbol">
            <Gamepad2 size={19} />
          </span>
          <div>
            NexArena workspace<small>Esports management</small>
          </div>
          <ChevronDown size={14} />
        </div>
        <span className="nav-heading">WORKSPACE</span>
        <nav>
          {navigation.map(([path, label, Icon], i) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              className={({ isActive }) =>
                (isActive ? "active " : "") + (i === 8 ? "nav-divider" : "")
              }
            >
              <Icon size={18} />
              <span>{label}</span>
              {path === "/alerts" && unresolved.length > 0 && (
                <em>{unresolved.length}</em>
              )}
              {path === "/" && <span className="active-dot" />}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="connection">
            <span className={"dot " + (live ? "green" : "")} />
            <span>
              {live ? "Live connection" : "Reconnecting…"}
              <small>
                {live ? "Your arena is in sync" : "Trying to reach the server"}
              </small>
            </span>
          </div>
          <div className="profile">
            <span className="avatar">
              {user.name
                .split(" ")
                .map((x) => x[0])
                .slice(0, 2)
                .join("")}
            </span>
            <div>
              {user.name}
              <small>
                {user.role === "ADMIN" ? "Administrator" : "Operations staff"}
              </small>
            </div>
            <button
              className="icon-button"
              aria-label="Sign out"
              onClick={async () => {
                try {
                  await api("/auth/logout", "POST");
                  logout();
                } catch (e) {
                  setToast((e as Error).message);
                }
              }}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            Workspace
            <ChevronRight size={14} />
            <span>{heading}</span>
          </div>
          <div className="topbar-actions">
            <div className="branch-select">
              <MapPin size={15} />
              <select
                aria-label="Branch filter"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
              >
                <option value="">All branches</option>
                {data.branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name.replace(" Gaming House", "")}
                  </option>
                ))}
              </select>
            </div>
            <span className="top-divider" />
            <button
              className="notification"
              aria-label="View alerts"
              onClick={() => navigate("/alerts")}
            >
              <Bell size={19} />
              {unresolved.length > 0 && <i />}
            </button>
            <span className="avatar small-avatar">{user.name.slice(0, 1)}</span>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                {location.pathname === "/"
                  ? "YOUR ARENA AT A GLANCE"
                  : "NEXARENA / OPERATIONS"}
              </div>
              <h1>
                {location.pathname === "/" ? "Command center" : heading}
                <span className="heading-dot" aria-hidden="true">
                  .
                </span>
              </h1>
              <p>
                {location.pathname === "/"
                  ? "Stay connected. Keep the games going."
                  : (
                      {
                        "/stations":
                          "Your stations, connected and under control.",
                        "/sessions":
                          "Track playtime. Keep every minute accounted for.",
                        "/reservations": "Make room for the next great game.",
                        "/wallets": "A clear view of every player’s balance.",
                        "/memberships":
                          "Give your community a reason to keep coming back.",
                        "/games": "One library. Every station. Ready to play.",
                        "/alerts": "Keep an eye on what needs your attention.",
                        "/users": "The people who make your arena.",
                        "/branches": "One workspace for all your locations.",
                      } as Record<string, string>
                    )[location.pathname]}
              </p>
            </div>
            <div className="heading-actions">
              {["/", "/stations", "/sessions"].includes(location.pathname) ? (
                <button className="button primary" onClick={() => start()}>
                  <Plus size={18} />
                  Start session
                </button>
              ) : location.pathname === "/reservations" ? (
                <button className="button primary" onClick={reserve}>
                  <Plus size={18} />
                  New reservation
                </button>
              ) : admin && location.pathname === "/games" ? (
                <button className="button primary" onClick={() => editGame()}>
                  <Plus size={18} />
                  Add game
                </button>
              ) : admin && location.pathname === "/memberships" ? (
                <button className="button primary" onClick={() => editPlan()}>
                  <Plus size={18} />
                  Create plan
                </button>
              ) : admin && location.pathname === "/branches" ? (
                <button className="button primary" onClick={() => editBranch()}>
                  <Plus size={18} />
                  Add branch
                </button>
              ) : admin && location.pathname === "/users" ? (
                <button
                  className="button primary"
                  onClick={() =>
                    setDialog({
                      title: "Add a person",
                      fields: [
                        { key: "name", label: "Full name" },
                        { key: "email", label: "Email", type: "email" },
                        {
                          key: "password",
                          label: "Password · minimum 10 characters",
                          type: "password",
                        },
                        {
                          key: "role",
                          label: "Role",
                          value: "CUSTOMER",
                          options: ["CUSTOMER", "STAFF", "ADMIN"].map((id) => ({
                            id,
                            name: id,
                          })),
                        },
                      ],
                      submit: (v) => api("/users", "POST", v),
                    })
                  }
                >
                  <Plus size={18} />
                  Add person
                </button>
              ) : null}
            </div>
          </div>
          {error && (
            <div className="error" role="alert">
              {error}
              <button onClick={() => void load()}>Retry</button>
            </div>
          )}
          {loading ? (
            <div className="loading-grid">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div className="skeleton" key={i} />
              ))}
            </div>
          ) : (
            <Routes>
              <Route
                path="/"
                element={
                  <>
                    <section className="hero-banner">
                      <div>
                        <Badge tone="cyan">
                          <Radio size={12} />
                          LIVE OPERATIONS
                        </Badge>
                        <h2>Every station. One arena.</h2>
                        <p>Your next great player experience starts here.</p>
                        <button
                          className="text-button"
                          onClick={() => navigate("/stations")}
                        >
                          Manage your stations
                          <ArrowRight size={16} />
                        </button>
                      </div>
                      <div className="hero-art" aria-hidden="true">
                        <div className="orbit orbit-one" />
                        <div className="orbit orbit-two" />
                        <div className="hero-screen">
                          <span />
                          <div>
                            <Zap size={46} />
                          </div>
                          <small>NEX / CONNECTED</small>
                        </div>
                        <div className="hero-chip">
                          <span className="dot green" />
                          ARENA NETWORK
                        </div>
                      </div>
                      <div className="hero-index">01 / CONTROL</div>
                    </section>
                    <div className="metrics">
                      {metric(
                        "Total stations",
                        nodes.length,
                        <Monitor size={17} />,
                        `${data.branches.filter((b) => !branch || b.id === branch).length} connected locations`,
                      )}
                      {metric(
                        "Online now",
                        nodes.filter((n) => n.status === "ONLINE").length,
                        <Radio size={17} />,
                        `${nodes.filter((n) => n.status === "OFFLINE").length} stations offline`,
                        "green",
                      )}
                      {metric(
                        "Active sessions",
                        active.length,
                        <Clock3 size={17} />,
                        active.length
                          ? "Players in the arena"
                          : "Ready for the next session",
                        "purple",
                      )}
                      {metric(
                        "Today’s revenue",
                        <>
                          {money(
                            sessions
                              .filter(
                                (s) =>
                                  s.end_time &&
                                  new Date(s.end_time).toDateString() ===
                                    new Date(time).toDateString(),
                              )
                              .reduce((sum, s) => sum + Number(s.cost), 0),
                          )}
                          <em>TND</em>
                        </>,
                        <CreditCard size={17} />,
                        "Completed session payments",
                        "cyan",
                      )}
                    </div>
                    <div className="section-title">
                      <div>
                        <h2>
                          Live gaming stations{" "}
                          <span className="count">{nodes.length}</span>
                        </h2>
                        <p>A real-time view of your arena floor.</p>
                      </div>
                      <div className="section-actions">
                        <span className="live-label">
                          <span className={"dot " + (live ? "green" : "")} />
                          {live ? "Live updates" : "Reconnecting"}
                        </span>
                        <button
                          className="text-button"
                          onClick={() => navigate("/stations")}
                        >
                          View all
                          <ArrowRight size={15} />
                        </button>
                      </div>
                    </div>
                    <div className="station-grid">
                      {nodes.slice(0, 4).map(stationCard)}
                    </div>
                    {!nodes.length && (
                      <Empty>No stations enrolled in this branch.</Empty>
                    )}
                    <div className="overview-bottom">
                      <Panel
                        title="Upcoming reservations"
                        action={
                          <button
                            className="text-button"
                            onClick={() => navigate("/reservations")}
                          >
                            View all
                            <ArrowRight size={14} />
                          </button>
                        }
                      >
                        {reservationsTable(
                          reservations
                            .filter(
                              (r) =>
                                r.status === "CONFIRMED" &&
                                new Date(r.end_time).getTime() > time,
                            )
                            .slice(0, 3),
                        )}
                      </Panel>
                      <Panel
                        title="Arena activity"
                        action={<Activity size={17} className="muted" />}
                      >
                        <div className="activity-feed">
                          {unresolved.slice(0, 3).map((a) => (
                            <div key={a.id}>
                              <span className="activity-icon warning">
                                <Bell size={16} />
                              </span>
                              <div>
                                <b>{a.message}</b>
                                <small>{stamp(a.created_at)}</small>
                              </div>
                            </div>
                          ))}
                          {data.commands
                            .filter((c) =>
                              nodes.some((n) => n.id === c.node_id),
                            )
                            .slice(0, 2)
                            .map((c) => (
                              <div key={c.id}>
                                <span className="activity-icon">
                                  <Zap size={16} />
                                </span>
                                <div>
                                  <b>
                                    {nname(c.node_id)} ·{" "}
                                    {c.type.toLowerCase().replaceAll("_", " ")}
                                  </b>
                                  <small>
                                    {c.status.toLowerCase()} ·{" "}
                                    {stamp(c.created_at)}
                                  </small>
                                </div>
                              </div>
                            ))}
                          {!unresolved.length && !data.commands.length && (
                            <div>
                              <span className="activity-icon">
                                <ShieldCheck size={18} />
                              </span>
                              <div>
                                <b>All clear. You’re in control.</b>
                                <small>No alerts or remote commands yet.</small>
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="activity-footer">
                          <ShieldCheck size={15} />
                          {unresolved.length
                            ? `${unresolved.length} alerts need your attention`
                            : "No unresolved alerts"}
                          <button
                            onClick={() => navigate("/alerts")}
                            aria-label="Open alerts"
                          >
                            <ArrowRight size={16} />
                          </button>
                        </div>
                      </Panel>
                    </div>
                  </>
                }
              />
              <Route
                path="/stations"
                element={
                  <>
                    <div className="filters">
                      <div className="search">
                        <Search size={17} />
                        <input
                          aria-label="Search stations"
                          placeholder="Search stations…"
                          value={search}
                          onChange={(e) => setSearch(e.target.value)}
                        />
                      </div>
                      <select
                        aria-label="Station status"
                        value={status}
                        onChange={(e) => setStatus(e.target.value)}
                      >
                        <option value="ALL">All statuses</option>
                        <option value="ONLINE">Online</option>
                        <option value="OFFLINE">Offline</option>
                        <option value="ACTIVE">In session</option>
                      </select>
                      <button
                        className="button secondary"
                        onClick={() => setList(!list)}
                      >
                        {list ? "Grid view" : "List view"}
                      </button>
                      <button
                        className="icon-button"
                        aria-label="Refresh stations"
                        onClick={() => void load()}
                      >
                        <RefreshCw size={17} />
                      </button>
                    </div>
                    <div
                      className={"station-grid " + (list ? "station-list" : "")}
                    >
                      {nodes
                        .filter(
                          (n) =>
                            n.name
                              .toLowerCase()
                              .includes(search.toLowerCase()) &&
                            (status === "ALL" ||
                              status === n.status ||
                              (status === "ACTIVE" &&
                                active.some((s) => s.node_id === n.id))),
                        )
                        .map(stationCard)}
                    </div>
                    {!nodes.filter(
                      (n) =>
                        n.name.toLowerCase().includes(search.toLowerCase()) &&
                        (status === "ALL" ||
                          status === n.status ||
                          (status === "ACTIVE" &&
                            active.some((s) => s.node_id === n.id))),
                    ).length && (
                      <Empty>
                        No stations match your filters. Connect an agent or
                        change your selection.
                      </Empty>
                    )}
                  </>
                }
              />
              <Route
                path="/sessions"
                element={
                  <>
                    <div className="metrics three">
                      {metric(
                        "Playing now",
                        active.length,
                        <Clock3 size={18} />,
                        "Active sessions",
                        "purple",
                      )}
                      {metric(
                        "Completed sessions",
                        sessions.filter((s) => s.status === "COMPLETED").length,
                        <Check size={18} />,
                        "Across selected locations",
                      )}
                      {metric(
                        "Billed revenue",
                        <>
                          {money(
                            sessions.reduce(
                              (sum, s) => sum + Number(s.cost),
                              0,
                            ),
                          )}
                          <em>TND</em>
                        </>,
                        <Wallet size={18} />,
                        "All completed sessions",
                        "cyan",
                      )}
                    </div>
                    <Panel title="Active sessions">
                      {sessionTable(active)}
                    </Panel>
                    <Panel title="Session history">
                      {sessionTable(
                        sessions.filter((s) => s.status !== "ACTIVE"),
                      )}
                    </Panel>
                  </>
                }
              />
              <Route
                path="/reservations"
                element={
                  <>
                    <div className="filters">
                      <CalendarDays size={20} />
                      <input
                        aria-label="Reservation date"
                        type="date"
                        value={day}
                        onChange={(e) => setDay(e.target.value)}
                      />
                      <span className="muted">
                        Times shown in your local timezone
                      </span>
                    </div>
                    <Panel title="Arena schedule">
                      <div className="timeline">
                        <div className="timeline-labels">
                          <span>STATION</span>
                          {[0, 4, 8, 12, 16, 20, 24].map((h) => (
                            <span key={h}>{String(h).padStart(2, "0")}:00</span>
                          ))}
                        </div>
                        {nodes.map((n) => (
                          <div className="timeline-row" key={n.id}>
                            <b>
                              {n.name}
                              <small>
                                {active.some((s) => s.node_id === n.id)
                                  ? "Occupied"
                                  : "No active session"}
                              </small>
                            </b>
                            <div className="timeline-track">
                              {reservations
                                .filter(
                                  (r) =>
                                    r.node_id === n.id &&
                                    r.status === "CONFIRMED" &&
                                    new Date(r.start_time) <
                                      new Date(day + "T23:59:59") &&
                                    new Date(r.end_time) >
                                      new Date(day + "T00:00:00"),
                                )
                                .map((r) => {
                                  const start = Math.max(
                                    0,
                                    ((new Date(r.start_time).getTime() -
                                      new Date(day + "T00:00:00").getTime()) /
                                      86400000) *
                                      100,
                                  );
                                  const end = Math.min(
                                    100,
                                    ((new Date(r.end_time).getTime() -
                                      new Date(day + "T00:00:00").getTime()) /
                                      86400000) *
                                      100,
                                  );
                                  return (
                                    <div
                                      key={r.id}
                                      className="reservation-block"
                                      style={{
                                        left: start + "%",
                                        width: Math.max(end - start, 1) + "%",
                                      }}
                                      title={`${uname(r.user_id)} · ${stamp(r.start_time)} – ${stamp(r.end_time)}`}
                                    >
                                      {uname(r.user_id)}
                                    </div>
                                  );
                                })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </Panel>
                    <Panel title="Reservations">
                      {reservationsTable(
                        reservations.filter(
                          (r) =>
                            new Date(r.start_time).toLocaleDateString(
                              "en-CA",
                            ) === day ||
                            new Date(r.end_time).toLocaleDateString("en-CA") ===
                              day,
                        ),
                      )}
                    </Panel>
                  </>
                }
              />
              <Route
                path="/wallets"
                element={
                  <>
                    <div className="filters">
                      <Users size={19} />
                      <select
                        aria-label="Select customer wallet"
                        value={customerId}
                        onChange={(e) => setCustomerId(e.target.value)}
                      >
                        {customers.map((u) => (
                          <option key={u.id} value={u.id}>
                            {u.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    {walletLoading ? (
                      <Empty>Loading wallet…</Empty>
                    ) : customerId ? (
                      <>
                        <div className="wallet-card">
                          <div>
                            <span className="eyebrow">PLAYER WALLET</span>
                            <h2>{uname(customerId)}</h2>
                            <span className="balance">
                              {money(balance)}
                              <small>TND</small>
                            </span>
                            <p>Available prepaid balance</p>
                          </div>
                          <Wallet size={76} />
                          {admin && (
                            <button
                              className="button primary"
                              onClick={() => {
                                const reference = crypto.randomUUID();
                                setDialog({
                                  title: "Top up wallet",
                                  subtitle: `Add credit for ${uname(customerId)}. Record the payment received at your arena.`,
                                  action: "Add credit",
                                  fields: [
                                    {
                                      key: "amount",
                                      label: "Amount · TND",
                                      type: "number",
                                      min: "0.001",
                                      step: "0.001",
                                      value: "20.000",
                                    },
                                  ],
                                  submit: (v) =>
                                    api(
                                      `/users/${customerId}/wallet/topup`,
                                      "POST",
                                      { ...v, reference },
                                    ),
                                });
                              }}
                            >
                              <Plus size={17} />
                              Top up wallet
                            </button>
                          )}
                        </div>
                        <Panel title="Transaction history">
                          <div className="table-wrap">
                            <table>
                              <thead>
                                <tr>
                                  <th>Transaction</th>
                                  <th>Date</th>
                                  <th>Reference</th>
                                  <th>Amount · TND</th>
                                </tr>
                              </thead>
                              <tbody>
                                {transactions.map((t) => (
                                  <tr key={t.id}>
                                    <td>
                                      <span className="inline-flex gap-2 items-center">
                                        {Number(t.amount) > 0 ? (
                                          <ArrowDownLeft
                                            size={17}
                                            className="cyan"
                                          />
                                        ) : (
                                          <ArrowUpRight size={17} />
                                        )}{" "}
                                        {t.type.replaceAll("_", " ")}
                                      </span>
                                    </td>
                                    <td>{stamp(t.created_at)}</td>
                                    <td className="mono">
                                      {t.reference.slice(0, 24)}…
                                    </td>
                                    <td
                                      className={
                                        Number(t.amount) > 0 ? "cyan" : ""
                                      }
                                    >
                                      {Number(t.amount) > 0 ? "+" : ""}
                                      {money(t.amount)}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            {!transactions.length && (
                              <Empty>No transactions yet.</Empty>
                            )}
                          </div>
                        </Panel>
                      </>
                    ) : (
                      <Empty>Add a customer to create a wallet.</Empty>
                    )}
                  </>
                }
              />
              <Route
                path="/memberships"
                element={
                  <>
                    <div className="plans">
                      {data.plans.map((p, i) => (
                        <article
                          className={"plan " + (i === 1 ? "featured" : "")}
                          key={p.id}
                        >
                          <div className="plan-icon">
                            <Crown size={23} />
                          </div>
                          <Badge tone={p.active ? "cyan" : ""}>
                            {p.active ? "Active plan" : "Disabled"}
                          </Badge>
                          <h2>{p.name}</h2>
                          <p>{p.description}</p>
                          <div className="plan-price">
                            {Number(p.price).toFixed(0)}
                            <small>TND / {p.duration_days} days</small>
                          </div>
                          <ul>
                            {p.benefits.split(";").map((b) => (
                              <li key={b}>
                                <Check size={15} />
                                {b}
                              </li>
                            ))}
                          </ul>
                          {admin && (
                            <div className="flex gap-2">
                              <button
                                className="button secondary"
                                onClick={() => editPlan(p)}
                              >
                                Edit plan
                              </button>
                              <button
                                className="button primary"
                                disabled={!p.active}
                                onClick={() =>
                                  setDialog({
                                    title: `Assign ${p.name}`,
                                    subtitle:
                                      "Internal membership assignment. No external payment is collected.",
                                    fields: [
                                      {
                                        key: "user_id",
                                        label: "Customer",
                                        options: customers,
                                      },
                                    ],
                                    submit: (v) =>
                                      api(
                                        `/users/${v.user_id}/membership`,
                                        "POST",
                                        { plan_id: p.id },
                                      ),
                                    action: "Assign membership",
                                  })
                                }
                              >
                                Assign
                                <ArrowRight size={15} />
                              </button>
                            </div>
                          )}
                        </article>
                      ))}
                    </div>
                    <Panel title="Member directory">
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Player</th>
                              <th>Plan</th>
                              <th>Expires</th>
                              <th>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.memberships.map((m) => (
                              <tr key={m.user_id}>
                                <td>
                                  <b>{uname(m.user_id)}</b>
                                </td>
                                <td>
                                  {
                                    data.plans.find((p) => p.id === m.plan_id)
                                      ?.name
                                  }
                                </td>
                                <td>{stamp(m.expiration_date)}</td>
                                <td>
                                  <Badge
                                    tone={m.status === "ACTIVE" ? "green" : ""}
                                  >
                                    {m.status.toLowerCase()}
                                  </Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {!data.memberships.length && (
                          <Empty>No memberships assigned yet.</Empty>
                        )}
                      </div>
                    </Panel>
                  </>
                }
              />
              <Route
                path="/games"
                element={
                  <div className="game-grid">
                    {data.games.map((g, i) => (
                      <article className="game-card" key={g.id}>
                        <div className={"game-art game-art-" + (i % 3)}>
                          <span className="game-art-index">
                            0{i + 1} / NEX LIBRARY
                          </span>
                          <Gamepad2 size={100} strokeWidth={0.7} />
                          <span className="game-art-title">{g.name}</span>
                          <Badge tone={g.active ? "green" : ""}>
                            {g.active ? "Active" : "Disabled"}
                          </Badge>
                        </div>
                        <div className="game-content">
                          <div className="eyebrow">
                            {g.genre} <span> / </span> {g.version}
                          </div>
                          <h2>{g.name}</h2>
                          <p>{g.description}</p>
                          <div className="game-availability">
                            <Monitor size={14} />
                            {g.node_ids.length} assigned stations
                          </div>
                          <details>
                            <summary>Configuration</summary>
                            <small className="mono break-all">
                              ID: {g.id}
                              <br />
                              {g.executable_path}
                            </small>
                          </details>
                          <div className="game-actions">
                            <button
                              className="button primary"
                              disabled={!g.active}
                              onClick={() => launch(g)}
                            >
                              Launch game
                              <ArrowUpRight size={15} />
                            </button>
                            {admin && (
                              <>
                                <button
                                  className="button secondary"
                                  onClick={() => editGame(g)}
                                >
                                  Edit
                                </button>
                                <button
                                  className="icon-button"
                                  aria-label={`Assign ${g.name} to a station`}
                                  onClick={() =>
                                    setDialog({
                                      title: "Assign game to station",
                                      fields: [
                                        {
                                          key: "node_id",
                                          label: "Station",
                                          options: nodes,
                                        },
                                      ],
                                      submit: (v) =>
                                        api(
                                          `/nodes/${v.node_id}/games/${g.id}`,
                                          "PUT",
                                        ),
                                    })
                                  }
                                >
                                  <Plus size={18} />
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      </article>
                    ))}
                    {!data.games.length && (
                      <Empty>Add your first game to the library.</Empty>
                    )}
                  </div>
                }
              />
              <Route
                path="/alerts"
                element={
                  <>
                    <Panel title={`Alerts · ${unresolved.length} unresolved`}>
                      {alerts.length ? (
                        <div className="alert-list">
                          {alerts.map((a) => (
                            <div
                              className={
                                "alert-item " + (a.resolved ? "resolved" : "")
                              }
                              key={a.id}
                            >
                              <span className="activity-icon warning">
                                <Bell size={20} />
                              </span>
                              <div>
                                <b>{a.message}</b>
                                <small>
                                  {nname(a.node_id)} · {stamp(a.created_at)}
                                </small>
                              </div>
                              <Badge tone={a.resolved ? "green" : "amber"}>
                                {a.resolved
                                  ? "Resolved"
                                  : a.severity.toLowerCase()}
                              </Badge>
                              {!a.resolved && (
                                <button
                                  className="button secondary small"
                                  onClick={() =>
                                    void act(`/alerts/${a.id}`, "PUT")
                                  }
                                >
                                  Resolve
                                  <Check size={14} />
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <Empty>
                          No alerts. Peripheral changes will appear here as
                          agents report them.
                        </Empty>
                      )}
                    </Panel>
                    <Panel title="Remote command history">
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Station</th>
                              <th>Command</th>
                              <th>Time</th>
                              <th>Status</th>
                              <th>Agent response</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.commands
                              .filter((c) =>
                                nodes.some((n) => n.id === c.node_id),
                              )
                              .map((c) => (
                                <tr key={c.id}>
                                  <td>{nname(c.node_id)}</td>
                                  <td>{c.type}</td>
                                  <td>{stamp(c.created_at)}</td>
                                  <td>
                                    <Badge
                                      tone={
                                        c.status === "SUCCEEDED"
                                          ? "green"
                                          : c.status === "PENDING"
                                            ? "cyan"
                                            : "amber"
                                      }
                                    >
                                      {c.status}
                                    </Badge>
                                  </td>
                                  <td>{c.result || "Waiting for agent…"}</td>
                                </tr>
                              ))}
                          </tbody>
                        </table>
                        {!data.commands.length && (
                          <Empty>No remote commands sent yet.</Empty>
                        )}
                      </div>
                    </Panel>
                  </>
                }
              />
              <Route
                path="/users"
                element={
                  <Panel title="People directory">
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th />
                          </tr>
                        </thead>
                        <tbody>
                          {data.users.map((u) => (
                            <tr key={u.id}>
                              <td>
                                <b>{u.name}</b>
                              </td>
                              <td>{u.email}</td>
                              <td>
                                <Badge
                                  tone={u.role === "ADMIN" ? "purple" : ""}
                                >
                                  {u.role}
                                </Badge>
                              </td>
                              <td>{u.active ? "Active" : "Disabled"}</td>
                              <td>
                                {admin && (
                                  <button
                                    className="text-button"
                                    onClick={() =>
                                      setDialog({
                                        title: "Edit person",
                                        fields: [
                                          {
                                            key: "name",
                                            label: "Name",
                                            value: u.name,
                                          },
                                          {
                                            key: "role",
                                            label: "Role",
                                            value: u.role,
                                            options: [
                                              "ADMIN",
                                              "STAFF",
                                              "CUSTOMER",
                                            ].map((id) => ({ id, name: id })),
                                          },
                                          {
                                            key: "active",
                                            label: "Account status",
                                            value: String(u.active),
                                            options: [
                                              { id: "true", name: "Active" },
                                              { id: "false", name: "Disabled" },
                                            ],
                                          },
                                        ],
                                        submit: (v) =>
                                          api(`/users/${u.id}`, "PUT", {
                                            ...v,
                                            active: v.active === "true",
                                          }),
                                      })
                                    }
                                  >
                                    Edit
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Panel>
                }
              />
              <Route
                path="/branches"
                element={
                  <div className="branch-grid">
                    {data.branches.map((b) => (
                      <Panel
                        key={b.id}
                        title={b.name}
                        action={<MapPin size={21} className="cyan" />}
                      >
                        <div className="branch-body">
                          <p>{b.address}</p>
                          <div className="branch-stats">
                            <div>
                              <strong>
                                {
                                  data.nodes.filter((n) => n.branch_id === b.id)
                                    .length
                                }
                              </strong>
                              <small>Stations</small>
                            </div>
                            <div>
                              <strong>
                                {
                                  data.nodes.filter(
                                    (n) =>
                                      n.branch_id === b.id &&
                                      n.status === "ONLINE",
                                  ).length
                                }
                              </strong>
                              <small>Online</small>
                            </div>
                          </div>
                          <label>
                            Branch ID for agent setup
                            <input readOnly value={b.id} />
                          </label>
                          <div className="flex gap-2">
                            <button
                              className="button primary"
                              onClick={() => {
                                setBranch(b.id);
                                navigate("/stations");
                              }}
                            >
                              View stations
                              <ArrowRight size={15} />
                            </button>
                            {admin && (
                              <button
                                className="button secondary"
                                onClick={() => editBranch(b)}
                              >
                                Edit branch
                              </button>
                            )}
                          </div>
                        </div>
                      </Panel>
                    ))}
                  </div>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          )}
          <footer>
            <span>
              NEXARENA<span className="footer-divider">/</span>Built for the
              next level.
            </span>
            <span>
              <span className={"dot " + (live ? "green" : "")} />
              {live ? "Systems connected" : "Connection interrupted"}
              <span className="footer-divider">·</span>
              {new Date(time).toLocaleDateString([], {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
            </span>
          </footer>
        </main>
      </div>
      {dialog && (
        <FormDialog
          dialog={dialog}
          close={() => setDialog(null)}
          done={() => {
            setDialog(null);
            void load();
            setToast("Request saved. Remote command results appear in Alerts.");
          }}
        />
      )}
      {selected && (
        <div className="modal-backdrop">
          <section
            className="modal station-detail"
            role="dialog"
            aria-modal="true"
            aria-label={selected.name + " details"}
          >
            <div className="panel-head">
              <div>
                <span className="eyebrow">STATION DETAILS</span>
                <h2>{selected.name}</h2>
              </div>
              <button
                className="icon-button"
                aria-label="Close station details"
                onClick={() => setDetail(null)}
              >
                <X />
              </button>
            </div>
            <Badge tone={selected.status === "ONLINE" ? "green" : ""}>
              {selected.status}
            </Badge>
            <dl className="system-info">
              <div>
                <dt>Location</dt>
                <dd>{bname(selected.branch_id)}</dd>
              </div>
              <div>
                <dt>Hostname / IP</dt>
                <dd>
                  {selected.hostname} / {selected.ip_address || "—"}
                </dd>
              </div>
              <div>
                <dt>Operating system</dt>
                <dd>{selected.os}</dd>
              </div>
              <div>
                <dt>Agent / last seen</dt>
                <dd>
                  {selected.agent_version || "Not connected"} /{" "}
                  {stamp(selected.last_heartbeat)}
                </dd>
              </div>
            </dl>
            {admin && (
              <button
                className="text-button mb-5"
                onClick={() => {
                  setDetail(null);
                  setDialog({
                    title: "Edit station",
                    subtitle:
                      "Update the agent configuration to match when moving a station between branches.",
                    fields: [
                      {
                        key: "name",
                        label: "Station name",
                        value: selected.name,
                      },
                      {
                        key: "branch_id",
                        label: "Branch",
                        value: selected.branch_id,
                        options: data.branches,
                      },
                    ],
                    submit: (v) => api("/nodes/" + selected.id, "PUT", v),
                  });
                }}
              >
                Edit station configuration
                <ArrowRight size={14} />
              </button>
            )}
            <h3>Latest hardware readings</h3>
            <p className="muted text-xs">
              {selected.telemetry.timestamp
                ? `Reported ${stamp(selected.telemetry.timestamp)}`
                : "Waiting for real agent telemetry. Unavailable sensors display —."}
            </p>
            <div className="sensor-grid">
              {(
                [
                  [Cpu, "CPU", selected.telemetry.cpu, "%"],
                  [MemoryStick, "RAM", selected.telemetry.ram, "%"],
                  [
                    Thermometer,
                    "CPU temp",
                    selected.telemetry.cpu_temperature,
                    "°C",
                  ],
                  [
                    Thermometer,
                    "GPU temp",
                    selected.telemetry.gpu_temperature,
                    "°C",
                  ],
                  [Fan, "Fan", selected.telemetry.fan_rpm, " RPM"],
                  [
                    Keyboard,
                    "Keyboard",
                    selected.telemetry.keyboard == null
                      ? null
                      : selected.telemetry.keyboard
                        ? "Connected"
                        : "Disconnected",
                    "",
                  ],
                  [
                    Mouse,
                    "Mouse",
                    selected.telemetry.mouse == null
                      ? null
                      : selected.telemetry.mouse
                        ? "Connected"
                        : "Disconnected",
                    "",
                  ],
                ] as const
              ).map(([Icon, label, value, unit]) => (
                <div key={label}>
                  <Icon size={17} />
                  <span>{label}</span>
                  <b>
                    {value == null
                      ? "—"
                      : typeof value === "number"
                        ? Math.round(value) + unit
                        : value}
                  </b>
                </div>
              ))}
            </div>
            <div className="detail-actions">
              <button
                className="button primary"
                disabled={
                  selected.status !== "ONLINE" ||
                  active.some((s) => s.node_id === selected.id)
                }
                onClick={() => {
                  setDetail(null);
                  start(selected.id);
                }}
              >
                <Plus size={15} />
                Start session
              </button>
              <button
                className="button secondary"
                disabled={selected.status !== "ONLINE"}
                onClick={() => {
                  setDetail(null);
                  command(selected, "lock");
                }}
              >
                <LockKeyhole size={15} />
                Lock PC
              </button>
              {admin && (
                <button
                  className="button danger"
                  disabled={selected.status !== "ONLINE"}
                  onClick={() => {
                    setDetail(null);
                    command(selected, "shutdown");
                  }}
                >
                  <Power size={15} />
                  Shut down
                </button>
              )}
            </div>
            <p className="muted text-xs mt-3">
              Windows unlock requires credentials at the station.
            </p>
            <h3 className="mt-6">Assigned games</h3>
            <div className="detail-games">
              {data.games
                .filter((g) => g.node_ids.includes(selected.id) && g.active)
                .map((g) => (
                  <button
                    key={g.id}
                    disabled={selected.status !== "ONLINE"}
                    onClick={() => {
                      setDetail(null);
                      launch(g, selected.id);
                    }}
                  >
                    <Gamepad2 size={16} />
                    {g.name}
                    <ArrowUpRight size={15} />
                  </button>
                ))}
            </div>
            <h3 className="mt-6">Recent station alerts</h3>
            {data.alerts
              .filter((a) => a.node_id === selected.id)
              .slice(0, 3)
              .map((a) => (
                <p className="muted text-sm mt-2" key={a.id}>
                  {a.message} · {stamp(a.created_at)}
                </p>
              ))}
            {!data.alerts.some((a) => a.node_id === selected.id) && (
              <p className="muted text-sm mt-2">No alerts for this station.</p>
            )}
          </section>
        </div>
      )}
      {toast && (
        <div className="toast" role="status">
          <Activity size={18} />
          <span>{toast}</span>
          <button
            aria-label="Dismiss notification"
            onClick={() => setToast("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
