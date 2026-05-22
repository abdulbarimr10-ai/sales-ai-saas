import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAppContext } from '../../context/AppContext';

export default function Sidebar() {
  const { isSidebarOpen, setIsSidebarOpen } = useAppContext();
  const location = useLocation();

  const links = [
    { name: 'Dashboard', path: '/dashboard', icon: 'dashboard' },
    { name: 'History', path: '/history', icon: 'history' },
    { name: 'Configuration', path: '/config', icon: 'settings' }
  ];

  if (!isSidebarOpen) return null;

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={() => setIsSidebarOpen(false)}
      ></div>
      <div className="fixed inset-y-0 left-0 w-64 bg-slate-900 border-r border-slate-700/50 shadow-2xl z-50 flex flex-col transition-transform transform translate-x-0">
        <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
          <h2 className="text-xl font-bold text-slate-50 font-['Space_Grotesk']">Menu</h2>
          <button 
            onClick={() => setIsSidebarOpen(false)}
            className="text-slate-400 hover:text-white p-2 rounded-full hover:bg-slate-800 transition-colors"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-2 px-4">
            {links.map((link) => {
              const isActive = location.pathname === link.path;
              return (
                <li key={link.name}>
                  <Link
                    to={link.path}
                    onClick={() => setIsSidebarOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
                      isActive 
                        ? 'bg-primary/20 text-primary border border-primary/30' 
                        : 'text-slate-300 hover:bg-slate-800/50 hover:text-white'
                    }`}
                  >
                    <span className="material-symbols-outlined">{link.icon}</span>
                    {link.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </>
  );
}
