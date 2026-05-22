import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiGetInitialData, apiCheckSession, apiGetHistoryLeads } from '../services/api';

const AppContext = createContext();

export function AppProvider({ children }) {
  const [leads, setLeads] = useState([]);
  const [history, setHistory] = useState([]);
  const [logs, setLogs] = useState([{ time: new Date().toLocaleTimeString(), msg: "System idle. Ready for command..." }]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const addLog = useCallback((msg) => {
    setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), msg }]);
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  const loadDashboardData = useCallback(async () => {
    try {
      const result = await apiGetInitialData();
      if (result.status === "success") {
        setHistory(result.history || []);
        // Note: the old vanilla JS set leads=[] on dashboard load, but let's keep leads from DB if needed
        // The old app did: historyList.innerHTML = ""; result.history.forEach(updateHistory); document.getElementById("cards").innerHTML = "Start a new search"
        setLeads([]); 
      }
    } catch (e) {
      console.error(e);
      addLog("❌ Load failed (check console)");
    }
  }, [addLog]);

  const loadHistoryLeadsForQuery = useCallback(async (query) => {
    addLog(`Restoring results for: "${query}"`);
    try {
      const result = await apiGetHistoryLeads(query);
      if (result.status === "success" && result.leads.length > 0) {
        setLeads(result.leads);
        addLog(`✅ Found ${result.leads.length} leads in local history.`);
      } else {
        addLog("⚠️ No leads found.");
        setLeads([]);
      }
    } catch (e) {
      console.error(e);
      addLog("❌ Failed to fetch history leads.");
    }
  }, [addLog]);

  useEffect(() => {
    async function checkAuth() {
      try {
        const res = await apiCheckSession();
        if (res.logged_in) {
          setIsAuthenticated(true);
          await loadDashboardData();
        } else {
          setIsAuthenticated(false);
        }
      } catch (e) {
        console.error("Auth check failed", e);
        setIsAuthenticated(false);
      } finally {
        setIsInitializing(false);
      }
    }
    checkAuth();
  }, [loadDashboardData]);

  const value = {
    leads,
    setLeads,
    history,
    setHistory,
    logs,
    addLog,
    clearLogs,
    isAuthenticated,
    setIsAuthenticated,
    isInitializing,
    loadDashboardData,
    loadHistoryLeadsForQuery,
    isSidebarOpen,
    setIsSidebarOpen
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  return useContext(AppContext);
}
