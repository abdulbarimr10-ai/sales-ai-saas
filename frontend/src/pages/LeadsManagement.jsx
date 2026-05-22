import { useState, useMemo } from 'react';
import { useAppContext } from '../context/AppContext';
import { apiAnalyzeOne, apiGenerateEmail, apiDeleteLead, apiBatchOutreach } from '../services/api';

export default function LeadsManagement() {
  const { leads, setLeads, addLog } = useAppContext();
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [analyzingIds, setAnalyzingIds] = useState(new Set());
  const [emailModalData, setEmailModalData] = useState(null);
  const [viewMode, setViewMode] = useState('grid');
  const [selectedLeadDetails, setSelectedLeadDetails] = useState(null);
  const [isAutomating, setIsAutomating] = useState(false);

  // Sorting logic from ui.js
  const sortedLeads = useMemo(() => {
    const priorityWeight = { high: 3, medium: 2, low: 1 };
    return [...leads].sort((a, b) => {
      const scoreA = (priorityWeight[a.priority] || 0) + (a.estimated_loss || 0);
      const scoreB = (priorityWeight[b.priority] || 0) + (b.estimated_loss || 0);
      return scoreB - scoreA;
    });
  }, [leads]);

  const toggleSelection = (id) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedIds(newSet);
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(new Set(sortedLeads.map(l => l.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const clearSelection = () => setSelectedIds(new Set());

  const handleAnalyzeOne = async (id, index) => {
    setAnalyzingIds(prev => new Set(prev).add(id));
    try {
      const res = await apiAnalyzeOne(id);
      if (res.status === "success") {
        setLeads(prev => prev.map(lead => 
          lead.id === id 
            ? { ...lead, analysis: res.analysis, google_rating: res.google_rating, detected_problem: res.detected_problem, website: res.website, outreach_email: res.outreach_email, linkedin_url: res.linkedin_url } 
            : lead
        ));
        addLog(`✅ Lead analyzed`);
      }
    } catch (e) {
      addLog("❌ Analysis failed");
    } finally {
      setAnalyzingIds(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiDeleteLead(id);
      setLeads(prev => prev.filter(l => l.id !== id));
      setSelectedIds(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    } catch (e) {
      addLog("❌ Delete failed");
    }
  };

  const handleBatchOutreach = async () => {
    if (selectedIds.size === 0) return;
    
    // VALIDATION
    const unanalyzed = Array.from(selectedIds).some(id => !leads.find(l => l.id === id)?.analysis);
    if (unanalyzed) {
      alert("Please analyze the selected leads before generating emails.");
      addLog("⚠️ Validation failed: Leads not analyzed");
      return;
    }

    addLog(`📩 Generating emails (${selectedIds.size})...`);
    
    // We don't have the specific search query here, but we can pass a dummy one or update locally
    const idsArray = Array.from(selectedIds);
    try {
      const tasks = idsArray.map(id => apiGenerateEmail(id).then(res => {
        if (res.status === "success") {
          setLeads(prev => prev.map(l => l.id === id ? { ...l, email_draft: res.email } : l));
          addLog(`✍️ Email done`);
        }
      }));
      await Promise.all(tasks);
      addLog("✅ All emails generated");
    } catch (e) {
      addLog("❌ Batch outreach failed");
    }
  };

  const startMassBlast = async () => {
    if (selectedIds.size === 0) return;
    addLog(`🚀 Starting mass audit (${selectedIds.size})...`);
    
    const idsArray = Array.from(selectedIds);
    for (let i = 0; i < idsArray.length; i++) {
      const id = idsArray[i];
      addLog(`🔄 Analyzing ${i + 1}/${idsArray.length}...`);
      await handleAnalyzeOne(id);
    }
    addLog("✅ Mass audit complete");
  };

  const autoSendSelected = async () => {
    if (selectedIds.size === 0) return;

    // VALIDATION
    const invalid = Array.from(selectedIds).some(id => {
       const l = leads.find(l => l.id === id);
       return !l?.analysis || !l?.email_draft;
    });
    if (invalid) {
      alert("Leads must be analyzed and have emails generated before sending.");
      addLog("⚠️ Validation failed: Missing analysis or email");
      return;
    }

    const idsArray = Array.from(selectedIds);
    addLog(`📩 Sending ${idsArray.length} emails...`);
    try {
      const res = await fetch('/auto_send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ids: idsArray })
      });
      const data = await res.json();
      if (data.status === "success") {
          addLog("✅ Emails sent & Excel updated");
          setLeads(data.leads); // Update from server
      } else {
          addLog("❌ Sending failed");
      }
    } catch (e) {
        addLog("❌ Sending failed");
    }
  };

  const handleAutomateSelected = async () => {
    if (selectedIds.size === 0) return;
    setIsAutomating(true);
    addLog(`🚀 Starting Automate Pipeline for ${selectedIds.size} leads...`);
    
    for (const id of Array.from(selectedIds)) {
      let currentLead = leads.find(l => l.id === id);
      if (!currentLead) continue;
      
      // Step 1: Analyze
      if (!currentLead.analysis) {
        addLog(`🔄 [${currentLead.name}] Analyzing...`);
        setAnalyzingIds(prev => new Set(prev).add(id));
        try {
          const res = await apiAnalyzeOne(id);
          if (res.status === "success") {
            currentLead = { ...currentLead, analysis: res.analysis, google_rating: res.google_rating, detected_problem: res.detected_problem, website: res.website, outreach_email: res.outreach_email, linkedin_url: res.linkedin_url };
            setLeads(prev => prev.map(l => l.id === id ? currentLead : l));
            addLog(`✅ [${currentLead.name}] Analyzed`);
          } else {
            addLog(`❌ [${currentLead.name}] Analysis failed. Skipping.`);
            setAnalyzingIds(prev => { const n = new Set(prev); n.delete(id); return n; });
            continue;
          }
        } catch (e) {
          addLog(`❌ [${currentLead.name}] Analysis failed. Skipping.`);
          setAnalyzingIds(prev => { const n = new Set(prev); n.delete(id); return n; });
          continue;
        }
        setAnalyzingIds(prev => { const n = new Set(prev); n.delete(id); return n; });
      }
      
      // Step 2: Generate Email
      if (!currentLead.email_draft) {
         addLog(`✍️ [${currentLead.name}] Generating email...`);
         try {
            const emailRes = await apiGenerateEmail(id);
            if (emailRes.status === "success") {
                currentLead = { ...currentLead, email_draft: emailRes.email };
                setLeads(prev => prev.map(l => l.id === id ? currentLead : l));
            } else {
                addLog(`❌ [${currentLead.name}] Email generation failed.`);
                continue;
            }
         } catch(e) {
            addLog(`❌ [${currentLead.name}] Email generation failed.`);
            continue;
         }
      }
      
      // Step 3: Auto Send
      if (currentLead.email_sent != 1 || currentLead.send_status !== "Sent") {
         addLog(`📩 [${currentLead.name}] Sending email...`);
         try {
            const sendRes = await fetch('/auto_send', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ ids: [id] })
            }).then(r => r.json());
            
            if (sendRes.status === "success") {
                addLog(`✅ [${currentLead.name}] Sent successfully!`);
                // Use the leads returned from server
                setLeads(sendRes.leads); 
                currentLead = sendRes.leads.find(l => l.id === id);
            } else {
                addLog(`❌ [${currentLead.name}] Failed to send.`);
            }
         } catch(e) {
            addLog(`❌ [${currentLead.name}] Failed to send.`);
         }
      }
    }
    setIsAutomating(false);
    addLog(`🎉 Automation Pipeline Complete!`);
  };

  const handleExportExcel = () => {
    window.location.href = '/export_excel';
  };

  return (
    <div className="pt-8">
      {/* Results Header Section */}
      <section className="flex flex-col gap-6 mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <input 
              type="checkbox" 
              checked={sortedLeads.length > 0 && selectedIds.size === sortedLeads.length}
              onChange={handleSelectAll}
              className="w-5 h-5 rounded border-slate-700 bg-slate-900 text-primary focus:ring-primary/40 transition-all cursor-pointer"
              title="Select All Visible Leads"
            />
            <h2 className="font-headline-lg text-headline-lg text-on-surface">Results ({sortedLeads.length})</h2>
          </div>
          <div className="flex bg-surface-container rounded-lg p-1 border border-outline-variant">
            <button 
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
              className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-primary-container text-on-primary-container text-sm font-medium transition-all"
            >
              <span className="material-symbols-outlined text-sm">{viewMode === 'grid' ? 'list' : 'grid_view'}</span>
              {viewMode === 'grid' ? 'List' : 'Grid'}
            </button>
          </div>
        </div>

        {/* Sub-header: Mass Blast */}
        <div className="bg-surface-container-high rounded-xl p-4 border border-slate-700/50 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button 
              onClick={startMassBlast}
              className="bg-error-container text-on-error-container hover:brightness-110 active:scale-95 transition-all px-6 py-2.5 rounded-lg font-label-caps flex items-center gap-2"
            >
              <span className="material-symbols-outlined">bolt</span>
              Mass Blast
            </button>
            <div className="flex items-center gap-2">
              {analyzingIds.size > 0 && (
                <>
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-tertiary opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-tertiary"></span>
                  </span>
                  <p className="font-mono-data text-[13px] text-tertiary">AI Engine: Scanning signals...</p>
                </>
              )}
            </div>
          </div>
          <button 
            onClick={handleExportExcel} 
            className="bg-slate-700 text-white hover:bg-slate-600 active:scale-95 transition-all px-4 py-2.5 rounded-xl font-label-caps flex items-center gap-2 shadow-lg uppercase text-sm"
          >
            <span className="material-symbols-outlined text-sm">download</span>
            Export Excel
          </button>
        </div>
      </section>

      <section className={viewMode === 'grid' ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-32" : "flex flex-col gap-4 mb-32"}>
        {sortedLeads.length === 0 ? (
          <div className="col-span-1 md:col-span-2 lg:col-span-3 flex flex-col items-center justify-center p-12 bg-surface-container border border-slate-700/50 rounded-xl mt-8">
            <span className="material-symbols-outlined text-6xl text-slate-500 mb-4">search_off</span>
            <h3 className="font-headline-lg text-body-lg text-on-surface mb-2">No Leads Found</h3>
            <p className="text-slate-400 font-body-md text-center max-w-md">
              Run a new pipeline command from the dashboard to generate leads, or select a previous run from your History.
            </p>
          </div>
        ) : (
          sortedLeads.map((lead, index) => {
          const isAnalyzed = !!lead.analysis;
          const auditFailed = lead.detected_problem === "Manual Audit Required.";
          const isDrafted = !!lead.email_draft;
          const isSent = lead.email_sent == 1 && lead.send_status === "Sent";
          const isAnalyzing = analyzingIds.has(lead.id);

          return (
            <div 
              key={lead.id} 
              onClick={() => setSelectedLeadDetails(lead)}
              className={`group relative cursor-pointer bg-surface-container border ${isAnalyzed ? 'border-primary/50' : 'border-slate-700'} rounded-xl overflow-hidden hover:border-blue-500/30 transition-all shadow-lg`}
            >
              <div className="p-4 flex gap-4 flex-col h-full">
                <div className="flex gap-4">
                  <div className="pt-1">
                    <input 
                      checked={selectedIds.has(lead.id)}
                      onChange={(e) => { e.stopPropagation(); toggleSelection(lead.id); }}
                      onClick={(e) => e.stopPropagation()}
                      className="w-5 h-5 rounded border-slate-700 bg-slate-900 text-primary focus:ring-primary/40 transition-all" 
                      type="checkbox"
                    />
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-headline-md text-body-lg text-on-surface">{lead.name}</h3>
                        <p className="text-body-sm text-on-surface-variant">{lead.industry || 'Unknown Industry'}</p>
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border font-bold uppercase tracking-wider ${
                        lead.priority === 'high' ? 'bg-primary/10 text-primary border-primary/20' : 
                        lead.priority === 'medium' ? 'bg-tertiary/10 text-tertiary border-tertiary/20' :
                        'bg-slate-700/50 text-slate-400 border-slate-600'
                      }`}>
                        {lead.priority || 'Unrated'}
                      </span>
                    </div>

                    <div className="space-y-1 mb-2">
                      <div className="flex items-center gap-2 text-on-surface-variant text-body-sm">
                        <span>{lead.outreach_email ? '✅ Email' : '⚪ No Email'}</span>
                        <span>{lead.linkedin_url ? '✅ LinkedIn' : '⚪ No LinkedIn'}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {isAnalyzed && lead.estimated_loss && (
                  <div className="text-xs text-yellow-400 bg-yellow-400/10 p-2 rounded-md font-bold">
                    💰 Potential Loss: ₹{Number(lead.estimated_loss).toLocaleString()}/month
                  </div>
                )}

                {isAnalyzed && lead.detected_problem && (
                  <div className="text-xs text-red-400 bg-red-400/10 p-2 rounded-md">
                    ⚠️ {lead.detected_problem}
                  </div>
                )}

                <div className="text-xs text-on-surface-variant italic h-16 overflow-y-auto mt-auto">
                  {lead.analysis || (isAnalyzing ? "Analyzing..." : "Click to Analyze")}
                </div>

                <div className="flex gap-2 mt-2">
                  {isSent ? (
                    <button className="flex-1 bg-green-500 text-white text-xs py-1.5 rounded font-bold" disabled>✅ Sent</button>
                  ) : isDrafted ? (
                    <button onClick={(e) => { e.stopPropagation(); setEmailModalData(lead); }} className="flex-1 bg-primary text-white text-xs py-1.5 rounded font-bold hover:brightness-110">📧 View Draft</button>
                  ) : (
                    <button onClick={(e) => { e.stopPropagation(); handleAnalyzeOne(lead.id, index); }} disabled={isAnalyzing} className="flex-1 bg-surface-container-high border border-outline-variant text-on-surface text-xs py-1.5 rounded font-bold hover:bg-surface-variant">
                      {isAnalyzing ? "⏳ Auditing..." : (isAnalyzed && !auditFailed ? "🔄 Re-Audit" : (auditFailed ? "⚠️ Audit Failed" : "🔍 Deep Audit"))}
                    </button>
                  )}
                  <button onClick={(e) => { e.stopPropagation(); handleDelete(lead.id); }} className="bg-red-500/20 text-red-400 text-xs px-3 py-1.5 rounded font-bold hover:bg-red-500/30">🗑</button>
                </div>
              </div>
              <div className={`h-1 w-full ${isAnalyzed ? 'bg-gradient-to-r from-blue-500/50 to-tertiary/50' : 'bg-slate-700/30'}`}></div>
            </div>
          );
          })
        )}
      </section>

      {/* Floating Action Bar */}
      {selectedIds.size > 0 && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-40 w-[90%] max-w-2xl">
          <div className="bg-slate-900/90 backdrop-blur-2xl border border-blue-500/40 rounded-2xl p-4 shadow-[0_20px_50px_rgba(0,0,0,0.6)] flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-primary text-on-primary h-8 w-8 flex items-center justify-center rounded-lg font-bold font-mono-data">
                {selectedIds.size}
              </div>
              <p className="font-headline-md text-body-md text-on-surface">Leads Selected</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button onClick={clearSelection} className="text-slate-400 hover:text-on-surface font-label-caps px-4 py-2 transition-colors uppercase text-sm">
                Clear All
              </button>
              <button 
                onClick={handleAutomateSelected} 
                disabled={isAutomating}
                className="bg-tertiary text-on-tertiary hover:brightness-110 active:scale-95 transition-all px-4 py-2.5 rounded-xl font-label-caps flex items-center gap-2 shadow-lg uppercase text-sm disabled:opacity-50"
              >
                {isAutomating ? <span className="material-symbols-outlined text-sm animate-spin">refresh</span> : <span className="material-symbols-outlined text-sm">smart_toy</span>}
                Automate Selected
              </button>
              <button 
                onClick={handleBatchOutreach} 
                disabled={isAutomating}
                className="bg-primary text-on-primary-container hover:brightness-110 active:scale-95 transition-all px-4 py-2.5 rounded-xl font-label-caps flex items-center gap-2 shadow-lg shadow-blue-500/20 uppercase text-sm disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-sm">magic_button</span>
                Generate Emails
              </button>
              <button 
                onClick={autoSendSelected} 
                disabled={isAutomating}
                className="bg-green-600 text-white hover:brightness-110 active:scale-95 transition-all px-4 py-2.5 rounded-xl font-label-caps flex items-center gap-2 shadow-lg uppercase text-sm disabled:opacity-50"
              >
                📩 Auto Send
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Email Modal */}
      {emailModalData && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-surface-container border border-outline-variant rounded-xl p-6 max-w-2xl w-full mx-4 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-on-surface">📧 Outreach Draft</h2>
              <button onClick={() => setEmailModalData(null)} className="text-slate-400 hover:text-white text-2xl">&times;</button>
            </div>
            <textarea 
              readOnly 
              className="w-full h-64 bg-slate-900 text-on-surface border border-slate-700 rounded-lg p-4 font-body-sm resize-none mb-4"
              value={emailModalData.email_draft || "No draft found"}
            />
            <div className="flex gap-4">
              <button 
                onClick={() => navigator.clipboard.writeText(emailModalData.email_draft)} 
                className="flex-1 bg-primary text-white py-2 rounded-lg font-bold hover:brightness-110"
              >
                📋 Copy Email
              </button>
              <button 
                onClick={() => setEmailModalData(null)} 
                className="flex-1 bg-surface-variant text-on-surface py-2 rounded-lg font-bold hover:bg-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Lead Modal */}
      {selectedLeadDetails && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container border border-outline-variant rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl relative">
            <button onClick={() => setSelectedLeadDetails(null)} className="absolute top-4 right-4 text-slate-400 hover:text-white p-2 rounded-full bg-slate-800/50 transition-colors">
              <span className="material-symbols-outlined">close</span>
            </button>
            <div className="flex justify-between items-start mb-6">
              <div className="pr-12">
                <h2 className="text-2xl font-bold text-on-surface font-['Space_Grotesk']">{selectedLeadDetails.name}</h2>
                <p className="text-primary mt-1 flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm">tag</span>
                  ID: {selectedLeadDetails.id} | {selectedLeadDetails.industry}
                </p>
              </div>
            </div>
            
            <div className="grid gap-6">
              {/* Core Information */}
              <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50">
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Core Info</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500 block mb-1">Website</span>
                    <a href={selectedLeadDetails.website} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline break-all">
                      {selectedLeadDetails.website || 'N/A'}
                    </a>
                  </div>
                  <div>
                    <span className="text-slate-500 block mb-1">LinkedIn</span>
                    <a href={selectedLeadDetails.linkedin_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline break-all">
                      {selectedLeadDetails.linkedin_url || 'N/A'}
                    </a>
                  </div>
                  <div>
                    <span className="text-slate-500 block mb-1">Email</span>
                    <span className="text-slate-200">{selectedLeadDetails.outreach_email || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block mb-1">Google Rating</span>
                    <span className="text-yellow-400 font-bold">{selectedLeadDetails.google_rating ? `⭐ ${selectedLeadDetails.google_rating}` : 'N/A'}</span>
                  </div>
                </div>
              </div>

              {/* Analysis & Problems */}
              <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50">
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">AI Deep Audit</h3>
                <div className="space-y-4">
                  {selectedLeadDetails.detected_problem && (
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-md">
                      <strong className="text-red-400 block mb-1">Detected Problem</strong>
                      <span className="text-slate-200 text-sm">{selectedLeadDetails.detected_problem}</span>
                    </div>
                  )}
                  {selectedLeadDetails.estimated_loss && (
                    <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-md">
                      <strong className="text-yellow-400 block mb-1">Estimated Monthly Loss</strong>
                      <span className="text-slate-200 text-sm">₹{Number(selectedLeadDetails.estimated_loss).toLocaleString()}</span>
                    </div>
                  )}
                  <div>
                    <strong className="text-slate-400 block mb-1 text-sm">Full Analysis</strong>
                    <p className="text-slate-300 text-sm whitespace-pre-wrap leading-relaxed bg-slate-950 p-3 rounded-md border border-slate-800">
                      {selectedLeadDetails.analysis || 'No detailed analysis available. Run Deep Audit.'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Description */}
              <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50">
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Description</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  {selectedLeadDetails.description || 'No description found.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
