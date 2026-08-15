import React, { useRef, useState } from "react";
import { Alert, Button } from "./common";

const MAX_EML_BYTES = 5 * 1024 * 1024;
const initialForm = { sender: "", recipients: "", subject: "", body_text: "", raw_headers: "" };

export default function EmailInput({ onSubmit, onUpload, submitting = false, uploading = false }) {
  const [form, setForm] = useState(initialForm);
  const [mode, setMode] = useState("manual");
  const [error, setError] = useState("");
  const [uploadMessage, setUploadMessage] = useState("");
  const fileInputRef = useRef(null);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setError("");
  }

  function submit(event) {
    event.preventDefault();
    setError("");
    const recipients = form.recipients.split(/[;,\n]/).map((item) => item.trim()).filter(Boolean);
    const invalidRecipient = recipients.find((recipient) => !isEmail(recipient));
    if (!isEmail(form.sender.trim())) {
      setError("Enter a valid sender email address.");
      return;
    }
    if (!recipients.length || invalidRecipient) {
      setError("Enter at least one valid recipient email address.");
      return;
    }
    if (!form.body_text.trim()) {
      setError("Add the plain-text email body before analyzing.");
      return;
    }
    const rawHeaders = form.raw_headers.split("\n").map((line) => {
      const separator = line.indexOf(":");
      return separator > 0 ? { name: line.slice(0, separator).trim(), value: line.slice(separator + 1).trim() } : null;
    }).filter((header) => header?.name && !/[\r\n]/.test(header.value));
    onSubmit({ sender: form.sender.trim(), recipients, subject: form.subject.trim() || null, body_text: form.body_text, raw_headers: rawHeaders });
  }

  async function upload(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setError("");
    setUploadMessage("");
    if (!file.name.toLowerCase().endsWith(".eml")) {
      setError("Choose an .eml file.");
      return;
    }
    if (file.size > MAX_EML_BYTES) {
      setError("The .eml file must be 5 MB or smaller.");
      return;
    }
    if (!onUpload) {
      setError("Raw .eml upload is not available in this workspace.");
      return;
    }
    try {
      const parsed = await onUpload(file);
      setForm({
        sender: parsed.sender || "",
        recipients: Array.isArray(parsed.recipients) ? parsed.recipients.join(", ") : "",
        subject: parsed.subject || "",
        body_text: parsed.body_text || "",
        raw_headers: Array.isArray(parsed.raw_headers) ? parsed.raw_headers.map((header) => `${header.name}: ${header.value}`).join("\n") : "",
      });
      setMode("manual");
      setUploadMessage("Email parsed safely. Review the extracted fields, then run the analysis.");
    } catch (uploadError) {
      setError(uploadError.message || "The .eml file could not be parsed.");
    }
  }

  return <div className="space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4"><div><h2 className="text-sm font-semibold text-white">Email source</h2><p className="mt-1 text-xs text-slate-500">Use structured fields or safely parse a raw message.</p></div><div className="inline-flex rounded-lg border border-slate-700 bg-slate-950/70 p-1" role="tablist" aria-label="Email input mode"><button type="button" role="tab" aria-selected={mode === "manual"} onClick={() => setMode("manual")} className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${mode === "manual" ? "bg-cyan-300 text-slate-950" : "text-slate-400 hover:text-slate-200"}`}>Manual input</button><button type="button" role="tab" aria-selected={mode === "upload"} onClick={() => setMode("upload")} className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${mode === "upload" ? "bg-cyan-300 text-slate-950" : "text-slate-400 hover:text-slate-200"}`}>Upload .eml</button></div></div>
    {uploadMessage ? <Alert tone="success">{uploadMessage}</Alert> : null}
    {mode === "upload" ? <UploadPanel onChange={upload} uploading={uploading} fileInputRef={fileInputRef} /> : null}
    {mode === "manual" ? <form onSubmit={submit} className="space-y-6">
      <div className="grid gap-5 sm:grid-cols-2"><Field label="Sender" htmlFor="sender" type="email" value={form.sender} onChange={(event) => update("sender", event.target.value)} placeholder="sender@example.com" required /><Field label="Recipients" htmlFor="recipients" value={form.recipients} onChange={(event) => update("recipients", event.target.value)} placeholder="analyst@example.com, team@example.com" hint="Separate multiple addresses with commas." required /></div>
      <Field label="Subject" htmlFor="subject" value={form.subject} onChange={(event) => update("subject", event.target.value)} placeholder="Account verification notice" />
      <div><label htmlFor="body_text" className="mb-2 block text-sm font-medium text-slate-200">Plain-text body <span className="text-rose-300">*</span></label><textarea id="body_text" value={form.body_text} onChange={(event) => update("body_text", event.target.value)} rows="10" required className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-cyan-300/60 focus:ring-2 focus:ring-cyan-300/10" placeholder="Paste the email body here. URLs are analyzed as text only." /></div>
      <div><label htmlFor="raw_headers" className="mb-2 block text-sm font-medium text-slate-200">Optional raw headers</label><textarea id="raw_headers" value={form.raw_headers} onChange={(event) => update("raw_headers", event.target.value)} rows="5" className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 font-mono text-xs leading-5 text-slate-300 outline-none transition placeholder:text-slate-600 focus:border-cyan-300/60 focus:ring-2 focus:ring-cyan-300/10" placeholder={"From: sender@example.com\nReply-To: reply@example.net\nAuthentication-Results: mx.example; spf=pass"} /><p className="mt-2 text-xs text-slate-600">One header per line. Header values are analyzed defensively and never sent anywhere else.</p></div>
      {error ? <p role="alert" className="text-sm text-rose-300">{error}</p> : null}
      <div className="flex flex-col-reverse justify-end gap-3 sm:flex-row"><Button type="button" variant="secondary" onClick={() => { setForm(initialForm); setError(""); setUploadMessage(""); }}>Clear fields</Button><Button type="submit" disabled={submitting}>{submitting ? "Analyzing email…" : "Analyze email"}</Button></div>
    </form> : null}
    {mode === "upload" && error ? <p role="alert" className="text-sm text-rose-300">{error}</p> : null}
  </div>;
}

function UploadPanel({ onChange, uploading, fileInputRef }) {
  return <div className="rounded-2xl border border-dashed border-cyan-300/25 bg-cyan-300/[0.03] p-6 text-center"><div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-200" aria-hidden="true">↥</div><h3 className="mt-4 text-sm font-semibold text-white">Upload a raw email message</h3><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">The backend extracts message fields and attachment metadata without opening attachments or visiting URLs.</p><input ref={fileInputRef} id="eml-upload" type="file" accept=".eml,message/rfc822" onChange={onChange} className="sr-only" disabled={uploading} /><label htmlFor="eml-upload" className="mt-5 inline-flex cursor-pointer items-center rounded-xl bg-cyan-300 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200">{uploading ? "Parsing email…" : "Choose .eml file"}</label><p className="mt-3 text-xs text-slate-600">Maximum size: 5 MB · Review extracted fields before analysis.</p></div>;
}

function Field({ label, htmlFor, hint, ...props }) {
  return <div><label htmlFor={htmlFor} className="mb-2 block text-sm font-medium text-slate-200">{label}{props.required ? <span className="text-rose-300"> *</span> : null}</label><input id={htmlFor} className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-cyan-300/60 focus:ring-2 focus:ring-cyan-300/10" {...props} />{hint ? <p className="mt-2 text-xs text-slate-600">{hint}</p> : null}</div>;
}

function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}
