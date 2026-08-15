import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import EmailInput from "../components/EmailInput";
import { Alert } from "../components/common";
import { api, getApiError } from "../lib/api";

export default function Analyze() {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);

  async function submit(payload) {
    setError("");
    setSubmitting(true);
    try {
      const { data } = await api.post("/api/analysis", payload);
      navigate(`/results/${data.analysis_id}`);
    } catch (requestError) {
      setError(getApiError(requestError, "The email could not be analyzed."));
    } finally {
      setSubmitting(false);
    }
  }

  async function upload(file) {
    setError("");
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post("/api/emails", formData, { headers: { "Content-Type": "multipart/form-data" } });
      return data;
    } catch (requestError) {
      const message = getApiError(requestError, "The .eml file could not be parsed.");
      setError(message);
      throw new Error(message);
    } finally {
      setUploading(false);
    }
  }

  return <div className="mx-auto max-w-4xl space-y-8"><header><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">New analysis</p><h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">Inspect an email</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Paste message information or upload a raw .eml file. PhishZero analyzes text, headers, and URLs offline; it does not visit links or execute attachments.</p></header>{error ? <Alert>{error}</Alert> : null}<section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl shadow-cyan-950/10 sm:p-8"><EmailInput onSubmit={submit} onUpload={upload} submitting={submitting} uploading={uploading} /></section><div className="grid gap-3 text-xs text-slate-600 sm:grid-cols-3"><p className="rounded-xl border border-slate-800/80 bg-slate-950/40 px-4 py-3">01 · Validate the message fields</p><p className="rounded-xl border border-slate-800/80 bg-slate-950/40 px-4 py-3">02 · Analyze through the backend</p><p className="rounded-xl border border-slate-800/80 bg-slate-950/40 px-4 py-3">03 · Review evidence and actions</p></div></div>;
}
