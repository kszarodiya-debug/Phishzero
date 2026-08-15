import React from "react";
import { formatClassification } from "../lib/analysis-utils";
import { riskStyle } from "./RiskScore";

const order = ["SAFE", "LOW_RISK", "SUSPICIOUS", "PHISHING"];

export default function ClassificationChart({ distribution = {}, total = 0 }) {
  return <div className="space-y-4" aria-label="Classification distribution">
    {order.map((classification) => {
      const count = Number(distribution[classification]) || 0;
      const percentage = total ? (count / total) * 100 : 0;
      const style = riskStyle(classification);
      return <div key={classification}>
        <div className="mb-1.5 flex items-center justify-between gap-3 text-xs"><span className={`font-medium ${style.tone}`}>{formatClassification(classification)}</span><span className="text-slate-500">{count} <span className="text-slate-700">({Math.round(percentage)}%)</span></span></div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-800" role="progressbar" aria-label={`${formatClassification(classification)} analyses`} aria-valuenow={count} aria-valuemin="0" aria-valuemax={Math.max(total, 1)}><div className={`h-full rounded-full ${barColor(classification)}`} style={{ width: `${percentage}%` }} /></div>
      </div>;
    })}
  </div>;
}

function barColor(classification) {
  return { SAFE: "bg-emerald-300", LOW_RISK: "bg-cyan-300", SUSPICIOUS: "bg-amber-300", PHISHING: "bg-rose-300" }[classification] || "bg-slate-400";
}
