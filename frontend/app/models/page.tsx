"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, CircleCheck, CircleX, Clock, Cpu } from "lucide-react";
import { getModels, type ModelStatus } from "@/lib/api";

const PROVIDER_COLORS: Record<string, string> = {
  openai:    "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
  anthropic: "text-amber-400 bg-amber-400/10 border-amber-400/30",
  ollama:    "text-sky-400 bg-sky-400/10 border-sky-400/30",
};

export default function ModelsPage() {
  const [models, setModels] = useState<ModelStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(async (showLoading = false) => {
    if (showLoading) setLoading(true);
    try {
      setModels(await getModels());
      setLastUpdated(new Date());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(true);
    // Auto-refresh every 30s
    const id = setInterval(() => load(), 30_000);
    return () => clearInterval(id);
  }, [load]);

  const available = models.filter(m => m.available).length;
  const total = models.length;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-3xl text-cream">Model Status</h1>
          <p className="text-ink-400 text-sm mt-1">
            Passive health check — updates after each request
            {lastUpdated && (
              <span className="ml-2 text-ink-500">
                · refreshed {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={() => load(true)}
          disabled={loading}
          className="flex items-center gap-2 text-sm text-ink-400 hover:text-cream border border-ink-600 hover:border-ink-500 rounded px-3 py-1.5 transition-colors disabled:opacity-40"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Summary bar */}
      {!loading && total > 0 && (
        <div className="flex items-center gap-4 bg-ink-800 border border-ink-700 rounded-lg px-5 py-4">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${available === total ? "bg-emerald-400" : available > 0 ? "bg-amber-400" : "bg-red-400"}`} />
            <span className="text-cream font-mono text-sm">
              {available}/{total} models available
            </span>
          </div>
          {available < total && (
            <span className="text-amber-400 text-xs font-mono border border-amber-400/30 bg-amber-400/10 rounded px-2 py-0.5">
              {total - available} in cooldown
            </span>
          )}
        </div>
      )}

      {/* Model grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-ink-800 border border-ink-700 rounded-lg p-5 animate-pulse h-32" />
          ))}
        </div>
      ) : models.length === 0 ? (
        <div className="text-center py-20">
          <Cpu className="w-10 h-10 text-ink-600 mx-auto mb-3" />
          <div className="text-ink-400 text-sm">No models configured.</div>
          <div className="text-ink-500 text-xs mt-1">
            Add models to <code className="font-mono">config.yaml</code> and restart.
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {models.map((model, i) => (
            <ModelCard key={model.id} model={model} delay={i * 50} />
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="border-t border-ink-700 pt-5">
        <h3 className="text-ink-400 text-xs font-mono uppercase tracking-widest mb-3">Health check logic</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-ink-400">
          <div className="flex items-start gap-2">
            <CircleCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-ink-200 font-mono">Available</div>
              <div>Fewer than 3 consecutive failures, or cooldown expired.</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Clock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-ink-200 font-mono">Cooldown</div>
              <div>3+ consecutive failures → 30s cooldown before next attempt.</div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <CircleX className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div>
              <div className="text-ink-200 font-mono">Fallback</div>
              <div>Gateway auto-routes to next available model by priority.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ModelCard({ model, delay }: { model: ModelStatus; delay: number }) {
  const providerStyle = PROVIDER_COLORS[model.provider] ?? "text-ink-300 bg-ink-700 border-ink-600";
  const isAvailable = model.available;

  return (
    <div
      className={`bg-ink-800 border rounded-lg p-5 flex flex-col gap-4 animate-slide-up transition-all ${
        isAvailable ? "border-ink-700" : "border-amber-600/30"
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Top row */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-mono text-sm text-cream truncate" title={model.id}>
            {model.id}
          </div>
          <div className="mt-1">
            <span className={`inline-flex items-center font-mono text-[11px] px-1.5 py-0.5 rounded border ${providerStyle}`}>
              {model.provider}
            </span>
          </div>
        </div>
        <div className="shrink-0 mt-0.5">
          {isAvailable ? (
            <CircleCheck className="w-5 h-5 text-emerald-400" />
          ) : (
            <Clock className="w-5 h-5 text-amber-400" />
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-ink-900 rounded px-3 py-2">
          <div className="text-ink-500 text-[10px] font-mono uppercase tracking-widest mb-0.5">Failures</div>
          <div className={`font-display text-xl leading-none ${model.consecutive_failures > 0 ? "text-amber-400" : "text-cream"}`}>
            {model.consecutive_failures}
          </div>
        </div>
        <div className="bg-ink-900 rounded px-3 py-2">
          <div className="text-ink-500 text-[10px] font-mono uppercase tracking-widest mb-0.5">
            {isAvailable ? "Status" : "Cooldown"}
          </div>
          {isAvailable ? (
            <div className="font-display text-xl leading-none text-emerald-400">OK</div>
          ) : (
            <div className="font-mono text-sm leading-none text-amber-400 mt-1">
              {model.cooldown_remaining_seconds}s
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
