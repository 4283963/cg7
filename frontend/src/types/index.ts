export type StressLevel = 'normal' | 'warning' | 'danger';
export type AlertLevel = 'warning' | 'danger';
export type AlertType = 'displacement' | 'shear' | 'moment';

export interface TenonNode {
  id: string;
  name: string;
  x: number;
  y: number;
  beam_length: number;
  section_width: number;
  section_height: number;
  elastic_modulus: number;
  shear_modulus: number;
  displacement: number;
  shear_force: number;
  bending_moment: number;
  stress_level: StressLevel;
  last_update: string;
}

export interface Connection {
  id: number;
  from_node: string;
  to_node: string;
  connection_type: string;
}

export interface TopologyData {
  nodes: TenonNode[];
  connections: Connection[];
}

export interface HistoryPoint {
  timestamp: string;
  displacement_um: number;
  shear_force_n: number;
  bending_moment_nm: number;
}

export interface AlertRule {
  node_id: string;
  displacement_threshold: number;
  shear_threshold: number;
  moment_threshold: number;
  updated_at?: string;
}

export interface AlertRecord {
  id: string;
  node_id: string;
  node_name: string;
  level: AlertLevel;
  alert_type: AlertType;
  value: number;
  threshold: number;
  timestamp: string;
  acknowledged: boolean;
}

export interface RealtimeUpdate {
  type: string;
  nodes: TenonNode[];
  alerts: AlertRecord[];
}
