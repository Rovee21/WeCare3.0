import { apiClient, unwrap } from '../api/client';

export async function getUserProfile() {
  return unwrap(await apiClient.GET('/api/profile/'));
}
