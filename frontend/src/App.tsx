import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { NodeDetailPage } from './pages/NodeDetailPage';
import { AlertsPage } from './pages/AlertsPage';
import { useRealtimeWebSocket } from './hooks/useRealtimeWebSocket';
import { useMonitorStore } from './store/monitorStore';
import { apiClient } from './services/api';

function AppContent() {
  useRealtimeWebSocket();
  const setTopology = useMonitorStore((s) => s.setTopology);
  const setNodes = useMonitorStore((s) => s.setNodes);
  const setRules = useMonitorStore((s) => s.setRules);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [topology, rules] = await Promise.all([
          apiClient.getTopology(),
          apiClient.getRules(),
        ]);
        setTopology(topology);
        setNodes(topology.nodes);
        setRules(rules);
      } catch (e) {
        console.error('Failed to load initial data:', e);
      }
    };
    loadInitialData();
  }, [setTopology, setNodes, setRules]);

  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/node/:id" element={<NodeDetailPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AppLayout>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
