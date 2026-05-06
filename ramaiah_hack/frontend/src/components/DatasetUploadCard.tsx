import { useMemo, useState } from "react";
import { api } from "../services/api";
import { Button } from "./ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "./ui/Card";
import { Badge } from "./ui/Badge";

const TARGETS = [
  { name: "oil_dataset.csv", type: "market" as const },
  { name: "equity_dataset.csv", type: "market" as const },
  { name: "multi_asset_dataset.csv", type: "market" as const },
  { name: "macro_dataset.csv", type: "macro" as const }
];

export function DatasetUploadCard(props: { onUploaded: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [target, setTarget] = useState(TARGETS[0].name);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const meta = useMemo(() => TARGETS.find((t) => t.name === target)!, [target]);

  async function upload() {
    if (!file) return;
    setBusy(true);
    setMsg(null);
    try {
      await api.uploadDataset({ file, target_name: target, dataset_type: meta.type });
      setMsg("Uploaded and reloaded.");
      setFile(null);
      props.onUploaded();
    } catch (e: any) {
      setMsg(e?.message ?? "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Dataset Upload</CardTitle>
          <Badge tone="info">Local CSV → backend ingestion</Badge>
        </div>
      </CardHeader>
      <CardBody>
        <div className="space-y-3">
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            <div>
              <div className="text-xs text-slate-400">Target file</div>
              <select
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                {TARGETS.map((t) => (
                  <option key={t.name} value={t.name}>
                    {t.name}
                  </option>
                ))}
              </select>
              <div className="mt-1 text-[11px] text-slate-500">
                Expected: {meta.type === "macro" ? "macro schema" : "market schema"} (backend normalizes)
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-400">CSV file</div>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 file:mr-3 file:rounded-lg file:border-0 file:bg-white/10 file:px-3 file:py-1 file:text-xs file:font-semibold file:text-slate-200 hover:file:bg-white/15"
              />
              <div className="mt-1 text-[11px] text-slate-500">{file ? file.name : "No file selected."}</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button onClick={upload} disabled={busy || !file}>
              {busy ? "Uploading..." : "Upload & Reload"}
            </Button>
            <Button
              variant="ghost"
              onClick={() => api.resetSimulation().then(props.onUploaded).catch(() => {})}
              disabled={busy}
            >
              Reset Simulation
            </Button>
            {msg && <div className="text-xs text-slate-300">{msg}</div>}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

