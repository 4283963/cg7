import { useEffect, useRef, useCallback } from 'react';
import { useMonitorStore } from '../store/monitorStore';
import { getWSUrl } from '../services/api';
import type { RealtimeUpdate } from '../types';

export function useRealtimeWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const updateFromRealtime = useMonitorStore((s) => s.updateFromRealtime);
  const setConnected = useMonitorStore((s) => s.setConnected);

  const connect = useCallback(() => {
    try {
      const wsUrl = getWSUrl();
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data: RealtimeUpdate = JSON.parse(event.data);
          updateFromRealtime({
            nodes: data.nodes,
            alerts: data.alerts,
          });
        } catch (e) {
          console.error('Failed to parse WS message:', e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        scheduleReconnect();
      };

      ws.onerror = () => {
        setConnected(false);
      };
    } catch (e) {
      console.error('WebSocket connection error:', e);
      scheduleReconnect();
    }
  }, [updateFromRealtime, setConnected]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current);
    }
    reconnectTimerRef.current = window.setTimeout(() => {
      connect();
    }, 3000);
  }, [connect]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return wsRef;
}
