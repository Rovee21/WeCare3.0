import * as SecureStore from 'expo-secure-store';
import { apiClient, unwrap } from '../api/client';

const TOKEN_KEY = 'wecare_session_token';
const PROFILE_KEY = 'wecare_user_profile';

export type StoredProfile = {
  token: string;
  language: string;
  participantId: string;
  weekNumber: number;
  group1: string;
  group2: string;
  group3: string;
  relationship: string;
};

export async function enrollWithCode(code: string): Promise<StoredProfile> {
  const data = unwrap(
    await apiClient.POST('/api/enroll/', {
      body: { code: code.trim().toUpperCase() },
    })
  );

  const profile: StoredProfile = {
    token: data.token,
    language: data.language,
    participantId: data.participant_id,
    weekNumber: data.week_number,
    group1: data.group1,
    group2: data.group2,
    group3: data.group3,
    relationship: data.adrd_relationship_group,
  };

  await SecureStore.setItemAsync(TOKEN_KEY, profile.token);
  await SecureStore.setItemAsync(PROFILE_KEY, JSON.stringify(profile));
  return profile;
}

export async function getStoredToken() {
  return await SecureStore.getItemAsync(TOKEN_KEY);
}

export async function getStoredProfile(): Promise<StoredProfile | null> {
  const raw = await SecureStore.getItemAsync(PROFILE_KEY);
  return raw ? JSON.parse(raw) : null;
}

export async function logout() {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(PROFILE_KEY);
}

// TODO: this only clears local SecureStore — it never calls DELETE /api/account/,
// so the participant's data isn't actually deleted server-side. The endpoint exists
// (participants/views.py delete_account) but nothing in the app calls it yet.
export async function deleteAccount() {
  await logout();
}
