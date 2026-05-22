import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { fetchWithCreds } from '../services/api';

export default function VerifyEmail() {
  const [status, setStatus] = useState('Verifying your email...');
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const verify = async () => {
      const params = new URLSearchParams(location.search);
      const token = params.get('token');
      const uid = params.get('uid');
      
      if (!token || !uid) {
        setStatus("❌ Invalid verification link. Missing parameters.");
        return;
      }

      try {
        // POST /api/auth/verify-email
        const res = await fetchWithCreds('/api/auth/verify-email', {
            method: 'POST',
            body: { token, uid }
        });
        
        if (res.status === 'success') {
            setStatus("✅ Email verified successfully! Redirecting to login...");
            setTimeout(() => navigate('/login'), 3000);
        } else {
            setStatus(`❌ Verification failed: ${res.message}`);
        }
      } catch (e) {
          setStatus("❌ A network error occurred.");
      }
    };
    verify();
  }, [location, navigate]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-background text-on-background">
        <div className="bg-surface-container border border-outline-variant p-xl rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
            <h1 className="font-headline-md text-center">{status}</h1>
        </div>
    </main>
  );
}
