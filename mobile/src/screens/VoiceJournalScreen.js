import {
  requestRecordingPermissionsAsync,
  setAudioModeAsync,
  useAudioRecorder,
} from 'expo-audio';
import React, { useEffect, useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function VoiceJournalScreen({ navigation }) {
  const audioRecorder = useAudioRecorder({
    extension: '.m4a',
    sampleRate: 44100,
    numberOfChannels: 1,
    bitRate: 128000,
    android: { outputFormat: 'mpeg4', audioEncoder: 'aac' },
    ios: { audioQuality: 127 },
  });

  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [intervalId, setIntervalId] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [savedUri, setSavedUri] = useState(null);

  const question = 'What was your most memorable experience today as a caregiver? Please share by recording it.';
  const maxTime = 300;

  useEffect(() => {
    requestPermission();
  }, []);

  async function requestPermission() {
    try {
      const permission = await requestRecordingPermissionsAsync();
      if (!permission.granted) {
        Alert.alert('Permission needed', 'We need microphone access to record.');
      }
    } catch (error) {
      console.error('Permission error:', error);
    }
  }

  async function startRecording() {
    try {
      await setAudioModeAsync({ playsInSilentMode: true, allowsRecording: true });
      await audioRecorder.prepareToRecordAsync();
      await audioRecorder.record();
      setIsRecording(true);
      setRecordingTime(0);

      const id = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= maxTime) {
            stopRecording();
            return maxTime;
          }
          return prev + 1;
        });
      }, 1000);
      setIntervalId(id);
    } catch (err) {
      Alert.alert('Error', 'Failed to start recording');
      console.error(err);
    }
  }

  async function stopRecording() {
    try {
      if (intervalId) {
        clearInterval(intervalId);
        setIntervalId(null);
      }
      await audioRecorder.stop();
      setIsRecording(false);

      const uri = audioRecorder.uri;
      if (!uri) {
        Alert.alert('Error', 'Recording failed — no file saved');
        return;
      }
      setSavedUri(uri);
      setShowConfirmation(true);
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to stop recording');
    }
  }

  function handleReRecord() {
    setShowConfirmation(false);
    setRecordingTime(0);
    setSavedUri(null);
  }

  function handleSubmit() {
    setShowConfirmation(false);
    navigation.navigate('Survey', {
      audioUri: savedUri,
      recordingSeconds: recordingTime,
    });
  }

  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function formatDate() {
    return new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
    });
  }

  if (showConfirmation) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.confirmationContainer}>
          <Text style={styles.confirmTitle}>Recording Complete!</Text>
          <Text style={styles.confirmDuration}>Duration: {formatTime(recordingTime)}</Text>
          <Text style={styles.confirmQuestion}>
            Are you sure you want to submit this recording?
          </Text>
          <TouchableOpacity style={styles.submitButton} onPress={handleSubmit}>
            <Text style={styles.submitButtonText}>✓ Yes, Submit</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.reRecordButton} onPress={handleReRecord}>
            <Text style={styles.reRecordButtonText}>🔄 No, Record Again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <Text style={styles.dateText}>{formatDate()}</Text>
        <View style={styles.questionContainer}>
          <Text style={styles.questionText}>{question}</Text>
        </View>
        <Text style={styles.instructionText}>
          Please find a quiet place to record your audio.
        </Text>
        <View style={styles.recordingArea}>
          <TouchableOpacity
            style={[styles.recordButton, isRecording && styles.recordButtonActive]}
            onPress={isRecording ? stopRecording : startRecording}
            activeOpacity={0.8}
          >
            <Text style={styles.micIcon}>🎙️</Text>
            <Text style={styles.recordButtonText}>
              {isRecording ? 'RECORDING...\nTAP TO STOP' : 'PRESS TO\nRECORD'}
            </Text>
          </TouchableOpacity>
          <Text style={styles.timerText}>
            {formatTime(recordingTime)} / {formatTime(maxTime)}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF5E6' },
  scrollContainer: { flexGrow: 1, padding: 20 },
  dateText: { fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginTop: 20, marginBottom: 20, color: '#333' },
  questionContainer: { backgroundColor: 'white', padding: 25, borderRadius: 20, marginBottom: 20, elevation: 3 },
  questionText: { fontSize: 20, textAlign: 'center', color: '#333', lineHeight: 28 },
  instructionText: { fontSize: 16, color: '#666', textAlign: 'center', marginBottom: 20, fontStyle: 'italic' },
  recordingArea: { flex: 1, justifyContent: 'center', alignItems: 'center', minHeight: 300 },
  recordButton: { width: 200, height: 200, borderRadius: 100, backgroundColor: '#FFB366', justifyContent: 'center', alignItems: 'center', elevation: 8 },
  recordButtonActive: { backgroundColor: '#FF6B6B' },
  micIcon: { fontSize: 60, marginBottom: 10 },
  recordButtonText: { fontSize: 16, fontWeight: 'bold', color: '#333', textAlign: 'center' },
  timerText: { fontSize: 22, fontWeight: 'bold', marginTop: 20, color: '#333' },
  confirmationContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 30 },
  confirmTitle: { fontSize: 28, fontWeight: 'bold', color: '#333', marginBottom: 15 },
  confirmDuration: { fontSize: 20, color: '#666', marginBottom: 20 },
  confirmQuestion: { fontSize: 20, color: '#333', textAlign: 'center', marginBottom: 30, lineHeight: 28 },
  submitButton: { backgroundColor: '#4CAF50', padding: 18, borderRadius: 25, width: '100%', marginBottom: 15 },
  submitButtonText: { fontSize: 20, fontWeight: 'bold', color: 'white', textAlign: 'center' },
  reRecordButton: { backgroundColor: '#FFB366', padding: 18, borderRadius: 25, width: '100%' },
  reRecordButtonText: { fontSize: 20, fontWeight: 'bold', color: '#333', textAlign: 'center' },
});