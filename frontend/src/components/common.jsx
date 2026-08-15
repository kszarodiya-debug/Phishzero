import React from "react";

export function ShieldIcon({ className = "h-6 w-6" }) {
  return (
    <svg aria-hidden="true" className={className} viewBox="0 0 32 32" fill="none">
      <path d="M16 3.5 26 7v7.7c0 6.1-4.1 11.3-10 13.8-5.9-2.5-10-7.7-10-13.8V7l10-3.5Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="m11.5 16 3 3 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Spinner({ label = "Loading" }) {
  return <span className="inline-flex items-center gap-2" aria-live="polite"><span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />{label}</span>;
}

export function LoadingState({ label = "Loading workspace" }) {
  return <div className="flex min-h-[42vh] items-center justify-center text-cyan-300"><Spinner label={label} /></div>;
}

export function ErrorState({ title = "Something went wrong", message, action }) {
  return <div className="mx-auto flex min-h-[42vh] max-w-xl flex-col items-center justify-center text-center"><div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-rose-400/20 bg-rose-400/10 text-rose-200" aria-hidden="true">!</div><h2 className="mt-5 text-lg font-semibold text-white">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-500">{message || "Please try again."}</p>{action ? <div className="mt-5">{action}</div> : null}</div>;
}

export function Alert({ children, tone = "error" }) {
  const tones = {
    error: "border-rose-400/20 bg-rose-400/10 text-rose-200",
    info: "border-cyan-400/20 bg-cyan-400/10 text-cyan-100",
    success: "border-emerald-400/20 bg-emerald-400/10 text-emerald-100",
  };
  return <div role="alert" className={`rounded-xl border px-4 py-3 text-sm ${tones[tone] || tones.error}`}>{children}</div>;
}

export function EmptyState({ title, message, action }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/50 px-6 py-12 text-center">
      <p className="text-base font-semibold text-slate-200">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">{message}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function Button({ children, variant = "primary", className = "", ...props }) {
  const styles = {
    primary: "bg-cyan-300 text-slate-950 hover:bg-cyan-200 focus-visible:ring-cyan-300",
    secondary: "border border-slate-700 bg-slate-900 text-slate-200 hover:border-slate-500 hover:bg-slate-800 focus-visible:ring-slate-400",
    danger: "border border-rose-400/30 bg-rose-400/10 text-rose-200 hover:bg-rose-400/20 focus-visible:ring-rose-300",
  };
  return <button className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant] || styles.primary} ${className}`} {...props}>{children}</button>;
}
