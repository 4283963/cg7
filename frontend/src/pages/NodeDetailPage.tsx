import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Activity, TrendingDown, Zap, Ruler, Settings2 } from 'lucide-react';
import { useMonitorStore } from '../store/monitorStore';
import { formatDisplacement, formatForce, formatMoment, stressLevelLabels } from '../utils/format';
import { TrendChart } from '../components/TrendChart';
import type { AlertRule } from '../types';

export function NodeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const nodes = useMonitorStore((s) => s.nodes);
  const [rule, setRule] = useState<AlertRule | null>(null);
  const [hours, setHours] = useState(24);

  const node = nodes.find((n) => n.id === id);
  const displayNodes = node ? [node] : [];

  useEffect(() => {
    if (!id) return;

    const loadData = async () => {
      try {
        const [historyRes, ruleRes] = await Promise.all([
          fetch(`/api/nodes/${id}/history?hours=${hours}`),
          fetch(`/api/rules/${id}`),
        ]);
        const historyData = await historyRes.json();
        const ruleData = await ruleRes.json();
        setRule(ruleData);
        void historyData;
      } catch (e) {
        console.error('Failed to load node data:', e);
      }
    };

    loadData();
  }, [id, hours]);

  if (!node) {
    return (
      <div className="h-full flex items-center justify-center text-sandalwood-400">
        节点不存在
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-4 gap-4 overflow-auto">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/dashboard')}
          className="p-2 rounded-lg card-dark hover:bg-sandalwood-800/50 transition-colors"
        >
          <ArrowLeft size={20} className="text-bronze-300" />
        </button>
        <div>
          <h1 className="font-song text-2xl text-bronze-100 font-bold">
            {node.name}
          </h1>
          <p className="text-sm text-sandalwood-400">
            节点 ID: {node.id}
          </p>
        </div>
        <div
          className={`
            ml-4 px-3 py-1.5 rounded-full text-sm font-medium
            ${node.stress_level === 'danger' ? 'bg-vermilion-500/20 text-vermilion-300 border border-vermilion-500/30' : ''}
            ${node.stress_level === 'warning' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : ''}
            ${node.stress_level === 'normal' ? 'bg-turquoise-500/20 text-turquoise-300 border border-turquoise-500/30' : ''}
          `}
        >
          {stressLevelLabels[node.stress_level]}状态
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="card-dark rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-turquoise-500/30 to-turquoise-600/10 flex items-center justify-center">
              <Ruler size={24} className="text-turquoise-400" />
            </div>
            <div>
              <p className="text-xs text-sandalwood-400">相对位移</p>
              <p className="text-xs text-sandalwood-500">Displacement</p>
            </div>
          </div>
          <div className="font-mono text-3xl font-bold text-bronze-100">
            {formatDisplacement(node.displacement)}
          </div>
          {rule && (
            <div className="mt-2 text-xs text-sandalwood-400">
              阈值: {rule.displacement_threshold} μm
            </div>
          )}
        </div>

        <div className="card-dark rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500/30 to-amber-600/10 flex items-center justify-center">
              <Zap size={24} className="text-amber-400" />
            </div>
            <div>
              <p className="text-xs text-sandalwood-400">剪切力</p>
              <p className="text-xs text-sandalwood-500">Shear Force</p>
            </div>
          </div>
          <div className="font-mono text-3xl font-bold text-bronze-100">
            {formatForce(node.shear_force)}
          </div>
          {rule && (
            <div className="mt-2 text-xs text-sandalwood-400">
              阈值: {formatForce(rule.shear_threshold)}
            </div>
          )}
        </div>

        <div className="card-dark rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-bronze-500/30 to-bronze-600/10 flex items-center justify-center">
              <Activity size={24} className="text-bronze-400" />
            </div>
            <div>
              <p className="text-xs text-sandalwood-400">弯矩</p>
              <p className="text-xs text-sandalwood-500">Bending Moment</p>
            </div>
          </div>
          <div className="font-mono text-3xl font-bold text-bronze-100">
            {formatMoment(node.bending_moment)}
          </div>
          {rule && (
            <div className="mt-2 text-xs text-sandalwood-400">
              阈值: {formatMoment(rule.moment_threshold)}
            </div>
          )}
        </div>

        <div className="card-dark rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-sandalwood-500/30 to-sandalwood-600/10 flex items-center justify-center">
              <Settings2 size={24} className="text-sandalwood-400" />
            </div>
            <div>
              <p className="text-xs text-sandalwood-400">梁长 / 截面</p>
              <p className="text-xs text-sandalwood-500">Beam Properties</p>
            </div>
          </div>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-sandalwood-400">梁长</span>
              <span className="font-mono text-bronze-100">{node.beam_length} m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sandalwood-400">截面</span>
              <span className="font-mono text-bronze-100">
                {node.section_width}×{node.section_height} m
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sandalwood-400">弹模</span>
              <span className="font-mono text-bronze-100">
                {(node.elastic_modulus / 1e9).toFixed(1)} GPa
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 flex-1 min-h-0">
        <div className="col-span-2 card-dark rounded-2xl p-5 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingDown size={20} className="text-bronze-400" />
              <h3 className="font-song text-lg text-bronze-100 font-semibold">
                位移趋势曲线
              </h3>
            </div>
            <div className="flex gap-1 text-xs">
              {[6, 12, 24, 72].map((h) => (
                <button
                  key={h}
                  onClick={() => setHours(h)}
                  className={`
                    px-3 py-1 rounded-md transition-colors
                    ${hours === h
                      ? 'bg-bronze-500/30 text-bronze-200'
                      : 'text-sandalwood-400 hover:text-bronze-200 hover:bg-sandalwood-800/50'
                    }
                  `}
                >
                  {h}小时
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 min-h-0">
            <TrendChart nodes={displayNodes} type="displacement" height={300} />
          </div>
        </div>

        <div className="card-dark rounded-2xl p-5 flex flex-col">
          <h3 className="font-song text-lg text-bronze-100 font-semibold mb-4">
            应力计算原理
          </h3>
          <div className="flex-1 overflow-y-auto text-sm text-sandalwood-300 space-y-4 pr-2">
            <div className="card-rice/5 rounded-lg p-4">
              <h4 className="font-song text-bronze-200 font-semibold mb-2">
                卡氏第二定理
              </h4>
              <p className="text-xs text-sandalwood-300 leading-relaxed">
                线弹性结构的应变能 U 对某一广义力 F 的偏导数，
                等于该力作用点沿力方向的广义位移 δ。
              </p>
              <div className="mt-3 p-3 bg-sandalwood-900/50 rounded font-mono text-xs text-bronze-300 text-center">
                δ = ∂U/∂F
              </div>
            </div>

            <div className="card-rice/5 rounded-lg p-4">
              <h4 className="font-song text-bronze-200 font-semibold mb-2">
                逆向求解公式
              </h4>
              <p className="text-xs text-sandalwood-300 leading-relaxed mb-2">
                给定位移 δ，反推剪切力 F 和弯矩 M：
              </p>
              <div className="space-y-2">
                <div className="p-2 bg-sandalwood-900/50 rounded font-mono text-xs text-bronze-300">
                  F = δ / (L³/3EI + kL/GA)
                </div>
                <div className="p-2 bg-sandalwood-900/50 rounded font-mono text-xs text-bronze-300">
                  M = F · L
                </div>
              </div>
            </div>

            <div className="card-rice/5 rounded-lg p-4">
              <h4 className="font-song text-bronze-200 font-semibold mb-2">
                参数说明
              </h4>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-sandalwood-400">E - 弹性模量</span>
                  <span className="font-mono text-bronze-300">
                    {(node.elastic_modulus / 1e9).toFixed(1)} GPa
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sandalwood-400">G - 剪切模量</span>
                  <span className="font-mono text-bronze-300">
                    {(node.shear_modulus / 1e9).toFixed(2)} GPa
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sandalwood-400">I - 惯性矩</span>
                  <span className="font-mono text-bronze-300">
                    {((node.section_width * node.section_height ** 3) / 12).toFixed(6)} m⁴
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sandalwood-400">k - 形状系数</span>
                  <span className="font-mono text-bronze-300">1.2 (矩形)</span>
                </div>
              </div>
            </div>

            <div className="text-center text-xs text-sandalwood-500 pb-2">
              数据每 2 秒自动更新
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
