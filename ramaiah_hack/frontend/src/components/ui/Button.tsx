import { clsx } from "clsx";
import type { ButtonHTMLAttributes } from "react";

export function Button({
  className,
  variant = "default",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "ghost";
}) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition",
        "ring-1 ring-white/10 hover:ring-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500/60",
        variant === "default" &&
          "bg-gradient-to-b from-white/10 to-white/5 hover:from-white/12 hover:to-white/6",
        variant === "ghost" && "bg-transparent hover:bg-white/5",
        className
      )}
      {...props}
    />
  );
}

