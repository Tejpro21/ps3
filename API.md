## API endpoints

### Health / discovery
- `GET /system-status`
- `GET /available-assets`

### Dashboard / analytics (backend computed)
- `GET /dashboard-data`
- `GET /portfolio-state`
- `GET /performance-metrics`
- `GET /trade-logs`

### Replay control + stream
- `POST /start-simulation`
  - body: `{ action: "play"|"pause"|"step_next"|"step_prev"|"set_speed"|"set_active", ticker?: string, speed?: number }`
- `GET /simulation-stream` (SSE)

### Local dataset upload (demo UX)
- `POST /upload-dataset?dataset_type=market|macro&target_name=<one of required csv names>`
  - multipart form: `file=@your.csv`
  - Backend reloads datasets immediately; rolls back on parse errors.

### Demo admin
- `POST /reset-simulation`

