import React from "react";
import { riskStyle } from "./RiskScore";

export default function StatusBadge({ classification, size = "md" }) {
  const style = riskStyle(classification);
  const sizes = {
    sm: "px-2 py-1 text-[10px]",
    md: "px-2.5 py-1.5 text-[11px]",
  };
  return <span className={`inline-flex items-center gap-1.5 rounded-full border border-current/15 bg-slate-950/80 font-bold uppercase tracking-[0.12em] ${style.tone} ${sizes[size] || sizes.md}`}><span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />{style.label}</span>;
}
