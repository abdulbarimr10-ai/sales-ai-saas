import { useEffect, useState } from 'react';
import { fetchWithCreds } from '../services/api';

export default function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadJobs = async () => {
    try {
      const res = await fetchWithCreds('/api/jobs', { method: 'GET' });
      if (res.status === 'success') {
        setJobs(res.data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
    // Poll every 5 seconds for live updates
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const cancelJob = async (jobId) => {
    try {
      const res = await fetchWithCreds(`/api/jobs/cancel/${jobId}`, { method: 'POST' });
      if (res.status === 'success') {
        loadJobs();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-400 bg-green-400/10 border-green-400/20';
      case 'running': return 'text-blue-400 bg-blue-400/10 border-blue-400/20 animate-pulse';
      case 'failed': return 'text-red-400 bg-red-400/10 border-red-400/20';
      case 'retrying': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
      default: return 'text-slate-400 bg-slate-400/10 border-slate-400/20';
    }
  };

  if (loading) return <div className="p-8 text-on-surface">Loading jobs...</div>;

  return (
    <div className="pt-8 pb-20 max-w-6xl mx-auto">
      <header className="mb-8">
        <h2 className="font-headline-lg text-headline-lg text-on-surface flex items-center gap-3">
          <span className="material-symbols-outlined text-3xl text-purple-400">queue</span> Background Jobs
        </h2>
        <p className="text-slate-400 mt-2 font-body-md">Monitor the real-time execution of your asynchronous outreach and AI tasks.</p>
      </header>

      <div className="bg-surface-container border border-slate-700 rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-800/50 border-b border-slate-700 font-label-caps text-xs text-slate-400 uppercase tracking-wider">
                <th className="p-4 font-medium">Job ID</th>
                <th className="p-4 font-medium">Type</th>
                <th className="p-4 font-medium">Status</th>
                <th className="p-4 font-medium">Started At</th>
                <th className="p-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {jobs.map(job => (
                <tr key={job.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-4 font-mono-data text-xs text-slate-300">
                    {job.id.split('-')[0]}...
                  </td>
                  <td className="p-4 text-sm font-semibold capitalize text-on-surface">
                    {job.job_type.replace(/_/g, ' ')}
                  </td>
                  <td className="p-4">
                    <span className={`px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest rounded-full border ${getStatusColor(job.status)}`}>
                      {job.status} {job.retry_count > 0 && `(Retry ${job.retry_count})`}
                    </span>
                    {job.error_message && (
                      <div className="mt-2 text-xs text-red-400 max-w-xs truncate" title={job.error_message}>
                        {job.error_message}
                      </div>
                    )}
                  </td>
                  <td className="p-4 text-xs text-slate-400">
                    {job.started_at ? new Date(job.started_at).toLocaleString() : 'Pending'}
                  </td>
                  <td className="p-4">
                    {(job.status === 'pending' || job.status === 'running' || job.status === 'retrying') && (
                      <button 
                        onClick={() => cancelJob(job.id)}
                        className="text-xs text-red-400 hover:text-red-300 bg-red-400/10 hover:bg-red-400/20 px-3 py-1.5 rounded transition-colors"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-slate-400 text-sm">
                    No background jobs found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
