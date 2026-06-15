import type { TenonNode, AlertRecord, TopologyData, HistoryPoint, AlertRule } from '../types';

const API_BASE = '/api';

export const apiClient = {
  async getTopology(): Promise<TopologyData> {
    const res = await fetch(`${API_BASE}/topology`);
    if (!res.ok) throw new Error('Failed to fetch topology');
    return res.json();
  },

  async getNodes(): Promise<TenonNode[]> {
    const res = await fetch(`${API_BASE}/nodes`);
    if (!res.ok) throw new Error('Failed to fetch nodes');
    return res.json();
  },

  async getNode(nodeId: string): Promise<TenonNode> {
    const res = await fetch(`${API_BASE}/nodes/${nodeId}`);
    if (!res.ok) throw new Error('Failed to fetch node');
    return res.json();
  },

  async getNodeHistory(nodeId: string, hours: number = 24): Promise<HistoryPoint[]> {
    const res = await fetch(`${API_BASE}/nodes/${nodeId}/history?hours=${hours}`);
    if (!res.ok) throw new Error('Failed to fetch history');
    const data = await res.json();
    return data.data;
  },

  async getAlerts(limit: number = 50, acknowledged?: boolean): Promise<AlertRecord[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (acknowledged !== undefined) {
      params.append('acknowledged', String(acknowledged));
    }
    const res = await fetch(`${API_BASE}/alerts?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch alerts');
    return res.json();
  },

  async acknowledgeAlert(alertId: string): Promise<AlertRecord> {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/ack`, {
      method: 'PUT',
    });
    if (!res.ok) throw new Error('Failed to acknowledge alert');
    return res.json();
  },

  async getRules(): Promise<AlertRule[]> {
    const res = await fetch(`${API_BASE}/rules`);
    if (!res.ok) throw new Error('Failed to fetch rules');
    return res.json();
  },

  async updateRule(nodeId: string, rule: AlertRule): Promise<AlertRule> {
    const res = await fetch(`${API_BASE}/rules/${nodeId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rule),
    });
    if (!res.ok) throw new Error('Failed to update rule');
    return res.json();
  },
};

export const getWSUrl = (): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/realtime`;
};
