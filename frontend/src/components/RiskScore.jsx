import React from "react";

const riskStyles = {
  SAFE: { label: "Safe", tone: "text-emerald-300", ring: "stroke-emerald-300", track: "stroke-emerald-300/10" },
  LOW_RISK: { label: "Low risk", tone: "text-cyan-300", ring: "stroke-cyan-300", track: "stroke-cyan-300/10" },
  SUSPICIOUS: { label: "Suspicious", tone: "text-amber-300", ring: "stroke-amber-300", track: "stroke-amber-300/10" },
  PHISHING: { label: "Phishing", tone: "text-rose-300", ring: "stroke-rose-300", track: "stroke-rose-300/10" },
};

export function riskStyle(classification) {
  return riskStyles[classification] || { label: classification || "Unknown", tone: "text-slate-300", ring: "stroke-slate-300", track: "stroke-slate-300/10" };
}

export default function RiskScore({ score = 0, classification, compact = false }) {
  const style = riskStyle(classification);
  const normalized = Math.max(0, Math.min(100, Number(score) || 0));
  const circumference = 2 * Math.PI * 48;
  return <div className={`flex items-center ${compact ? "gap-3" : "gap-7"}`}><div className={`relative ${compact ? "h-16 w-16" : "h-36 w-36"}`}><svg className="h-full w-full -rotate-90" viewBox="0 0 112 112" aria-label={`Risk score ${Math.round(normalized)} out of 100`} role="img"><circle cx="56" cy="56" r="48" fill="none" strokeWidth="8" className={style.track} /><circle cx="56" cy="56" r="48" fill="none" strokeWidth="8" strokeLinecap="round" className={style.ring} strokeDasharray={circumference} strokeDashoffset={circumference * (1 - normalized / 100)} /></svg><span className={`absolute inset-0 flex items-center justify-center font-bold ${compact ? "text-base" : "text-3xl"} ${style.tone}`}>{Math.round(normalized)}</span></div><div><p className={`font-semibold ${compact ? "text-sm" : "text-xl"} ${style.tone}`}>{style.label}</p>{!compact ? <p className="mt-1 text-sm text-slate-500">Confidence-aware risk score</p> : null}</div></div>;
}
