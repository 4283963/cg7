import type { StressLevel } from '../types';

export const stressColors = {
  normal: {
    primary: '#2E8B8B',
    light: '#53A4A4',
    glow: 'rgba(46, 139, 139, 0.5)',
  },
  warning: {
    primary: '#E07B39',
    light: '#F59F44',
    glow: 'rgba(224, 123, 57, 0.5)',
  },
  danger: {
    primary: '#B8342A',
    light: '#D94436',
    glow: 'rgba(184, 52, 42, 0.6)',
  },
};

export function getStressColor(level: StressLevel): string {
  return stressColors[level].primary;
}

export function getStressGlow(level: StressLevel): string {
  return stressColors[level].glow;
}

export function formatNumber(num: number, decimals: number = 1): string {
  return num.toFixed(decimals);
}

export function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatDateTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDisplacement(um: number): string {
  if (Math.abs(um) >= 1000) {
    return `${(um / 1000).toFixed(2)} mm`;
  }
  return `${um.toFixed(1)} μm`;
}

export function formatForce(n: number): string {
  if (Math.abs(n) >= 1000) {
    return `${(n / 1000).toFixed(2)} kN`;
  }
  return `${n.toFixed(1)} N`;
}

export function formatMoment(nm: number): string {
  if (Math.abs(nm) >= 1000) {
    return `${(nm / 1000).toFixed(2)} kN·m`;
  }
  return `${nm.toFixed(1)} N·m`;
}

export const alertTypeLabels: Record<string, string> = {
  displacement: '位移超限',
  shear: '剪力超限',
  moment: '弯矩超限',
};

export const stressLevelLabels: Record<string, string> = {
  normal: '正常',
  warning: '预警',
  danger: '危险',
};
