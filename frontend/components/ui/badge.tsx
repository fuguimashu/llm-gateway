import { cn } from "@/lib/utils";

interface BadgeProps {
  variant?: "success" | "error" | "warning" | "neutral";
  children: React.ReactNode;
  className?: string;
}

const styles = {
  success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  error:   "bg-red-500/15 text-red-400 border-red-500/30",
  warning: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  neutral: "bg-ink-700 text-ink-300 border-ink-600",
};

export function Badge({ variant = "neutral", children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-mono text-[11px] px-1.5 py-0.5 rounded border",
        styles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
