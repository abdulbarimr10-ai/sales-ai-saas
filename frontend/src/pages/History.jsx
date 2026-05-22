import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import { apiDeleteHistory } from '../services/api';

export default function History() {
  const { history, setHistory, loadHistoryLeadsForQuery, addLog } = useAppContext();
  const [deletingQueries, setDeletingQueries] = useState(new Set());
  const navigate = useNavigate();

  const handleRunQuery = async (query) => {
    await loadHistoryLeadsForQuery(query);
    navigate('/leads');
  };

  const handleDelete = async (query, e) => {
    e.stopPropagation();
    
    if (!window.confirm(`Are you sure you want to delete "${query}" from your history?`)) {
      return;
    }

    setDeletingQueries(prev => new Set(prev).add(query));

    try {
      // apiDeleteHistory already returns the parsed JSON due to .then(res => res.json()) in api.js
      const data = await apiDeleteHistory(query);
      
      if (data.status === 'success') {
        setHistory(prev => prev.filter(q => q !== query));
        addLog(`✅ Deleted from history: "${query}"`);
      } else {
        addLog("❌ Failed to delete history item.");
      }
    } catch (err) {
      console.error(err);
      addLog("❌ Error deleting history item.");
    } finally {
      setDeletingQueries(prev => {
        const next = new Set(prev);
        next.delete(query);
        return next;
      });
    }
  };

  return (
    <div className="pt-8">
      <header className="mb-8">
        <h2 className="font-headline-lg text-headline-lg text-on-surface flex items-center gap-3">
          <span className="material-symbols-outlined text-3xl text-primary">history</span>
          History
        </h2>
        <p className="text-slate-400 mt-2 font-body-md">Review and rerun past pipeline commands.</p>
      </header>

      <div className="flex flex-col gap-4 mb-32">
        {history.length === 0 ? (
          <div className="bg-surface-container border border-slate-700/50 p-12 rounded-xl text-center flex flex-col items-center justify-center gap-4">
            <span className="material-symbols-outlined text-4xl text-slate-500">history_toggle_off</span>
            <p className="text-on-surface-variant font-body-lg">No history found.</p>
            <p className="text-slate-500 text-sm">Run a pipeline command from the dashboard to see it here.</p>
          </div>
        ) : (
          history.map((query, index) => (
            <div 
              key={index} 
              onClick={() => handleRunQuery(query)}
              className="group cursor-pointer bg-surface-container border border-slate-700 hover:border-primary/50 p-5 rounded-xl shadow-lg transition-all hover:bg-surface-container-high flex justify-between items-center"
            >
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-primary/10 text-primary flex items-center justify-center group-hover:bg-primary group-hover:text-on-primary transition-colors">
                  <span className="material-symbols-outlined text-[20px]">search</span>
                </div>
                <div>
                  <h3 className="font-headline-md text-on-surface capitalize">{query}</h3>
                  <p className="text-xs text-slate-400 font-mono-data mt-1">Status: Archived • Click to Restore</p>
                </div>
              </div>
              
              <button 
                onClick={(e) => handleDelete(query, e)}
                disabled={deletingQueries.has(query)}
                className={`opacity-0 group-hover:opacity-100 transition-opacity p-2 rounded-full active:scale-95 ${
                  deletingQueries.has(query) 
                    ? 'text-slate-500 cursor-not-allowed opacity-100' 
                    : 'text-slate-400 hover:text-red-400 hover:bg-red-400/10'
                }`}
                title="Delete from History"
              >
                {deletingQueries.has(query) ? (
                  <span className="material-symbols-outlined text-[20px] animate-spin">refresh</span>
                ) : (
                  <span className="material-symbols-outlined text-[20px]">delete</span>
                )}
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
