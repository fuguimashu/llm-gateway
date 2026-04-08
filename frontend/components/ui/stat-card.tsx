import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  icon: LucideIcon;
  accent?: boolean;
}

export function StatCard({ label, value, sub, icon: Icon, accent }: StatCardProps) {
  return (
    <div className={cn(
      "bg-ink-800 border rounded-lg p-5 flex flex-col gap-3",
      accent ? "border-amber-600/40" : "border-ink-700"
    )}>
      <div className="flex items-center justify-between">
        <span className="text-ink-400 text-xs uppercase tracking-widest font-mono">{label}</span>
        <div className={cn(
          "w-7 h-7 rounded flex items-center justify-center",
          accent ? "bg-amber-600/20" : "bg-ink-700"
        )}>
          <Icon className={cn("w-4 h-4", accent ? "text-amber-500" : "text-ink-300")} />
        </div>
      </div>
      <div>
        <div className="font-display text-3xl text-cream leading-none">{value}</div>
        {sub && <div className="text-ink-400 text-xs mt-1 font-mono">{sub}</div>}
      </div>
    </div>
  );
}
