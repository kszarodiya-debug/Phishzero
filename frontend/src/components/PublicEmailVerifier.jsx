import React, { useState } from "react";
import { api, getApiError } from "../lib/api";
import { demoEmails } from "../lib/demo-emails";
import RiskScore from "./RiskScore";
import SecurityChart from "./SecurityChart";
import ThreatCard from "./ThreatCard";

const blankForm = { sender: "", recipient: "", subject: "", body: "", url: "", headers: "" };

const spamDemoForm = {
  sender: "security-alert@account-review.example",
  recipient: "demo@example.com",
  subject: "URGENT: Verify your account immediately",
  body: "Your account will be suspended today. Click http://198.51.100.24/verify and enter your password to keep access.",
  url: "http://198.51.100.24/verify",
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
const demoOrder = ["safe", "spam", "suspicious", "phishing"];
const allDemos = { ...demoEmails, phishing: { label: "Phishing email", icon: "🔴", description: "Urgency, credentials, a raw IP URL, and failed authentication.", form: spamDemoForm, result: spamDemoResult } };

export default function PublicEmailVerifier() {
  const [form, setForm] = useState({ ...spamDemoForm });
  const [selectedDemo, setSelectedDemo] = useState("phishing");
  const [result, setResult] = useState(null);
  const [demoLoaded, setDemoLoaded] = useState(true);
  const [state, setState] = useState({ loading: false, error: "" });

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setResult(null);
    setSelectedDemo(null);
    setDemoLoaded(false);
    setState({ loading: false, error: "" });
  }

  function loadDemo(key, shouldScroll = false) {
    const demo = allDemos[key];
    setForm({ ...demo.form });
    setSelectedDemo(key);
    setResult(null);
    setDemoLoaded(true);
    setState({ loading: false, error: "" });
    if (shouldScroll) document.getElementById("verify")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function clearForm() {
    setForm({ ...blankForm });
    setSelectedDemo(null);
    setResult(null);
    setDemoLoaded(false);
    setState({ loading: false, error: "" });
  }

  async function submit(event) {
    event.preventDefault();
    setResult(null);
    setState({ loading: true, error: "" });
    const sender = form.sender.trim();
    const recipient = form.recipient.trim();
    const subject = form.subject.trim();
    const body = form.body.trim();
    const url = form.url.trim();
    if (!sender || !recipient) return setState({ loading: false, error: "Please enter both sender and recipient email addresses." });
    if (!isEmail(sender) || !isEmail(recipient)) return setState({ loading: false, error: "Please enter valid sender and recipient email addresses." });
    if (!body) return setState({ loading: false, error: "Please enter an email body before analyzing." });
    if (url && !isHttpUrl(url)) return setState({ loading: false, error: "Please enter a valid HTTP or HTTPS URL, or leave the URL field empty." });
    const rawHeaders = form.headers.split("\n").map((line) => {
      const separator = line.indexOf(":");
      return separator > 0 ? { name: line.slice(0, separator).trim(), value: line.slice(separator + 1).trim() } : null;
    }).filter((header) => header?.name && header?.value);
    const analyzedBody = url && !body.includes(url) ? `${body}\nLink supplied by sender: ${url}` : body;

    try {
      const { data } = await api.post("/api/public/analysis", {
        sender,
        recipients: [recipient],
        subject: subject || null,
        body_text: analyzedBody,
        raw_headers: rawHeaders,
      });
      setResult({ ...data, isDemo: false });
      setState({ loading: false, error: "" });
    } catch (error) {
      if (demoLoaded && selectedDemo) {
        setResult({ ...allDemos[selectedDemo].result, isDemo: true });
        setState({ loading: false, error: "" });
      } else {
        setState({ loading: false, error: getApiError(error, "The verification service is unavailable right now.") });
      }
    }
  }

  return <section id="verify" className="border-y border-emerald-300/10 bg-emerald-300/[0.03]">
    <div className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:px-10 lg:py-28">
      <div className="grid gap-10 lg:grid-cols-[0.72fr_1.28fr] lg:items-start">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-300">🔍 Email analyzer</p>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Analyze an email before you trust it.</h2>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-400">Paste a message or choose a labeled sample. PhishZero combines text, URL, sender, and authentication signals into a report a non-technical user can understand.</p>
          <div className="mt-8 space-y-3 text-sm leading-6 text-slate-300"><p>01 · Choose a safe sample or enter your own dummy message.</p><p>02 · Click <strong className="text-emerald-300">ANALYZE EMAIL</strong>.</p><p>03 · Review the score, evidence, explanation, and next action.</p></div>
          <p className="mt-8 text-xs leading-5 text-slate-600">Use only authorized, non-sensitive content. URLs are inspected as strings and never opened. Attachments are not accepted in this public demo.</p>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5 shadow-2xl shadow-emerald-950/20 sm:p-7">
          <div className="mb-6"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-200">🧪 Try demo emails</p><p className="mt-2 text-xs leading-5 text-slate-500">Fictional examples for a fast, safe hackathon presentation.</p><div className="mt-4 grid gap-2 sm:grid-cols-2">{demoOrder.map((key) => <button key={key} type="button" onClick={() => loadDemo(key, true)} className={`rounded-xl border px-3 py-3 text-left text-xs font-semibold transition hover:-translate-y-0.5 ${demoButtonClass(key)}`}><span className="block">{allDemos[key].icon} {allDemos[key].label}</span><span className="mt-1 block text-[10px] font-normal opacity-70">{allDemos[key].description}</span></button>)}</div></div>
          {demoLoaded ? <p className="mb-5 rounded-xl border border-cyan-300/20 bg-cyan-300/5 px-4 py-3 text-xs leading-5 text-cyan-100" role="status">{allDemos[selectedDemo]?.label || "Demo email"} loaded. Review the fields, then click <strong>ANALYZE EMAIL</strong>.</p> : null}
          <form onSubmit={submit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id="demo-sender" label="Sender email" value={form.sender} onChange={(event) => update("sender", event.target.value)} placeholder="sender@example.com" type="email" required />
              <Field id="demo-recipient" label="Recipient email" value={form.recipient} onChange={(event) => update("recipient", event.target.value)} placeholder="you@example.com" type="email" required />
            </div>
            <Field id="demo-subject" label="Subject" value={form.subject} onChange={(event) => update("subject", event.target.value)} placeholder="Account verification notice" />
            <label className="block"><span className="mb-2 block text-sm font-medium text-slate-200">Email body <span className="text-rose-300">*</span></span><textarea id="demo-body" required value={form.body} onChange={(event) => update("body", event.target.value)} rows="6" placeholder="Paste the email body here..." className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-600 focus:border-emerald-300/60 focus:ring-2 focus:ring-emerald-300/10" /></label>
            <Field id="demo-url" label="Optional URL / link" value={form.url} onChange={(event) => update("url", event.target.value)} placeholder="https://example.com/verify" type="url" />
            <label className="block"><span className="mb-2 block text-sm font-medium text-slate-200">Optional raw headers</span><textarea id="demo-headers" value={form.headers} onChange={(event) => update("headers", event.target.value)} rows="3" placeholder="Authentication-Results: mx.example; spf=pass" className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3 font-mono text-xs leading-5 text-slate-300 outline-none placeholder:text-slate-600 focus:border-emerald-300/60 focus:ring-2 focus:ring-emerald-300/10" /></label>
            {state.error ? <p role="alert" className="rounded-xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{state.error}</p> : null}
            <div className="flex flex-col-reverse gap-3 sm:flex-row"><button type="button" onClick={clearForm} className="inline-flex flex-1 items-center justify-center rounded-xl border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-300 transition hover:border-slate-500 hover:bg-slate-900">Clear</button><button type="submit" disabled={state.loading} className="inline-flex flex-[2] items-center justify-center rounded-xl bg-emerald-300 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-200 disabled:cursor-wait disabled:opacity-60">{state.loading ? "Analyzing…" : "ANALYZE EMAIL"}</button></div>
          </form>
          {result ? <Feedback result={result} /> : null}
        </div>
      </div>
    </div>
  </section>;
}

function Field({ id, label, ...props }) {
  return <label className="block" htmlFor={id}><span className="mb-2 block text-sm font-medium text-slate-200">{label}{props.required ? <span className="text-rose-300"> *</span> : null}</span><input id={id} className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm text-slate-100 outline-none placeholder:text-slate-600 focus:border-emerald-300/60 focus:ring-2 focus:ring-emerald-300/10" {...props} /></label>;
}

function Feedback({ result }) {
  const tone = tones[result.classification] || tones.LOW_RISK;
  const score = Math.max(0, Math.min(100, Number(result.risk_score) || 0));
  const threats = Array.isArray(result.threats) ? result.threats : [];
  return <div className={`mt-8 rounded-3xl border p-5 ${tone} sm:p-6`} aria-live="polite">
    <div className="flex flex-wrap items-start justify-between gap-5"><div><p className="text-[10px] font-bold uppercase tracking-[0.2em] opacity-70">PhishZero security report</p><p className="mt-2 text-2xl font-semibold">{formatSecurityType(result.security_type)}</p><p className="mt-1 text-xs opacity-75">Classification: {formatClassification(result.classification)} · Risk level: {riskLevel(score)}</p></div><RiskScore score={score} classification={result.classification} compact /></div>
    {result.isDemo ? <p className="mt-5 rounded-xl border border-cyan-200/20 bg-cyan-200/10 px-4 py-3 text-xs leading-5 text-cyan-100">Controlled demo output shown because the live backend is unavailable. No URL was visited and no email was sent.</p> : null}
    <div className="mt-6 grid gap-3 sm:grid-cols-3"><Metric label="Risk score" value={`${Math.round(score)}/100`} /><Metric label="Risk level" value={riskLevel(score)} /><Metric label="Confidence" value={`${Math.round((Number(result.confidence) || 0) * 100)}%`} /></div>
    <div className="mt-5"><div className="mb-2 flex justify-between text-xs opacity-75"><span>Risk meter</span><span>{Math.round(score)}%</span></div><div className="h-3 overflow-hidden rounded-full bg-slate-950/40" role="progressbar" aria-label="Risk score" aria-valuenow={Math.round(score)} aria-valuemin="0" aria-valuemax="100"><div className="h-full rounded-full bg-current transition-all" style={{ width: `${score}%` }} /></div></div>
    <div className="mt-7"><p className="text-xs font-bold uppercase tracking-[0.16em] opacity-70">Component signals</p><div className="mt-4 rounded-2xl bg-slate-950/20 p-4"><SecurityChart scores={{ text: result.text_score, url: result.url_score, headers: result.header_score, domain_security: result.domain_score, social_engineering: result.social_engineering_score }} /></div></div>
    <div className="mt-7 grid gap-5 lg:grid-cols-2"><Panel title="Detected indicators" subtitle="Evidence returned by the analysis"><div className="space-y-3">{threats.length ? threats.map((threat, index) => <ThreatCard key={`${threat.indicator_type}-${threat.value}-${index}`} threat={threat} />) : <p className="text-sm opacity-75">No specific indicators were returned.</p>}</div></Panel><Panel title="Why this result" subtitle="Plain-language explanation"><p className="text-sm leading-6 opacity-90">{result.summary}</p>{result.reasons?.length ? <ul className="mt-4 space-y-2 text-sm leading-6 opacity-85">{result.reasons.map((reason, index) => <li key={`${reason}-${index}`}>• {reason}</li>)}</ul> : null}</Panel></div>
    <Panel title="Recommended action" subtitle="What to do next"><ul className="space-y-2 text-sm leading-6 opacity-90">{result.recommended_actions?.length ? result.recommended_actions.map((action, index) => <li key={`${action}-${index}`}>✓ {action}</li>) : <li>No additional action was returned.</li>}</ul></Panel>
    {result.analyzed_urls?.length ? <div className="mt-5 rounded-2xl border border-current/10 bg-slate-950/20 p-4"><p className="text-xs font-bold uppercase tracking-[0.16em] opacity-70">Analyzed URL strings</p><p className="mt-3 break-all font-mono text-xs opacity-80">{result.analyzed_urls.join(" · ")}</p><p className="mt-2 text-[11px] opacity-60">These strings were analyzed without visiting the destinations.</p></div> : null}
    <p className="mt-5 text-[11px] opacity-60">Model: {result.model_version || "Unavailable"}. This is decision support, not a guarantee; verify suspicious messages independently.</p>
  </div>;
}

function Panel({ title, subtitle, children }) { return <section className="mt-5 rounded-2xl border border-current/10 bg-slate-950/20 p-4"><h3 className="text-sm font-semibold">{title}</h3><p className="mt-1 text-[11px] opacity-65">{subtitle}</p><div className="mt-4">{children}</div></section>; }
function Metric({ label, value }) { return <div className="rounded-xl border border-current/10 bg-slate-950/20 p-3"><p className="text-[11px] opacity-65">{label}</p><p className="mt-1 text-lg font-semibold">{value}</p></div>; }
function isEmail(value) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value); }
function isHttpUrl(value) { try { const parsed = new URL(value); return parsed.protocol === "http:" || parsed.protocol === "https:"; } catch { return false; } }
function riskLevel(score) { if (score >= 76) return "CRITICAL"; if (score >= 51) return "HIGH"; if (score >= 26) return "MEDIUM"; return "LOW"; }
function formatSecurityType(value) { return String(value || "UNKNOWN").replaceAll("_", " "); }
function formatClassification(value) { return value === "LOW_RISK" ? "SPAM / LOW RISK" : String(value || "UNKNOWN").replaceAll("_", " "); }
function demoButtonClass(key) { return { safe: "border-emerald-300/20 bg-emerald-300/5 text-emerald-100 hover:border-emerald-300/50", spam: "border-amber-300/20 bg-amber-300/5 text-amber-100 hover:border-amber-300/50", suspicious: "border-orange-300/20 bg-orange-300/5 text-orange-100 hover:border-orange-300/50", phishing: "border-rose-300/20 bg-rose-300/5 text-rose-100 hover:border-rose-300/50" }[key]; }

