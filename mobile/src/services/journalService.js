import { apiFetch, BASE_URL } from './api';
import { getToken } from './api';

export async function getJournalPrompt() {
  return await apiFetch('/journal/prompt/');
}

export async function directUpload({ audioUri, recordingSeconds, emotionLabel, vjStressLevel }) {
  const token = await getToken();

  const formData = new FormData();
  formData.append('audio', {
    uri: audioUri,
    type: 'audio/m4a',
    name: `recording_${Date.now()}.m4a`,
  });
  formData.append('recording_seconds', String(recordingSeconds));
  formData.append('emotion_label', emotionLabel);
  formData.append('vj_stress_level', String(vjStressLevel));

  const response = await fetch(`${BASE_URL}/journal/direct-upload/`, {
    method: 'POST',
    headers: { Authorization: `Token ${token}` },
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Upload failed');
  return data;
}

export async function getUploadUrl() {
  return await apiFetch('/journal/upload/', { method: 'POST' });
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
  return await apiFetch('/journal/submit/', {
    method: 'POST',
    body: JSON.stringify({
      audio_s3_key: audioS3Key,
      recording_seconds: recordingSeconds,
      vj_stress_level: vjStressLevel ?? null,
    }),
  });
}
