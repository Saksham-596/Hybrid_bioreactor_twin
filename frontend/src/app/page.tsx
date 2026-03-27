"use client";
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Activity, AlertTriangle, Play, Beaker, Settings2, Database } from 'lucide-react';

export default function BioreactorDashboard() {
  const [isClient, setIsClient] = useState(false);
  const [params, setParams] = useState({
    mu_max: 0.5, Ks: 2.0, Y: 0.5, D: 0.1, Sf: 20.0, toxicity_factor: 0.1
  });
  const [data, setData] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch History from MongoDB
  const fetchHistory = async () => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/history`);
      const result = await response.json();
      if (result.status === 'success') {
        setHistory(result.history);
      }
    } catch (error) {
      console.error("Failed to fetch history:", error);
    }
  };

  // Run Simulation & Update History
  const runSimulation = async () => {
    setLoading(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/simulate/hybrid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...params, t_end: 50, steps: 100 }),
      });
      const result = await response.json();
      setData(result.data);
      await fetchHistory(); // Trigger a history update immediately after running
    } catch (error) {
      console.error("Simulation failed:", error);
    } finally {
      setLoading(false);
    }
  };

  // Initial Load
  useEffect(() => { 
    setIsClient(true);
    runSimulation(); 
    fetchHistory();
  }, []);

  const InputField = ({ label, name, min, max, step }: any) => (
    <div className="mb-4">
      <div className="flex justify-between mb-1">
        <label className="text-xs font-mono text-slate-400 uppercase">{label}</label>
        <span className="text-xs font-bold text-cyan-400">{params[name as keyof typeof params]}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step}
        value={params[name as keyof typeof params]}
        onChange={(e) => setParams({ ...params, [name]: parseFloat(e.target.value) })}
        className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
      />
    </div>
  );

  if (!isClient) return null; // Prevents Recharts width(-1) error on SSR

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tighter flex items-center gap-2">
            <Beaker className="text-cyan-500" /> BIO-TWIN <span className="text-slate-500 font-light">v1.0</span>
          </h1>
          <p className="text-xs text-slate-500 font-mono mt-1">HYBRID PHYSICS-ML ANALYTICS ENGINE ACTIVE</p>
        </div>
        <button 
          onClick={runSimulation}
          disabled={loading}
          className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded-md flex items-center gap-2 font-bold transition-all disabled:opacity-50"
        >
          {loading ? <Activity className="animate-spin" /> : <Play size={18} />}
          RUN SIMULATION
        </button>
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* LEFT COLUMN: Controls & History */}
        <div className="col-span-12 lg:col-span-3 space-y-6">
          
          {/* Parameters Panel */}
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 shadow-2xl">
            <h2 className="text-sm font-bold mb-6 flex items-center gap-2 border-b border-slate-800 pb-2">
              <Settings2 size={16} /> PARAMETERS
            </h2>
            <InputField label="Max Growth Rate (μmax)" name="mu_max" min="0.1" max="1.5" step="0.05" />
            <InputField label="Half-Velocity (Ks)" name="Ks" min="0.5" max="10.0" step="0.5" />
            <InputField label="Yield (Y)" name="Y" min="0.1" max="0.9" step="0.05" />
            <InputField label="Dilution Rate (D)" name="D" min="0.0" max="0.5" step="0.01" />
            <InputField label="Feed Substrate (Sf)" name="Sf" min="10" max="100" step="5" />
            
            <div className="mt-8 pt-6 border-t border-slate-800">
              <h2 className="text-sm font-bold mb-4 flex items-center gap-2 text-rose-400">
                <AlertTriangle size={16} /> ML CORRECTION
              </h2>
              <InputField label="Unmodeled Toxicity" name="toxicity_factor" min="0.0" max="0.5" step="0.01" />
            </div>
          </div>

          {/* Cloud Batch History Panel */}
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800 shadow-2xl">
            <h2 className="text-sm font-bold mb-4 flex items-center gap-2 text-slate-300 border-b border-slate-800 pb-2">
              <Database size={16} className="text-cyan-400" /> CLOUD BATCH HISTORY
            </h2>
            <div className="space-y-3 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
              {history.length === 0 ? (
                <p className="text-xs text-slate-500 font-mono text-center py-4">No batches recorded yet.</p>
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
                      <p className="text-xs text-slate-400 font-mono">
                        {new Date(run.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </p>
                      <p className="text-xs font-bold text-rose-400 font-mono mt-1">
                        Tox: {run.parameters.toxicity_factor.toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">Final Mass</p>
                      <p className="text-sm font-bold text-cyan-400 font-mono">
                        {run.final_hybrid_biomass.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: Main Chart Area */}
        <div className="col-span-12 lg:col-span-9 space-y-8">
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
            <h2 className="text-sm font-bold mb-4 text-slate-400 font-mono">PRIMARY ANALYTICS: BIOMASS GROWTH (X)</h2>
            <div style={{ width: '100%', height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={12} label={{ value: 'Time (hours)', position: 'insideBottom', offset: -5 }} />
                  <YAxis stroke="#64748b" fontSize={12} label={{ value: 'Conc (g/L)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }} />
                  <Legend verticalAlign="top" height={36}/>
                  <Line type="monotone" dataKey="ideal_biomass" stroke="#94a3b8" strokeDasharray="5 5" name="Pure Physics (Monod)" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="hybrid_biomass" stroke="#06b6d4" name="Hybrid Prediction (ML-Corrected)" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Secondary Error Chart */}
          <div className="bg-slate-900/50 p-6 rounded-xl border border-slate-800">
            <h2 className="text-sm font-bold mb-4 text-rose-400 font-mono">ML ERROR MAGNITUDE (RESIDUAL)</h2>
            <div style={{ width: '100%', height: 250 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" hide />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }} />
                  <Area type="monotone" dataKey="error_magnitude" stroke="#f43f5e" fill="#f43f5e33" name="Correction Delta" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}