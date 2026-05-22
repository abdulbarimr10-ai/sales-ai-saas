import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchWithCreds } from '../services/api';
import { useAppContext } from '../context/AppContext';

export default function Sessions() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');
  const navigate = useNavigate();
  const { setIsAuthenticated } = useAppContext();

  const loadSessions = async () => {
    try {
      const res = await fetchWithCreds('/api/auth/sessions', { method: 'GET' });
      if (res.status === 'success') {
        setSessions(res.data);
      }
    } catch (e) {
      setStatus("Failed to load sessions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const revokeSession = async (sessionId) => {
    try {
      const res = await fetchWithCreds(`/api/auth/sessions/${sessionId}`, { method: 'DELETE' });
      if (res.status === 'success') {
        setStatus("Session revoked");
        loadSessions();
      }
    } catch (e) {
      setStatus("Failed to revoke session");
    }
  };

  const revokeAll = async () => {
    try {
      const res = await fetchWithCreds(`/api/auth/logout-all`, { method: 'POST' });
      if (res.status === 'success') {
        // Logged out — update auth state and navigate via React Router
        setIsAuthenticated(false);
        navigate('/login');
      }
    } catch (e) {
      setStatus("Failed to revoke all sessions");
    }
  };

  if (loading) return <div className="p-8 text-on-surface">Loading sessions...</div>;

  return (
    <div className="pt-8 pb-20 max-w-4xl mx-auto">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h2 className="font-headline-lg text-headline-lg text-on-surface flex items-center gap-3">
            <span className="material-symbols-outlined text-3xl">devices</span> Active Sessions
          </h2>
          <p className="text-slate-400 mt-2 font-body-md">Manage the devices that are currently logged into your account.</p>
        </div>
        <button onClick={revokeAll} className="bg-red-500/20 text-red-400 hover:bg-red-500 hover:text-white px-4 py-2 rounded-lg font-semibold transition-colors border border-red-500/30">
          Sign out of all devices
        </button>
      </header>

      {status && <div className="mb-4 text-blue-400 font-semibold">{status}</div>}

      <div className="space-y-4">
        {sessions.map(session => (
          <div key={session.session_id} className="bg-surface-container-low border border-slate-700 p-6 rounded-xl flex justify-between items-center shadow-lg">
            <div className="flex gap-4 items-center">
              <span className="material-symbols-outlined text-4xl text-blue-500">
                {session.device_name.toLowerCase().includes('mac') || session.device_name.toLowerCase().includes('windows') ? 'computer' : 'smartphone'}
              </span>
              <div>
                <h3 className="font-headline-md text-on-surface">{session.device_name}</h3>
                <p className="text-sm text-slate-400">IP: {session.ip_address}</p>
                <p className="text-xs text-slate-500 mt-1">Last active: {new Date(session.last_active_at).toLocaleString()}</p>
              </div>
            </div>
            <button 
              onClick={() => revokeSession(session.session_id)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-600 transition-colors"
            >
              Revoke
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
