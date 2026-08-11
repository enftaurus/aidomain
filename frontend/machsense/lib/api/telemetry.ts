import { api } from "./client";

export interface TelemetryOut {
  id: number;
  machine_id: number;
  timestamp?: string;
  rpm?: number;
  temperature?: number;
  vibration_rms?: number;
  kurtosis?: number;
  crest_factor?: number;
  dominant_frequency?: number;
  health_score?: number;
}

export interface TelemetryCreate {
  machine_id: number;
  rpm?: number;
  temperature?: number;
  accel_x?: number;
  accel_y?: number;
  accel_z?: number;
  vibration_rms?: number;
  kurtosis?: number;
  crest_factor?: number;
  dominant_frequency?: number;
  health_score?: number;
}

export const telemetryApi = {
  getRecent: (machine_id: number, limit = 60) =>
    api.get<TelemetryOut[]>(`/telemetry/${machine_id}?limit=${limit}`),
  ingest: (data: TelemetryCreate) =>
    api.post<TelemetryOut>("/telemetry/ingest", data),
  injectMock: (machine_id: number, mode: "normal" | "warning" | "critical" = "normal") =>
    api.post<TelemetryOut>(`/telemetry/mock/${machine_id}?mode=${mode}`),
};
