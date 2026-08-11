import { api } from "./client";

export interface AlertOut {
  id: number;
  machine_id: number;
  severity: string;
  alert_type: string;
  title: string;
  description?: string;
  confidence?: number;
  status: string;
  evidence?: string;
  recommended_action?: string;
  created_at?: string;
  resolved_at?: string;
}

export interface AlertCreate {
  machine_id: number;
  severity?: string;
  alert_type?: string;
  title: string;
  description?: string;
  confidence?: number;
  evidence?: string;
  recommended_action?: string;
}

export const alertsApi = {
  list: (params?: { machine_id?: number; status?: string }) => {
    const qs = new URLSearchParams();
    if (params?.machine_id) qs.set("machine_id", String(params.machine_id));
    if (params?.status) qs.set("status", params.status);
    return api.get<AlertOut[]>(`/alerts/?${qs}`);
  },
  get: (id: number) => api.get<AlertOut>(`/alerts/${id}`),
  create: (data: AlertCreate) => api.post<AlertOut>("/alerts/", data),
  acknowledge: (id: number) => api.patch<AlertOut>(`/alerts/${id}/acknowledge`),
  resolve: (id: number) => api.patch<AlertOut>(`/alerts/${id}/resolve`),
};
