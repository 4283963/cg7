import { useState, useEffect } from 'react';
import { AlertTriangle, Check, Clock, Filter, ChevronDown, Settings } from 'lucide-react';
import { useMonitorStore } from '../store/monitorStore';
import { alertTypeLabels, formatDateTime, formatDisplacement, formatForce, formatMoment } from '../utils/format';
import type { AlertRecord, AlertRule, TenonNode } from '../types';

export function AlertsPage() {
  const nodes = useMonitorStore((s) => s.nodes);
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [filterLevel, setFilterLevel] = useState<string>('all');
  const [filterAck, setFilterAck] = useState<string>('all');
  const [showRulePanel, setShowRulePanel] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [alertsRes, rulesRes] = await Promise.all([
          fetch('/api/alerts?limit=100'),
          fetch('/api/rules'),
        ]);
        const alertsData = await alertsRes.json();
        const rulesData = await rulesRes.json();
        setAlerts(alertsData);
        setRules(rulesData);
      } catch (e) {
        console.error('Failed to load alerts:', e);
      }
    };
    loadData();
  }, []);

  const displayAlerts = alerts.filter((a) => {
    if (filterLevel !== 'all' && a.level !== filterLevel) return false;
    if (filterAck === 'ack' && !a.acknowledged) return false;
    if (filterAck === 'unack' && a.acknowledged) return false;
    return true;
  });

  const handleAcknowledge = async (alertId: string) => {
    try {
      await fetch(`/api/alerts/${alertId}/ack`, {
        method: 'PUT',
      });
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a))
      );
    } catch (e) {
      console.error('Failed to acknowledge alert:', e);
    }
  };

  const handleSaveRule = async (rule: AlertRule) => {
    try {
      const res = await fetch(`/api/rules/${rule.node_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rule),
      });
      const updated = await res.json();
      setRules((prev) =>
        prev.map((r) => (r.node_id === rule.node_id ? updated : r))
      );
      setEditingRule(null);
    } catch (e) {
      console.error('Failed to update rule:', e);
    }
  };

  const stats = {
    total: alerts.length,
    unacknowledged: alerts.filter((a) => !a.acknowledged).length,
    danger: alerts.filter((a) => a.level === 'danger').length,
    warning: alerts.filter((a) => a.level === 'warning').length,
  };

  const getNode = (nodeId: string): TenonNode | undefined => {
    return nodes.find((n) => n.id === nodeId);
  };

  const formatValue = (type: string, value: number): string => {
    switch (type) {
      case 'displacement':
        return formatDisplacement(value);
      case 'shear':
        return formatForce(value);
      case 'moment':
        return formatMoment(value);
      default:
        return value.toFixed(1);
    }
  };

  return (
    <div className="h-full flex flex-col p-4 gap-4 overflow-hidden">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-song text-2xl text-bronze-100 font-bold">
            预警中心
          </h1>
          <p className="text-sm text-sandalwood-400 mt-1">
            管理所有预警记录和预警规则配置
          </p>
        </div>
        <button
          onClick={() => setShowRulePanel(!showRulePanel)}
          className={`
            px-4 py-2 rounded-lg flex items-center gap-2 text-sm
            transition-all duration-200
            ${showRulePanel
              ? 'bg-bronze-500/30 text-bronze-200 border border-bronze-500/30'
              : 'card-dark text-sandalwood-300 hover:text-bronze-200'
            }
          `}
        >
          <Settings size={16} />
          预警规则配置
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="card-dark rounded-2xl p-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-bronze-500/20 flex items-center justify-center">
              <AlertTriangle size={24} className="text-bronze-400" />
            </div>
            <div>
              <p className="text-xs text-sandalwood-400">预警总数</p>
              <p className="font-mono text-2xl font-bold text-bronze-100">{stats.total}</p>
            </div>
          </div>
        </div>

        <div className="card-dark rounded-2xl p-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-vermilion-500/20 flex items-center justify-center">
              <AlertTriangle size={24} className="text-vermilion-400" />
            </div>
            <div>
              <p className="text-xs text-sandalwood-400">危险预警</p>
              <p className="font-mono text-2xl font-bold text-vermilion-400">{stats.danger}</p>
            </div>
          </div>
        </div>

        <div className="card-dark rounded-2xl p-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
              <AlertTriangle size={24} className="text-amber-400" />
            </div>
            <div>
              <p className="text-xs text-sandalwood-400">预警提醒</p>
              <p className="font-mono text-2xl font-bold text-amber-400">{stats.warning}</p>
            </div>
          </div>
        </div>

        <div className="card-dark rounded-2xl p-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-turquoise-500/20 flex items-center justify-center">
              <Clock size={24} className="text-turquoise-400" />
            </div>
            <div>
              <p className="text-xs text-sandalwood-400">待处理</p>
              <p className="font-mono text-2xl font-bold text-turquoise-400">{stats.unacknowledged}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex gap-4 min-h-0 overflow-hidden">
        <div className="flex-1 card-dark rounded-2xl p-5 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-song text-lg text-bronze-100 font-semibold">
              预警记录
            </h3>
            <div className="flex items-center gap-2 text-sm">
              <Filter size={14} className="text-sandalwood-400" />
              <select
                value={filterLevel}
                onChange={(e) => setFilterLevel(e.target.value)}
                className="bg-sandalwood-900/50 border border-bronze-500/20 rounded-md px-2 py-1 text-xs text-sandalwood-300"
              >
                <option value="all">全部等级</option>
                <option value="danger">危险</option>
                <option value="warning">预警</option>
              </select>
              <select
                value={filterAck}
                onChange={(e) => setFilterAck(e.target.value)}
                className="bg-sandalwood-900/50 border border-bronze-500/20 rounded-md px-2 py-1 text-xs text-sandalwood-300"
              >
                <option value="all">全部状态</option>
                <option value="unack">未确认</option>
                <option value="ack">已确认</option>
              </select>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {displayAlerts.length === 0 && (
              <div className="text-center text-sandalwood-400 py-12 text-sm">
                暂无预警记录
              </div>
            )}
            {displayAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`
                  rounded-xl p-4 transition-all duration-200
                  ${alert.level === 'danger'
                    ? 'bg-vermilion-500/10 border border-vermilion-500/30'
                    : 'bg-amber-500/10 border border-amber-500/30'
                  }
                  ${alert.acknowledged ? 'opacity-60' : ''}
                `}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div
                      className={`
                        w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                        ${alert.level === 'danger' ? 'bg-vermilion-500/30' : 'bg-amber-500/30'}
                      `}
                    >
                      <AlertTriangle
                        size={20}
                        className={alert.level === 'danger' ? 'text-vermilion-400' : 'text-amber-400'}
                      />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-song font-semibold text-bronze-100">
                          {alert.node_name}
                        </span>
                        <span
                          className={`
                            px-2 py-0.5 rounded text-xs font-medium
                            ${alert.level === 'danger'
                              ? 'bg-vermilion-500/30 text-vermilion-300'
                              : 'bg-amber-500/30 text-amber-300'
                            }
                          `}
                        >
                          {alert.level === 'danger' ? '危险' : '预警'}
                        </span>
                        {alert.acknowledged && (
                          <span className="px-2 py-0.5 rounded text-xs bg-sandalwood-500/30 text-sandalwood-300">
                            已确认
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-sandalwood-300 mt-1">
                        {alertTypeLabels[alert.alert_type]}
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-xs text-sandalwood-400">
                        <span>
                          当前: <span className="font-mono text-bronze-300">
                            {formatValue(alert.alert_type, alert.value)}
                          </span>
                        </span>
                        <span>
                          阈值: <span className="font-mono text-sandalwood-500">
                            {formatValue(alert.alert_type, alert.threshold)}
                          </span>
                        </span>
                        <span className="text-sandalwood-500">
                          {formatDateTime(alert.timestamp)}
                        </span>
                      </div>
                    </div>
                  </div>
                  {!alert.acknowledged && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      className="px-3 py-1.5 rounded-md bg-turquoise-500/20 text-turquoise-300 text-xs
                        hover:bg-turquoise-500/30 transition-colors flex items-center gap-1"
                    >
                      <Check size={12} />
                      确认
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {showRulePanel && (
          <div className="w-80 card-dark rounded-2xl p-5 flex flex-col animate-fade-in">
            <h3 className="font-song text-lg text-bronze-100 font-semibold mb-4">
              预警规则配置
            </h3>
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {rules.map((rule) => {
                const node = getNode(rule.node_id);
                const isEditing = editingRule?.node_id === rule.node_id;

                return (
                  <div
                    key={rule.node_id}
                    className="rounded-xl p-3 bg-sandalwood-800/30 border border-bronze-500/10"
                  >
                    <div
                      className="flex items-center justify-between cursor-pointer"
                      onClick={() => setEditingRule(isEditing ? null : rule)}
                    >
                      <span className="text-sm font-medium text-bronze-100">
                        {node?.name || rule.node_id}
                      </span>
                      <ChevronDown
                        size={16}
                        className={`text-sandalwood-400 transition-transform ${isEditing ? 'rotate-180' : ''}`}
                      />
                    </div>

                    {isEditing && (
                      <div className="mt-3 space-y-3 pt-3 border-t border-bronze-500/10">
                        <div>
                          <label className="text-xs text-sandalwood-400 block mb-1">
                            位移阈值 (μm)
                          </label>
                          <input
                            type="number"
                            value={editingRule?.displacement_threshold || 0}
                            onChange={(e) =>
                              setEditingRule({
                                ...editingRule!,
                                displacement_threshold: Number(e.target.value),
                              })
                            }
                            className="w-full bg-sandalwood-900/50 border border-bronze-500/20 rounded-md px-3 py-2
                              text-sm text-bronze-100 font-mono focus:outline-none focus:border-bronze-500/50"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-sandalwood-400 block mb-1">
                            剪力阈值 (N)
                          </label>
                          <input
                            type="number"
                            value={editingRule?.shear_threshold || 0}
                            onChange={(e) =>
                              setEditingRule({
                                ...editingRule!,
                                shear_threshold: Number(e.target.value),
                              })
                            }
                            className="w-full bg-sandalwood-900/50 border border-bronze-500/20 rounded-md px-3 py-2
                              text-sm text-bronze-100 font-mono focus:outline-none focus:border-bronze-500/50"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-sandalwood-400 block mb-1">
                            弯矩阈值 (N·m)
                          </label>
                          <input
                            type="number"
                            value={editingRule?.moment_threshold || 0}
                            onChange={(e) =>
                              setEditingRule({
                                ...editingRule!,
                                moment_threshold: Number(e.target.value),
                              })
                            }
                            className="w-full bg-sandalwood-900/50 border border-bronze-500/20 rounded-md px-3 py-2
                              text-sm text-bronze-100 font-mono focus:outline-none focus:border-bronze-500/50"
                          />
                        </div>
                        <button
                          onClick={() => handleSaveRule(editingRule!)}
                          className="w-full py-2 rounded-md bg-bronze-500/30 text-bronze-200 text-sm
                            hover:bg-bronze-500/40 transition-colors font-medium"
                        >
                          保存规则
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
