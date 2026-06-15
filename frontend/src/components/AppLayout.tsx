import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, AlertTriangle, Settings, Wifi, WifiOff } from 'lucide-react';
import { useMonitorStore } from '../store/monitorStore';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation();
  const isConnected = useMonitorStore((s) => s.isConnected);
  const lastUpdate = useMonitorStore((s) => s.lastUpdate);

  const navItems = [
    { path: '/dashboard', label: '监测总览', icon: LayoutDashboard },
    { path: '/alerts', label: '预警中心', icon: AlertTriangle },
  ];

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-ink-dark via-sandalwood-900 to-ink-dark">
      <header className="h-14 px-6 flex items-center justify-between border-b border-bronze-500/20 bg-sandalwood-900/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-bronze-400 to-bronze-600 flex items-center justify-center shadow-glow-bronze">
            <span className="font-song font-bold text-sandalwood-900 text-lg">榫</span>
          </div>
          <div>
            <h1 className="font-song font-bold text-bronze-100 text-lg leading-tight">
              古建骨架应力监测台
            </h1>
            <p className="text-xs text-sandalwood-400">
              榫卯关节微米级沉降与受力安全预警系统
            </p>
          </div>
        </div>

        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`
                  px-4 py-2 rounded-lg flex items-center gap-2 text-sm
                  transition-all duration-200
                  ${isActive
                    ? 'bg-bronze-500/20 text-bronze-200 border border-bronze-500/30'
                    : 'text-sandalwood-300 hover:text-bronze-200 hover:bg-sandalwood-800/50'
                  }
                `}
              >
                <Icon size={16} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs">
            {isConnected ? (
              <>
                <Wifi size={14} className="text-turquoise-400" />
                <span className="text-turquoise-400">实时连接</span>
              </>
            ) : (
              <>
                <WifiOff size={14} className="text-sandalwood-500" />
                <span className="text-sandalwood-500">连接断开</span>
              </>
            )}
          </div>
          {lastUpdate && (
            <div className="text-xs text-sandalwood-400">
              更新: {new Date(lastUpdate).toLocaleTimeString('zh-CN')}
            </div>
          )}
          <button className="p-2 rounded-lg text-sandalwood-400 hover:text-bronze-200 hover:bg-sandalwood-800/50 transition-colors">
            <Settings size={18} />
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-hidden">
        {children}
      </main>

      <footer className="h-8 px-6 flex items-center justify-between border-t border-bronze-500/10 text-xs text-sandalwood-500 bg-sandalwood-900/50">
        <span>国家级文物保护单位 · 木结构安全监测系统 v1.0</span>
        <span>基于卡氏第二定理 · 微米级精度</span>
      </footer>
    </div>
  );
}
