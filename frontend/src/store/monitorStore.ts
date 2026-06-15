import { create } from 'zustand';
import type { TenonNode, AlertRecord, TopologyData, AlertRule } from '../types';

interface MonitorState {
  nodes: TenonNode[];
  alerts: AlertRecord[];
  topology: TopologyData | null;
  selectedNodeId: string | null;
  rules: AlertRule[];
  isConnected: boolean;
  lastUpdate: string | null;

  setNodes: (nodes: TenonNode[]) => void;
  setAlerts: (alerts: AlertRecord[]) => void;
  setTopology: (topology: TopologyData) => void;
  setSelectedNode: (nodeId: string | null) => void;
  setRules: (rules: AlertRule[]) => void;
  setConnected: (connected: boolean) => void;
  updateFromRealtime: (data: { nodes: TenonNode[]; alerts: AlertRecord[] }) => void;
}

export const useMonitorStore = create<MonitorState>((set) => ({
  nodes: [],
  alerts: [],
  topology: null,
  selectedNodeId: null,
  rules: [],
  isConnected: false,
  lastUpdate: null,

  setNodes: (nodes) => set({ nodes }),
  setAlerts: (alerts) => set({ alerts }),
  setTopology: (topology) => set({ topology }),
  setSelectedNode: (nodeId) => set({ selectedNodeId: nodeId }),
  setRules: (rules) => set({ rules }),
  setConnected: (isConnected) => set({ isConnected }),

  updateFromRealtime: (data) => set((state) => {
    const newAlerts = data.alerts.length > 0 
      ? [...data.alerts, ...state.alerts].slice(0, 100)
      : state.alerts;
    
    return {
      nodes: data.nodes,
      alerts: newAlerts,
      lastUpdate: new Date().toISOString(),
    };
  }),
}));
