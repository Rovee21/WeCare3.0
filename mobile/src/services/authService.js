import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'wecare_session_token';
const PROFILE_KEY = 'wecare_user_profile';

// Stub: replace with real API call when backend is ready
export async function enrollWithCode(code) {
  // TODO: POST /api/enroll { code }
  // Returns: { token, language, participantId, weekNumber, group }
  const mockResponse = {
    token: 'mock-token-' + code,
    language: 'en',
    participantId: '00142',
    weekNumber: 2,
    group: 'Treatment',
  };
  await SecureStore.setItemAsync(TOKEN_KEY, mockResponse.token);
  await SecureStore.setItemAsync(PROFILE_KEY, JSON.stringify(mockResponse));
  return mockResponse;
}

export async function getStoredToken() {
  return await SecureStore.getItemAsync(TOKEN_KEY);
}

export async function getStoredProfile() {
  const raw = await SecureStore.getItemAsync(PROFILE_KEY);
  return raw ? JSON.parse(raw) : null;
}

export async function logout() {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(PROFILE_KEY);
}

export async function deleteAccount() {
  // TODO: DELETE /api/account
  await logout();
}
