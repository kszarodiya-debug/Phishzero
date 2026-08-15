import React from "react";

export default function SecurityChart({ scores = {} }) {
  const items = [["Text model", scores.text], ["URL model", scores.url], ["Header signals", scores.headers], ["Domain signals", scores.domain_security], ["Social engineering", scores.social_engineering]].filter(([, value]) => value != null && Number.isFinite(Number(value)));
  if (!items.length) return <p className="text-sm text-slate-500">No component scores were returned.</p>;
  return <div className="space-y-4">{items.map(([label, value]) => { const numeric = Math.max(0, Math.min(100, Number(value))); return <div key={label}><div className="mb-1.5 flex justify-between text-xs"><span className="text-slate-400">{label}</span><span className="font-medium text-slate-300">{Math.round(numeric)}/100</span></div><div className="h-2 overflow-hidden rounded-full bg-slate-800"><div className={`h-full rounded-full ${barColor(numeric)}`} style={{ width: `${numeric}%` }} /></div></div>; })}</div>;
}

function barColor(value) {
  if (value >= 76) return "bg-rose-300";
  if (value >= 51) return "bg-amber-300";
  if (value >= 26) return "bg-cyan-300";
  return "bg-emerald-300";
}
