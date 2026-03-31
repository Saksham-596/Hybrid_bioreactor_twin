"use client";
import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Play, Factory, Settings2, Database, Trash2, Wind, Droplets } from 'lucide-react';

export default function BioreactorDashboard() {
  const [isClient, setIsClient] = useState(false);
  const [params, setParams] = useState({
    Aeration_rate: 60.0,
    Air_head_pressure: 1.1,
    DO2: 15.0,
    O2_percent_outgas: 18.0,
    Substrate_concentration: 10.0,
    Oil_flow: 20.0,
    Vessel_Volume: 60000.0,
    Vessel_Weight: 60000.0
  });
  const [data, setData] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionID, setSessionID] = useState("");

  useEffect(() => {
    let id = localStorage.getItem("bioreactor_session_id");
    if (!id) {
      id = "session_" + Math.random().toString(36).substring(2, 15);
      localStorage.setItem("bioreactor_session_id", id);
    }
    setSessionID(id);
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (sessionID) {
      fetchHistory(sessionID);
    }
  }, [sessionID]);

  const fetchHistory = async (id: string) => {
    if (!id) return;
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/history?session_id=${id}`);
      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success') {
          setHistory(result.history);
        }
      }
    } catch (error) {
      console.error("Failed to fetch history:", error);
    }
  };
  
  const runSimulation = async () => {
    if (!sessionID) return;
    setLoading(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/simulate/hybrid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...params, session_id: sessionID }),
      });
      const result = await response.json();
      setData(result.data);
      await fetchHistory(sessionID); 
    } catch (error) {
      console.error("Simulation failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    if (!sessionID) return;
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await fetch(`${API_BASE}/history/clear?session_id=${sessionID}`, { method: 'DELETE' });
      setHistory([]);
      setData([]);
    } catch (error) {
      console.error("Failed to clear history:", error);
    }
  };

  const InputField = ({ label, name, min, max, step }: any) => (
    <div className="mb-4">
      <div className="flex justify-between mb-1">
        <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">{label}</label>
        <span className="text-xs font-bold text-cyan-400">{params[name as keyof typeof params]}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step}
        value={params[name as keyof typeof params]}
        onChange={(e) => setParams({ ...params, [name]: parseFloat(e.target.value) })}
        className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
      />
    </div>
  );

  if (!isClient) return null; 

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tighter flex items-center gap-2">
            <Factory className="text-cyan-500" /> INDUSTRIAL BIO-TWIN <span className="text-slate-500 font-light">v2.0</span>
          </h1>
          <p className="text-xs text-slate-500 font-mono mt-1">100,000L XGBOOST PREDICTIVE ENGINE ACTIVE</p>
        </div>
        <button
          onClick={runSimulation}
          disabled={loading}
          className="bg-cyan-600 hover:bg-cyan-500 text-white px-8 py-2.5 rounded-md flex items-center gap-2 font-bold transition-all disabled:opacity-50"
        >
          {loading ? <Activity className="animate-spin" /> : <Play size={18} fill="currentColor" />}
          RUN BATCH SIMULATION
        </button>
      </div>

      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-3 space-y-6">
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 shadow-2xl">
            <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-2">
              <h2 className="text-sm font-bold flex items-center gap-2 text-slate-300">
                <Settings2 size={16} className="text-cyan-400" /> SETPOINTS
              </h2>
            </div>
            
            <h3 className="text-xs font-bold text-emerald-400 mb-4 flex items-center gap-1"><Wind size={14} /> GAS & PRESSURE</h3>
            <InputField label="Aeration Rate (L/h)" name="Aeration_rate" min="0" max="150" step="1" />
            <InputField label="Air Head Pressure (bar)" name="Air_head_pressure" min="0.5" max="2.0" step="0.1" />
            <InputField label="Dissolved O2 (mg/L)" name="DO2" min="0" max="30" step="0.5" />
            <InputField label="Off-gas O2 (%)" name="O2_percent_outgas" min="10" max="25" step="0.5" />

            <div className="my-6 border-t border-slate-800"></div>

            <h3 className="text-xs font-bold text-amber-400 mb-4 flex items-center gap-1"><Droplets size={14} /> FEED & VESSEL</h3>
            <InputField label="Substrate Sugar (g/L)" name="Substrate_concentration" min="0" max="50" step="1" />
            <InputField label="Anti-foam Oil Flow (L/hr)" name="Oil_flow" min="0" max="50" step="1" />
            <InputField label="Vessel Volume (L)" name="Vessel_Volume" min="10000" max="100000" step="1000" />
            <InputField label="Vessel Weight (Kg)" name="Vessel_Weight" min="10000" max="100000" step="1000" />
          </div>

          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 shadow-2xl flex flex-col h-75">
            <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-2">
              <h2 className="text-sm font-bold flex items-center gap-2 text-slate-300">
                <Database size={16} className="text-cyan-400" /> BATCH HISTORY
              </h2>
              <button
                onClick={clearHistory}
                disabled={history.length === 0}
                className="text-xs flex items-center gap-1 bg-slate-800 hover:bg-rose-900/50 text-rose-400 border border-slate-700 hover:border-rose-500 px-2 py-1 rounded transition-colors disabled:opacity-30 disabled:hover:bg-slate-800 disabled:hover:border-slate-700 disabled:cursor-not-allowed"
              >
                <Trash2 size={12} /> CLEAR
              </button>
            </div>
            
            <div className="space-y-3 overflow-y-auto pr-2 custom-scrollbar grow">
              {history.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <p className="text-xs text-slate-500 font-mono text-center">No batches recorded.</p>
                </div>
              ) : (
                history.map((run: any, idx: number) => (
                  <div
                    key={idx}
                    onClick={() => {
                      if (run.data) setData(run.data);
                      if (run.parameters) setParams(run.parameters);
                    }}
                    className="bg-slate-800/50 p-3 rounded border border-slate-700 flex justify-between items-center hover:bg-slate-700 cursor-pointer transition-colors"
                  >
                    <div>
                      <p className="text-[10px] text-slate-400 font-mono">
                        {new Date(run.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                      <p className="text-xs font-bold text-amber-400 font-mono mt-1">
                        Vol: {(run.parameters.Vessel_Volume / 1000).toFixed(0)}k L
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[9px] text-slate-400 font-mono uppercase tracking-wider">Final Yield</p>
                      <p className="text-sm font-bold text-cyan-400 font-mono">
                        {run.final_predicted_biomass?.toFixed(2) || "0.00"} g/L
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-9 flex flex-col">
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 grow flex flex-col min-h-175">
            <div className="flex justify-between items-center mb-6 border-b border-slate-800 pb-4">
              <h2 className="text-sm font-bold text-slate-300 font-mono flex items-center gap-2">
                <Activity size={18} className="text-cyan-400" />
                BIOMASS GROWTH PREDICTION (250 HOURS)
              </h2>
              <div className="text-right">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Model Confidence</span>
                <span className="text-sm font-mono font-bold text-emerald-400">R² = 98.68%</span>
              </div>
            </div>
            
            <div className="w-full grow">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorBiomass" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis 
                    dataKey="time" 
                    stroke="#64748b" 
                    fontSize={12} 
                    tickFormatter={(val) => `${val}h`}
                    minTickGap={30}
                  />
                  <YAxis 
                    stroke="#64748b" 
                    fontSize={12} 
                    tickFormatter={(val) => `${val}`}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                    itemStyle={{ color: '#06b6d4', fontWeight: 'bold' }}
                    labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                    formatter={(value) => {
                      const numeric = typeof value === 'number' ? value : Number(value) || 0;
                      return [`${numeric.toFixed(2)} g/L`, 'Biomass'];
                    }}
                    labelFormatter={(label) => `Time: ${label} hours`}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="predicted_biomass_g_L" 
                    stroke="#06b6d4" 
                    strokeWidth={3}
                    fillOpacity={1} 
                    fill="url(#colorBiomass)" 
                    name="Predicted Biomass" 
                    isAnimationActive={true}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}