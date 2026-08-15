import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Alert, Button, Spinner } from "../components/common";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, authError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  async function submit(event) { event.preventDefault(); setError(""); setLoading(true); try { await login(form.email, form.password); navigate(location.state?.from || "/dashboard", { replace: true }); } catch (err) { setError(err.message); } finally { setLoading(false); } }
  return <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl shadow-cyan-950/20 sm:p-8"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Welcome back</p><h1 className="mt-3 text-2xl font-semibold text-white">Sign in to your console</h1><p className="mt-2 text-sm leading-6 text-slate-500">Review email signals in your protected workspace.</p></div>{error || authError ? <div className="mt-6"><Alert>{error || authError}</Alert></div> : null}<form onSubmit={submit} className="mt-7 space-y-5"><label className="block"><span className="mb-2 block text-sm font-medium text-slate-200">Email</span><input type="email" required autoComplete="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-300/60 focus:ring-2 focus:ring-cyan-300/10" /></label><label className="block"><span className="mb-2 block text-sm font-medium text-slate-200">Password</span><input type="password" required autoComplete="current-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-300/60 focus:ring-2 focus:ring-cyan-300/10" /></label><Button type="submit" className="w-full" disabled={loading}>{loading ? <Spinner label="Signing in" /> : "Sign in"}</Button></form><p className="mt-7 text-center text-sm text-slate-500">New to PhishZero? <Link className="font-semibold text-cyan-300 hover:text-cyan-200" to="/register">Create an account</Link></p></section>;
}
