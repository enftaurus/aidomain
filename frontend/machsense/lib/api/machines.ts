import { api } from "./client";

export interface MachineOut {
  id: number;
  machine_code: string;
  name: string;
  description?: string;
  location?: string;
  machine_type?: string;
  status: string;
  health_score?: number;
  rpm?: number;
  temperature?: number;
  vibration_rms?: number;
  kurtosis?: number;
  crest_factor?: number;
  created_at?: string;
  updated_at?: string;
}

export interface MachineCreate {
  machine_code: string;
  name: string;
  description?: string;
  location?: string;
  machine_type?: string;
}

export interface ShutdownRequest {
  reason: string;
  confirmed: boolean;
}

export const machinesApi = {
  list: () => api.get<MachineOut[]>("/machines/"),
  get: (id: number) => api.get<MachineOut>(`/machines/${id}`),
  create: (data: MachineCreate) => api.post<MachineOut>("/machines/", data),
  update: (id: number, data: Partial<MachineCreate & { status: string }>) =>
    api.patch<MachineOut>(`/machines/${id}`, data),
  shutdown: (id: number, payload: ShutdownRequest) =>
    api.post<{ message: string }>(`/machines/${id}/shutdown`, payload),
  start: (id: number) =>
    api.post<{ message: string }>(`/machines/${id}/start`),
  delete: (id: number) =>
    api.delete<{ message: string }>(`/machines/${id}`),
};
