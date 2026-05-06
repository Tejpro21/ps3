import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export function MultiAssetPerformanceChart(props: {
  equityCurve: { timestamp: string; equity: number }[];
  assetPerf: { ticker: string; series: { timestamp: string; value: number }[] }[];
}) {
  // Merge by timestamp (simple: use equity timestamps as backbone)
  const rows = props.equityCurve.map((e) => {
    const r: any = { timestamp: e.timestamp, equity: e.equity };
    for (const a of props.assetPerf) {
      const hit = a.series.find((s) => s.timestamp === e.timestamp);
      if (hit) r[a.ticker] = hit.value;
    }
    return r;
  });

  const palette = ["rgba(59,130,246,0.85)", "rgba(16,185,129,0.85)", "rgba(226,232,240,0.55)", "rgba(148,163,184,0.55)"];

  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer>
        <LineChart data={rows} margin={{ left: 10, right: 18, top: 10, bottom: 10 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis
            dataKey="timestamp"
            tick={{ fill: "rgba(148,163,184,0.7)", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            hide
          />
          <YAxis tick={{ fill: "rgba(148,163,184,0.7)", fontSize: 11 }} tickLine={false} axisLine={false} width={70} />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null;
              const ts = (payload[0].payload as any).timestamp;
              return (
                <div className="rounded-2xl border border-white/10 bg-ink-900/80 px-3 py-2 text-xs text-slate-200 shadow-glass backdrop-blur-md">
                  <div className="text-[11px] text-slate-400">{String(ts).slice(0, 19).replace("T", " ")}</div>
                  <div className="mt-1 space-y-1">
                    {payload.map((p: any) => (
                      <div key={p.dataKey} className="flex items-center justify-between gap-6">
                        <span className="text-slate-300">{p.dataKey}</span>
                        <span className="font-semibold text-slate-100">
                          {typeof p.value === "number" ? p.value.toFixed(4) : "—"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            }}
          />
          <Legend />
          <Line type="monotone" dataKey="equity" stroke="rgba(59,130,246,0.9)" strokeWidth={1.4} dot={false} />
          {props.assetPerf.slice(0, 4).map((a, i) => (
            <Line key={a.ticker} type="monotone" dataKey={a.ticker} stroke={palette[i % palette.length]} strokeWidth={1.1} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

