import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import StatusBadge from "../components/StatusBadge";
import { Button, EmptyState, ErrorState, LoadingState } from "../components/common";
import RiskScore from "../components/RiskScore";
import { api, getApiError } from "../lib/api";
import { CLASSIFICATIONS, formatAnalysisDate, formatClassification } from "../lib/analysis-utils";

export default function History() {
  const [analyses, setAnalyses] = useState([]);
  const [filters, setFilters] = useState({ search: "", classification: "ALL" });
  const [state, setState] = useState({ loading: true, error: "" });

  const loadHistory = useCallback(async () => {
    setState({ loading: true, error: "" });
    try {
      const { data } = await api.get("/api/analysis/history?limit=100");
      setAnalyses(Array.isArray(data) ? data : []);
      setState({ loading: false, error: "" });
    } catch (error) {
      setState({ loading: false, error: getApiError(error, "Analysis history could not be loaded.") });
    }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const filtered = useMemo(() => analyses.filter((analysis) => {
    const search = filters.search.trim().toLowerCase();
    const matchesSearch = !search || `${analysis.summary || ""} ${analysis.analysis_id}`.toLowerCase().includes(search);
    const matchesClassification = filters.classification === "ALL" || analysis.classification === filters.classification;
    return matchesSearch && matchesClassification;
  }), [analyses, filters]);

  if (state.loading) return <LoadingState label="Loading analysis history" />;
  if (state.error) return <ErrorState title="History unavailable" message={state.error} action={<Button variant="secondary" onClick={loadHistory}>Retry</Button>} />;

  return <div className="space-y-8"><header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Audit trail</p><h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">Analysis history</h1><p className="mt-2 text-sm text-slate-500">Only your own analysis records are shown. Filters apply to the loaded history.</p></div><Link to="/analyze"><Button>Analyze an email</Button></Link></header>
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4" aria-label="History filters"><div className="grid gap-3 md:grid-cols-[1fr_220px_auto]"><label className="sr-only" htmlFor="history-search">Search history</label><input id="history-search" type="search" value={filters.search} onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} placeholder="Search by result or analysis ID" className="rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-2.5 text-sm text-slate-100 outline-none placeholder:text-slate-600 focus:border-cyan-300/60 focus:ring-2 focus:ring-cyan-300/10" /><label className="sr-only" htmlFor="history-classification">Filter by classification</label><select id="history-classification" value={filters.classification} onChange={(event) => setFilters((current) => ({ ...current, classification: event.target.value }))} className="rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-2.5 text-sm text-slate-300 outline-none focus:border-cyan-300/60 focus:ring-2 focus:ring-cyan-300/10"><option value="ALL">All classifications</option>{CLASSIFICATIONS.map((classification) => <option key={classification} value={classification}>{formatClassification(classification)}</option>)}</select><button type="button" onClick={() => setFilters({ search: "", classification: "ALL" })} className="rounded-xl border border-slate-700 px-4 py-2.5 text-sm font-semibold text-slate-300 transition hover:border-slate-500 hover:text-white">Clear</button></div><p className="mt-3 text-xs text-slate-600">Showing {filtered.length} of {analyses.length} available analyses</p></section>
    {filtered.length ? <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70"><div className="hidden grid-cols-[minmax(0,1.6fr)_140px_110px_160px] gap-4 border-b border-slate-800 px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-600 md:grid"><span>Analysis</span><span>Classification</span><span>Risk</span><span>Reviewed</span></div><div className="divide-y divide-slate-800/80">{filtered.map((analysis) => <HistoryRow key={analysis.analysis_id} analysis={analysis} />)}</div></div> : <EmptyState title={analyses.length ? "No matching analyses" : "Your history is empty"} message={analyses.length ? "Try a different search or classification filter." : "Completed analyses will appear here with their scores, indicators, and explanations."} action={analyses.length ? <Button variant="secondary" onClick={() => setFilters({ search: "", classification: "ALL" })}>Clear filters</Button> : <Link to="/analyze"><Button>Analyze your first email</Button></Link>} />}
  </div>;
}

function HistoryRow({ analysis }) {
  return <div className="grid gap-4 p-5 transition hover:bg-slate-800/30 md:grid-cols-[minmax(0,1.6fr)_140px_110px_160px] md:items-center"><div className="min-w-0"><p className="text-xs text-slate-600">Analysis #{analysis.analysis_id}</p><p className="mt-2 line-clamp-2 text-sm font-medium leading-6 text-slate-200">{analysis.summary || "Analysis result"}</p><div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-600"><span>{analysis.threats?.length || 0} indicators</span><span>{analysis.analyzed_urls?.length || 0} URLs</span><span>{Math.round((Number(analysis.confidence) || 0) * 100)}% confidence</span></div></div><div><StatusBadge classification={analysis.classification} size="sm" /></div><div><RiskScore compact score={analysis.risk_score} classification={analysis.classification} /></div><div className="flex items-center justify-between gap-3 md:block"><p className="text-xs text-slate-500">{formatAnalysisDate(analysis.created_at)}</p><Link to={`/results/${analysis.analysis_id}`} className="mt-2 inline-block text-xs font-semibold text-cyan-300 hover:text-cyan-200">View result →</Link></div></div>;
}
