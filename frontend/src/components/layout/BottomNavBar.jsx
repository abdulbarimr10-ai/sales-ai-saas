import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { path: '/leads', label: 'Leads', icon: 'person_search' },
  { path: '/config', label: 'Config', icon: 'settings' }, // Note: Added this to cover AI config
  { path: '/history', label: 'History', icon: 'history' }
];

export default function BottomNavBar() {
  const location = useLocation();

  return (
    <nav className="fixed bottom-0 w-full z-50 flex justify-around items-center h-20 pb-safe px-6 bg-slate-900/90 backdrop-blur-xl border-t border-slate-700 rounded-t-lg shadow-[0_-4px_20px_rgba(0,0,0,0.4)]">
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        return (
          <Link
            key={item.path}
            to={item.path}
            className={`flex flex-col items-center justify-center rounded-xl px-4 py-1 transition-all active:scale-90 duration-200 ${
              isActive
                ? 'text-blue-500 bg-blue-500/10'
                : 'text-slate-500 hover:text-blue-400'
            }`}
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            <span className="font-['Space_Grotesk'] text-[10px] font-medium uppercase tracking-widest mt-1">
              {item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
