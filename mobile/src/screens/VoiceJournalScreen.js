import {
  requestRecordingPermissionsAsync,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioPlayer,
  useAudioPlayerStatus,
} from 'expo-audio';
import React, { useEffect, useRef, useState } from 'react';
import {
  Alert,
  Animated,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Slider from '@react-native-community/slider';
import { Colors } from '../constants/colors';
import { scaleFont } from '../constants/typography';

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

  // Playback of the just-recorded file on the confirmation screen — purely local file
  // playback, no upload/network involved yet.
  const playbackPlayer = useAudioPlayer(savedUri || undefined);
  const playbackStatus = useAudioPlayerStatus(playbackPlayer);
  const [isSeeking, setIsSeeking] = useState(false);
  const [seekValue, setSeekValue] = useState(0);

  // Landing-screen animations: the "View History" button fades out and the mic circle
  // grows while recording is in progress, then both reverse on re-record.
  const historyOpacity = useRef(new Animated.Value(1)).current;
  const micScale = useRef(new Animated.Value(1)).current;

  function animateRecordingStart() {
    Animated.parallel([
      Animated.timing(historyOpacity, { toValue: 0, duration: 250, useNativeDriver: true }),
      Animated.timing(micScale, { toValue: 1.2, duration: 250, useNativeDriver: true }),
    ]).start();
  }

  function animateRecordingReset() {
    Animated.parallel([
      Animated.timing(historyOpacity, { toValue: 1, duration: 250, useNativeDriver: true }),
      Animated.timing(micScale, { toValue: 1, duration: 250, useNativeDriver: true }),
    ]).start();
  }

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
      animateRecordingStart();

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
    animateRecordingReset();
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
          <TouchableOpacity
            testID="voice-journal-playback-button"
            style={styles.playbackButton}
            onPress={() => (playbackStatus.playing ? playbackPlayer.pause() : playbackPlayer.play())}
          >
            <Text style={styles.playbackButtonText}>
              {playbackStatus.playing ? '⏸ Pause' : '▶ Play Recording'}
            </Text>
          </TouchableOpacity>
          <View style={styles.seekBarContainer}>
            <Slider
              testID="voice-journal-playback-seekbar"
              style={styles.seekBar}
              minimumValue={0}
              maximumValue={playbackStatus.duration || 1}
              value={isSeeking ? seekValue : playbackStatus.currentTime}
              minimumTrackTintColor={Colors.accent}
              maximumTrackTintColor={Colors.border}
              thumbTintColor={Colors.accent}
              onSlidingStart={() => setIsSeeking(true)}
              onValueChange={setSeekValue}
              onSlidingComplete={value => {
                setIsSeeking(false);
                playbackPlayer.seekTo(value);
              }}
            />
            <View style={styles.seekTimeRow}>
              <Text style={styles.seekTimeText}>
                {formatTime(Math.floor(isSeeking ? seekValue : playbackStatus.currentTime))}
              </Text>
              <Text style={styles.seekTimeText}>{formatTime(Math.floor(playbackStatus.duration || 0))}</Text>
            </View>
          </View>
          <TouchableOpacity testID="voice-journal-submit-button" style={styles.submitButton} onPress={handleSubmit}>
            <Text style={styles.submitButtonText}>✓ Yes, Submit</Text>
          </TouchableOpacity>
          <TouchableOpacity testID="voice-journal-rerecord-button" style={styles.reRecordButton} onPress={handleReRecord}>
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
          <Animated.View style={{ transform: [{ scale: micScale }] }}>
            <TouchableOpacity
              testID="voice-journal-record-button"
              style={[styles.recordButton, isRecording && styles.recordButtonActive]}
              onPress={isRecording ? stopRecording : startRecording}
              activeOpacity={0.8}
            >
              <Text style={styles.micIcon}>🎙️</Text>
              <Text style={styles.recordButtonText}>
                {isRecording ? 'RECORDING...\nTAP TO STOP' : 'PRESS TO\nRECORD'}
              </Text>
            </TouchableOpacity>
          </Animated.View>
          <Text style={styles.timerText}>
            {formatTime(recordingTime)} / {formatTime(maxTime)}
          </Text>
          <Animated.View
            style={{ opacity: historyOpacity }}
            pointerEvents={isRecording ? 'none' : 'auto'}
          >
            <TouchableOpacity
              testID="voice-journal-history-button"
              style={styles.historyButton}
              onPress={() => navigation.navigate('VoiceJournalHistory')}
              activeOpacity={0.85}
            >
              <Text style={styles.historyButtonText}>📜 View History</Text>
            </TouchableOpacity>
          </Animated.View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scrollContainer: { flexGrow: 1, padding: 20 },
  dateText: { fontSize: scaleFont(24), fontWeight: 'bold', textAlign: 'center', marginTop: 20, marginBottom: 20, color: Colors.textPrimary },
  questionContainer: { backgroundColor: Colors.cardBackground, padding: 25, borderRadius: 20, marginBottom: 20, elevation: 3 },
  questionText: { fontSize: scaleFont(20), textAlign: 'center', color: Colors.textPrimary, lineHeight: 34 },
  instructionText: { fontSize: scaleFont(16), color: Colors.textSecondary, textAlign: 'center', marginBottom: 20, fontStyle: 'italic' },
  recordingArea: { flex: 1, justifyContent: 'center', alignItems: 'center', minHeight: 300 },
  recordButton: { width: 200, height: 200, borderRadius: 100, backgroundColor: Colors.primary, justifyContent: 'center', alignItems: 'center', elevation: 8 },
  recordButtonActive: { backgroundColor: Colors.accent },
  micIcon: { fontSize: 60, marginBottom: 10 }, // decorative icon glyph, not reading text — left unscaled
  // Deliberately NOT run through scaleFont(): this label sits inside a fixed 200x200
  // circle across two lines ("RECORDING...\nTAP TO STOP") — the full body-text scale
  // would risk it overflowing the circle, so it gets a smaller, hand-picked bump instead.
  recordButtonText: { fontSize: 17, fontWeight: 'bold', color: Colors.white, textAlign: 'center' },
  timerText: { fontSize: scaleFont(22), fontWeight: 'bold', marginTop: 20, color: Colors.textPrimary },
  historyButton: {
    marginTop: 28,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 18,
    backgroundColor: Colors.accentLight,
  },
  historyButtonText: { fontSize: scaleFont(14), fontWeight: '600', color: Colors.accent },
  confirmationContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 30 },
  confirmTitle: { fontSize: scaleFont(28), fontWeight: 'bold', color: Colors.textPrimary, marginBottom: 15 },
  confirmDuration: { fontSize: scaleFont(20), color: Colors.textSecondary, marginBottom: 20 },
  confirmQuestion: { fontSize: scaleFont(20), color: Colors.textPrimary, textAlign: 'center', marginBottom: 30, lineHeight: 34 },
  playbackButton: { backgroundColor: Colors.primaryLight, padding: 16, borderRadius: 25, width: '100%', marginBottom: 10 },
  playbackButtonText: { fontSize: scaleFont(18), fontWeight: 'bold', color: Colors.white, textAlign: 'center' },
  seekBarContainer: { width: '100%', marginBottom: 15 },
  seekBar: { width: '100%', height: 40 },
  seekTimeRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: -4, paddingHorizontal: 4 },
  seekTimeText: { fontSize: scaleFont(13), color: Colors.textSecondary, fontWeight: '500' },
  submitButton: { backgroundColor: Colors.accent, padding: 18, borderRadius: 25, width: '100%', marginBottom: 15 },
  submitButtonText: { fontSize: scaleFont(20), fontWeight: 'bold', color: Colors.white, textAlign: 'center' },
  reRecordButton: { backgroundColor: Colors.primary, padding: 18, borderRadius: 25, width: '100%' },
  reRecordButtonText: { fontSize: scaleFont(20), fontWeight: 'bold', color: Colors.white, textAlign: 'center' },
});