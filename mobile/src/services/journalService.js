import { apiFetch } from './api';

export async function getJournalPrompt() {
  return await apiFetch('/journal/prompt/');
}

export async function directUpload({ audioUri, recordingSeconds, emotionLabel, vjStressLevel }) {
  const { getStoredToken } = await import('./authService');
  const token = await getStoredToken();
  
  console.log('Uploading to:', 'http://192.168.4.133:8000/api/journal/direct-upload/');
  console.log('Audio URI:', audioUri);
  console.log('Token:', token);

  const formData = new FormData();
  formData.append('audio', {
    uri: audioUri,
    type: 'audio/m4a',
    name: `recording_${Date.now()}.m4a`,
  });
  formData.append('recording_seconds', String(recordingSeconds));
  formData.append('emotion_label', emotionLabel);
  formData.append('vj_stress_level', String(vjStressLevel));

  const response = await fetch('http://192.168.4.133:8000/api/journal/direct-upload/', {
    method: 'POST',
    headers: {
      'Authorization': `Token ${token}`,
    },
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || 'Upload failed');
  }

  return data;
}