import React from "react";
import { Link, Outlet } from "react-router-dom";
import { ShieldIcon } from "../components/common";

export default function AuthLayout() {
  return <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-4 py-10 text-slate-100"><div className="absolute -left-24 top-0 h-80 w-80 rounded-full bg-cyan-500/10 blur-3xl" /><div className="absolute -right-24 bottom-0 h-96 w-96 rounded-full bg-indigo-500/10 blur-3xl" /><div className="relative w-full max-w-md"><Link to="/login" className="mx-auto mb-8 flex w-fit items-center gap-3 text-sm font-bold text-white"><span className="rounded-xl bg-cyan-400/10 p-2 text-cyan-300 ring-1 ring-cyan-300/20"><ShieldIcon /></span>PhishZero</Link><Outlet /><p className="mt-8 text-center text-xs text-slate-600">Defensive cybersecurity research · URLs are never visited</p></div></main>;
}
