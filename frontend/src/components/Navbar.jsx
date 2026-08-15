import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button, ShieldIcon } from "./common";

export default function Navbar({ onMenuClick }) {
  const { user, logout } = useAuth();
  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button type="button" onClick={onMenuClick} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden" aria-label="Open navigation menu">
            <svg aria-hidden="true" className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" /></svg>
          </button>
          <Link to="/dashboard" className="flex items-center gap-2.5 text-sm font-bold tracking-tight text-white">
            <span className="rounded-lg bg-cyan-400/10 p-1.5 text-cyan-300 ring-1 ring-cyan-300/20"><ShieldIcon className="h-6 w-6" /></span>
            <span>PhishZero</span>
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-xs font-medium text-slate-200">{user?.display_name || user?.email}</p>
            <p className="text-[11px] text-emerald-300">Protected workspace</p>
          </div>
          <Button variant="secondary" className="px-3 py-2 text-xs" onClick={logout}>Sign out</Button>
        </div>
      </div>
    </header>
  );
}
