import React, { useState } from "react";
import { api, getApiError } from "../lib/api";

const spamDemoForm = {
  sender: "security-alert@account-review.example",
  recipient: "demo@example.com",
  subject: "URGENT: Verify your account immediately",
  body: "Your account will be suspended today. Click http://198.51.100.24/verify and enter your password to keep access.",
  headers: "Authentication-Results: mx.example; spf=fail; dkim=fail; dmarc=fail",
};
const spamDemoResult = {
  classification: "PHISHING",
  security_type: "UNSAFE",
  risk_score: 96,
  confidence: 0.98,
  text_score: 92,
  url_score: 98,
  header_score: 95,
  analyzed_urls: ["http://198.51.100.24/verify"],
  model_version: "controlled-demo-v1",
  summary: "This controlled demo email shows multiple phishing indicators.",
  reasons: [
    "Urgent account language pressures the recipient to act immediately.",
    "The message requests a password after directing the recipient to a link.",
    "The URL uses an IP address and plain HTTP instead of a trusted domain.",
    "The supplied demo headers show SPF, DKIM, and DMARC failures.",
  ],
  recommended_actions: [
    "Do not click the suspicious link.",
    "Do not submit credentials.",
    "Verify the sender through an independent official channel.",
  ],
  isDemo: true,
};
const tones = {
  SAFE: "border-emerald-400/30 bg-emerald-400/10 text-emerald-100",
  LOW_RISK: "border-cyan-400/30 bg-cyan-400/10 text-cyan-100",
  SUSPICIOUS: "border-amber-400/30 bg-amber-400/10 text-amber-100",
  PHISHING: "border-rose-400/30 bg-rose-400/10 text-rose-100",
};

export default function PublicEmailVerifier() {
  const [form, setForm] = useState(spamDemoForm);
  const [result, setResult] = useState(null);
  const [demoLoaded, setDemoLoaded] = useState(true);
  const [state, setState] = useState({ loading: false, error: "" });

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setResult(null);
    setDemoLoaded(false);
    setState({ loading: false, error: "" });
  }

  function loadSpamDemo() {
    setForm(spamDemoForm);
    setResult(null);
    setDemoLoaded(true);
    setState({ loading: false, error: "" });
  }

  async function submit(event) {
    event.preventDefault();
    setResult(null);
    setState({ loading: true, error: "" });
    const rawHeaders = form.headers.split("\n").map((line) => {
      const separator = line.indexOf(":");
      return separator > 0 ? { name: line.slice(0, separator).trim(), value: line.slice(separator + 1).trim() } : null;
    }).filter((header) => header?.name && header?.value);

    try {
      const { data } = await api.post("/api/public/analysis", {
        sender: form.sender.trim(),
        recipients: [form.recipient.trim()],
        subject: form.subject.trim() || null,
        body_text: form.body.trim(),
        raw_headers: rawHeaders,
      });
      setResult(data);
      setState({ loading: false, error: "" });
    } catch (error) {
      if (demoLoaded) {
        setResult(spamDemoResult);
        setState({ loading: false, error: "" });
      } else {
        setState({ loading: false, error: getApiError(error, "The verification service is unavailable right now.") });
      }
    }
  }

  return <section id="verify" className="border-y border-emerald-300/10 bg-emerald-300/[0.03]">
    <div className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:px-10 lg:py-28">
      <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-300">Public email check</p>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Verify a message before you trust it.</h2>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-400">Paste a controlled test email and receive an evidence-based safety feedback report. Public checks are analyzed without being saved to an account.</p>
          <p className="mt-6 text-xs leading-5 text-slate-600">Do not submit passwords, private correspondence, or other sensitive content. URLs are analyzed as strings and never visited.</p>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl shadow-emerald-950/20 sm:p-7">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-amber-300/20 bg-amber-300/5 px-4 py-3"><div><p className="text-xs font-semibold text-amber-100">Need a quick demo?</p><p className="mt-1 text-xs text-amber-100/60">Load a safe, controlled spam-style example.</p></div><button type="button" onClick={loadSpamDemo} className="rounded-lg border border-amber-300/30 px-3 py-2 text-xs font-semibold text-amber-100 transition hover:bg-amber-300/10">Load spam demo</button></div>
          {demoLoaded ? <p className="mb-5 rounded-xl border border-cyan-300/20 bg-cyan-300/5 px-4 py-3 text-xs leading-5 text-cyan-100" role="status">Demo email loaded. Review the filled fields, then click <strong>Verify this email</strong> to send it through the real backend analyzer.</p> : null}
          <form onSubmit={submit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Sender" value={form.sender} onChange={(event) => update("sender", event.target.value)} placeholder="sender@example.com" type="email" required />
              <Field label="Recipient" value={form.recipient} onChange={(event) => update("recipient", event.target.value)} placeholder="you@example.com" type="email" required />
            </div>
            <Field label="Subject" value={form.subject} onChange={(event) => update("subject", event.target.value)} placeholder="Account verification notice" />
            <label className="block"><span className="mb-2 block text-sm font-medium text-slate-200">Email body <span className="text-rose-300">*</span></span><textarea required value={form.body} onChange={(event) => update("body", event.target.value)} rows="6" placeholder="Paste the email body here..." className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-600 focus:border-emerald-300/60 focus:ring-2 focus:ring-emerald-300/10" /></label>
            <label className="block"><span className="mb-2 block text-sm font-medium text-slate-200">Optional headers</span><textarea value={form.headers} onChange={(event) => update("headers", event.target.value)} rows="3" placeholder="Authentication-Results: mx.example; spf=pass" className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3 font-mono text-xs leading-5 text-slate-300 outline-none placeholder:text-slate-600 focus:border-emerald-300/60 focus:ring-2 focus:ring-emerald-300/10" /></label>
            {state.error ? <p role="alert" className="rounded-xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{state.error}</p> : null}
            <button type="submit" disabled={state.loading} className="inline-flex w-full items-center justify-center rounded-xl bg-emerald-300 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-200 disabled:cursor-wait disabled:opacity-60">{state.loading ? "Checking email…" : "Verify this email"}</button>
          </form>
          {result ? <Feedback result={result} /> : null}
        </div>
      </div>
    </div>
  </section>;
}

function Field({ label, ...props }) {
  return <label className="block"><span className="mb-2 block text-sm font-medium text-slate-200">{label}{props.required ? <span className="text-rose-300"> *</span> : null}</span><input className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm text-slate-100 outline-none placeholder:text-slate-600 focus:border-emerald-300/60 focus:ring-2 focus:ring-emerald-300/10" {...props} /></label>;
}

function Feedback({ result }) {
  const tone = tones[result.classification] || tones.LOW_RISK;
  return <div className={`mt-6 rounded-2xl border p-5 ${tone}`} aria-live="polite">
    {result.isDemo ? <p className="mb-4 rounded-lg border border-cyan-200/20 bg-cyan-200/10 px-3 py-2 text-xs leading-5 text-cyan-100">Controlled demo output shown because the live backend is unavailable. No URL was visited and no email was sent.</p> : null}
    <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-[0.18em] opacity-70">Verification feedback</p><p className="mt-2 text-xl font-semibold">{formatSecurityType(result.security_type)}</p><p className="mt-1 text-xs opacity-70">Classification: {result.classification.replace("_", " ")}</p></div><p className="text-right text-sm font-semibold">Risk {Math.round(result.risk_score)}/100<br /><span className="text-xs opacity-70">{Math.round(result.confidence * 100)}% confidence</span></p></div>
    <p className="mt-4 text-sm leading-6 opacity-90">{result.summary}</p>
    {result.reasons?.length ? <div className="mt-4"><p className="text-xs font-bold uppercase tracking-[0.14em] opacity-70">Why</p><ul className="mt-2 space-y-1 text-sm">{result.reasons.slice(0, 5).map((reason) => <li key={reason}>• {reason}</li>)}</ul></div> : null}
    {result.recommended_actions?.length ? <div className="mt-4"><p className="text-xs font-bold uppercase tracking-[0.14em] opacity-70">Recommended action</p><ul className="mt-2 space-y-1 text-sm">{result.recommended_actions.slice(0, 4).map((action) => <li key={action}>✓ {action}</li>)}</ul></div> : null}
  </div>;
}

function formatSecurityType(value) {
  return String(value || "UNKNOWN").replaceAll("_", " ");
}

