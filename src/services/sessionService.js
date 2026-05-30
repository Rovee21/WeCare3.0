import { apiFetch } from './api';

export async function getTodaysSession() {
  return await apiFetch('/api/sessions/today/');
}

export async function getAllSessions() {
  return await apiFetch('/api/sessions/');
}

export async function markAsRead(sessionId) {
  return await apiFetch(`/api/sessions/${sessionId}/read/`, { method: 'POST' });
}

export async function logEngagement(eventData) {
  return await apiFetch('/api/engagement/', {
    method: 'POST',
    body: JSON.stringify(eventData),
  });
}
