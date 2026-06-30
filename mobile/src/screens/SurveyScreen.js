import React, { useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { directUpload } from '../services/journalService';

export default function SurveyScreen({ navigation, route }) {
  const { audioUri, recordingSeconds } = route.params;
  const [selectedEmotion, setSelectedEmotion] = useState(null);
  const [stressLevel, setStressLevel] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [showThankYou, setShowThankYou] = useState(false);

  const emotions = [
    { label: 'Happy',   emoji: '😊', color: '#FFD93D' },
    { label: 'Sad',     emoji: '😢', color: '#6BCB77' },
    { label: 'Angry',   emoji: '😠', color: '#FF6B6B' },
    { label: 'Anxious', emoji: '😰', color: '#4D96FF' },
    { label: 'Calm',    emoji: '😌', color: '#95E1D3' },
    { label: 'Excited', emoji: '🤩', color: '#FFA07A' },
    { label: 'Tired',   emoji: '😴', color: '#B4A7D6' },
  ];

  const stressLevels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  async function handleConfirm() {
    if (!selectedEmotion || stressLevel === null) {
      Alert.alert('Incomplete', 'Please select both an emotion and stress level');
      return;
    }

    setSubmitting(true);
    try {
      await directUpload({
        audioUri,
        recordingSeconds,
        emotionLabel: selectedEmotion.toLowerCase(),
        vjStressLevel: stressLevel,
      });
      setShowThankYou(true);
    } catch (error) {
      console.error('Upload error:', error);
      Alert.alert('Upload Failed', 'Could not save your recording. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (showThankYou) {
    return (
      <SafeAreaView style={styles.thankYouContainer}>
        <Text style={styles.checkmark}>✓</Text>
        <Text style={styles.thankYouTitle}>All done!</Text>
        <Text style={styles.thankYouText}>Your recording has been saved.</Text>
        <Text style={styles.thankYouSubtext}>Have a wonderful day!</Text>
        <TouchableOpacity
          style={styles.homeButton}
          onPress={() => navigation.navigate('MainTabs')}
        >
          <Text style={styles.homeButtonText}>Go to Home</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.sectionTitle}>How were you feeling?</Text>
        <View style={styles.emotionGrid}>
          {emotions.map(emotion => (
            <TouchableOpacity
              key={emotion.label}
              style={[
                styles.emotionButton,
                { backgroundColor: emotion.color },
                selectedEmotion === emotion.label && styles.emotionButtonSelected,
              ]}
              onPress={() => setSelectedEmotion(emotion.label)}
            >
              <Text style={styles.emotionEmoji}>{emotion.emoji}</Text>
              <Text style={styles.emotionLabel}>{emotion.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.sectionTitle}>Rate your stress level</Text>
        <Text style={styles.stressSubtitle}>1 = Very Low  ·  10 = Very High</Text>
        <View style={styles.stressGrid}>
          {stressLevels.map(level => (
            <TouchableOpacity
              key={level}
              style={[styles.stressButton, stressLevel === level && styles.stressButtonSelected]}
              onPress={() => setStressLevel(level)}
            >
              <Text style={[styles.stressText, stressLevel === level && styles.stressTextSelected]}>
                {level}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      {selectedEmotion && stressLevel !== null && (
        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.confirmButton, submitting && styles.confirmButtonDisabled]}
            onPress={handleConfirm}
            disabled={submitting}
          >
            <Text style={styles.confirmText}>
              {submitting ? 'Saving...' : '✓ Confirm'}
            </Text>
          </TouchableOpacity>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF5E6' },
  content: { padding: 20, paddingTop: 40, paddingBottom: 20 },
  sectionTitle: { fontSize: 22, fontWeight: 'bold', color: '#333', textAlign: 'center', marginBottom: 10 },
  stressSubtitle: { fontSize: 16, color: '#666', textAlign: 'center', marginBottom: 20 },
  emotionGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginBottom: 30 },
  emotionButton: { width: '30%', aspectRatio: 1, borderRadius: 15, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  emotionButtonSelected: { borderWidth: 3, borderColor: '#333' },
  emotionEmoji: { fontSize: 32, marginBottom: 4 },
  emotionLabel: { fontSize: 13, fontWeight: 'bold', color: '#333' },
  stressGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginBottom: 20 },
  stressButton: { width: '18%', aspectRatio: 1, borderRadius: 10, backgroundColor: '#E8E8E8', justifyContent: 'center', alignItems: 'center', marginBottom: 8 },
  stressButtonSelected: { backgroundColor: '#FFB366', borderWidth: 2, borderColor: '#333' },
  stressText: { fontSize: 18, fontWeight: 'bold', color: '#666' },
  stressTextSelected: { color: '#333' },
  footer: { paddingHorizontal: 20, paddingBottom: 20, paddingTop: 10, backgroundColor: '#FFF5E6' },
  confirmButton: { backgroundColor: '#4CAF50', padding: 18, borderRadius: 25 },
  confirmButtonDisabled: { opacity: 0.6 },
  confirmText: { fontSize: 20, fontWeight: 'bold', color: 'white', textAlign: 'center' },
  thankYouContainer: { flex: 1, backgroundColor: '#FFF5E6', justifyContent: 'center', alignItems: 'center', padding: 40 },
  checkmark: { fontSize: 100, color: '#4CAF50', marginBottom: 20 },
  thankYouTitle: { fontSize: 32, fontWeight: 'bold', color: '#333', marginBottom: 15 },
  thankYouText: { fontSize: 22, color: '#666', textAlign: 'center', marginBottom: 10 },
  thankYouSubtext: { fontSize: 18, color: '#888', textAlign: 'center', marginBottom: 30 },
  homeButton: { backgroundColor: '#4CAF50', padding: 15, borderRadius: 10, width: '100%' },
  homeButtonText: { fontSize: 18, color: 'white', fontWeight: '600', textAlign: 'center' },
});