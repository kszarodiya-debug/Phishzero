import React from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ShieldIcon } from "./common";

const links = [
  { to: "/dashboard", label: "Overview", icon: "grid" },
  { to: "/analyze", label: "Analyze email", icon: "scan" },
  { to: "/history", label: "Analysis history", icon: "clock" },
  { to: "/settings", label: "Settings", icon: "settings" },
];

function NavIcon({ name }) {
  const paths = {
    grid: <><rect x="4" y="4" width="6" height="6" rx="1" /><rect x="14" y="4" width="6" height="6" rx="1" /><rect x="4" y="14" width="6" height="6" rx="1" /><rect x="14" y="14" width="6" height="6" rx="1" /></>,
    scan: <><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3" /><path d="m9 12 2 2 4-4" /></>,
    clock: <><circle cx="12" cy="12" r="8" /><path d="M12 8v4l2.5 2" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.7 1.7-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5v.2h-2.4v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1L8 17l.1-.1A1.7 1.7 0 0 0 8.4 15a1.7 1.7 0 0 0-1.5-1H6v-2.4h.9a1.7 1.7 0 0 0 1.5-1A1.7 1.7 0 0 0 8.1 9L8 8.9l1.7-1.7.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5v-.2h2.4v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 9l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.5 1h.2v2.4h-.2a1.7 1.7 0 0 0-1.5.6Z" /></>,
  };
  return <svg aria-hidden="true" className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

export default function Sidebar({ open, onClose }) {
  const { user } = useAuth();
  return (
    <>
      {open ? <button type="button" aria-label="Close navigation menu" onClick={onClose} className="fixed inset-0 z-40 bg-slate-950/70 lg:hidden" /> : null}
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-800 bg-slate-950 px-4 py-5 transition-transform lg:static lg:z-0 lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="mb-8 flex items-center justify-between px-2 lg:hidden"><span className="text-sm font-bold text-white">Navigation</span><button type="button" onClick={onClose} className="rounded p-1 text-slate-400 hover:text-white" aria-label="Close navigation"><span aria-hidden="true">×</span></button></div>
        <div className="hidden items-center gap-3 px-3 pb-8 lg:flex"><span className="text-cyan-300"><ShieldIcon /></span><div><p className="text-sm font-bold text-white">PhishZero</p><p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Security console</p></div></div>
        <nav aria-label="Primary navigation" className="space-y-1">
          <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-600">Workspace</p>
          {links.map((link) => <NavLink key={link.to} to={link.to} onClick={onClose} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${isActive ? "bg-cyan-300/10 text-cyan-200 ring-1 ring-cyan-300/20" : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"}`}><NavIcon name={link.icon} /><span>{link.label}</span></NavLink>)}
        </nav>
        <div className="mt-auto rounded-2xl border border-slate-800 bg-slate-900/60 p-4"><p className="text-xs font-semibold text-slate-300">Defensive by design</p><p className="mt-2 text-xs leading-5 text-slate-500">Analysis stays offline. URLs are never visited and attachments are never executed.</p><p className="mt-4 truncate text-[11px] text-slate-600">{user?.email}</p></div>
      </aside>
    </>
  );
}
