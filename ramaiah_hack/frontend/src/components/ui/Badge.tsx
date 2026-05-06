import { clsx } from "clsx";
import type { PropsWithChildren } from "react";

export function Badge({
  children,
  tone = "neutral",
  className
}: PropsWithChildren<{ tone?: "neutral" | "buy" | "sell" | "info"; className?: string }>) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ring-1",
        tone === "neutral" && "bg-white/5 text-slate-200 ring-white/10",
        tone === "info" && "bg-blue-500/10 text-blue-200 ring-blue-400/20",
        tone === "buy" && "bg-emerald-500/10 text-emerald-200 ring-emerald-400/20",
        tone === "sell" && "bg-red-500/10 text-red-200 ring-red-400/20",
        className
      )}
    >
      {children}
    </span>
  );
}

