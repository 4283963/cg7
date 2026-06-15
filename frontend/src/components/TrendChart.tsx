import { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { HistoryPoint, TenonNode } from '../types';

interface TrendChartProps {
  nodes: TenonNode[];
  type?: 'displacement' | 'shear' | 'moment';
  height?: number;
}

const typeConfig = {
  displacement: {
    name: '位移',
    unit: 'μm',
    color: '#2E8B8B',
  },
  shear: {
    name: '剪切力',
    unit: 'N',
    color: '#E07B39',
  },
  moment: {
    name: '弯矩',
    unit: 'N·m',
    color: '#C9A961',
  },
};

export function TrendChart({ nodes, type = 'displacement', height = 280 }: TrendChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [historyData, setHistoryData] = useState<Record<string, HistoryPoint[]>>({});

  useEffect(() => {
    const loadHistory = async () => {
      const dataMap: Record<string, HistoryPoint[]> = {};
      const displayNodes = nodes.slice(0, 5);
      
      for (const node of displayNodes) {
        try {
          const res = await fetch(`/api/nodes/${node.id}/history?hours=24`);
          const data = await res.json();
          dataMap[node.id] = data.data || [];
        } catch (e) {
          console.error(`Failed to load history for ${node.id}:`, e);
        }
      }
      setHistoryData(dataMap);
    };

    if (nodes.length > 0) {
      loadHistory();
    }
  }, [nodes]);

  useEffect(() => {
    if (!chartRef.current) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, 'dark');
    }

    const config = typeConfig[type];
    const displayNodes = nodes.slice(0, 5);

    const series = displayNodes.map((node, index) => {
      const data = historyData[node.id] || [];
      const color = node.stress_level === 'danger'
        ? '#B8342A'
        : node.stress_level === 'warning'
          ? '#E07B39'
          : `hsl(${180 + index * 30}, 50%, 50%)`;

      return {
        name: node.name,
        type: 'line' as const,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: node.stress_level === 'normal' ? 1.5 : 2.5,
          color,
        },
        areaStyle: index === 0 ? {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(46, 139, 139, 0.3)' },
            { offset: 1, color: 'rgba(46, 139, 139, 0.02)' },
          ]),
        } : undefined,
        data: data.map((p) => {
          const value = type === 'displacement'
            ? p.displacement_um
            : type === 'shear'
              ? p.shear_force_n
              : p.bending_moment_nm;
          return [p.timestamp, value];
        }),
      };
    });

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(26, 20, 16, 0.95)',
        borderColor: 'rgba(201, 169, 97, 0.3)',
        borderWidth: 1,
        textStyle: {
          color: '#E8DCC8',
          fontSize: 12,
          fontFamily: "'Noto Sans SC', sans-serif",
        },
        axisPointer: {
          lineStyle: {
            color: 'rgba(201, 169, 97, 0.5)',
            type: 'dashed',
          },
        },
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return '';
          const time = new Date(params[0].axisValue).toLocaleString('zh-CN', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
          });
          let html = `<div style="margin-bottom: 6px; color: #C9A961;">${time}</div>`;
          params.forEach((item: any) => {
            html += `<div style="display: flex; justify-content: space-between; gap: 20px; margin: 4px 0;">
              <span style="display: flex; align-items: center; gap: 6px;">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${item.color};"></span>
                ${item.seriesName}
              </span>
              <span style="font-weight: 600; font-family: monospace;">
                ${item.value[1].toFixed(1)} ${config.unit}
              </span>
            </div>`;
          });
          return html;
        },
      },
      legend: {
        data: displayNodes.map((n) => n.name),
        textStyle: {
          color: '#D4C19E',
          fontSize: 11,
        },
        top: 5,
        right: 10,
        itemWidth: 16,
        itemHeight: 2,
      },
      grid: {
        left: 50,
        right: 20,
        top: 40,
        bottom: 30,
      },
      xAxis: {
        type: 'time',
        axisLine: {
          lineStyle: {
            color: 'rgba(201, 169, 97, 0.2)',
          },
        },
        axisLabel: {
          color: '#D4C19E',
          fontSize: 10,
          formatter: (value: number) => {
            const date = new Date(value);
            return `${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
          },
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: 'rgba(201, 169, 97, 0.08)',
            type: 'dashed',
          },
        },
      },
      yAxis: {
        type: 'value',
        name: config.name + ' (' + config.unit + ')',
        nameTextStyle: {
          color: '#D4C19E',
          fontSize: 11,
        },
        axisLine: {
          show: false,
        },
        axisLabel: {
          color: '#D4C19E',
          fontSize: 10,
          formatter: (value: number) => {
            if (Math.abs(value) >= 1000) {
              return (value / 1000).toFixed(1) + 'k';
            }
            return value.toFixed(0);
          },
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(201, 169, 97, 0.08)',
            type: 'dashed',
          },
        },
      },
      series,
      animationDuration: 1000,
      animationEasing: 'cubicOut',
    };

    chartInstance.current.setOption(option, true);

    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [nodes, historyData, type]);

  return (
    <div
      ref={chartRef}
      style={{ width: '100%', height: `${height}px` }}
    />
  );
}
