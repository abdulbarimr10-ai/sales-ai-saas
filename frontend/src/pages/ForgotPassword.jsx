import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchWithCreds } from '../services/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleReset = async (e) => {
    e.preventDefault();
    if (!email) return;
    setIsLoading(true);
    setStatus('');
    try {
      const res = await fetchWithCreds('/api/auth/request-password-reset', {
        method: 'POST',
        body: { email }
      });
      
      setStatus(res.message || "If that email exists, a reset link has been sent.");
    } catch (err) {
      setStatus("An error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden px-gutter bg-background text-on-background">
      <div className="w-full max-w-md space-y-xl z-10">
        <div className="text-center space-y-sm">
          <h1 className="font-headline-lg text-headline-lg text-on-background tracking-tighter">
            Reset Access
          </h1>
          <p className="text-on-surface-variant font-body-sm max-w-[280px] mx-auto opacity-80">
            Enter your email address to receive a secure password reset link.
          </p>
        </div>

        <div className="bg-surface-container border border-outline-variant p-xl rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-xl">
          <form className="space-y-lg" onSubmit={handleReset}>
            <div className="space-y-sm">
              <label className="font-label-caps text-label-caps text-on-surface-variant px-xs">Email</label>
              <div className="relative group">
                <span className="material-symbols-outlined absolute left-md top-1/2 -translate-y-1/2 text-outline group-focus-within:text-primary transition-colors text-[20px]">alternate_email</span>
                <input 
                  className="w-full bg-surface-container-lowest border border-outline-variant focus:border-primary focus:ring-1 focus:ring-primary/30 rounded-lg py-md pl-12 pr-md text-body-sm transition-all outline-none placeholder:text-outline/50" 
                  placeholder="Enter your email" 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            {status && (
              <p className="text-xs text-blue-400 text-center mt-2">{status}</p>
            )}

            <div className="pt-sm space-y-md">
              <button 
                type="submit"
                disabled={isLoading}
                className="w-full bg-primary-container hover:bg-primary-container/90 text-on-primary-container font-headline-md text-[16px] py-md rounded-lg shadow-lg active:scale-[0.98] transition-all flex items-center justify-center gap-sm disabled:opacity-50"
              >
                {isLoading ? 'Sending...' : 'Send Reset Link'}
              </button>
              <button 
                className="w-full border border-outline-variant hover:bg-surface-container-high text-on-surface font-label-caps py-md rounded-lg active:scale-[0.98] transition-all uppercase tracking-widest text-[11px] disabled:opacity-50" 
                type="button"
                onClick={() => navigate('/login')}
              >
                Back to Login
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}
