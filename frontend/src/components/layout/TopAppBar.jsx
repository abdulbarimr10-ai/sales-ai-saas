import React, { useState, useRef, useEffect } from 'react';
import { useAppContext } from '../../context/AppContext';
import { useNavigate, Link } from 'react-router-dom';
import { apiLogout } from '../../services/api';

export default function TopAppBar() {
  const { isSidebarOpen, setIsSidebarOpen, setIsAuthenticated } = useAppContext();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsProfileOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setIsProfileOpen(false);
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleLogout = async () => {
    try {
      await apiLogout();
      setIsAuthenticated(false);
      navigate('/');
    } catch (error) {
      console.error("Logout failed", error);
    }
  };

  return (
    <header className="fixed top-0 w-full z-50 flex justify-between items-center px-4 h-16 bg-slate-900/80 backdrop-blur-xl border-b border-slate-700/50 shadow-[0_10px_30px_rgba(0,0,0,0.5)] transition-all">
      <div className="flex items-center gap-4">
        <button 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className={`p-2 rounded-full transition-all active:scale-95 ${
            isSidebarOpen 
              ? 'text-white bg-primary/20 hover:bg-primary/30' 
              : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
          }`}
          aria-label="Toggle Sidebar"
          aria-expanded={isSidebarOpen}
        >
          <span className="material-symbols-outlined">menu</span>
        </button>
        <h1 className="text-lg font-bold text-slate-50 tracking-tighter font-['Space_Grotesk']">
          Sales AI
        </h1>
      </div>
      
      <div className="flex items-center gap-4 relative" ref={dropdownRef}>
        <button 
          onClick={() => setIsProfileOpen(!isProfileOpen)}
          className="h-9 w-9 rounded-full overflow-hidden border-2 border-slate-700 hover:border-primary/50 transition-all focus:outline-none focus:ring-2 focus:ring-primary/50 active:scale-95"
          aria-haspopup="true"
          aria-expanded={isProfileOpen}
        >
          <img
            alt="User Profile"
            className="w-full h-full object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuC48Qb9aqLkPAeZH1dceCUvKFHMV3Fnq1VmW4Z2M0_v_7QjsYQwrx9KJuzvFDneAfshR_BfvawO-ODTA49CdBKPunwIany6weZ_8ndSu_6Wm5WOLbNupVsiAJ9sHDrsGl_h9rhpr5hxMLh33S-c0YO2A7JLRitxwWkCJesYgfO5XJ01KiLVqdMPm9177By6cm475I1BOzjs_B829beeEOFuOt3yw8pN4qqv5Vm68KPUEufDHf3Z_FfUubELDbr8uo2vv1tk8kfADKLR"
          />
        </button>

        {/* Profile Dropdown */}
        <div 
          className={`absolute right-0 top-14 w-64 bg-slate-900 border border-slate-700/50 shadow-2xl rounded-xl overflow-hidden transition-all duration-200 transform origin-top-right ${
            isProfileOpen 
              ? 'opacity-100 scale-100 translate-y-0' 
              : 'opacity-0 scale-95 -translate-y-2 pointer-events-none'
          }`}
        >
          <div className="p-4 border-b border-slate-700/50 bg-slate-800/20">
            <p className="text-sm font-semibold text-slate-50">Sales Admin</p>
            <p className="text-xs text-slate-400 mt-1 truncate">admin@sales-ai.com</p>
          </div>
          <div className="p-2">
            <Link 
              to="/config" 
              onClick={() => setIsProfileOpen(false)}
              className="flex items-center gap-3 w-full px-3 py-2.5 text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800/50 rounded-lg transition-colors"
            >
              <span className="material-symbols-outlined text-[20px]">settings</span>
              Settings
            </Link>
          </div>
          <div className="p-2 border-t border-slate-700/50">
            <button 
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-3 py-2.5 text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-lg transition-colors"
            >
              <span className="material-symbols-outlined text-[20px]">logout</span>
              Sign out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
