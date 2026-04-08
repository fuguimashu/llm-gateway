"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  KeyRound,
  ScrollText,
  Cpu,
  ShieldCheck,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/",        label: "Dashboard", icon: LayoutDashboard },
  { href: "/keys",    label: "Keys",      icon: KeyRound },
  { href: "/logs",    label: "Logs",      icon: ScrollText },
  { href: "/models",  label: "Models",    icon: Cpu },
];

export function Nav() {
  const path = usePathname();

  function handleLogout() {
    localStorage.removeItem("llm_gateway_master_key");
    window.location.reload();
  }

  return (
    <nav className="w-52 shrink-0 border-r border-ink-700 bg-ink-800 flex flex-col h-full">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-ink-700">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded bg-amber-600/20 border border-amber-600/40 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-4 h-4 text-amber-500" />
          </div>
          <div>
            <div className="font-display text-base text-cream leading-tight">LLM Gateway</div>
            <div className="text-ink-400 text-[10px] font-mono leading-none mt-0.5">v1.0.0</div>
          </div>
        </div>
      </div>

      {/* Links */}
      <div className="flex-1 px-3 py-4 space-y-0.5">
        {links.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? path === "/" : path.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-colors group",
                active
                  ? "bg-amber-600/15 text-amber-400"
                  : "text-ink-300 hover:text-cream hover:bg-ink-700"
              )}
            >
              <Icon className={cn("w-4 h-4 shrink-0", active ? "text-amber-500" : "text-ink-400 group-hover:text-cream")} />
              {label}
              {active && (
                <span className="ml-auto w-1 h-4 rounded-full bg-amber-500" />
              )}
            </Link>
          );
        })}
      </div>

      {/* Logout */}
      <div className="px-3 py-4 border-t border-ink-700">
        <button
          onClick={handleLogout}
          className="flex items-center gap-2.5 px-3 py-2 rounded text-sm text-ink-400 hover:text-red-400 hover:bg-red-400/10 transition-colors w-full"
        >
          <LogOut className="w-4 h-4" />
          Change key
        </button>
      </div>
    </nav>
  );
}
