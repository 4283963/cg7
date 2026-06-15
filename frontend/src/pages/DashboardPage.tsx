import { useMemo } from 'react';
import { TopologyMap } from '../components/TopologyMap';
import { NodeCard } from '../components/NodeCard';
import { TrendChart } from '../components/TrendChart';
import { AlertBanner } from '../components/AlertBanner';
import { useMonitorStore } from '../store/monitorStore';
import { Activity, TrendingDown, AlertTriangle, Clock } from 'lucide-react';

export function DashboardPage() {
  const nodes = useMonitorStore((s) => s.nodes);
  const alerts = useMonitorStore((s) => s.alerts);

  const sortedNodes = useMemo(() => {
    const levelOrder = { danger: 0, warning: 1, normal: 2 };
    return [...nodes].sort((a, b) => {
      const levelDiff = levelOrder[a.stress_level] - levelOrder[b.stress_level];
      if (levelDiff !== 0) return levelDiff;
      return b.displacement - a.displacement;
    });
  }, [nodes]);

  const stats = useMemo(() => {
    const normal = nodes.filter((n) => n.stress_level === 'normal').length;
    const warning = nodes.filter((n) => n.stress_level === 'warning').length;
    const danger = nodes.filter((n) => n.stress_level === 'danger').length;
    const avgDisplacement = nodes.length > 0
      ? nodes.reduce((sum, n) => sum + n.displacement, 0) / nodes.length
      : 0;
    return { normal, warning, danger, avgDisplacement, total: nodes.length };
  }, [nodes]);

  const unacknowledgedAlerts = alerts.filter((a) => !a.acknowledged).length;

  return (
    <div className="h-full flex flex-col">
      <AlertBanner />

      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          <div className="card-dark rounded-2xl p-5 flex-1 min-h-0 overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="font-song text-xl text-bronze-100 font-semibold">
                  古建骨架拓扑图
                </h2>
                <p className="text-xs text-sandalwood-400 mt-0.5">
                  点击节点查看详细数据
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-turquoise-500"></span>
                  <span className="text-sandalwood-300">正常 ({stats.normal})</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                  <span className="text-sandalwood-300">预警 ({stats.warning})</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-vermilion-500"></span>
                  <span className="text-sandalwood-300">危险 ({stats.danger})</span>
                </div>
              </div>
            </div>
            <div className="h-[calc(100%-60px)]">
              <TopologyMap width={600} height={420} />
            </div>
          </div>

          <div className="card-dark rounded-2xl p-5 h-[300px]">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-song text-lg text-bronze-100 font-semibold flex items-center gap-2">
                <TrendingDown size={18} className="text-bronze-400" />
                沉降趋势曲线
              </h3>
              <span className="text-xs text-sandalwood-400">近 24 小时 · 前 5 个节点</span>
            </div>
            <TrendChart nodes={sortedNodes.slice(0, 5)} type="displacement" height={220} />
          </div>
        </div>

        <div className="w-[380px] flex flex-col gap-4 flex-shrink-0">
          <div className="grid grid-cols-2 gap-3">
            <div className="card-dark rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-turquoise-500/20 flex items-center justify-center">
                  <Activity size={16} className="text-turquoise-400" />
                </div>
                <span className="text-xs text-sandalwood-400">监测节点</span>
              </div>
              <div className="font-mono text-2xl font-bold text-bronze-100">
                {stats.total}
                <span className="text-sm font-normal text-sandalwood-400 ml-1">个</span>
              </div>
            </div>

            <div className="card-dark rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                  <AlertTriangle size={16} className="text-amber-400" />
                </div>
                <span className="text-xs text-sandalwood-400">未处理预警</span>
              </div>
              <div className={`font-mono text-2xl font-bold ${unacknowledgedAlerts > 0 ? 'text-amber-400' : 'text-bronze-100'}`}>
                {unacknowledgedAlerts}
                <span className="text-sm font-normal text-sandalwood-400 ml-1">条</span>
              </div>
            </div>

            <div className="card-dark rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-bronze-500/20 flex items-center justify-center">
                  <TrendingDown size={16} className="text-bronze-400" />
                </div>
                <span className="text-xs text-sandalwood-400">平均位移</span>
              </div>
              <div className="font-mono text-2xl font-bold text-bronze-100">
                {stats.avgDisplacement.toFixed(0)}
                <span className="text-sm font-normal text-sandalwood-400 ml-1">μm</span>
              </div>
            </div>

            <div className="card-dark rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-turquoise-500/20 flex items-center justify-center">
                  <Clock size={16} className="text-turquoise-400" />
                </div>
                <span className="text-xs text-sandalwood-400">采样频率</span>
              </div>
              <div className="font-mono text-2xl font-bold text-bronze-100">
                2
                <span className="text-sm font-normal text-sandalwood-400 ml-1">秒/次</span>
              </div>
            </div>
          </div>

          <div className="card-dark rounded-2xl p-4 flex-1 min-h-0 flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-song text-lg text-bronze-100 font-semibold">
                核心节点状态
              </h3>
              <span className="text-xs text-sandalwood-400">按风险排序</span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
              {sortedNodes.map((node) => (
                <NodeCard key={node.id} node={node} />
              ))}
              {sortedNodes.length === 0 && (
                <div className="text-center text-sandalwood-400 py-8 text-sm">
                  加载中...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
