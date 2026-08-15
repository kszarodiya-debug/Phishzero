import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Navbar onMenuClick={() => setSidebarOpen(true)} />
      <div className="flex min-h-[calc(100vh-4rem)]">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="min-w-0 flex-1 bg-[radial-gradient(circle_at_top_right,_rgba(8,145,178,0.08),_transparent_34rem)]"><div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-10 lg:py-10"><Outlet /></div></main>
      </div>
    </div>
  );
}
