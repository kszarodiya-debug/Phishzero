import React from "react";

const GITHUB_URL = "https://github.com/kszarodiya-debug/Phishzero";

const features = [
  {
    eyebrow: "01 / TEXT INTELLIGENCE",
    title: "Read the message, not just the subject line.",
    body: "TF-IDF and Logistic Regression surface spam-like language, urgency, credential requests, and other social-engineering signals.",
    icon: "scan",
  },
  {
    eyebrow: "02 / URL ANALYSIS",
    title: "Inspect links without opening them.",
    body: "URLs are scored from their strings alone using hostname, path, IP, shortening, and suspicious-character features.",
    icon: "link",
  },
  {
    eyebrow: "03 / TRUST SIGNALS",
    title: "Make header evidence visible.",
    body: "SPF, DKIM, DMARC, From, Reply-To, and Return-Path signals are compared to expose inconsistencies in the message path.",
    icon: "shield",
  },
];

const protections = [
  "Attachments are never executed or opened automatically.",
  "URLs are never visited, crawled, or submitted credentials to.",
  "Email HTML is treated as untrusted data; JavaScript is never executed.",
  "Explanations are generated only from evidence actually found.",
];

function Icon({ name, className = "h-5 w-5" }) {
  const paths = {
    arrow: <path d="M5 12h13m-6-6 6 6-6 6" />,
    check: <path d="m5 12 4 4L19 6" />,
    link: <><path d="M10 13a5 5 0 0 0 7.07.07l1.41-1.41a5 5 0 0 0-7.07-7.07L10.6 5.4" /><path d="M14 11a5 5 0 0 0-7.07-.07L5.52 12.34a5 5 0 0 0 7.07 7.07l.81-.81" /></>,
    scan: <><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3" /><path d="m9 12 2 2 4-4" /></>,
    shield: <path d="M12 3 5 6v5c0 4.55 2.99 8.39 7 9.7 4.01-1.31 7-5.15 7-9.7V6l-7-3Zm-3 9 2 2 4-4" />,
    spark: <><path d="m12 3 1.6 5.4L19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6L12 3Z" /><path d="m19 16 .7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7L19 16Z" /></>,
  };

  return <svg aria-hidden="true" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

function Logo() {
  return <span className="flex items-center gap-3 text-sm font-bold tracking-tight text-white"><span className="grid h-9 w-9 place-items-center rounded-xl bg-cyan-300 text-slate-950 shadow-lg shadow-cyan-500/20"><Icon name="shield" className="h-5 w-5" /></span><span>Phish<span className="text-cyan-300">Zero</span></span></span>;
}

export default function Showcase() {
  return <div className="min-h-screen overflow-hidden bg-slate-950 text-slate-100">
    <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-xl">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-5 sm:px-8 lg:px-10">
        <a href="#top" aria-label="PhishZero home"><Logo /></a>
        <nav className="hidden items-center gap-8 text-sm text-slate-400 md:flex" aria-label="Primary navigation">
          <a className="transition hover:text-white" href="#capabilities">Capabilities</a>
          <a className="transition hover:text-white" href="#workflow">How it works</a>
          <a className="transition hover:text-white" href="#security">Security</a>
        </nav>
        <a className="inline-flex items-center gap-2 rounded-full border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:border-cyan-300/50 hover:text-cyan-200" href={GITHUB_URL} target="_blank" rel="noreferrer">View project <Icon name="arrow" className="h-4 w-4" /></a>
      </div>
    </header>

    <main id="top">
      <section className="relative isolate border-b border-slate-800/80 bg-grid">
        <div className="absolute inset-x-0 top-0 -z-10 h-96 bg-[radial-gradient(ellipse_at_top,rgba(34,211,238,0.16),transparent_65%)]" />
        <div className="mx-auto grid max-w-7xl gap-16 px-5 pb-24 pt-20 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:px-10 lg:pb-32 lg:pt-28">
          <div>
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/5 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200"><span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,0.9)]" /> Defensive email intelligence</div>
            <h1 className="max-w-3xl text-5xl font-semibold leading-[1.05] tracking-[-0.04em] text-white sm:text-6xl lg:text-7xl">See the signal behind the <span className="text-cyan-300">suspicion.</span></h1>
            <p className="mt-7 max-w-xl text-base leading-8 text-slate-400 sm:text-lg">PhishZero turns suspicious email into an evidence-led security brief—combining text, URL, and header signals without opening what you should not trust.</p>
            <div className="mt-9 flex flex-wrap gap-3">
              <a className="inline-flex items-center gap-2 rounded-full bg-cyan-300 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-200" href="#workflow">Explore the detection flow <Icon name="arrow" className="h-4 w-4" /></a>
              <a className="inline-flex items-center gap-2 rounded-full border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900" href="#security">Built defensively <Icon name="shield" className="h-4 w-4" /></a>
            </div>
            <div className="mt-14 grid max-w-lg grid-cols-3 gap-5 border-t border-slate-800 pt-6">
              <div><p className="text-2xl font-semibold text-white">03</p><p className="mt-1 text-xs leading-5 text-slate-500">signal families</p></div>
              <div><p className="text-2xl font-semibold text-white">0</p><p className="mt-1 text-xs leading-5 text-slate-500">URLs visited</p></div>
              <div><p className="text-2xl font-semibold text-white">100%</p><p className="mt-1 text-xs leading-5 text-slate-500">evidence-led</p></div>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-lg lg:ml-auto">
            <div className="absolute -inset-8 rounded-[3rem] bg-cyan-400/10 blur-3xl" />
            <div className="relative rounded-[2rem] border border-slate-700 bg-slate-900/90 p-5 shadow-2xl shadow-cyan-950/40 sm:p-7">
              <div className="flex items-center justify-between border-b border-slate-800 pb-5"><div><p className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300">System blueprint</p><p className="mt-2 text-sm font-semibold text-white">Evidence-led analysis</p></div><span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-200">Passive only</span></div>
              <div className="mt-7 space-y-5">
                {[['Text intelligence', 'Social language & intent', '72%', 'bg-violet-300'], ['URL analysis', 'Structure & destination clues', '54%', 'bg-cyan-300'], ['Header signals', 'SPF / DKIM / DMARC', '38%', 'bg-emerald-300']].map(([label, description, width, color]) => <div key={label}><div className="flex items-end justify-between gap-3"><div><p className="text-sm font-medium text-slate-200">{label}</p><p className="mt-1 text-xs text-slate-500">{description}</p></div><span className="font-mono text-xs text-slate-400">signal</span></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800"><div className={`h-full rounded-full ${color}`} style={{ width }} /></div></div>)}
              </div>
              <div className="mt-8 grid grid-cols-2 gap-3"><div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4"><p className="text-xs text-slate-500">Decision layer</p><p className="mt-2 text-lg font-semibold text-white">Risk + reasons</p></div><div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4"><p className="text-xs text-slate-500">Safety boundary</p><p className="mt-2 text-lg font-semibold text-white">No outbound fetch</p></div></div>
              <div className="mt-5 flex items-center gap-2 text-xs text-slate-500"><Icon name="check" className="h-4 w-4 text-emerald-300" /> Attachments remain metadata. Links remain strings.</div>
            </div>
          </div>
        </div>
      </section>

      <section id="capabilities" className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:px-10 lg:py-32">
        <div className="max-w-2xl"><p className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-300">One message. Multiple signals.</p><h2 className="mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">A clearer way to review risky email.</h2><p className="mt-5 text-base leading-7 text-slate-400">PhishZero keeps the analyst in control while bringing the most useful defensive checks into one readable result.</p></div>
        <div className="mt-14 grid gap-5 lg:grid-cols-3">{features.map((feature) => <article key={feature.title} className="group rounded-3xl border border-slate-800 bg-slate-900/50 p-6 transition hover:-translate-y-1 hover:border-cyan-300/30 hover:bg-slate-900"><div className="flex items-center justify-between"><span className="grid h-11 w-11 place-items-center rounded-2xl bg-cyan-300/10 text-cyan-300 ring-1 ring-cyan-300/20"><Icon name={feature.icon} className="h-5 w-5" /></span><span className="text-[10px] font-bold tracking-[0.16em] text-slate-600">{feature.eyebrow}</span></div><h3 className="mt-8 text-xl font-semibold leading-7 text-white">{feature.title}</h3><p className="mt-4 text-sm leading-7 text-slate-400">{feature.body}</p><div className="mt-8 flex items-center gap-2 text-xs font-semibold text-cyan-300 opacity-0 transition group-hover:opacity-100">Evidence first <Icon name="arrow" className="h-4 w-4" /></div></article>)}</div>
      </section>

      <section id="workflow" className="border-y border-slate-800/80 bg-slate-900/30">
        <div className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:px-10 lg:py-32"><div className="grid gap-14 lg:grid-cols-[0.8fr_1.2fr] lg:items-start"><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-300">How it works</p><h2 className="mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">From raw email to a security brief.</h2><p className="mt-5 text-base leading-7 text-slate-400">The pipeline is designed to make a suspicious message understandable without increasing the blast radius.</p></div><div className="space-y-4">{[['01', 'Ingest safely', 'Manual fields or an .eml file are parsed as untrusted data. Attachment metadata is recorded without opening the file.'], ['02', 'Analyze passively', 'Text, URL strings, and available authentication headers are evaluated locally. No destination is visited.'], ['03', 'Explain the result', 'Weighted risk signals become a classification, confidence, evidence list, and practical next actions.']].map(([number, title, body]) => <div key={number} className="grid gap-4 rounded-2xl border border-slate-800 bg-slate-950/60 p-5 sm:grid-cols-[3.5rem_1fr] sm:items-start"><span className="font-mono text-sm text-cyan-300">{number}</span><div><h3 className="text-base font-semibold text-white">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-400">{body}</p></div></div>)}</div></div></div>
      </section>

      <section id="security" className="mx-auto max-w-7xl px-5 py-24 sm:px-8 lg:px-10 lg:py-32"><div className="grid gap-12 lg:grid-cols-[1fr_0.9fr] lg:items-center"><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-300">Defensive by design</p><h2 className="mt-4 max-w-xl text-3xl font-semibold tracking-tight text-white sm:text-4xl">The safest analysis is the one that does not open another door.</h2><div className="mt-8 space-y-4">{protections.map((protection) => <div key={protection} className="flex gap-3 text-sm leading-6 text-slate-300"><span className="mt-1 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-emerald-300/10 text-emerald-300"><Icon name="check" className="h-3.5 w-3.5" /></span>{protection}</div>)}</div></div><div className="rounded-[2rem] border border-emerald-300/15 bg-emerald-300/5 p-7"><div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-300/10 text-emerald-300"><Icon name="spark" className="h-5 w-5" /></span><div><p className="text-sm font-semibold text-emerald-100">Authorized research only</p><p className="mt-1 text-xs text-emerald-100/60">Built for controlled defensive testing.</p></div></div><p className="mt-8 text-2xl font-semibold leading-9 text-white">Understand the threat before it becomes an incident.</p><p className="mt-4 text-sm leading-7 text-emerald-50/60">PhishZero is an AI-assisted research project, not a replacement for a security team or a verdict on its own.</p></div></div></section>

      <section id="architecture" className="border-t border-slate-800/80 bg-slate-900/30"><div className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:px-10"><div className="flex flex-col justify-between gap-8 sm:flex-row sm:items-end"><div><p className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-300">Built for the hackathon floor</p><h2 className="mt-4 text-3xl font-semibold tracking-tight text-white">A focused security story, backed by a real pipeline.</h2></div><a className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-300 hover:text-cyan-200" href={GITHUB_URL} target="_blank" rel="noreferrer">Inspect the source <Icon name="arrow" className="h-4 w-4" /></a></div><div className="mt-12 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4"><div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5"><p className="text-slate-500">Frontend</p><p className="mt-2 font-semibold text-white">React · Vite · Tailwind</p></div><div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5"><p className="text-slate-500">Backend</p><p className="mt-2 font-semibold text-white">FastAPI · SQLAlchemy</p></div><div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5"><p className="text-slate-500">ML layer</p><p className="mt-2 font-semibold text-white">TF-IDF · Random Forest</p></div><div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-5"><p className="text-slate-500">Decision</p><p className="mt-2 font-semibold text-white">Risk + explanations</p></div></div></div></section>
    </main>

    <footer className="border-t border-slate-800/80"><div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-8 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-8 lg:px-10"><div><Logo /><p className="mt-3 max-w-sm leading-5">AI-powered email spam and phishing detection for defensive cybersecurity research.</p></div><div className="sm:text-right"><p>Project Owner</p><p className="mt-1 font-semibold text-slate-300">Kunal S. Zarodiya</p><a className="mt-3 inline-block text-cyan-300 hover:text-cyan-200" href={GITHUB_URL} target="_blank" rel="noreferrer">github.com/kszarodiya-debug/Phishzero</a></div></div></footer>
  </div>;
}
