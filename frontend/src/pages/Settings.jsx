import React from "react";
import { useAuth } from "../context/AuthContext";

export default function Settings() {
  const { user } = useAuth();
  return <div className="mx-auto max-w-3xl space-y-8"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Workspace</p><h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">Settings</h1><p className="mt-2 text-sm text-slate-500">Review your account and the current analysis boundaries.</p></div><section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6"><h2 className="text-sm font-semibold text-white">Account profile</h2><dl className="mt-5 divide-y divide-slate-800/80">{[["Email", user?.email], ["Display name", user?.display_name || "Not set"], ["Member since", formatDate(user?.created_at)]].map(([label, value]) => <div key={label} className="flex flex-col gap-1 py-4 sm:flex-row sm:items-center sm:justify-between"><dt className="text-sm text-slate-500">{label}</dt><dd className="text-sm font-medium text-slate-200">{value}</dd></div>)}</dl></section><section className="rounded-2xl border border-cyan-400/15 bg-cyan-400/5 p-6"><h2 className="text-sm font-semibold text-cyan-100">Security boundaries</h2><ul className="mt-4 space-y-3 text-sm leading-6 text-cyan-50/70"><li>• Email attachments are never executed or opened automatically.</li><li>• URLs are analyzed from their strings and are never visited or crawled.</li><li>• Analysis history is scoped to your authenticated account.</li></ul></section></div>;
}

function formatDate(value) { if (!value) return "Unknown"; try { return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(value)); } catch { return "Unknown"; } }
