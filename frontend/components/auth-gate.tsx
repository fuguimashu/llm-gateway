"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import { ShieldCheck, KeyRound } from "lucide-react";

const KEY = "llm_gateway_master_key";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [needsKey, setNeedsKey] = useState(false);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(KEY);
    if (stored) {
      setReady(true);
    } else {
      setNeedsKey(true);
    }
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    setTesting(true);
    setError("");
    try {
      // Validate by hitting /health (no auth) then /v1/keys (needs master key)
      await getHealth();
      localStorage.setItem(KEY, input.trim());
      setReady(true);
      setNeedsKey(false);
    } catch {
      setError("Could not reach the gateway. Check the API URL and key.");
    } finally {
      setTesting(false);
    }
  }

  if (ready) return <>{children}</>;

  if (!needsKey) return null; // hydrating

  return (
    <div className="min-h-screen bg-ink-900 flex items-center justify-center p-6">
      <div className="w-full max-w-sm">
        {/* Logo mark */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-9 h-9 rounded bg-amber-600/20 border border-amber-600/40 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5 text-amber-500" />
          </div>
          <span className="font-display text-xl text-cream">LLM Gateway</span>
        </div>

        <div className="bg-ink-800 border border-ink-600 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-1">
            <KeyRound className="w-4 h-4 text-amber-500" />
            <h2 className="font-display text-lg text-cream">Enter master key</h2>
          </div>
          <p className="text-ink-300 text-sm mb-5">
            Set in <code className="font-mono text-amber-400/80 text-xs">config.yaml → settings.master_key</code>
          </p>

          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="password"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="your-master-key"
              className="w-full font-mono text-sm bg-ink-900 border border-ink-600 rounded px-3 py-2 text-cream placeholder-ink-400 focus:outline-none focus:border-amber-600 transition-colors"
              autoFocus
            />

            {error && (
              <p className="text-red-400 text-xs">{error}</p>
            )}

            <button
              type="submit"
              disabled={testing || !input.trim()}
              className="w-full bg-amber-600 hover:bg-amber-500 disabled:opacity-40 disabled:cursor-not-allowed text-ink-900 font-medium text-sm rounded px-4 py-2 transition-colors"
            >
              {testing ? "Connecting…" : "Connect"}
            </button>
          </form>
        </div>

        <p className="text-center text-ink-400 text-xs mt-4">
          Key stored in browser localStorage
        </p>
      </div>
    </div>
  );
}
