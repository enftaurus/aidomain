import { api } from "./client";

export interface MaintenanceOut {
  id: number;
  machine_id: number;
  engineer_id?: number;
  scheduled_by?: number;
  scheduled_at?: string;
  maintenance_type: string;
  description?: string;
  status: string;
  engineer_notes?: string;
  factory_notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MaintenanceCreate {
  machine_id: number;
  engineer_id?: number;
  scheduled_at?: string;
  maintenance_type?: string;
  description?: string;
  factory_notes?: string;
}

export const maintenanceApi = {
  list: (machine_id?: number) => {
    const qs = machine_id ? `?machine_id=${machine_id}` : "";
    return api.get<MaintenanceOut[]>(`/maintenance/${qs}`);
  },
  get: (id: number) => api.get<MaintenanceOut>(`/maintenance/${id}`),
  create: (data: MaintenanceCreate) => api.post<MaintenanceOut>("/maintenance/", data),
  update: (id: number, data: { status?: string; engineer_notes?: string; factory_notes?: string }) =>
    api.patch<MaintenanceOut>(`/maintenance/${id}`, data),
};
