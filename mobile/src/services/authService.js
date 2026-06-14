import * as SecureStore from 'expo-secure-store';
import i18n from '../i18n/i18n';
import { apiFetch } from './api';

const TOKEN_KEY = 'wecare_session_token';
const PROFILE_KEY = 'wecare_user_profile';

export async function enrollWithCode(code) {
  const data = await apiFetch('/api/enroll/', {
    method: 'POST',
    body: JSON.stringify({ code }),
  });

  await SecureStore.setItemAsync(TOKEN_KEY, data.token);
  await SecureStore.setItemAsync(PROFILE_KEY, JSON.stringify(data));

  // Set app language from the participant's survey data
  if (data.language && i18n.language !== data.language) {
    await i18n.changeLanguage(data.language);
  }

  return data;
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
  await apiFetch('/api/account/', { method: 'DELETE' });
  await logout();
}
