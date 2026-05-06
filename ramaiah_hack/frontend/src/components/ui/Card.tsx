import { clsx } from "clsx";
import type { PropsWithChildren } from "react";

export function Card({
  children,
  className
}: PropsWithChildren<{
  className?: string;
}>) {
  return (
    <div
      className={clsx(
        "rounded-2xl bg-white/5 shadow-glass backdrop-blur-md ring-1 ring-white/10",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children }: PropsWithChildren) {
  return <div className="px-4 pt-4 pb-2">{children}</div>;
}

export function CardTitle({ children }: PropsWithChildren) {
  return <div className="text-sm font-semibold tracking-wide text-slate-200">{children}</div>;
}

export function CardBody({ children, className }: PropsWithChildren<{ className?: string }>) {
  return <div className={clsx("px-4 pb-4", className)}>{children}</div>;
}

