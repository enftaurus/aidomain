import { api, BASE_URL } from "./client";

export interface ReportOut {
  id: number;
  machine_id: number;
  alert_id?: number;
  maintenance_id?: number;
  report_type: string;
  trigger_event?: string;
  ai_result?: string;
  html_path?: string;
  pdf_path?: string;
  generated_at?: string;
}

export const reportsApi = {
  list: (params?: { machine_id?: number; report_type?: string }) => {
    const qs = new URLSearchParams();
    if (params?.machine_id) qs.set("machine_id", String(params.machine_id));
    if (params?.report_type) qs.set("report_type", params.report_type);
    return api.get<ReportOut[]>(`/reports/?${qs}`);
  },
  get: (id: number) => api.get<ReportOut>(`/reports/${id}`),
  generate: (machine_id: number) =>
    api.post<{ message: string }>(`/reports/generate/${machine_id}`),
  downloadUrl: (id: number) => `${BASE_URL}/reports/${id}/download`,
};
