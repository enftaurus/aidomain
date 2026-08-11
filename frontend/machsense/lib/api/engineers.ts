import { api } from "./client";
import type { UserOut } from "./auth";

export interface AssignmentOut {
  id: number;
  engineer_id: number;
  machine_id: number;
  assigned_at?: string;
  assigned_by?: number;
  is_active: boolean;
}

export const engineersApi = {
  list: () => api.get<UserOut[]>("/engineers/"),
  get: (id: number) => api.get<UserOut>(`/engineers/${id}`),
  getMachines: (engineerId: number) => api.get<any[]>(`/engineers/${engineerId}/machines`),
  assign: (engineer_id: number, machine_id: number) =>
    api.post<AssignmentOut>("/engineers/assignments", { engineer_id, machine_id }),
  removeAssignment: (assignmentId: number) =>
    api.delete<{ message: string }>(`/engineers/assignments/${assignmentId}`),
  getAllAssignments: () =>
    api.get<AssignmentOut[]>("/engineers/assignments/all"),
  getMachineAssignments: (machineId: number) =>
    api.get<AssignmentOut[]>(`/engineers/assignments/machine/${machineId}`),
};

