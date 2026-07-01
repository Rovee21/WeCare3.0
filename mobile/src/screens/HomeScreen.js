import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { getTodaysSession } from '../services/sessionService';
import { getStoredProfile } from '../services/authService';
import { Colors } from '../constants/colors';

function IconCircle({ emoji }) {
  return (
    <View style={styles.iconCircle}>
      <Text style={styles.iconEmoji}>{emoji}</Text>
    </View>
  );
}

export default function HomeScreen({ navigation }) {
  const { t } = useTranslation();
  const [todaysSession, setTodaysSession] = useState(null);
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    getTodaysSession().then(setTodaysSession);
    getStoredProfile().then(setProfile);
  }, []);

  const name = profile?.label ?? '';
  const greeting = `${t('home.greeting')}${name ? ' ' + name : ''}`;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.greeting}>{greeting}</Text>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {profile?.participantId ? profile.participantId.slice(-2) : ''}
            </Text>
          </View>
        </View>

        {/* Today's session featured card */}
        {todaysSession && (
          <TouchableOpacity
            style={styles.sessionCard}
            onPress={() => navigation.navigate('Courses', {
              screen: 'DailySession',
              params: { course: todaysSession },
            })}
            activeOpacity={0.85}
          >
            <Text style={styles.sessionLabel}>
              {t('home.todaysSession')} · WEEK {todaysSession.week_number}
            </Text>
            <Text style={styles.sessionTitle}>{todaysSession.title}</Text>
            <View style={styles.startButton}>
              <Text style={styles.startButtonText}>{t('home.startSession')}</Text>
            </View>
          </TouchableOpacity>
        )}

        {/* Courses card */}
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('Courses')}
          activeOpacity={0.85}
        >
          <View style={styles.cardBody}>
            <View style={styles.cardLeft}>
              <Text style={styles.cardTitle}>{t('home.coursesCard')}</Text>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{t('home.coursesNotWatched', { n: 2 })}</Text>
              </View>
            </View>
            <IconCircle emoji="📚" />
          </View>
        </TouchableOpacity>

        {/* Voice Journal card */}
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('Journal')}
          activeOpacity={0.85}
        >
          <View style={styles.cardBody}>
            <View style={styles.cardLeft}>
              <Text style={styles.cardTitle}>{t('home.voiceJournal')}</Text>
              <Text style={styles.cardSub}>{t('home.lastEntry')}</Text>
            </View>
            <IconCircle emoji="🎙️" />
          </View>
        </TouchableOpacity>

        {/* Contact Us card */}
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('Contact')}
          activeOpacity={0.85}
        >
          <View style={styles.cardBody}>
            <View style={styles.cardLeft}>
              <Text style={styles.cardTitle}>{t('home.contactUs')}</Text>
            </View>
            <IconCircle emoji="📞" />
          </View>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: 20, paddingTop: 12 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  greeting: {
    fontSize: 26,
    fontWeight: '700',
    color: Colors.textPrimary,
    flex: 1,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 12,
  },
  avatarText: { fontSize: 13, fontWeight: '600', color: Colors.textSecondary },
  sessionCard: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    padding: 20,
    marginBottom: 14,
  },
  sessionLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  sessionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.white,
    marginBottom: 16,
  },
  startButton: {
    backgroundColor: Colors.accent,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignSelf: 'flex-start',
  },
  startButtonText: { color: Colors.white, fontWeight: '600', fontSize: 14 },
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 20,
    marginBottom: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  cardBody: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cardLeft: { flex: 1, paddingRight: 12 },
  cardTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 8,
  },
  badge: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.accentLight,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  badgeText: {
    fontSize: 12,
    color: Colors.accent,
    fontWeight: '500',
  },
  cardSub: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  iconCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconEmoji: { fontSize: 22 },
});
