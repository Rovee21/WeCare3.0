import * as SecureStore from 'expo-secure-store';

// EXPO_PUBLIC_API_URL overrides this — set it in mobile/.env for physical-device testing
// (your machine's LAN IP, e.g. http://192.168.1.42:8000) or Android emulator (http://10.0.2.2:8000).
// iOS Simulator shares the host's network namespace, so localhost works there by default.
export const BASE_URL = __DEV__
  ? (process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000') + '/api'
  : 'https://your-production-domain.com/api';

const TOKEN_KEY = 'wecare_session_token';

export async function getToken() {
  return await SecureStore.getItemAsync(TOKEN_KEY);
}
