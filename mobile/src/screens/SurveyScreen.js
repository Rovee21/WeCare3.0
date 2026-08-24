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
import { Colors } from '../constants/colors';
import { scaleFont } from '../constants/typography';
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
          testID="survey-home-button"
          style={styles.homeButton}
          onPress={() => navigation.reset({ index: 0, routes: [{ name: 'MainTabs' }] })}
        >
          <Text style={styles.homeButtonText}>Go Home</Text>
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
              testID={`survey-emotion-${emotion.label.toLowerCase()}`}
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
              testID={`survey-stress-${level}`}
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
            testID="survey-confirm-button"
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
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 20, paddingTop: 40, paddingBottom: 20 },
  sectionTitle: { fontSize: scaleFont(22), fontWeight: 'bold', color: Colors.textPrimary, textAlign: 'center', marginBottom: 10 },
  stressSubtitle: { fontSize: scaleFont(16), color: Colors.textSecondary, textAlign: 'center', marginBottom: 20 },
  emotionGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginBottom: 30 },
  emotionButton: { width: '30%', aspectRatio: 1, borderRadius: 15, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  emotionButtonSelected: { borderWidth: 3, borderColor: Colors.primary },
  emotionEmoji: { fontSize: scaleFont(32), marginBottom: 4 },
  emotionLabel: { fontSize: scaleFont(13), fontWeight: 'bold', color: Colors.textPrimary },
  stressGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginBottom: 20 },
  stressButton: { width: '18%', aspectRatio: 1, borderRadius: 10, backgroundColor: Colors.cardBackground, borderWidth: 1, borderColor: Colors.border, justifyContent: 'center', alignItems: 'center', marginBottom: 8 },
  stressButtonSelected: { backgroundColor: Colors.primary, borderWidth: 2, borderColor: Colors.primary },
  stressText: { fontSize: scaleFont(18), fontWeight: 'bold', color: Colors.textSecondary },
  stressTextSelected: { color: Colors.white },
  footer: { paddingHorizontal: 20, paddingBottom: 20, paddingTop: 10, backgroundColor: Colors.background },
  confirmButton: { backgroundColor: Colors.accent, padding: 18, borderRadius: 25 },
  confirmButtonDisabled: { opacity: 0.6 },
  confirmText: { fontSize: scaleFont(20), fontWeight: 'bold', color: Colors.white, textAlign: 'center' },
  thankYouContainer: { flex: 1, backgroundColor: Colors.background, justifyContent: 'center', alignItems: 'center', padding: 40 },
  checkmark: { fontSize: 100, color: Colors.primary, marginBottom: 20 }, // decorative icon glyph, not reading text — left unscaled
  thankYouTitle: { fontSize: scaleFont(32), fontWeight: 'bold', color: Colors.textPrimary, marginBottom: 15 },
  thankYouText: { fontSize: scaleFont(22), color: Colors.textSecondary, textAlign: 'center', marginBottom: 10 },
  thankYouSubtext: { fontSize: scaleFont(18), color: Colors.textSecondary, textAlign: 'center', marginBottom: 30 },
  homeButton: { backgroundColor: Colors.accent, padding: 15, borderRadius: 10, width: '100%' },
  homeButtonText: { fontSize: scaleFont(18), color: Colors.white, fontWeight: '600', textAlign: 'center' },
});