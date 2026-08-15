import React from "react";

export default function UrlTable({ urls = [] }) {
  if (!urls.length) return <p className="text-sm text-slate-500">No URLs were extracted from this email.</p>;
  return <div className="overflow-x-auto"><table className="w-full min-w-[520px] text-left text-sm"><thead className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-600"><tr><th className="px-3 py-3 font-medium">URL</th><th className="px-3 py-3 font-medium">Domain</th><th className="px-3 py-3 font-medium">Status</th></tr></thead><tbody className="divide-y divide-slate-800/80">{urls.map((url) => { let domain = "—"; try { domain = new URL(url).hostname; } catch {} return <tr key={url}><td className="max-w-sm truncate px-3 py-3 font-mono text-xs text-slate-300" title={url}>{url}</td><td className="px-3 py-3 text-slate-400">{domain}</td><td className="px-3 py-3"><span className="rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-400">Analyzed</span></td></tr>; })}</tbody></table></div>;
}
