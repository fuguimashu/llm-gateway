"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Activity,
  CheckCircle2,
  Coins,
  Timer,
  RefreshCw,
} from "lucide-react";
import { getDashboardStats, getLogs, type DashboardStats, type RequestLog } from "@/lib/api";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { fmtDate, fmtMs, fmtTokens } from "@/lib/utils";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recent, setRecent] = useState<RequestLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    try {
      const [s, logs] = await Promise.all([
        getDashboardStats(),
        getLogs({ page: 1, page_size: 15 }),
      ]);
      setStats(s);
      setRecent(logs.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-ink-400 text-sm font-mono animate-pulse">Loading…</div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl text-cream">Dashboard</h1>
          <p className="text-ink-400 text-sm mt-1">Gateway overview and recent activity</p>
        </div>
        <button
          onClick={() => load(true)}
          disabled={refreshing}
          className="flex items-center gap-2 text-sm text-ink-400 hover:text-cream border border-ink-600 hover:border-ink-500 rounded px-3 py-1.5 transition-colors disabled:opacity-40"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Requests"
          value={stats ? String(stats.total_requests) : "—"}
          icon={Activity}
          accent
        />
        <StatCard
          label="Success Rate"
          value={stats ? `${stats.success_rate.toFixed(1)}%` : "—"}
          icon={CheckCircle2}
        />
        <StatCard
          label="Total Tokens"
          value={stats ? fmtTokens(stats.total_tokens) : "—"}
          sub="prompt + completion"
          icon={Coins}
        />
        <StatCard
          label="Avg Latency"
          value={stats ? fmtMs(stats.avg_latency_ms) : "—"}
          sub="total response time"
          icon={Timer}
        />
      </div>

      {/* Recent requests table */}
      <div className="bg-ink-800 border border-ink-700 rounded-lg overflow-hidden">
        <div className="px-5 py-4 border-b border-ink-700 flex items-center justify-between">
          <h2 className="font-display text-lg text-cream">Recent Requests</h2>
          <a href="/logs" className="text-amber-500 hover:text-amber-400 text-xs font-mono transition-colors">
            View all →
          </a>
        </div>

        {recent.length === 0 ? (
          <div className="py-16 text-center text-ink-400 text-sm">
            No requests yet. Start proxying to see activity here.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-700">
                  {["Time", "Model", "Status", "Tokens", "Latency"].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-ink-400 text-xs font-mono uppercase tracking-widest font-normal">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recent.map((log, i) => (
                  <tr
                    key={log.id}
                    className="border-b border-ink-700/50 hover:bg-ink-700/30 transition-colors"
                    style={{ animationDelay: `${i * 30}ms` }}
                  >
                    <td className="px-5 py-3 font-mono text-ink-300 text-xs whitespace-nowrap">
                      {fmtDate(log.created_at)}
                    </td>
                    <td className="px-5 py-3 font-mono text-amber-400/90 text-xs">
                      {log.model}
                    </td>
                    <td className="px-5 py-3">
                      <Badge variant={log.status === "success" ? "success" : "error"}>
                        {log.status}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 font-mono text-ink-300 text-xs">
                      {fmtTokens(log.total_tokens)}
                    </td>
                    <td className="px-5 py-3 font-mono text-ink-300 text-xs">
                      {fmtMs(log.total_latency_ms)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
