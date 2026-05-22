import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  apiGetSettings, apiSaveSettings, apiGoogleLogin, apiGoogleDisconnect,
  apiGetKeys, apiAddKey, apiUpdateKey, apiDeleteKey, apiTestKey,
  apiGetGmailStatus, apiTestGmail, apiGetUsage
} from '../services/api';

export default function AIConfiguration() {
  // Legacy settings (will migrate fully in later phases)
  const [serper, setSerper] = useState('');
  const [apollo, setApollo] = useState('');
  const [model, setModel] = useState('ollama');
  const [gmailAddress, setGmailAddress] = useState('');
  
  // BYOK States
  const [providerKeys, setProviderKeys] = useState({});
  const [keyInputs, setKeyInputs] = useState({ openai: '', gemini: '', claude: '' });
  const [loadingStates, setLoadingStates] = useState({});
  const [usage, setUsage] = useState([]);
  
  const [status, setStatus] = useState('');
  const location = useLocation();

  useEffect(() => {
    loadAllData();

    // Check URL params for OAuth results
    const params = new URLSearchParams(location.search);
    if (params.get('gmail') === 'connected') {
      showStatus('✅ Gmail Connected Successfully');
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (params.get('error')) {
      showStatus(`❌ OAuth Error: ${params.get('error')}`);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [location]);

  const loadAllData = async () => {
    try {
      // Load legacy settings
      const res = await apiGetSettings();
      if (res.status === "success") {
        setSerper(res.serper || "");
        setApollo(res.apollo || "");
        setModel(res.model || "ollama");
      }
      
      // Load BYOK keys
      await loadKeys();

      // Load Usage
      const usageRes = await apiGetUsage();
      if(usageRes.status === 'success' && usageRes.data) {
        setUsage(usageRes.data);
      }

      // Load Gmail Status
      const gmailRes = await apiGetGmailStatus();
      if(gmailRes.status === 'success' && gmailRes.data) {
        setGmailAddress(gmailRes.data.gmail_address);
      }
    } catch (e) {
      console.error("Data load failed", e);
    }
  };

  const loadKeys = async () => {
    try {
      const res = await apiGetKeys();
      if (res.status === "success" && res.data) {
        const keysMap = {};
        res.data.forEach(k => { keysMap[k.provider] = k; });
        setProviderKeys(keysMap);
      }
    } catch (e) {
      console.error("Failed to load keys", e);
    }
  };

  const showStatus = (msg) => {
    setStatus(msg);
    setTimeout(() => setStatus(''), 4000);
  };

  const handleSaveLegacySettings = async () => {
    showStatus('Saving...');
    try {
      // The backend expects openai, gemini, claude, but we won't send them here anymore or we send empty 
      // since they are managed via the new /api/keys endpoints. 
      // To prevent overwriting with blanks in legacy endpoint, we just omit or send existing.
      const data = { serper, apollo, model };
      const res = await apiSaveSettings(data);
      if (res.status === "success") {
        showStatus("✅ Settings saved successfully");
      } else {
        showStatus("❌ Failed to save");
      }
    } catch (e) {
      showStatus("❌ Failed to save");
    }
  };

  const handleKeyAction = async (provider, action) => {
    setLoadingStates(prev => ({ ...prev, [provider]: true }));
    try {
      if (action === 'save' || action === 'update') {
        const key = keyInputs[provider];
        if (!key) {
          showStatus("⚠️ Please enter a key first.");
          setLoadingStates(prev => ({ ...prev, [provider]: false }));
          return;
        }
        
        const res = action === 'save' 
          ? await apiAddKey(provider, key)
          : await apiUpdateKey(provider, key);
          
        if (res.status === 'success') {
          showStatus(`✅ ${provider.toUpperCase()} key securely stored.`);
          setKeyInputs(prev => ({ ...prev, [provider]: '' }));
          await loadKeys();
        } else {
          showStatus(`❌ Failed: ${res.message || 'Validation error'}`);
        }
      } 
      else if (action === 'test') {
        showStatus(`Testing connection for ${provider}...`);
        const res = await apiTestKey(provider);
        if (res.status === 'success') {
          showStatus(`✅ ${provider.toUpperCase()} connection successful!`);
        } else {
          showStatus(`❌ ${provider.toUpperCase()} connection failed.`);
        }
      }
      else if (action === 'delete') {
        const res = await apiDeleteKey(provider);
        if (res.status === 'success') {
          showStatus(`✅ ${provider.toUpperCase()} key removed.`);
          await loadKeys();
        }
      }
    } catch (e) {
      showStatus(`❌ Action failed for ${provider}`);
    } finally {
      setLoadingStates(prev => ({ ...prev, [provider]: false }));
    }
  };

  const handleGoogleConnect = async () => {
    try {
      showStatus('Redirecting to Google...');
      const res = await apiGoogleLogin();
      if (res.status === 'success' && res.url) {
        window.location.href = res.url;
      } else {
        showStatus('❌ Failed to initiate connection');
      }
    } catch (e) {
      showStatus('❌ Network error');
    }
  };

  const handleGoogleDisconnect = async () => {
    try {
      showStatus('Disconnecting...');
      const res = await apiGoogleDisconnect();
      if (res.status === 'success') {
        setGmailAddress('');
        showStatus('✅ Disconnected');
      }
    } catch (e) {
      showStatus('❌ Disconnect failed');
    }
  };

  const renderProviderCard = (provider, title, placeholder) => {
    const isSaved = !!providerKeys[provider];
    const keyData = providerKeys[provider];
    const isLoading = loadingStates[provider];

    return (
      <div className="space-y-2 border border-slate-700/50 p-4 rounded-lg bg-slate-800/40">
        <div className="flex justify-between items-center">
          <label className="font-label-caps text-label-caps text-slate-300 capitalize">{title}</label>
          {isSaved && (
            <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${keyData.is_valid ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
              {keyData.is_valid ? 'Active' : 'Invalid'}
            </span>
          )}
        </div>
        
        {!isSaved ? (
          <div className="flex gap-2">
            <input 
              className="flex-1 bg-background border border-slate-700 rounded-lg py-2 px-3 text-sm text-on-surface focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all font-mono-data" 
              type="password" 
              placeholder={placeholder}
              value={keyInputs[provider] || ''}
              onChange={(e) => setKeyInputs(prev => ({ ...prev, [provider]: e.target.value }))}
              disabled={isLoading}
            />
            <button 
              onClick={() => handleKeyAction(provider, 'save')}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50"
            >
              Save
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-3 bg-background border border-slate-700 rounded-lg py-2 px-3">
              <span className="material-symbols-outlined text-green-500 text-sm">lock</span>
              <span className="font-mono-data text-sm text-slate-300 flex-1">{keyData.key_prefix}</span>
              <button 
                onClick={() => handleKeyAction(provider, 'delete')}
                disabled={isLoading}
                className="text-slate-400 hover:text-red-400 transition-colors"
                title="Delete Key"
              >
                <span className="material-symbols-outlined text-[18px]">delete</span>
              </button>
            </div>
            
            {/* Update existing key row */}
            <div className="flex gap-2">
               <input 
                  className="flex-1 bg-background border border-slate-700 rounded-lg py-1.5 px-3 text-xs text-on-surface focus:ring-1 focus:ring-blue-500 outline-none font-mono-data" 
                  type="password" 
                  placeholder="Enter new key to replace..."
                  value={keyInputs[provider] || ''}
                  onChange={(e) => setKeyInputs(prev => ({ ...prev, [provider]: e.target.value }))}
                  disabled={isLoading}
                />
                <button 
                  onClick={() => handleKeyAction(provider, 'update')}
                  disabled={isLoading || !keyInputs[provider]}
                  className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-3 py-1.5 rounded-lg text-xs transition-colors disabled:opacity-50"
                >
                  Update
                </button>
                <button 
                  onClick={() => handleKeyAction(provider, 'test')}
                  disabled={isLoading}
                  className="bg-slate-700 hover:bg-blue-600 text-slate-200 px-3 py-1.5 rounded-lg text-xs transition-colors disabled:opacity-50"
                >
                  Test
                </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="pt-8 pb-20">
      <header className="mb-12">
        <h2 className="font-headline-lg text-headline-lg text-on-surface flex items-center gap-3">
          <span className="text-2xl">⚙️</span> Settings &amp; Integrations
        </h2>
        <p className="text-slate-400 mt-2 font-body-md">Manage your secure Bring Your Own Key (BYOK) vault and RevOps tools.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* BYOK Vault Card */}
        <section className="lg:col-span-8 bg-surface-container-low border border-slate-700 rounded-xl overflow-hidden shadow-lg backdrop-blur-md">
          <div className="p-6 border-b border-slate-700 bg-slate-800/30 flex justify-between items-center">
            <h3 className="font-headline-md text-sm text-on-surface-variant flex items-center gap-2">
              <span className="material-symbols-outlined text-blue-500">lock_person</span> BYOK Vault (AES-256 Encrypted)
            </h3>
            <span className="px-3 py-1 rounded-full bg-tertiary-container/20 text-tertiary text-[10px] font-bold uppercase tracking-widest border border-tertiary/30">Private</span>
          </div>

          <div className="p-8 space-y-6">
            <p className="text-sm text-slate-400 mb-4">
              Your keys are encrypted in the database. They are only decrypted temporarily in memory when executing your pipelines. We never store plaintext keys.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {renderProviderCard('openai', 'OpenAI API Key', 'sk-proj-...')}
              {renderProviderCard('claude', 'Claude API Key', 'sk-ant-...')}
              {renderProviderCard('gemini', 'Gemini API Key', 'AIzaSy...')}
            </div>

            <div className="pt-6 border-t border-slate-700/50 mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="font-label-caps text-label-caps text-slate-400">Serper API Key</label>
                <div className="relative">
                  <input 
                    className="w-full bg-background border border-slate-700 rounded-lg py-3 px-4 text-on-surface focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all font-mono-data" 
                    type="password" 
                    placeholder="Paste Serper.dev key"
                    value={serper}
                    onChange={(e) => setSerper(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="font-label-caps text-label-caps text-slate-400">Apollo API Key</label>
                <div className="relative">
                  <input 
                    className="w-full bg-background border border-slate-700 rounded-lg py-3 px-4 text-on-surface focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none transition-all font-mono-data" 
                    type="password" 
                    placeholder="Paste Apollo API key"
                    value={apollo}
                    onChange={(e) => setApollo(e.target.value)}
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Sidebar Cards */}
        <section className="lg:col-span-4 space-y-6">
          
          <div className="bg-surface-container-low border border-slate-700 rounded-xl p-6 shadow-lg">
            <h3 className="font-headline-md text-sm text-on-surface-variant flex items-center gap-2 mb-6">
              <span className="material-symbols-outlined text-blue-500">psychology</span> Default AI Provider
            </h3>
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="font-label-caps text-label-caps text-slate-400">Model selection</label>
                <select 
                  className="w-full bg-background border border-slate-700 rounded-lg py-3 px-4 text-on-surface focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none appearance-none cursor-pointer"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                >
                  <option value="openai">OpenAI (GPT-4o)</option>
                  <option value="claude">Anthropic (Claude 3.5 Sonnet)</option>
                  <option value="gemini">Google (Gemini 1.5 Pro)</option>
                  <option value="ollama">Local Mistral (Ollama)</option>
                </select>
                <p className="text-[10px] text-slate-500 mt-1">Make sure you have saved the API key for your selected provider.</p>
              </div>
            </div>
          </div>

          <div className="bg-surface-container-low border border-slate-700 rounded-xl p-6 shadow-lg">
            <h3 className="font-headline-md text-sm text-on-surface-variant flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-red-500">mail</span> Email Integrations
            </h3>
            <div className="space-y-4">
              <p className="text-xs text-slate-400">Connect your Gmail account to send hyper-personalized cold outreach directly from this platform.</p>
              
              {gmailAddress ? (
                <div className="p-4 rounded-lg bg-slate-800 border border-slate-700 flex flex-col gap-3">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                    <span className="text-sm font-semibold text-on-surface">{gmailAddress}</span>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={async () => {
                        showStatus('Testing Gmail...');
                        const res = await apiTestGmail();
                        if(res.status === 'success') showStatus('✅ Gmail connection active');
                        else showStatus('❌ Gmail connection failed');
                      }}
                      className="flex-1 text-xs py-2 px-4 bg-slate-700 hover:bg-blue-600 text-slate-200 rounded transition-colors text-center border border-slate-600"
                    >
                      Test
                    </button>
                    <button 
                      onClick={handleGoogleDisconnect}
                      className="flex-1 text-xs py-2 px-4 bg-slate-700 hover:bg-red-500/20 hover:text-red-400 text-slate-300 rounded transition-colors text-center border border-slate-600"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              ) : (
                <button 
                  onClick={handleGoogleConnect}
                  className="w-full py-3 bg-white text-black font-semibold text-sm rounded-lg hover:bg-slate-200 active:scale-95 transition-all flex items-center justify-center gap-2 shadow-lg"
                >
                  <img src="https://www.google.com/favicon.ico" alt="Google" className="w-4 h-4" />
                  Connect Gmail
                </button>
              )}
            </div>
          </div>

        </section>

        {/* Action Area */}
        <div className="lg:col-span-12 mt-4 flex flex-col md:flex-row items-center justify-between gap-6 p-8 bg-slate-900/50 border border-slate-700 rounded-xl border-dashed">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500">
              <span className="material-symbols-outlined text-3xl">cloud_sync</span>
            </div>
            <div>
              <p className="font-body-md font-semibold text-on-surface">Synchronize Preferences</p>
              <p className="text-xs text-slate-500">Save your default AI provider, Serper, and Apollo settings.</p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-3 w-full md:w-auto">
            {status && <span className="text-sm font-semibold text-blue-400 transition-opacity">{status}</span>}
            <button 
              onClick={handleSaveLegacySettings}
              className="w-full md:w-auto px-10 py-4 bg-blue-500 text-on-primary font-headline-md text-sm rounded-lg hover:bg-blue-400 active:scale-95 transition-all shadow-lg shadow-blue-500/20"
            >
              Save Preferences
            </button>
          </div>
        </div>

        {/* Usage Dashboard */}
        <div className="lg:col-span-12 mt-8">
          <h2 className="font-headline-lg text-headline-lg text-on-surface flex items-center gap-3 mb-6">
            <span className="material-symbols-outlined text-green-400 text-3xl">monitoring</span> API Usage & Costs
          </h2>
          
          {usage.length === 0 ? (
            <div className="bg-surface-container-low border border-slate-700 rounded-xl p-8 text-center">
              <span className="material-symbols-outlined text-4xl text-slate-500 mb-2">query_stats</span>
              <p className="text-sm text-slate-400">No AI generations tracked yet.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {usage.map((u) => (
                <div key={u.provider} className="bg-slate-800 p-6 rounded-xl border border-slate-700 flex flex-col gap-3 shadow-lg hover:border-slate-500 transition-colors">
                  <div className="flex justify-between items-center">
                    <span className="font-headline-md text-sm capitalize text-on-surface">{u.provider}</span>
                    <span className="text-xs text-slate-400 bg-slate-900 px-2 py-1 rounded-full">{u.total_requests} calls</span>
                  </div>
                  <div className="text-3xl font-bold text-on-surface tracking-tight">
                    ${parseFloat(u.total_cost).toFixed(4)}
                  </div>
                  <div className="text-xs text-slate-400 flex justify-between items-center mt-2 border-t border-slate-700 pt-3">
                    <span>Tokens Used:</span>
                    <span className="font-mono-data font-bold text-slate-200">{u.total_tokens.toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
