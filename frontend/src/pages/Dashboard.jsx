import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiProcess } from '../services/api';
import { useAppContext } from '../context/AppContext';

export default function Dashboard() {
  const [industry, setIndustry] = useState('');
  const [location, setLocation] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const navigate = useNavigate();
  const { setLeads, logs, addLog, setHistory } = useAppContext();
  const logsEndRef = useRef(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleRunPipeline = async () => {
    if (!industry) {
      addLog("⚠️ Select an industry.");
      return;
    }
    if (!location || location.trim() === "") {
      addLog("⚠️ Enter location.");
      return;
    }

    let userInput = "";
    if (industry === "diagnostic center") {
      userInput = `diagnostic center near ${location}`;
    } else {
      userInput = `${industry} in ${location}`;
    }

    setIsProcessing(true);
    addLog(`📡 Searching leads for: ${userInput}...`);
    
    // Update history in UI optimistically
    setHistory(prev => [userInput, ...prev]);

    try {
      const result = await apiProcess(userInput);

      if (typeof result.data === "string") {
        addLog(`❌ Server error or message: ${result.data}`);
      } else {
        setLeads(result.data);
        addLog(`✅ Leads loaded (${result.data.length} found).`);
        navigate('/leads');
      }
    } catch (e) {
      addLog("❌ Server error");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
      {/* Welcome Hero Section (Asymmetric Layout) */}
      <div className="col-span-12 md:col-span-8 flex flex-col justify-center py-8">
        <span className="font-label-caps text-tertiary mb-2">INTELLIGENCE ENGINE ACTIVE</span>
        <h2 className="font-headline-lg text-headline-lg text-primary mb-4">Command the Sales Pipeline</h2>
        <p className="font-body-lg text-on-surface-variant max-w-xl">
          Deploy high-velocity AI agents to identify, qualify, and engage prospects across specialized industries with surgical precision.
        </p>
      </div>
      
      <div className="col-span-12 md:col-span-4 flex items-center justify-center">
        <div className="relative w-full aspect-square max-w-[280px]">
          <div className="absolute inset-0 bg-primary/10 rounded-full blur-3xl"></div>
          <img 
            alt="AI Visual" 
            className="relative z-10 w-full h-full object-contain rounded-2xl" 
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuDfAa9XuJtpoZo9up4wyHq8YxJ7ggpsiZwrYR1_g7KeAO0_v0tV37Nw1_XnpUtLgFR2ZKyEB0m7FzsHRnm74x8m3pJu3Y8ChfmvnurEpzc0nx_8EE2xqyfMV2-jzn7L5mWSLnVU89dULx6kSWQ1lWiWMbopF7VhhGf7twGrXlr2kwRlv5VVXRiiIEIB64t30faL9V0U9HF9_qTyCWktco1Aw7BJq4So0Sjyf7eKgH45sjlcwfYKhIZHaNcupxHjOEjxJeoNQsHzGq_i"
          />
        </div>
      </div>

      {/* Pipeline Configuration Grid */}
      <div className="col-span-12 grid grid-cols-1 md:grid-cols-3 gap-gutter">
        {/* Industry Selection Card */}
        <div className="glass-panel p-6 rounded-xl flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-tertiary">factory</span>
            <h3 className="font-headline-md text-body-lg font-bold">Target Industry</h3>
          </div>
          <div className="relative">
            <select 
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="w-full bg-surface-container-lowest border border-outline-variant text-on-surface rounded-lg px-4 py-3 focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none font-body-md"
            >
              <option value="">Select Target Segment</option>
              <option value="dental clinic">Dental</option>
              <option value="skin clinic">Skin</option>
              <option value="physiotherapy clinic">Physio</option>
              <option value="diagnostic center">Diagnostic</option>
            </select>
            <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-outline">expand_more</span>
          </div>
        </div>

        {/* Location Input Card */}
        <div className="glass-panel p-6 rounded-xl flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-tertiary">location_on</span>
            <h3 className="font-headline-md text-body-lg font-bold">Region focus</h3>
          </div>
          <div className="relative">
            <input 
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full bg-surface-container-lowest border border-outline-variant text-on-surface rounded-lg px-4 py-3 focus:border-primary focus:ring-1 focus:ring-primary outline-none font-body-md" 
              placeholder="Enter city or region..." 
              type="text"
            />
          </div>
        </div>

        {/* Action Card */}
        <div className="bg-primary-container p-6 rounded-xl flex flex-col justify-between shadow-[0_4px_20px_rgba(77,142,255,0.3)]">
          <div className="flex flex-col gap-1">
            <h3 className="font-headline-md text-on-primary-container font-bold">Initialize Run</h3>
            <p className="text-sm text-on-primary-container/80">Confirm parameters and execute.</p>
          </div>
          <button 
            disabled={isProcessing}
            onClick={handleRunPipeline}
            className="w-full bg-on-primary-container text-primary-fixed py-3 rounded-lg font-bold flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-95 transition-all mt-4 disabled:opacity-50"
          >
            {isProcessing ? (
              <span className="material-symbols-outlined animate-spin">refresh</span>
            ) : (
              <span className="material-symbols-outlined">play_arrow</span>
            )}
            {isProcessing ? 'Processing...' : 'Run Pipeline'}
          </button>
        </div>
      </div>

      {/* System Logs Section */}
      <div className="col-span-12 glass-panel rounded-xl overflow-hidden mb-8 mt-8">
        <div className="px-6 py-4 border-b border-slate-700/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-tertiary">terminal</span>
            <h3 className="font-headline-md text-body-md font-bold uppercase tracking-wider">System Logs</h3>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-tertiary animate-pulse"></div>
            <span className="font-mono-data text-xs text-tertiary">STABLE</span>
          </div>
        </div>
        <div className="p-6 bg-slate-950/50 font-mono-data text-sm space-y-3 min-h-[200px] max-h-[300px] overflow-y-auto">
          {logs.map((log, i) => (
            <div key={i} className="flex gap-4">
              <span className="text-slate-500">[{log.time}]</span>
              <span className={log.msg.includes('❌') ? "text-red-400" : log.msg.includes('⚠️') ? "text-yellow-400" : "text-slate-400"}>
                {log.msg}
              </span>
            </div>
          ))}
          <div className="flex gap-4 animate-pulse">
            <span className="text-slate-500">_</span>
          </div>
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
}
