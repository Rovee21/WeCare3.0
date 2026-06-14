import { apiFetch } from './api';

export async function getUserProfile() {
  return await apiFetch('/api/profile/');
}
