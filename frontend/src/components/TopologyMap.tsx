import { useState, useMemo } from 'react';
import type { TenonNode, StressLevel } from '../types';
import { stressColors, formatDisplacement, formatForce, formatMoment } from '../utils/format';
import { useMonitorStore } from '../store/monitorStore';
import { useNavigate } from 'react-router-dom';

interface TopologyMapProps {
  width?: number;
  height?: number;
}

interface NodeTooltip {
  node: TenonNode;
  x: number;
  y: number;
}

const connectionColors: Record<string, string> = {
  'column-base': '#8B5E34',
  'column': '#A67D4D',
  'beam': '#BF9F73',
  'eave': '#D4C19E',
  'roof-ridge': '#C9A961',
};

export function TopologyMap({ width = 600, height = 480 }: TopologyMapProps) {
  const topology = useMonitorStore((s) => s.topology);
  const nodes = useMonitorStore((s) => s.nodes);
  const selectedNodeId = useMonitorStore((s) => s.selectedNodeId);
  const setSelectedNode = useMonitorStore((s) => s.setSelectedNode);
  const navigate = useNavigate();
  const [tooltip, setTooltip] = useState<NodeTooltip | null>(null);

  const nodeMap = useMemo(() => {
    const map = new Map<string, TenonNode>();
    nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [nodes]);

  const getNodeColor = (level: StressLevel) => stressColors[level].primary;

  const handleNodeClick = (node: TenonNode) => {
    setSelectedNode(node.id);
    navigate(`/node/${node.id}`);
  };

  const handleNodeEnter = (node: TenonNode, e: React.MouseEvent) => {
    setTooltip({
      node,
      x: e.clientX,
      y: e.clientY,
    });
  };

  const handleNodeLeave = () => {
    setTooltip(null);
  };

  if (!topology || nodes.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center text-sandalwood-300">
        <div className="text-center">
          <div className="animate-pulse">加载拓扑数据中...</div>
        </div>
      </div>
    );
  }

  const viewBox = `0 0 ${width} ${height}`;

  return (
    <div className="relative w-full h-full overflow-hidden grain-overlay">
      <svg
        viewBox={viewBox}
        className="w-full h-full"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <radialGradient id="bgGlow" cx="50%" cy="40%" r="60%">
            <stop offset="0%" stopColor="#2D1F17" stopOpacity="1" />
            <stop offset="100%" stopColor="#1A1410" stopOpacity="0.5" />
          </radialGradient>
          
          <filter id="glow-normal">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          
          <filter id="glow-warning">
            <feGaussianBlur stdDeviation="5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          
          <filter id="glow-danger">
            <feGaussianBlur stdDeviation="7" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <pattern id="woodGrain" patternUnits="userSpaceOnUse" width="40" height="40">
            <rect width="40" height="40" fill="#4A2C20" />
            <path d="M0 10 Q 10 5, 20 10 T 40 10" stroke="#5A3828" strokeWidth="0.5" fill="none" opacity="0.3" />
            <path d="M0 25 Q 10 20, 20 25 T 40 25" stroke="#3A2218" strokeWidth="0.5" fill="none" opacity="0.3" />
          </pattern>

          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#C9A961" opacity="0.6" />
          </marker>
        </defs>

        <rect width={width} height={height} fill="url(#bgGlow)" />

        <g className="connections">
          {topology.connections.map((conn, index) => {
            const fromNode = nodeMap.get(conn.from_node);
            const toNode = nodeMap.get(conn.to_node);
            if (!fromNode || !toNode) return null;

            const strokeColor = connectionColors[conn.connection_type] || '#8B5E34';
            const maxStress: StressLevel = fromNode.stress_level === 'danger' || toNode.stress_level === 'danger'
              ? 'danger'
              : fromNode.stress_level === 'warning' || toNode.stress_level === 'warning'
                ? 'warning'
                : 'normal';
            const strokeWidth = maxStress === 'danger' ? 3 : maxStress === 'warning' ? 2.5 : 2;

            const midX = (fromNode.x + toNode.x) / 2;
            const midY = (fromNode.y + toNode.y) / 2;

            return (
              <g key={`conn-${index}`}>
                <line
                  x1={fromNode.x}
                  y1={fromNode.y}
                  x2={toNode.x}
                  y2={toNode.y}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth + 2}
                  opacity="0.2"
                  className="beam-line"
                  style={{ animationDelay: `${index * 0.1}s` }}
                />
                <line
                  x1={fromNode.x}
                  y1={fromNode.y}
                  x2={toNode.x}
                  y2={toNode.y}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  strokeLinecap="round"
                  className="beam-line"
                  style={{ animationDelay: `${index * 0.1}s` }}
                />
                {conn.connection_type === 'column' && (
                  <>
                    <line
                      x1={midX - 8}
                      y1={midY - 4}
                      x2={midX - 8}
                      y2={midY + 4}
                      stroke="#C9A961"
                      strokeWidth="1"
                      opacity="0.6"
                    />
                    <line
                      x1={midX + 8}
                      y1={midY - 4}
                      x2={midX + 8}
                      y2={midY + 4}
                      stroke="#C9A961"
                      strokeWidth="1"
                      opacity="0.6"
                    />
                  </>
                )}
              </g>
            );
          })}
        </g>

        <g className="nodes">
          {nodes.map((node, index) => {
            const isSelected = node.id === selectedNodeId;
            const color = getNodeColor(node.stress_level);
            const glowFilter = node.stress_level === 'danger'
              ? 'url(#glow-danger)'
              : node.stress_level === 'warning'
                ? 'url(#glow-warning)'
                : 'url(#glow-normal)';
            const nodeRadius = node.stress_level === 'danger' ? 12 : node.stress_level === 'warning' ? 10 : 8;

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                className="cursor-pointer transition-transform duration-200 hover:scale-110"
                style={{
                  transformOrigin: `${node.x}px ${node.y}px`,
                  animationDelay: `${index * 0.1 + 0.5}s`,
                }}
                onClick={() => handleNodeClick(node)}
                onMouseEnter={(e) => handleNodeEnter(node, e)}
                onMouseLeave={handleNodeLeave}
              >
                <circle
                  r={nodeRadius + 6}
                  fill="none"
                  stroke={color}
                  strokeWidth="1"
                  opacity="0.3"
                  className={node.stress_level !== 'normal' ? 'animate-breathe' : ''}
                />
                
                <circle
                  r={nodeRadius + 2}
                  fill={color}
                  opacity="0.2"
                  filter={glowFilter}
                />

                <circle
                  r={nodeRadius}
                  fill={color}
                  stroke={isSelected ? '#C9A961' : 'rgba(245, 240, 230, 0.5)'}
                  strokeWidth={isSelected ? 3 : 1.5}
                  filter={glowFilter}
                />

                <circle
                  r={nodeRadius * 0.4}
                  fill="rgba(255, 255, 255, 0.4)"
                  cy={-nodeRadius * 0.2}
                />

                {node.stress_level === 'danger' && (
                  <circle
                    r={nodeRadius + 15}
                    fill="none"
                    stroke={color}
                    strokeWidth="1"
                    opacity="0.4"
                    className="animate-ping"
                  />
                )}

                <text
                  y={nodeRadius + 18}
                  textAnchor="middle"
                  fill="#E8DCC8"
                  fontSize="11"
                  fontFamily="'Noto Sans SC', sans-serif"
                  fontWeight={isSelected ? '700' : '400'}
                >
                  {node.name}
                </text>
              </g>
            );
          })}
        </g>

        <g>
          <line x1="60" y1={height - 30} x2={width - 60} y2={height - 30} stroke="#4A2C20" strokeWidth="20" strokeLinecap="round" />
          <line x1="60" y1={height - 30} x2={width - 60} y2={height - 30} stroke="#6E4823" strokeWidth="12" strokeLinecap="round" />
          <text x={width / 2} y={height - 8} textAnchor="middle" fill="#8B5E34" fontSize="10" opacity="0.6">
            石  基  座
          </text>
        </g>
      </svg>

      {tooltip && (
        <div
          className="fixed z-50 pointer-events-none"
          style={{
            left: tooltip.x + 15,
            top: tooltip.y - 10,
          }}
        >
          <div className="card-rice rounded-lg p-3 min-w-[200px] shadow-xl">
            <div className="font-song font-bold text-lg border-b border-bronze-300/50 pb-1 mb-2">
              {tooltip.node.name}
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-sandalwood-600">位移量</span>
                <span className="font-mono font-medium">
                  {formatDisplacement(tooltip.node.displacement)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sandalwood-600">剪切力</span>
                <span className="font-mono font-medium">
                  {formatForce(tooltip.node.shear_force)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sandalwood-600">弯矩</span>
                <span className="font-mono font-medium">
                  {formatMoment(tooltip.node.bending_moment)}
                </span>
              </div>
              <div className="flex justify-between pt-1 border-t border-bronze-300/30">
                <span className="text-sandalwood-600">状态</span>
                <span
                  className={`font-bold ${
                    tooltip.node.stress_level === 'danger'
                      ? 'text-vermilion-600'
                      : tooltip.node.stress_level === 'warning'
                        ? 'text-amber-600'
                        : 'text-turquoise-700'
                  }`}
                >
                  {tooltip.node.stress_level === 'danger'
                    ? '危险'
                    : tooltip.node.stress_level === 'warning'
                      ? '预警'
                      : '正常'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
