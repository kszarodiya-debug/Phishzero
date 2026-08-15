import React from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/common";

export default function NotFound() { return <div className="mx-auto max-w-lg py-20 text-center"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">404</p><h1 className="mt-4 text-3xl font-semibold text-white">This page is outside the console.</h1><p className="mt-3 text-sm text-slate-500">Use the navigation to return to your security workspace.</p><Link to="/dashboard" className="mt-6 inline-block"><Button>Back to overview</Button></Link></div>; }
