import { api } from "./client";

export interface NotificationOut {
  id: number;
  recipient_id: number;
  machine_id?: number;
  alert_id?: number;
  maintenance_id?: number;
  type: string;
  title: string;
  message?: string;
  is_read: boolean;
  created_at?: string;
}

export const notificationsApi = {
  list: (unread_only = false) =>
    api.get<NotificationOut[]>(`/notifications/?unread_only=${unread_only}`),
  markRead: (id: number) => api.patch<{ message: string }>(`/notifications/${id}/read`),
  markAllRead: () => api.post<{ message: string }>("/notifications/read-all"),
};
