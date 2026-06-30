import * as SecureStore from 'expo-secure-store';

// Change this to your machine's local IP when testing on a physical device
// e.g. 'http://192.168.1.42:8000'
export const BASE_URL = __DEV__ ? 'http://192.168.4.196:8000/api' : 'https://your-production-domain.com/api';

const TOKEN_KEY = 'wecare_session_token';

export async function getToken() {
  return await SecureStore.getItemAsync(TOKEN_KEY);
}

export async function apiFetch(path, options = {}) {
  const token = await getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Token ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const error = new Error(body.detail || `HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) return null;
  return response.json();
}
