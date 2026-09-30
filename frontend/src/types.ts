export type User = {
  id: string;
  name: string;
  email: string;
  role: string;
  active: boolean;
};
export type Branch = { id: string; name: string; address: string };
export type Telemetry = {
  cpu?: number | null;
  ram?: number | null;
  cpu_temperature?: number | null;
  gpu_temperature?: number | null;
  fan_rpm?: number | null;
  keyboard?: boolean | null;
  mouse?: boolean | null;
  timestamp?: string;
};
export type Node = {
  id: string;
  name: string;
  hostname: string;
  branch_id: string;
  status: string;
  ip_address: string;
  os: string;
  agent_version: string;
  last_heartbeat: string | null;
  telemetry: Telemetry;
};
export type Session = {
  id: string;
  node_id: string;
  user_id: string;
  start_time: string;
  end_time: string | null;
  rate: string;
  cost: string;
  status: string;
};
export type Plan = {
  id: string;
  name: string;
  description: string;
  price: string;
  duration_days: number;
  benefits: string;
  active: boolean;
};
export type Membership = {
  user_id: string;
  plan_id: string;
  expiration_date: string;
  status: string;
};
export type Reservation = {
  id: string;
  user_id: string;
  node_id: string;
  branch_id: string;
  start_time: string;
  end_time: string;
  status: string;
};
export type Game = {
  id: string;
  name: string;
  description: string;
  genre: string;
  version: string;
  executable_path: string;
  active: boolean;
  node_ids: string[];
};
export type Alert = {
  id: string;
  node_id: string;
  severity: string;
  message: string;
  created_at: string;
  resolved: boolean;
};
export type Command = {
  id: string;
  node_id: string;
  type: string;
  status: string;
  result: string;
  created_at: string;
};
export type Transaction = {
  id: string;
  amount: string;
  type: string;
  created_at: string;
  reference: string;
};
export type Data = {
  branches: Branch[];
  nodes: Node[];
  users: User[];
  sessions: Session[];
  plans: Plan[];
  memberships: Membership[];
  reservations: Reservation[];
  games: Game[];
  alerts: Alert[];
  commands: Command[];
};
