import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import type { Regime, SystemStatus } from "../types/api";

function regimeTone(r?: Regime): "neutral" | "info" | "buy" | "sell" {
  if (!r) return "neutral";
  if (r === "bullish") return "buy";
  if (r === "bearish") return "sell";
  return "info";
}

export function TopNav(props: {
  system?: SystemStatus;
  activeTicker: string;
  regime?: Regime;
  playing: boolean;
  speed: number;
  onPlayPause: () => void;
}) {
  const ok = props.system?.ok ?? false;
  return (
    <div className="sticky top-0 z-30 border-b border-white/10 bg-ink-950/60 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-blue-500/30 to-emerald-500/15 ring-1 ring-white/10" />
          <div>
            <div className="text-sm font-semibold tracking-wide text-slate-100">
              Hedge Fund Risk Modeling System
            </div>
            <div className="text-xs text-slate-400">Local Quant Intelligence Terminal</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge tone={ok ? "buy" : "sell"}>{ok ? "Backend: ONLINE" : "Backend: OFFLINE"}</Badge>
          <Badge tone="info">Replay: {props.playing ? "PLAYING" : "PAUSED"}</Badge>
          <Badge tone="neutral">Ticker: {props.activeTicker || "—"}</Badge>
          <Badge tone={regimeTone(props.regime)}>Regime: {props.regime || "—"}</Badge>
          <Badge tone="neutral">Speed: {props.speed.toFixed(1)}x</Badge>
          <Button variant="ghost" onClick={props.onPlayPause}>
            {props.playing ? "Pause" : "Play"}
          </Button>
        </div>
      </div>
    </div>
  );
}

