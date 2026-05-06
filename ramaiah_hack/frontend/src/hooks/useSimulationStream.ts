import { useEffect, useRef } from "react";
import type { SSEEvent } from "../types/api";
import { API_BASE } from "../services/api";

export function useSimulationStream(onEvent: (evt: SSEEvent) => void) {
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/simulation-stream`);
    es.onmessage = (msg) => {
      try {
        const evt = JSON.parse(msg.data) as SSEEvent;
        onEventRef.current(evt);
      } catch {
        // ignore parse errors
      }
    };
    es.onerror = () => {
      // EventSource auto-reconnects; keep calm
    };
    return () => es.close();
  }, []);
}

