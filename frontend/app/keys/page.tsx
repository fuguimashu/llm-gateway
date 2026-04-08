"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Plus,
  Trash2,
  RotateCcw,
  Copy,
  Check,
  KeyRound,
  X,
} from "lucide-react";
import {
  listKeys,
  createKey,
  deleteKey,
  activateKey,
  type VirtualKey,
  type VirtualKeyCreated,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { fmtDate, truncateKey } from "@/lib/utils";

export default function KeysPage() {
  const [keys, setKeys] = useState<VirtualKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newKey, setNewKey] = useState<VirtualKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setKeys(await listKeys());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleDeactivate(id: string) {
    await deleteKey(id);
    setKeys(prev => prev.map(k => k.id === id ? { ...k, is_active: false } : k));
  }

  async function handleActivate(id: string) {
    const updated = await activateKey(id);
    setKeys(prev => prev.map(k => k.id === id ? updated : k));
  }

  function handleCreated(k: VirtualKeyCreated) {
    setNewKey(k);
    setKeys(prev => [k, ...prev]);
  }

  function copyKey() {
    if (!newKey) return;
    navigator.clipboard.writeText(newKey.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl text-cream">Virtual Keys</h1>
          <p className="text-ink-400 text-sm mt-1">Manage API keys issued to clients</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-amber-600 hover:bg-amber-500 text-ink-900 font-medium text-sm rounded px-4 py-2 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Key
        </button>
      </div>

      {/* New key reveal banner */}
      {newKey && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4 flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="text-emerald-400 text-xs font-mono mb-1 uppercase tracking-widest">New key — copy it now, it won&apos;t be shown again</div>
            <code className="font-mono text-sm text-cream break-all">{newKey.key}</code>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={copyKey}
              className="flex items-center gap-1.5 border border-emerald-500/40 hover:bg-emerald-500/20 text-emerald-400 text-xs rounded px-3 py-1.5 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? "Copied" : "Copy"}
            </button>
            <button
              onClick={() => setNewKey(null)}
              className="text-ink-400 hover:text-cream transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Keys table */}
      <div className="bg-ink-800 border border-ink-700 rounded-lg overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-ink-400 text-sm font-mono animate-pulse">Loading…</div>
        ) : keys.length === 0 ? (
          <div className="py-16 text-center">
            <KeyRound className="w-8 h-8 text-ink-600 mx-auto mb-3" />
            <div className="text-ink-400 text-sm">No keys yet. Create one to get started.</div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-700">
                  {["Name", "Key ID", "Models", "Last Used", "Status", ""].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-ink-400 text-xs font-mono uppercase tracking-widest font-normal">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {keys.map((key) => (
                  <tr key={key.id} className="border-b border-ink-700/50 hover:bg-ink-700/30 transition-colors">
                    <td className="px-5 py-3 text-cream font-medium">{key.name}</td>
                    <td className="px-5 py-3">
                      <code className="font-mono text-xs text-amber-400/80">{truncateKey(key.id)}</code>
                    </td>
                    <td className="px-5 py-3 text-ink-300 text-xs">
                      {key.models ? (
                        <div className="flex flex-wrap gap-1">
                          {key.models.split(",").map(m => (
                            <span key={m} className="bg-ink-700 border border-ink-600 rounded px-1.5 py-0.5 font-mono text-[11px] text-ink-200">
                              {m.trim()}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-ink-500 italic">all models</span>
                      )}
                    </td>
                    <td className="px-5 py-3 font-mono text-ink-400 text-xs whitespace-nowrap">
                      {key.last_used_at ? fmtDate(key.last_used_at) : "never"}
                    </td>
                    <td className="px-5 py-3">
                      <Badge variant={key.is_active ? "success" : "neutral"}>
                        {key.is_active ? "active" : "inactive"}
                      </Badge>
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1 justify-end">
                        {key.is_active ? (
                          <button
                            onClick={() => handleDeactivate(key.id)}
                            className="p-1.5 rounded text-ink-400 hover:text-red-400 hover:bg-red-400/10 transition-colors"
                            title="Deactivate"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleActivate(key.id)}
                            className="p-1.5 rounded text-ink-400 hover:text-emerald-400 hover:bg-emerald-400/10 transition-colors"
                            title="Re-activate"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Key Modal */}
      {showModal && (
        <CreateKeyModal
          onClose={() => setShowModal(false)}
          onCreate={(k) => { handleCreated(k); setShowModal(false); }}
        />
      )}
    </div>
  );
}

function CreateKeyModal({
  onClose,
  onCreate,
}: {
  onClose: () => void;
  onCreate: (k: VirtualKeyCreated) => void;
}) {
  const [name, setName] = useState("");
  const [models, setModels] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      const k = await createKey(name.trim(), models.trim() || null);
      onCreate(k);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create key");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-ink-800 border border-ink-600 rounded-lg p-6 w-full max-w-md shadow-2xl animate-slide-up">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-display text-xl text-cream">Create Virtual Key</h2>
          <button onClick={onClose} className="text-ink-400 hover:text-cream transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-ink-300 text-xs font-mono uppercase tracking-widest mb-1.5">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Production App"
              className="w-full bg-ink-900 border border-ink-600 rounded px-3 py-2 text-cream text-sm placeholder-ink-500 focus:outline-none focus:border-amber-600 transition-colors"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-ink-300 text-xs font-mono uppercase tracking-widest mb-1.5">
              Allowed Models
              <span className="text-ink-500 normal-case ml-1">(comma-separated, blank = all)</span>
            </label>
            <input
              type="text"
              value={models}
              onChange={(e) => setModels(e.target.value)}
              placeholder="openai/gpt-4o, anthropic/claude-sonnet-4-6"
              className="w-full font-mono text-xs bg-ink-900 border border-ink-600 rounded px-3 py-2 text-cream placeholder-ink-500 focus:outline-none focus:border-amber-600 transition-colors"
            />
          </div>

          {error && <p className="text-red-400 text-xs">{error}</p>}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-ink-600 hover:border-ink-500 text-ink-300 hover:text-cream text-sm rounded px-4 py-2 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !name.trim()}
              className="flex-1 bg-amber-600 hover:bg-amber-500 disabled:opacity-40 text-ink-900 font-medium text-sm rounded px-4 py-2 transition-colors"
            >
              {submitting ? "Creating…" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
