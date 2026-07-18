import * as SecureStore from 'expo-secure-store';

// Change this to your machine's local IP when testing on a physical device
// e.g. 'http://192.168.1.42:8000'
export const BASE_URL = __DEV__ ? 'http://10.0.0.16:8000/api' : 'https://your-production-domain.com/api';

const TOKEN_KEY = 'wecare_session_token';

export async function getToken() {
  return await SecureStore.getItemAsync(TOKEN_KEY);
}
