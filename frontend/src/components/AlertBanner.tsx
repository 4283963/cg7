import { useState, useEffect } from 'react';
import { alertTypeLabels, formatTime } from '../utils/format';
import { AlertTriangle, X, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useMonitorStore } from '../store/monitorStore';

export function AlertBanner() {
  const alerts = useMonitorStore((s) => s.alerts);
  const [dismissed, setDismissed] = useState(false);
  const navigate = useNavigate();

  const unacknowledgedAlerts = alerts.filter((a) => !a.acknowledged);
  const hasDanger = unacknowledgedAlerts.some((a) => a.level === 'danger');
  const latestAlert = unacknowledgedAlerts[0];

  useEffect(() => {
    if (unacknowledgedAlerts.length > 0) {
      setDismissed(false);
    }
  }, [unacknowledgedAlerts.length]);

  if (dismissed || unacknowledgedAlerts.length === 0) {
    return null;
  }

  const bgClass = hasDanger
    ? 'bg-gradient-to-r from-vermilion-600/90 to-vermilion-500/80'
    : 'bg-gradient-to-r from-amber-600/90 to-amber-500/80';

  const handleClick = () => {
    navigate('/alerts');
  };

  return (
    <div
      className={`
        ${bgClass}
        text-white px-4 py-2.5
        flex items-center justify-between
        animate-slide-down
        shadow-lg
        cursor-pointer
        hover:brightness-110 transition-all duration-200
      `}
      onClick={handleClick}
    >
      <div className="flex items-center gap-3">
        <AlertTriangle
          size={20}
          className={`animate-pulse ${hasDanger ? 'text-white' : 'text-amber-100'}`}
        />
        <div>
          <span className="font-song font-semibold text-sm">
            {hasDanger ? '危险预警' : '预警提醒'}
          </span>
          {latestAlert && (
            <span className="ml-2 text-sm opacity-90">
              {latestAlert.node_name} · {alertTypeLabels[latestAlert.alert_type]}
              {' '}· 当前 {latestAlert.value.toFixed(1)} (阈值 {latestAlert.threshold})
            </span>
          )}
          <span className="ml-3 text-xs opacity-75">
            共 {unacknowledgedAlerts.length} 条未处理预警
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs opacity-80">
          {latestAlert && formatTime(latestAlert.timestamp)}
        </span>
        <ChevronRight size={16} className="opacity-80" />
        <button
          onClick={(e) => {
            e.stopPropagation();
            setDismissed(true);
          }}
          className="ml-1 p-1 rounded hover:bg-white/20 transition-colors"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
}
