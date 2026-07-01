import { apiFetch } from './api';

export async function getTodaysSession() {
  return await apiFetch('/sessions/today/');
}

export async function getAllSessions() {
  return await apiFetch('/sessions/');
}

export async function markAsRead(courseId) {
  return await apiFetch(`/sessions/${courseId}/read/`, { method: 'POST' });
}

export async function logEngagement(eventData) {
  return await apiFetch('/engagement/', {
    method: 'POST',
    body: JSON.stringify(eventData),
  });
}
