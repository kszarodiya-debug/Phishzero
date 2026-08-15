import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ClassificationChart from "../components/ClassificationChart";
import { Button, EmptyState, ErrorState, LoadingState } from "../components/common";
import RiskScore, { riskStyle } from "../components/RiskScore";
import StatusBadge from "../components/StatusBadge";
import { api, getApiError } from "../lib/api";
import { formatAnalysisDate, summarizeAnalyses } from "../lib/analysis-utils";

export default function Dashboard() {
  const [analyses, setAnalyses] = useState([]);
  const [state, setState] = useState({ loading: true, error: "" });

  const loadHistory = useCallback(async () => {
    setState({ loading: true, error: "" });
    try {
      const { data } = await api.get("/api/analysis/history?limit=100");
      setAnalyses(Array.isArray(data) ? data : []);
    } catch (error) {
      setState({ loading: false, error: getApiError(error, "The security overview could not be loaded.") });
      return;
    }
    setState({ loading: false, error: "" });
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  if (state.loading) return <LoadingState label="Loading security overview" />;
  if (state.error) return <ErrorState title="Overview unavailable" message={state.error} action={<Button variant="secondary" onClick={loadHistory}>Retry</Button>} />;

  const summary = summarizeAnalyses(analyses);
  return <div className="space-y-8">
    <header className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Security overview</p><h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">Your analysis workspace</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">A focused view of the emails reviewed in your protected workspace.</p></div><Link to="/analyze"><Button>Analyze an email</Button></Link></header>

    <section aria-labelledby="classification-stats"><div className="mb-4 flex items-center justify-between"><h2 id="classification-stats" className="text-sm font-semibold text-white">Classification status</h2><span className="text-xs text-slate-600">{summary.total} available analyses</span></div><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"><Stat label="Total analyzed" value={summary.total} detail="Available history" tone="slate" /><Stat label="Safe" value={summary.safe} detail="No elevated signal" tone="emerald" /><Stat label="Spam / low risk" value={summary.spam} detail="Low-risk classification" tone="cyan" /><Stat label="Suspicious" value={summary.suspicious} detail="Needs review" tone="amber" /><Stat label="Phishing" value={summary.phishing} detail="Highest priority" tone="rose" /></div></section>

    <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6"><div className="flex items-start justify-between gap-4"><div><h2 className="text-sm font-semibold text-white">Classification distribution</h2><p className="mt-1 text-xs leading-5 text-slate-500">How your available analyses are distributed.</p></div><span className="rounded-full bg-slate-950 px-3 py-1 text-xs text-slate-500">{summary.flagged} flagged</span></div><div className="mt-6"><ClassificationChart distribution={summary.distribution} total={summary.total} /></div></div>
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6"><div><h2 className="text-sm font-semibold text-white">Risk statistics</h2><p className="mt-1 text-xs leading-5 text-slate-500">Summary of scores returned by the backend risk engine.</p></div><div className="mt-6 grid gap-3 sm:grid-cols-2"><RiskStat label="Average risk" value={`${Math.round(summary.averageRisk)}/100`} detail="Across available scores" tone="cyan" /><RiskStat label="Highest risk" value={`${Math.round(summary.highestRisk)}/100`} detail="Highest recorded score" tone={summary.highestRisk >= 76 ? "rose" : "amber"} /><RiskStat label="Flagged rate" value={`${summary.total ? Math.round((summary.flagged / summary.total) * 100) : 0}%`} detail="Suspicious + phishing" tone="amber" /><RiskStat label="Average confidence" value={`${Math.round(summary.averageConfidence * 100)}%`} detail="Model confidence returned" tone="emerald" /></div></div>
    </section>

    {analyses.length ? <section aria-labelledby="recent-analyses"><div className="mb-4 flex items-center justify-between"><div><h2 id="recent-analyses" className="text-sm font-semibold text-white">Recent analyses</h2><p className="mt-1 text-xs text-slate-500">Most recent results from your analysis history.</p></div><Link to="/history" className="text-xs font-semibold text-cyan-300 hover:text-cyan-200">View all history →</Link></div><div className="grid gap-4 lg:grid-cols-2">{analyses.slice(0, 4).map((analysis) => <AnalysisCard key={analysis.analysis_id} analysis={analysis} />)}</div></section> : <EmptyState title="No analyses yet" message="Submit an email to see evidence-backed risk scores and recommended actions." action={<Link to="/analyze"><Button>Start your first analysis</Button></Link>} />}
  </div>;
}

function AnalysisCard({ analysis }) {
  const style = riskStyle(analysis.classification);
  return <Link to={`/results/${analysis.analysis_id}`} className="group rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-600 hover:bg-slate-900"><div className="flex items-start justify-between gap-4"><div className="min-w-0"><p className="text-xs text-slate-600">Analysis #{analysis.analysis_id}</p><h3 className="mt-2 line-clamp-2 text-sm font-semibold leading-6 text-slate-200 group-hover:text-white">{analysis.summary}</h3></div><StatusBadge classification={analysis.classification} size="sm" /></div><div className="mt-5 flex items-center justify-between gap-4"><RiskScore compact score={analysis.risk_score} classification={analysis.classification} /><div className="text-right"><p className={`text-sm font-semibold ${style.tone}`}>{Math.round((Number(analysis.confidence) || 0) * 100)}% confidence</p><p className="mt-1 text-xs text-slate-600">{formatAnalysisDate(analysis.created_at, { dateStyle: "medium" })}</p></div></div></Link>;
}

function Stat({ label, value, detail, tone = "slate" }) {
  const colors = { slate: "text-white", emerald: "text-emerald-300", cyan: "text-cyan-300", amber: "text-amber-300", rose: "text-rose-300" };
  return <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4"><p className="text-xs text-slate-500">{label}</p><p className={`mt-3 text-2xl font-semibold ${colors[tone] || colors.slate}`}>{value}</p><p className="mt-1 text-[11px] text-slate-600">{detail}</p></div>;
}

function RiskStat({ label, value, detail, tone }) {
  const colors = { emerald: "text-emerald-300", cyan: "text-cyan-300", amber: "text-amber-300", rose: "text-rose-300" };
  return <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4"><p className="text-xs text-slate-500">{label}</p><p className={`mt-2 text-2xl font-semibold ${colors[tone] || "text-white"}`}>{value}</p><p className="mt-1 text-[11px] text-slate-600">{detail}</p></div>;
}
