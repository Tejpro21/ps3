import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Card, CardBody, CardHeader, CardTitle } from "./ui/Card";

function fmt(n: number | undefined, kind: "money" | "pct" | "ratio" | "num") {
  if (n === undefined || Number.isNaN(n)) return "—";
  if (kind === "money")
    return n.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  if (kind === "pct") return `${(n * 100).toFixed(2)}%`;
  if (kind === "ratio") return n.toFixed(2);
  return n.toFixed(2);
}

export function MetricCard(props: {
  title: string;
  value?: number;
  kind: "money" | "pct" | "ratio" | "num";
  accent?: "blue" | "emerald" | "red";
}) {
  const [display, setDisplay] = useState<number | undefined>(props.value);
  const target = props.value;

  useEffect(() => {
    if (target === undefined || Number.isNaN(target)) {
      setDisplay(undefined);
      return;
    }
    const start = performance.now();
    const from = display ?? target;
    const dur = 650;
    let raf = 0;
    const tick = (t: number) => {
      const k = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1 - k, 3);
      setDisplay(from + (target - from) * eased);
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target]);

  const glow = useMemo(() => {
    if (props.accent === "emerald") return "shadow-[0_0_0_1px_rgba(16,185,129,0.18)_inset]";
    if (props.accent === "red") return "shadow-[0_0_0_1px_rgba(239,68,68,0.18)_inset]";
    return "shadow-[0_0_0_1px_rgba(59,130,246,0.18)_inset]";
  }, [props.accent]);

  return (
    <Card className={`relative overflow-hidden ${glow}`}>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <CardHeader>
          <CardTitle>{props.title}</CardTitle>
        </CardHeader>
        <CardBody className="pt-0">
          <div className="text-2xl font-semibold tracking-tight text-slate-50">{fmt(display, props.kind)}</div>
          <div className="mt-1 text-xs text-slate-400">Institutional snapshot · server-computed</div>
        </CardBody>
      </motion.div>
    </Card>
  );
}

