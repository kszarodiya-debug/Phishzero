import React from "react";

const severityStyles = { low: "border-slate-700 bg-slate-900/60 text-slate-300", medium: "border-amber-400/20 bg-amber-400/5 text-amber-200", high: "border-rose-400/20 bg-rose-400/5 text-rose-200", critical: "border-rose-300/40 bg-rose-400/10 text-rose-100" };

export default function ThreatCard({ threat }) {
  const severity = String(threat.severity || "medium").toLowerCase();
  return <article className={`rounded-xl border p-4 ${severityStyles[severity] || severityStyles.medium}`}><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold">{threat.description || threat.indicator_type}</p><p className="mt-1 font-mono text-xs opacity-70">{threat.value}</p></div><span className="rounded-full border border-current/20 px-2 py-1 text-[10px] font-bold uppercase tracking-wider">{severity}</span></div><p className="mt-3 text-[11px] uppercase tracking-wider opacity-50">{threat.source || "security signal"}</p></article>;
}
