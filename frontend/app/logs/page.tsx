"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, ChevronLeft, ChevronRight, AlertCircle } from "lucide-react";
import { getLogs, type RequestLog, type LogsPage } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { fmtDate, fmtMs, fmtTokens } from "@/lib/utils";

const PAGE_SIZE = 50;

export default function LogsPage() {
  const [data, setData] = useState<LogsPage | null>(null);
  const [page, setPage] = useState(1);
  const [modelFilter, setModelFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const load = useCallback(async (p: number, model: string, status: string) => {
    setLoading(true);
    try {
      const res = await getLogs({
        page: p,
        page_size: PAGE_SIZE,
        model: model || undefined,
        status: status || undefined,
      });
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(page, modelFilter, statusFilter);
  }, [load, page, modelFilter, statusFilter]);

  function handleFilter(model: string, status: string) {
    setModelFilter(model);
    setStatusFilter(status);
    setPage(1);
  }

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-3xl text-cream">Request Logs</h1>
          <p className="text-ink-400 text-sm mt-1">
            {data ? `${data.total.toLocaleString()} total requests` : "Loading…"}
          </p>
        </div>
        <button
          onClick={() => load(page, modelFilter, statusFilter)}
          disabled={loading}
          className="flex items-center gap-2 text-sm text-ink-400 hover:text-cream border border-ink-600 hover:border-ink-500 rounded px-3 py-1.5 transition-colors disabled:opacity-40"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <input
          type="text"
          value={modelFilter}
          onChange={(e) => handleFilter(e.target.value, statusFilter)}
          placeholder="Filter by model…"
          className="font-mono text-xs bg-ink-800 border border-ink-600 rounded px-3 py-1.5 text-cream placeholder-ink-500 focus:outline-none focus:border-amber-600 transition-colors w-64"
        />
        <select
          value={statusFilter}
          onChange={(e) => handleFilter(modelFilter, e.target.value)}
          className="font-mono text-xs bg-ink-800 border border-ink-600 rounded px-3 py-1.5 text-cream focus:outline-none focus:border-amber-600 transition-colors"
        >
          <option value="">All statuses</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
        </select>
        {(modelFilter || statusFilter) && (
          <button
            onClick={() => handleFilter("", "")}
            className="text-xs text-ink-400 hover:text-cream border border-ink-600 rounded px-3 py-1.5 transition-colors"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      <div className="bg-ink-800 border border-ink-700 rounded-lg overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-ink-400 text-sm font-mono animate-pulse">Loading…</div>
        ) : !data || data.items.length === 0 ? (
          <div className="py-16 text-center text-ink-400 text-sm">No logs match your filters.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-700">
                  {["Time", "Model", "Status", "Prompt", "Completion", "Total", "TTFT", "Duration", ""].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-ink-400 text-xs font-mono uppercase tracking-widest font-normal whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((log) => (
                  <>
                    <tr
                      key={log.id}
                      className="border-b border-ink-700/50 hover:bg-ink-700/30 transition-colors cursor-pointer"
                      onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                    >
                      <td className="px-4 py-3 font-mono text-ink-300 text-xs whitespace-nowrap">
                        {fmtDate(log.created_at)}
                      </td>
                      <td className="px-4 py-3 font-mono text-amber-400/90 text-xs whitespace-nowrap max-w-[160px] truncate">
                        {log.model}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={log.status === "success" ? "success" : "error"}>
                          {log.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-ink-300 text-xs">{fmtTokens(log.prompt_tokens)}</td>
                      <td className="px-4 py-3 font-mono text-ink-300 text-xs">{fmtTokens(log.completion_tokens)}</td>
                      <td className="px-4 py-3 font-mono text-ink-300 text-xs">{fmtTokens(log.total_tokens)}</td>
                      <td className="px-4 py-3 font-mono text-ink-300 text-xs">{fmtMs(log.latency_ms)}</td>
                      <td className="px-4 py-3 font-mono text-ink-300 text-xs">{fmtMs(log.total_latency_ms)}</td>
                      <td className="px-4 py-3">
                        {log.error_message && (
                          <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                        )}
                      </td>
                    </tr>
                    {expandedId === log.id && log.error_message && (
                      <tr key={`${log.id}-exp`} className="border-b border-ink-700/50 bg-red-500/5">
                        <td colSpan={9} className="px-4 py-3">
                          <div className="font-mono text-xs text-red-400 whitespace-pre-wrap">{log.error_message}</div>
                        </td>
                      </tr>
                    )}
                    {expandedId === log.id && !log.error_message && (
                      <tr key={`${log.id}-exp`} className="border-b border-ink-700/50 bg-ink-700/20">
                        <td colSpan={9} className="px-4 py-3">
                          <div className="font-mono text-xs text-ink-400">
                            request_id: <span className="text-cream">{log.request_id}</span>
                            {log.virtual_key_id && (
                              <> · key: <span className="text-cream">{log.virtual_key_id.slice(0, 20)}…</span></>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {data && totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-ink-400 text-xs font-mono">
            Page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
              className="p-1.5 rounded border border-ink-600 text-ink-400 hover:text-cream hover:border-ink-500 disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="p-1.5 rounded border border-ink-600 text-ink-400 hover:text-cream hover:border-ink-500 disabled:opacity-30 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
