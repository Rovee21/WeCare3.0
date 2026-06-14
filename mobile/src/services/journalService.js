import { apiFetch } from './api';

export async function getJournalPrompt() {
  return await apiFetch('/api/journal/prompt/');
}

export async function getUploadUrl() {
  return await apiFetch('/api/journal/upload-url/', { method: 'POST' });
}

export async function uploadAudio(uploadUrl, audioUri) {
  const response = await fetch(audioUri);
  const blob = await response.blob();
  await fetch(uploadUrl, {
    method: 'PUT',
    headers: { 'Content-Type': 'audio/mp4' },
    body: blob,
  });
}

export async function submitJournalEntry({ audioS3Key, recordingSeconds, vjStressLevel }) {
  return await apiFetch('/api/journal/submit/', {
    method: 'POST',
    body: JSON.stringify({
      audio_s3_key: audioS3Key,
      recording_seconds: recordingSeconds,
      vj_stress_level: vjStressLevel ?? null,
    }),
  });
}
