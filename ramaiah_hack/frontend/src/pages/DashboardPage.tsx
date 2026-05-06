import { useEffect, useMemo, useState } from "react";
import { api } from "../services/api";
import { useSimulationStream } from "../hooks/useSimulationStream";
import type { DashboardData, Regime, SSEEvent, SystemStatus } from "../types/api";
import { TopNav } from "../layouts/TopNav";
import { MetricCard } from "../components/MetricCard";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { CandleReplayChart } from "../charts/CandleReplayChart";
import { Pie, PieChart, ResponsiveContainer, Tooltip as RTooltip } from "recharts";
import { DatasetUploadCard } from "../components/DatasetUploadCard";
import { MultiAssetPerformanceChart } from "../charts/MultiAssetPerformanceChart";

const SPEEDS = [0.5, 1, 2, 5] as const;

function toneForSignal(s: string): "neutral" | "buy" | "sell" | "info" {
  if (s === "BUY") return "buy";
  if (s === "SELL") return "sell";
  return "neutral";
}

export default function DashboardPage() {
  const [system, setSystem] = useState<SystemStatus>();
  const [dash, setDash] = useState<DashboardData>();
  const [trades, setTrades] = useState<any[]>([]);
  const [tickerQuery, setTickerQuery] = useState("");

  const active = dash?.active_ticker ?? system?.simulation.active_ticker ?? "";
  const playing = dash?.status.playing ?? system?.simulation.playing ?? false;
  const speed = dash?.status.speed ?? system?.simulation.speed ?? 1;

  const regime: Regime | undefined = useMemo(() => {
    const row = dash?.latest_signals.find((x) => x.ticker === active);
    return row?.regime;
  }, [dash?.latest_signals, active]);

  async function refresh() {
    const [s, d, tl] = await Promise.all([api.systemStatus(), api.dashboardData(), api.tradeLogs()]);
    setSystem(s);
    setDash(d);
    setTrades(tl.trades ?? []);
  }

  useEffect(() => {
    refresh().catch(() => {});
    const t = setInterval(() => api.systemStatus().then(setSystem).catch(() => {}), 1500);
    return () => clearInterval(t);
  }, []);

  useSimulationStream((evt: SSEEvent) => {
    if (evt.type === "snapshot") setDash(evt.data);
    if (evt.type === "step") {
      // Pull a fresh window occasionally; keeps UI consistent without heavy per-candle payloads.
      if (evt.step % 2 === 0) api.dashboardData().then(setDash).catch(() => {});
    }
    if (evt.type === "trade") {
      // trade event implies state change; refresh snapshot
      Promise.all([api.dashboardData(), api.tradeLogs()])
        .then(([d, tl]) => {
          setDash(d);
          setTrades(tl.trades ?? []);
        })
        .catch(() => {});
    }
  });

  const filtered = useMemo(() => {
    const assets = dash?.assets ?? [];
    const q = tickerQuery.trim().toUpperCase();
    if (!q) return assets;
    return assets.filter((a) => a.includes(q));
  }, [dash?.assets, tickerQuery]);

  const hero = dash?.metrics ?? {};
  const portfolioValue = dash?.portfolio?.equity ?? dash?.portfolio?.cash ?? 0;
  const alloc = dash?.portfolio.allocation ?? {};
  const allocData = Object.entries(alloc).map(([name, value]) => ({ name, value }));

  return (
    <div className="min-h-screen">
      <TopNav
        system={system}
        activeTicker={active}
        regime={regime}
        playing={playing}
        speed={speed}
        onPlayPause={() => api.startSimulation({ action: playing ? "pause" : "play" }).catch(() => {})}
      />

      <div className="mx-auto max-w-[1400px] px-5 py-6">
        {/* Hero metrics */}
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-7">
          <MetricCard title="Portfolio Value" kind="money" value={portfolioValue} accent="blue" />
          <MetricCard title="Sharpe Ratio" kind="ratio" value={hero.sharpe} accent="emerald" />
          <MetricCard title="Max Drawdown" kind="pct" value={hero.max_drawdown} accent="red" />
          <MetricCard title="VaR (95%)" kind="pct" value={hero.var_95} accent="red" />
          <MetricCard title="Volatility" kind="pct" value={hero.volatility} accent="blue" />
          <MetricCard title="Alpha" kind="num" value={hero.alpha} accent="emerald" />
          <MetricCard title="Beta" kind="num" value={hero.beta} accent="blue" />
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-12">
          {/* Replay Engine */}
          <Card className="xl:col-span-8">
            <CardHeader>
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <CardTitle>Candle Replay Engine</CardTitle>
                  <div className="mt-1 text-xs text-slate-400">
                    Candle-by-candle · overlays progressive · backend-driven indicators & signals
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <Button onClick={() => api.startSimulation({ action: "step_prev" }).catch(() => {})}>
                    Prev
                  </Button>
                  <Button onClick={() => api.startSimulation({ action: playing ? "pause" : "play" }).catch(() => {})}>
                    {playing ? "Pause" : "Play"}
                  </Button>
                  <Button onClick={() => api.startSimulation({ action: "step_next" }).catch(() => {})}>
                    Next
                  </Button>
                  <div className="ml-2 flex items-center gap-1">
                    {SPEEDS.map((s) => (
                      <Button
                        key={s}
                        variant={Math.abs(speed - s) < 1e-6 ? "default" : "ghost"}
                        onClick={() => api.startSimulation({ action: "set_speed", speed: s }).catch(() => {})}
                      >
                        {s}x
                      </Button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
                <div className="flex items-center gap-2">
                  <div className="text-xs text-slate-400">Ticker</div>
                  <input
                    value={tickerQuery}
                    onChange={(e) => setTickerQuery(e.target.value)}
                    placeholder="Search..."
                    className="w-52 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:ring-2 focus:ring-blue-500/50"
                  />
                  <div className="flex flex-wrap gap-1">
                    {filtered.slice(0, 8).map((t) => (
                      <button
                        key={t}
                        onClick={() => api.startSimulation({ action: "set_active", ticker: t }).then(refresh).catch(() => {})}
                        className={`rounded-full px-2 py-1 text-xs ring-1 transition ${
                          t === active
                            ? "bg-blue-500/15 text-blue-200 ring-blue-400/25"
                            : "bg-white/5 text-slate-200 ring-white/10 hover:bg-white/8"
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 text-xs text-slate-400">
                  <div>
                    Step <span className="text-slate-200">{dash?.timeline.step ?? 0}</span> /{" "}
                    <span className="text-slate-200">{dash?.timeline.total ?? 0}</span>
                  </div>
                  <Badge tone="info">{dash?.timeline.timestamp ?? "—"}</Badge>
                </div>
              </div>
            </CardHeader>
            <CardBody className="pt-0">
              <CandleReplayChart candles={dash?.candles ?? []} />
            </CardBody>
          </Card>

          {/* Right column: signals + explainability + portfolio */}
          <div className="xl:col-span-4 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Live Signals</CardTitle>
              </CardHeader>
              <CardBody>
                <div className="max-h-[220px] overflow-auto pr-2">
                  <table className="w-full text-xs">
                    <thead className="text-slate-400">
                      <tr className="text-left">
                        <th className="pb-2">Ticker</th>
                        <th className="pb-2">Signal</th>
                        <th className="pb-2">Conf.</th>
                        <th className="pb-2">ATR</th>
                        <th className="pb-2">Sent.</th>
                        <th className="pb-2">Regime</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(dash?.latest_signals ?? []).slice(0, 50).map((r) => (
                        <tr key={r.ticker} className="border-t border-white/5">
                          <td className="py-2 font-medium text-slate-100">{r.ticker}</td>
                          <td className="py-2">
                            <Badge tone={toneForSignal(r.signal)}>{r.signal}</Badge>
                          </td>
                          <td className="py-2 text-slate-200">{r.confidence.toFixed(2)}</td>
                          <td className="py-2 text-slate-400">{r.atr14?.toFixed(4) ?? "—"}</td>
                          <td className="py-2 text-slate-400">
                            {r.sentiment === null || r.sentiment === undefined ? "—" : r.sentiment.toFixed(2)}
                          </td>
                          <td className="py-2 text-slate-400">{r.regime}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Explainability</CardTitle>
              </CardHeader>
              <CardBody>
                <div className="space-y-2">
                  {(dash?.explainability ?? [])
                    .slice()
                    .reverse()
                    .slice(0, 6)
                    .map((e, idx) => (
                      <div key={`${e.timestamp}-${idx}`} className="rounded-xl bg-white/5 p-3 ring-1 ring-white/10">
                        <div className="flex items-center justify-between">
                          <div className="text-xs font-semibold text-slate-100">
                            {e.ticker} <span className="text-slate-500">·</span> {e.timestamp}
                          </div>
                          <Badge tone={toneForSignal(e.signal)}>{e.signal}</Badge>
                        </div>
                        <div className="mt-2 text-xs text-slate-300">{e.rationale}</div>
                        <div className="mt-2 grid grid-cols-3 gap-2 text-[11px] text-slate-400">
                          <div>RSI {e.rsi14?.toFixed(2) ?? "—"}</div>
                          <div>SMA {e.rsi_sma9?.toFixed(2) ?? "—"}</div>
                          <div>ATR {e.atr14?.toFixed(4) ?? "—"}</div>
                          <div>EMA {e.ema200?.toFixed(2) ?? "—"}</div>
                          <div>SSMA {e.ssma9?.toFixed(2) ?? "—"}</div>
                          <div>Conf {e.confidence.toFixed(2)}</div>
                        </div>
                      </div>
                    ))}
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Portfolio</CardTitle>
              </CardHeader>
              <CardBody>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-xl bg-white/5 p-3 ring-1 ring-white/10">
                    <div className="text-slate-400">Cash</div>
                    <div className="mt-1 text-sm font-semibold text-slate-50">
                      {dash?.portfolio.cash?.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }) ??
                        "—"}
                    </div>
                  </div>
                  <div className="rounded-xl bg-white/5 p-3 ring-1 ring-white/10">
                    <div className="text-slate-400">Realized PnL</div>
                    <div className="mt-1 text-sm font-semibold text-slate-50">
                      {dash?.portfolio.realized_pnl?.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }) ??
                        "—"}
                    </div>
                  </div>
                  <div className="rounded-xl bg-white/5 p-3 ring-1 ring-white/10">
                    <div className="text-slate-400">Exposure</div>
                    <div className="mt-1 text-sm font-semibold text-slate-50">
                      {dash?.portfolio.exposure?.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }) ??
                        "—"}
                    </div>
                  </div>
                  <div className="rounded-xl bg-white/5 p-3 ring-1 ring-white/10">
                    <div className="text-slate-400">Unrealized PnL</div>
                    <div className="mt-1 text-sm font-semibold text-slate-50">
                      {dash?.portfolio.unrealized_pnl?.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }) ??
                        "—"}
                    </div>
                  </div>
                </div>

                <div className="mt-4">
                  <div className="text-xs font-semibold text-slate-200">Open Positions</div>
                  <div className="mt-2 space-y-2">
                    {Object.values(dash?.portfolio.positions ?? {}).length === 0 ? (
                      <div className="text-xs text-slate-500">No open positions.</div>
                    ) : (
                      Object.values(dash?.portfolio.positions ?? {}).map((p) => (
                        <div key={p.ticker} className="rounded-xl bg-white/5 p-3 ring-1 ring-white/10">
                          <div className="flex items-center justify-between">
                            <div className="text-xs font-semibold text-slate-100">{p.ticker}</div>
                            <div className="text-xs text-slate-400">Qty {p.qty.toFixed(2)}</div>
                          </div>
                          <div className="mt-2 grid grid-cols-3 gap-2 text-[11px] text-slate-400">
                            <div>Avg {p.avg_price.toFixed(2)}</div>
                            <div>SL {p.stop_loss.toFixed(2)}</div>
                            <div>TP {p.take_profit.toFixed(2)}</div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-12">
          {/* Upload */}
          <div className="xl:col-span-12">
            <DatasetUploadCard onUploaded={() => refresh().catch(() => {})} />
          </div>

          {/* Allocation */}
          <Card className="xl:col-span-4">
            <CardHeader>
              <CardTitle>Allocation</CardTitle>
            </CardHeader>
            <CardBody>
              {allocData.length === 0 ? (
                <div className="text-xs text-slate-500">No allocations yet (no open positions).</div>
              ) : (
                <div className="h-[240px]">
                  <ResponsiveContainer>
                    <PieChart>
                      <RTooltip
                        content={({ active, payload }) => {
                          if (!active || !payload || payload.length === 0) return null;
                          const p: any = payload[0];
                          return (
                            <div className="rounded-2xl border border-white/10 bg-ink-900/80 px-3 py-2 text-xs text-slate-200 shadow-glass backdrop-blur-md">
                              <div className="font-semibold">{p.name}</div>
                              <div className="text-slate-400">{(p.value * 100).toFixed(2)}%</div>
                            </div>
                          );
                        }}
                      />
                      <Pie
                        data={allocData}
                        dataKey="value"
                        nameKey="name"
                        outerRadius={86}
                        innerRadius={52}
                        stroke="rgba(255,255,255,0.10)"
                        fill="rgba(59,130,246,0.35)"
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
              <div className="mt-2 grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                {allocData.slice(0, 6).map((a) => (
                  <div key={a.name} className="flex items-center justify-between rounded-lg bg-white/5 px-2 py-1 ring-1 ring-white/10">
                    <span className="text-slate-200">{a.name}</span>
                    <span>{(a.value * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>

          {/* Trade History */}
          <Card className="xl:col-span-5">
            <CardHeader>
              <CardTitle>Trade History</CardTitle>
            </CardHeader>
            <CardBody>
              <div className="max-h-[260px] overflow-auto pr-2">
                <table className="w-full text-xs">
                  <thead className="text-slate-400">
                    <tr className="text-left">
                      <th className="pb-2">Time</th>
                      <th className="pb-2">Ticker</th>
                      <th className="pb-2">Side</th>
                      <th className="pb-2">PnL</th>
                      <th className="pb-2">SL</th>
                      <th className="pb-2">TP</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades
                      .slice()
                      .reverse()
                      .slice(0, 80)
                      .map((t, i) => (
                        <tr key={`${t.timestamp}-${t.ticker}-${i}`} className="border-t border-white/5">
                          <td className="py-2 text-slate-400">{String(t.timestamp).slice(0, 19).replace("T", " ")}</td>
                          <td className="py-2 font-medium text-slate-100">{t.ticker}</td>
                          <td className="py-2">
                            <Badge tone={toneForSignal(t.side)}>{t.side}</Badge>
                          </td>
                          <td className={`py-2 ${t.pnl >= 0 ? "text-emerald-200" : "text-red-200"}`}>
                            {t.pnl === undefined ? "—" : Number(t.pnl).toFixed(2)}
                          </td>
                          <td className="py-2 text-slate-400">{t.stop_loss ? Number(t.stop_loss).toFixed(2) : "—"}</td>
                          <td className="py-2 text-slate-400">{t.take_profit ? Number(t.take_profit).toFixed(2) : "—"}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </CardBody>
          </Card>

          {/* Multi-asset performance */}
          <Card className="xl:col-span-9">
            <CardHeader>
              <CardTitle>Multi-Asset Performance</CardTitle>
              <div className="mt-1 text-xs text-slate-400">Equity curve + normalized asset performance (backend-computed)</div>
            </CardHeader>
            <CardBody>
              <MultiAssetPerformanceChart
                equityCurve={dash?.equity_curve ?? []}
                assetPerf={dash?.asset_performance ?? []}
              />
            </CardBody>
          </Card>

          {/* System Health */}
          <Card className="xl:col-span-3">
            <CardHeader>
              <CardTitle>System Health</CardTitle>
            </CardHeader>
            <CardBody>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-2 ring-1 ring-white/10">
                  <span className="text-slate-400">Backend</span>
                  <Badge tone={system?.ok ? "buy" : "sell"}>{system?.ok ? "Connected" : "Disconnected"}</Badge>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-2 ring-1 ring-white/10">
                  <span className="text-slate-400">Loaded Assets</span>
                  <span className="text-slate-200">{system?.assets_loaded ?? dash?.assets.length ?? 0}</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-2 ring-1 ring-white/10">
                  <span className="text-slate-400">Macro</span>
                  <Badge tone={system?.macro_loaded ? "info" : "neutral"}>
                    {system?.macro_loaded ? "Loaded" : "Not loaded"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-2 ring-1 ring-white/10">
                  <span className="text-slate-400">Replay Progress</span>
                  <span className="text-slate-200">
                    {dash?.timeline.step ?? 0} / {dash?.timeline.total ?? 0}
                  </span>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}

