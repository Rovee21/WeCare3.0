import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { getTodaysSession } from '../services/sessionService';
import { getStoredProfile } from '../services/authService';
import { Colors } from '../constants/colors';

export default function HomeScreen({ navigation }) {
  const { t } = useTranslation();
  const [todaysSession, setTodaysSession] = useState(null);
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    getTodaysSession().then(setTodaysSession);
    getStoredProfile().then(setProfile);
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>{t('home.greeting')}</Text>
            <Text style={styles.welcomeBack}>{t('home.welcomeBack')} 👋</Text>
          </View>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {profile?.participantId ? profile.participantId.slice(-2) : ''}
            </Text>
          </View>
        </View>

        {todaysSession && (
          <TouchableOpacity
            style={styles.sessionCard}
            onPress={() => navigation.navigate('CoursesStack', {
              screen: 'DailySession',
              params: { course: todaysSession },
            })}
          >
            <Text style={styles.sessionLabel}>
              {t('home.todaysSession')} · Week {todaysSession.weekNumber}, Day 3
            </Text>
            <Text style={styles.sessionTitle}>{todaysSession.title}</Text>
            <View style={styles.startButton}>
              <Text style={styles.startButtonText}>{t('home.startSession')}</Text>
            </View>
          </TouchableOpacity>
        )}

        <View style={styles.cardRow}>
          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigation.navigate('Courses')}
          >
            <Text style={styles.cardIcon}>📖</Text>
            <Text style={styles.cardTitle}>{t('home.goToCourses')}</Text>
            <Text style={styles.cardSubtitle}>{t('home.goToCoursesSubtitle')}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionCard}
            onPress={() => navigation.navigate('Journal')}
          >
            <Text style={styles.cardIcon}>🎙️</Text>
            <Text style={styles.cardTitle}>{t('home.voiceJournal')}</Text>
            <Text style={styles.cardSubtitle}>
              {t('home.voiceJournalSubtitle', { week: profile?.weekNumber ?? 1 })}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: 20 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 24,
  },
  greeting: { fontSize: 16, color: Colors.textSecondary },
  welcomeBack: { fontSize: 22, fontWeight: '700', color: Colors.textPrimary },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.cardBackground,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  avatarText: { fontSize: 13, fontWeight: '600', color: Colors.textSecondary },
  sessionCard: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  sessionLabel: { fontSize: 13, color: 'rgba(255,255,255,0.7)', marginBottom: 6 },
  sessionTitle: { fontSize: 20, fontWeight: '700', color: Colors.white, marginBottom: 16 },
  startButton: {
    backgroundColor: Colors.accent,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignSelf: 'flex-start',
  },
  startButtonText: { color: Colors.white, fontWeight: '600', fontSize: 14 },
  cardRow: { flexDirection: 'row', gap: 12 },
  actionCard: {
    flex: 1,
    backgroundColor: Colors.cardBackground,
    borderRadius: 16,
    padding: 16,
  },
  cardIcon: { fontSize: 24, marginBottom: 8 },
  cardTitle: { fontSize: 15, fontWeight: '600', color: Colors.textPrimary, marginBottom: 4 },
  cardSubtitle: { fontSize: 12, color: Colors.textSecondary },
});
