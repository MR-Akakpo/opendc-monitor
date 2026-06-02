Write-Host "Creating STELLARIX OpenDC Frontend..."

Set-Location "C:\Projects\opendc-monitor\platform"

if (!(Test-Path "frontend")) {
    New-Item -ItemType Directory -Force -Path "frontend" | Out-Null
}

Set-Location "frontend"

npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm

npm install lucide-react framer-motion recharts axios clsx tailwind-merge

New-Item -ItemType Directory -Force -Path "src\components" | Out-Null
New-Item -ItemType Directory -Force -Path "src\services" | Out-Null
New-Item -ItemType Directory -Force -Path "src\data" | Out-Null

@'
import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8001",
  timeout: 5000,
});

export async function getStatistics() {
  const res = await api.get("/statistics");
  return res.data;
}

export async function getActiveAlarms() {
  const res = await api.get("/alarms/active");
  return res.data;
}

export async function getEvents() {
  const res = await api.get("/events?limit=20");
  return res.data;
}
'@ | Set-Content -Encoding UTF8 "src\services\api.ts"

@'
"use client";

import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  BatteryCharging,
  Flame,
  Gauge,
  Server,
  Snowflake,
  Zap,
} from "lucide-react";

const statusColor: Record<string, string> = {
  NORMAL: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
  WARNING: "border-orange-500/40 bg-orange-500/10 text-orange-300",
  CRITICAL: "border-red-500/40 bg-red-500/10 text-red-300",
  UNKNOWN: "border-slate-500/40 bg-slate-500/10 text-slate-300",
};

export function StatusCard({
  title,
  value,
  unit,
  status,
  icon,
}: {
  title: string;
  value: string | number;
  unit?: string;
  status: "NORMAL" | "WARNING" | "CRITICAL" | "UNKNOWN";
  icon: "power" | "cooling" | "fuel" | "ups" | "server" | "alarm" | "gauge";
}) {
  const Icon =
    icon === "power"
      ? Zap
      : icon === "cooling"
      ? Snowflake
      : icon === "fuel"
      ? Flame
      : icon === "ups"
      ? BatteryCharging
      : icon === "server"
      ? Server
      : icon === "alarm"
      ? AlertTriangle
      : Gauge;

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      className={ounded-2xl border p-5 shadow-xl backdrop-blur }
    >
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-300">{title}</p>
        <Icon className="h-6 w-6" />
      </div>

      <div className="mt-5 flex items-end gap-2">
        <h2 className="text-4xl font-bold text-white">{value}</h2>
        {unit && <span className="pb-1 text-sm text-slate-400">{unit}</span>}
      </div>

      <div className="mt-4 flex items-center gap-2">
        <span className={h-2.5 w-2.5 rounded-full } />
        <span className="text-xs font-semibold">{status}</span>
      </div>
    </motion.div>
  );
}

export function SingleLineDiagram() {
  const nodes = [
    { name: "UTILITY", icon: Zap, status: "NORMAL" },
    { name: "TCO A/B", icon: Activity, status: "NORMAL" },
    { name: "UPS A/B", icon: BatteryCharging, status: "WARNING" },
    { name: "PDU IT", icon: Server, status: "NORMAL" },
    { name: "IT LOAD", icon: Gauge, status: "NORMAL" },
  ];

  return (
    <div className="rounded-3xl border border-blue-500/20 bg-slate-950/80 p-6 shadow-2xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Electrical Single Line</h2>
          <p className="text-sm text-slate-400">Dynamic power flow overview</p>
        </div>
        <Zap className="h-8 w-8 text-blue-400" />
      </div>

      <div className="grid grid-cols-1 items-center gap-4 md:grid-cols-5">
        {nodes.map((node, index) => {
          const Icon = node.icon;
          const color =
            node.status === "NORMAL"
              ? "border-emerald-400 text-emerald-300"
              : node.status === "WARNING"
              ? "border-orange-400 text-orange-300"
              : "border-red-500 text-red-300";

          return (
            <div key={node.name} className="flex items-center">
              <motion.div
                animate={{ boxShadow: ["0 0 0px #38bdf8", "0 0 20px #38bdf8", "0 0 0px #38bdf8"] }}
                transition={{ duration: 2, repeat: Infinity }}
                className={w-full rounded-2xl border bg-slate-900 p-4 text-center }
              >
                <Icon className="mx-auto mb-2 h-7 w-7" />
                <p className="text-sm font-bold">{node.name}</p>
                <p className="mt-1 text-xs">{node.status}</p>
              </motion.div>

              {index < nodes.length - 1 && (
                <div className="mx-2 hidden h-1 w-10 overflow-hidden rounded bg-blue-900 md:block">
                  <motion.div
                    animate={{ x: ["-100%", "100%"] }}
                    transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
                    className="h-full w-1/2 bg-blue-400"
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
'@ | Set-Content -Encoding UTF8 "src\components\DashboardWidgets.tsx"

@'
"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Activity, Database, Server, Zap } from "lucide-react";
import { SingleLineDiagram, StatusCard } from "@/components/DashboardWidgets";
import { getActiveAlarms, getEvents, getStatistics } from "@/services/api";

export default function Home() {
  const [stats, setStats] = useState<any>(null);
  const [alarms, setAlarms] = useState<any>({});
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const s = await getStatistics();
        const a = await getActiveAlarms();
        const e = await getEvents();

        setStats(s);
        setAlarms(a);
        setEvents(e.events || []);
      } catch (err) {
        console.error(err);
      }
    }

    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  const activeAlarmCount = alarms ? Object.keys(alarms).length : 0;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#0f3b6b_0,#020617_45%,#000_100%)] text-white">
      <div className="flex">
        <aside className="hidden min-h-screen w-72 border-r border-blue-500/20 bg-slate-950/80 p-6 lg:block">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-blue-500/20 p-3">
              <Zap className="h-7 w-7 text-blue-300" />
            </div>
            <div>
              <h1 className="text-lg font-black">STELLARIX</h1>
              <p className="text-xs text-blue-300">OpenDC Monitor</p>
            </div>
          </div>

          <nav className="mt-10 space-y-3 text-sm text-slate-300">
            {["Dashboard", "Power", "Environment", "HVAC", "Fuel", "Alarms", "Events", "Maintenance", "Reports"].map(
              (item) => (
                <div
                  key={item}
                  className="rounded-xl px-4 py-3 hover:bg-blue-500/10 hover:text-blue-200"
                >
                  {item}
                </div>
              )
            )}
          </nav>
        </aside>

        <section className="flex-1 p-6 lg:p-8">
          <header className="mb-8 flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
            <div>
              <p className="text-sm uppercase tracking-[0.4em] text-blue-300">Datacenter Operations Platform</p>
              <h2 className="mt-2 text-4xl font-black">STELLARIX OpenDC Monitor</h2>
              <p className="mt-2 text-slate-400">Real-time monitoring, alarms, events and electrical operations.</p>
            </div>

            <div className="flex items-center gap-3 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-5 py-3">
              <Activity className="h-5 w-5 text-emerald-300" />
              <span className="text-sm font-bold text-emerald-300">SYSTEM ONLINE</span>
            </div>
          </header>

          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <StatusCard title="Active Alarms" value={activeAlarmCount} status={activeAlarmCount > 0 ? "WARNING" : "NORMAL"} icon="alarm" />
            <StatusCard title="Total Events" value={stats?.total_events ?? "..."} status="NORMAL" icon="gauge" />
            <StatusCard title="Warnings" value={stats?.warning_events ?? "..."} status={(stats?.warning_events ?? 0) > 0 ? "WARNING" : "NORMAL"} icon="power" />
            <StatusCard title="Critical" value={stats?.critical_events ?? "..."} status={(stats?.critical_events ?? 0) > 0 ? "CRITICAL" : "NORMAL"} icon="server" />
          </div>

          <div className="mt-6 grid gap-6 xl:grid-cols-3">
            <div className="xl:col-span-2">
              <SingleLineDiagram />
            </div>

            <div className="rounded-3xl border border-orange-500/20 bg-slate-950/80 p-6 shadow-2xl">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold">Alarm Center</h2>
                  <p className="text-sm text-slate-400">Latest active events</p>
                </div>
                <AlertTriangle className="h-7 w-7 text-orange-300" />
              </div>

              <div className="space-y-3">
                {events.length === 0 && <p className="text-sm text-slate-400">No recent events.</p>}

                {events.slice(-7).reverse().map((event, index) => (
                  <div key={index} className="rounded-2xl border border-slate-700 bg-slate-900/80 p-4">
                    <div className="flex items-center justify-between">
                      <span className={
                        event.severity === "CRITICAL"
                          ? "text-red-300"
                          : event.severity === "WARNING"
                          ? "text-orange-300"
                          : "text-emerald-300"
                      }>
                        {event.event_type}
                      </span>
                      <span className="text-xs text-slate-500">{event.severity}</span>
                    </div>
                    <p className="mt-2 text-sm font-bold">{event.equipment}</p>
                    <p className="text-xs text-slate-400">{event.metric} = {event.value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6 grid gap-5 md:grid-cols-3">
            <StatusCard title="UPS Global Load" value="62" unit="%" status="NORMAL" icon="ups" />
            <StatusCard title="Fuel Level" value="78" unit="%" status="NORMAL" icon="fuel" />
            <StatusCard title="Cooling Health" value="94" unit="%" status="NORMAL" icon="cooling" />
          </div>

          <div className="mt-6 rounded-3xl border border-blue-500/20 bg-slate-950/80 p-6">
            <div className="mb-4 flex items-center gap-3">
              <Database className="h-6 w-6 text-blue-300" />
              <h2 className="text-xl font-bold">Top Unstable Equipment</h2>
            </div>

            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {stats?.top_equipment &&
                Object.entries(stats.top_equipment).slice(0, 8).map(([eq, count]: any) => (
                  <div key={eq} className="rounded-2xl border border-slate-700 bg-slate-900 p-4">
                    <p className="text-sm font-bold text-white">{eq}</p>
                    <p className="mt-2 text-2xl font-black text-blue-300">{count}</p>
                    <p className="text-xs text-slate-500">events</p>
                  </div>
                ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
'@ | Set-Content -Encoding UTF8 "src\app\page.tsx"

@'
@import "tailwindcss";

:root {
  --background: #020617;
  --foreground: #ffffff;
}

body {
  background: var(--background);
  color: var(--foreground);
}
'@ | Set-Content -Encoding UTF8 "src\app\globals.css"

Write-Host "Frontend generated successfully."
npm run dev
