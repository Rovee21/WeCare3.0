import * as SecureStore from 'expo-secure-store';
import { BASE_URL } from './api';

const TOKEN_KEY = 'wecare_session_token';
const PROFILE_KEY = 'wecare_user_profile';

export async function enrollWithCode(code) {
  const url = `${BASE_URL}/enroll/`;
  console.log('Calling:', url);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code.trim().toUpperCase() }),
    });

    console.log('Status:', response.status);
    const data = await response.json();
    console.log('Data:', JSON.stringify(data));

    if (!response.ok) {
      throw new Error(data.detail || 'Invalid enrollment code');
    }

    const profile = {
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
  } catch (e) {
    console.log('Error:', e.message);
    throw e;
  }
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
  await logout();
}