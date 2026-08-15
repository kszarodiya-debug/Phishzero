import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AnalysisResult from "../components/AnalysisResult";
import { Button, ErrorState, LoadingState } from "../components/common";
import { api, getApiError } from "../lib/api";

export default function Results() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [state, setState] = useState({ loading: true, error: "" });

  useEffect(() => {
    let active = true;
    setState({ loading: true, error: "" });
    api.get(`/api/analysis/${id}`).then(({ data }) => {
      if (active) setAnalysis(data);
    }).catch((error) => {
      if (active) setState({ loading: false, error: getApiError(error, "This analysis could not be loaded.") });
    }).finally(() => {
      if (active) setState((current) => ({ ...current, loading: false }));
    });
    return () => { active = false; };
  }, [id]);

  if (state.loading) return <LoadingState label="Loading analysis result" />;
  if (state.error || !analysis) return <ErrorState title="Analysis unavailable" message={state.error || "Analysis not found."} action={<Link to="/history"><Button variant="secondary">Back to history</Button></Link>} />;
  return <div className="space-y-5"><div className="flex flex-wrap items-center justify-between gap-3"><Link to="/history" className="text-sm font-medium text-slate-500 hover:text-cyan-300">← Back to history</Link><Link to="/analyze"><Button variant="secondary">Analyze another</Button></Link></div><AnalysisResult analysis={analysis} /></div>;
}
