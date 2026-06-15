import type { TenonNode } from '../types';
import { formatDisplacement, formatForce, formatMoment, stressLevelLabels } from '../utils/format';
import { stressColors } from '../utils/format';
import { useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

interface NodeCardProps {
  node: TenonNode;
  onClick?: () => void;
}

export function NodeCard({ node, onClick }: NodeCardProps) {
  const navigate = useNavigate();
  const colors = stressColors[node.stress_level];

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/node/${node.id}`);
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`
        card-dark rounded-xl p-4 cursor-pointer transition-all duration-300
        hover:translate-y-[-2px] hover:shadow-lg
        min-w-[220px] flex-shrink-0
        ${node.stress_level === 'danger' ? 'border-vermilion-500/50' : ''}
        ${node.stress_level === 'warning' ? 'border-amber-500/50' : ''}
      `}
      style={{
        boxShadow: node.stress_level !== 'normal'
          ? `0 0 20px ${colors.glow}`
          : undefined,
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-song font-semibold text-bronze-100 text-base">
            {node.name}
          </h3>
          <div className="text-xs text-sandalwood-300 mt-0.5">
            ID: {node.id}
          </div>
        </div>
        <div
          className={`
            px-2 py-0.5 rounded-full text-xs font-medium
            ${node.stress_level === 'danger' ? 'bg-vermilion-500/20 text-vermilion-300' : ''}
            ${node.stress_level === 'warning' ? 'bg-amber-500/20 text-amber-300' : ''}
            ${node.stress_level === 'normal' ? 'bg-turquoise-500/20 text-turquoise-300' : ''}
          `}
        >
          {stressLevelLabels[node.stress_level]}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sandalwood-300 text-xs">位移量</span>
          <span className="font-mono text-sm font-medium text-bronze-100">
            {formatDisplacement(node.displacement)}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sandalwood-300 text-xs">剪切力</span>
          <span className="font-mono text-sm font-medium text-bronze-100">
            {formatForce(node.shear_force)}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sandalwood-300 text-xs">弯矩</span>
          <span className="font-mono text-sm font-medium text-bronze-100">
            {formatMoment(node.bending_moment)}
          </span>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-bronze-500/20 flex items-center justify-between">
        <span className="text-xs text-sandalwood-400">
          {new Date(node.last_update).toLocaleTimeString('zh-CN')}
        </span>
        <span className="text-xs text-bronze-400 flex items-center gap-1">
          详情 <ArrowRight size={12} />
        </span>
      </div>
    </div>
  );
}
