'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export default function Home() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/api/dashboard`);
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch:', err);
      // Fallback: show error but keep UI alive
    }
    setLoading(false);
  };

  const refreshPipeline = async () => {
    setRefreshing(true);
    try {
      await axios.post(`${API_BASE}/api/refresh`);
      // Wait 10 seconds for pipeline to start generating, then fetch
      setTimeout(() => {
        fetchDashboard();
        setRefreshing(false);
      }, 10000);
    } catch (err) {
      console.error('Refresh failed:', err);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-blue-500 border-r-2 border-purple-500 mx-auto"></div>
          <p className="mt-4 text-slate-400">Loading ontology-driven content...</p>
        </div>
      </div>
    );
  }

  const categories = ['today_in_business', 'research_and_development', 'history'];
  const labels = {
    today_in_business: '📊 Today in Business',
    research_and_development: '🔬 Research & Development',
    history: '📜 History (On This Day)'
  };

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <h1 className="text-4xl font-extrabold bg-gradient-to-r from-blue-400 via-purple-400 to-amber-400 bg-clip-text text-transparent">
            🧠 Ontology News Engine
          </h1>
          <p className="text-slate-400 mt-1">27 Triggers · 10 Brakes · 16 Subcategories</p>
        </div>
        <button
          onClick={refreshPipeline}
          disabled={refreshing}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded-full font-semibold transition flex items-center gap-2"
        >
          {refreshing ? (
            <>
              <span className="animate-spin inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
              Generating...
            </>
          ) : (
            '🔄 Refresh Pipeline'
          )}
        </button>
      </div>

      {/* Deep Dive Spotlight (Weekly) */}
      {data?.deep_dive_article && (
        <div className="mb-10 p-6 bg-gradient-to-r from-amber-900/40 to-slate-800/60 rounded-2xl border border-amber-500/40 shadow-xl shadow-amber-500/10">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl">🏆</span>
            <span className="text-amber-400 font-bold tracking-widest text-sm uppercase">Deep Dive of the Week</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-white leading-tight">
            {data.deep_dive_article.title}
          </h2>
          <p className="text-slate-300 mt-2">
            Subcategory: <span className="text-amber-300 font-medium">{data.deep_dive_article.subcategory}</span>
          </p>
          <a
            href={`${API_BASE}/api/deep-dive/${data.deep_dive_article.url.split('/').pop()}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block mt-4 bg-amber-600 hover:bg-amber-700 px-6 py-2 rounded-full font-semibold transition"
          >
            📖 Read Full Article →
          </a>
        </div>
      )}

      {/* 3-Column Grid for Posters */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {categories.map((catKey) => (
          <div key={catKey} className="bg-slate-900/50 rounded-2xl p-4 border border-slate-800">
            <h2 className="text-xl font-bold text-blue-300 mb-4">{labels[catKey]}</h2>
            {data && data[catKey] ? (
              Object.keys(data[catKey]).map((subcat) => {
                const subData = data[catKey][subcat];
                if (!subData || !subData.poster) return null;
                const posterFilename = subData.poster.split('/').pop();
                return (
                  <div key={subcat} className="mb-6 bg-slate-800 rounded-xl overflow-hidden border border-slate-700 hover:border-blue-500/50 transition">
                    <div className="p-3 bg-slate-900/50 flex justify-between items-center">
                      <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                        {subcat.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full">
                        Top 5
                      </span>
                    </div>
                    <img
                      src={`${API_BASE}/api/poster/${posterFilename}`}
                      alt={`${subcat} poster`}
                      className="w-full aspect-[1/1.4] object-cover bg-slate-900"
                      loading="lazy"
                    />
                    <div className="p-3">
                      <a
                        href={`${API_BASE}/api/poster/${posterFilename}`}
                        download
                        className="inline-flex items-center gap-1 text-sm bg-green-600/20 hover:bg-green-600/40 text-green-300 px-4 py-1.5 rounded-full transition w-full justify-center"
                      >
                        ⬇ Download A4 Poster
                      </a>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-slate-500 text-sm">No data yet. Run pipeline.</p>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-12 pt-6 border-t border-slate-800 text-center text-slate-500 text-sm">
        Powered by Groq (LLM) · Gemini (Image Gen) · Ontology v2.0 · Daily pipeline runs at 6:00 AM
      </div>
    </main>
  );
}