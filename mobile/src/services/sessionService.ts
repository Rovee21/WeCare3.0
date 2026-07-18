import { apiClient, unwrap } from '../api/client';
import type { components } from '../generated/schema';

type EngagementLog = components['schemas']['EngagementLog'];

export async function getTodaysSession() {
  return unwrap(await apiClient.GET('/api/sessions/today/'));
}

export async function getAllSessions() {
  return unwrap(await apiClient.GET('/api/sessions/'));
}

export async function markAsRead(courseId: number) {
  return unwrap(
    await apiClient.POST('/api/sessions/{session_id}/read/', {
      params: { path: { session_id: courseId } },
    })
  );
}

export async function logEngagement(eventData: EngagementLog) {
  return unwrap(await apiClient.POST('/api/engagement/', { body: eventData }));
}
