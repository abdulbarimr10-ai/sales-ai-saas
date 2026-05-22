import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiLogin, apiSignup } from '../services/api';
import { useAppContext } from '../context/AppContext';

export default function Login() {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { setIsAuthenticated, loadDashboardData } = useAppContext();

  const handleAuth = async (type) => {
    if (!user || !pass) {
      setErrorMsg("Fill all fields");
      return;
    }
    
    setIsLoading(true);
    setErrorMsg('');
    
    try {
      let result;
      if (type === "signup") {
        result = await apiSignup(user, pass);
      } else {
        result = await apiLogin(user, pass);
      }

      if (result.status === "success") {
        setIsAuthenticated(true);
        await loadDashboardData();
        navigate('/dashboard');
      } else {
        setErrorMsg(result.message || "Auth failed");
      }
    } catch (e) {
      setErrorMsg("Server error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden px-gutter bg-background text-on-background">
      {/* Ambient Background Gradients */}
      <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] -z-10"></div>
      <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-tertiary/5 rounded-full blur-[120px] -z-10"></div>
      
      <div className="w-full max-w-md space-y-xl z-10">
        {/* Brand Section */}
        <div className="text-center space-y-sm">
          <div className="inline-flex items-center justify-center p-sm bg-primary/10 rounded-xl mb-md">
            <span className="material-symbols-outlined text-primary text-3xl">hub</span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-on-background tracking-tighter">
            Sales AI
          </h1>
          <p className="text-on-surface-variant font-body-sm max-w-[280px] mx-auto opacity-80">
            High-velocity revenue operations and automated intelligence engine.
          </p>
        </div>

        {/* Login Form Container */}
        <div className="bg-surface-container border border-outline-variant p-xl rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-xl">
          <form className="space-y-lg" onSubmit={(e) => { e.preventDefault(); handleAuth('login'); }}>
            <div className="space-y-sm">
              <label className="font-label-caps text-label-caps text-on-surface-variant px-xs">Email</label>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-md top-1/2 -translate-y-1/2 text-outline group-focus-within:text-primary transition-colors text-[20px]">alternate_email</span>
                <input 
                  className="w-full bg-surface-container-lowest border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary/30 rounded-lg py-md pl-12 pr-md text-body-sm transition-all outline-none placeholder:text-outline/50" 
                  placeholder="Enter your email" 
                  type="email" 
                  value={user}
                  onChange={(e) => setUser(e.target.value)}
                />
              </div>
            </div>
            
            <div className="space-y-sm">
              <div className="flex justify-between items-center px-xs">
                <label className="font-label-caps text-label-caps text-on-surface-variant">Password</label>
                <button type="button" onClick={() => navigate('/forgot-password')} className="text-[11px] text-primary hover:underline decoration-primary/30 font-medium">Reset Access</button>
              </div>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-md top-1/2 -translate-y-1/2 text-outline group-focus-within:text-primary transition-colors text-[20px]">lock</span>
                <input 
                  className="w-full bg-surface-container-lowest border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary/30 rounded-lg py-md pl-12 pr-md text-body-sm transition-all outline-none placeholder:text-outline/50" 
                  placeholder="••••••••" 
                  type="password" 
                  value={pass}
                  onChange={(e) => setPass(e.target.value)}
                />
              </div>
            </div>

            {errorMsg && (
              <p className="text-xs text-[#ef4444] text-center mt-2">{errorMsg}</p>
            )}

            <div className="pt-sm space-y-md">
              <button 
                type="submit"
                disabled={isLoading}
                className="w-full bg-primary-container hover:bg-primary-container/90 text-on-primary-container font-headline-md text-[16px] py-md rounded-lg shadow-lg active:scale-[0.98] transition-all flex items-center justify-center gap-sm disabled:opacity-50"
              >
                {isLoading ? 'Processing...' : 'Login'}
                {!isLoading && <span className="material-symbols-outlined text-[18px]">arrow_forward</span>}
              </button>

              <div className="relative flex items-center py-sm">
                <div className="flex-grow border-t border-outline-variant"></div>
                <span className="flex-shrink mx-md text-outline font-label-caps text-[10px]">Or continue with</span>
                <div className="flex-grow border-t border-outline-variant"></div>
              </div>

              <button 
                className="w-full border border-outline-variant hover:bg-surface-container-high text-on-surface font-label-caps py-md rounded-lg active:scale-[0.98] transition-all uppercase tracking-widest text-[11px] disabled:opacity-50" 
                type="button"
                disabled={isLoading}
                onClick={() => handleAuth('signup')}
              >
                Sign Up
              </button>
            </div>
          </form>
        </div>

        {/* Reliability Status */}
        <div className="flex items-center justify-center gap-md">
          <div className="flex items-center gap-xs">
            <div className="w-2 h-2 bg-[#00e676] rounded-full animate-pulse shadow-[0_0_8px_rgba(0,230,118,0.6)]"></div>
            <span className="font-mono-data text-[11px] text-on-surface-variant">Systems Operational</span>
          </div>
          <div className="w-1 h-1 bg-outline-variant rounded-full"></div>
          <div className="flex items-center gap-xs">
            <span className="material-symbols-outlined text-[14px] text-tertiary">security</span>
            <span className="font-mono-data text-[11px] text-on-surface-variant">Encrypted Node</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="absolute bottom-margin left-0 w-full text-center px-gutter">
        <p className="font-mono-data text-[11px] tracking-[0.2em] uppercase text-outline opacity-60">
          v1.0 Reliability Engine
        </p>
      </footer>

      {/* Bottom Detail */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-48 h-1 bg-primary/20 rounded-t-full"></div>

      {/* Side Visual Decorative Element */}
      <div className="hidden lg:block fixed left-12 top-1/2 -translate-y-1/2 space-y-xl opacity-20">
        <div className="flex flex-col gap-sm">
          <div className="h-24 w-[1px] bg-gradient-to-b from-transparent via-primary to-transparent"></div>
          <span className="font-mono-data text-[10px] [writing-mode:vertical-lr] tracking-widest uppercase">RevOps Ready</span>
          <div className="h-24 w-[1px] bg-gradient-to-b from-transparent via-primary to-transparent"></div>
        </div>
      </div>
    </main>
  );
}
