import { apiClient, unwrap } from '../api/client';
import { BASE_URL, getToken } from './api';

export async function getJournalPrompt() {
  return unwrap(await apiClient.GET('/api/journal/prompt/'));
}

type DirectUploadArgs = {
  audioUri: string;
  recordingSeconds: number;
  emotionLabel: string;
  vjStressLevel: number;
};

// drf-spectacular models Django's FileField as a `string` (format: uri) in the OpenAPI
// schema, since OpenAPI has no distinct binary type for multipart fields. That makes the
// generated type for `audio` unusable for an actual file upload, so this call bypasses the
// typed client and talks to the endpoint directly, same as before codegen.
export async function directUpload({ audioUri, recordingSeconds, emotionLabel, vjStressLevel }: DirectUploadArgs) {
  const token = await getToken();

  const formData = new FormData();
  formData.append('audio', {
    uri: audioUri,
    type: 'audio/m4a',
    name: `recording_${Date.now()}.m4a`,
  } as unknown as Blob);
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
  return unwrap(await apiClient.POST('/api/journal/upload/', {}));
}

export async function uploadAudio(uploadUrl: string, audioUri: string) {
  const response = await fetch(audioUri);
  const blob = await response.blob();
  await fetch(uploadUrl, {
    method: 'PUT',
    headers: { 'Content-Type': 'audio/mp4' },
    body: blob,
  });
}

type SubmitJournalEntryArgs = {
  audioS3Key: string;
  recordingSeconds: number;
  vjStressLevel?: number | null;
};

export async function submitJournalEntry({ audioS3Key, recordingSeconds, vjStressLevel }: SubmitJournalEntryArgs) {
  return unwrap(
    await apiClient.POST('/api/journal/submit/', {
      body: {
        audio_s3_key: audioS3Key,
        recording_seconds: recordingSeconds,
        vj_stress_level: vjStressLevel ?? null,
      },
    })
  );
}
