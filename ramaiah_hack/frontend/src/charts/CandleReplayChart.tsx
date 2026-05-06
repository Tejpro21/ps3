import {
  CartesianGrid,
  ComposedChart,
  Customized,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { Candle } from "../types/api";

type CandlePoint = Candle & { i: number };

function CandlesLayer(props: any) {
  const { xAxisMap, yAxisMap, data } = props;
  const xAxis = xAxisMap?.[Object.keys(xAxisMap)[0]];
  const yAxis = yAxisMap?.[Object.keys(yAxisMap)[0]];
  if (!xAxis || !yAxis || !data) return null;

  const xScale = xAxis.scale;
  const yScale = yAxis.scale;
  const band = typeof xScale.bandwidth === "function" ? xScale.bandwidth() : 8;
  const w = Math.max(3, Math.min(10, band * 0.65));

  return (
    <g>
      {(data as CandlePoint[]).map((d) => {
        const o = d.open ?? d.close;
        const c = d.close ?? d.open;
        const h = d.high ?? (o ?? c);
        const l = d.low ?? (o ?? c);
        if (o == null || c == null || h == null || l == null) return null;

        const x = xScale(d.i) + band / 2;
        const yO = yScale(o);
        const yC = yScale(c);
        const yH = yScale(h);
        const yL = yScale(l);

        const up = c >= o;
        const stroke = up ? "rgba(16,185,129,0.75)" : "rgba(239,68,68,0.75)";
        const fill = up ? "rgba(16,185,129,0.20)" : "rgba(239,68,68,0.20)";
        const top = Math.min(yO, yC);
        const bottom = Math.max(yO, yC);
        const bodyH = Math.max(2, bottom - top);

        return (
          <g key={d.timestamp}>
            <line x1={x} x2={x} y1={yH} y2={yL} stroke={stroke} strokeWidth={1} />
            <rect x={x - w / 2} y={top} width={w} height={bodyH} fill={fill} stroke={stroke} strokeWidth={1} rx={2} />
          </g>
        );
      })}
    </g>
  );
}

function fmt(n: number | null | undefined) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return n.toFixed(4);
}

export function CandleReplayChart(props: { candles: Candle[] }) {
  const data: CandlePoint[] = props.candles.map((c, i) => ({ ...c, i }));
  return (
    <div className="h-[420px] w-full">
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ left: 10, right: 18, top: 10, bottom: 10 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis dataKey="i" tick={{ fill: "rgba(148,163,184,0.7)", fontSize: 11 }} tickLine={false} axisLine={false} />
          <YAxis
            tick={{ fill: "rgba(148,163,184,0.7)", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            domain={["dataMin", "dataMax"]}
            width={70}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload || payload.length === 0) return null;
              const d = payload[0].payload as CandlePoint;
              return (
                <div className="rounded-2xl border border-white/10 bg-ink-900/80 px-3 py-2 text-xs text-slate-200 shadow-glass backdrop-blur-md">
                  <div className="text-[11px] text-slate-400">{d.timestamp}</div>
                  <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-1">
                    <div>O: {fmt(d.open)}</div>
                    <div>H: {fmt(d.high)}</div>
                    <div>L: {fmt(d.low)}</div>
                    <div>C: {fmt(d.close)}</div>
                    <div className="text-slate-400">ATR: {fmt(d.atr14)}</div>
                    <div className="text-slate-400">RSI: {fmt(d.rsi14)}</div>
                    <div className="text-slate-400">RSI-SMA: {fmt(d.rsi_sma9)}</div>
                    <div className="text-slate-400">EMA200: {fmt(d.ema200)}</div>
                    <div className="text-slate-400">SSMA9: {fmt(d.ssma9)}</div>
                  </div>
                </div>
              );
            }}
          />

          <Customized component={CandlesLayer} />
          <Line type="monotone" dataKey="close" stroke="rgba(226,232,240,0.35)" strokeWidth={1.0} dot={false} />
          <Line type="monotone" dataKey="ema200" stroke="rgba(59,130,246,0.85)" strokeWidth={1.2} dot={false} />
          <Line type="monotone" dataKey="ssma9" stroke="rgba(16,185,129,0.85)" strokeWidth={1.1} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

