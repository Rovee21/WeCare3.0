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
        <Text style={styles.greeting}>{greeting}</Text>

        {/* Courses card */}
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('Courses')}
          activeOpacity={0.85}
        >
          <View style={styles.cardBody}>
            <View style={styles.cardLeft}>
              {todaysSession && (
                <Text style={styles.weekLabel}>WEEK {todaysSession.week_number}</Text>
              )}
              <Text style={styles.cardTitle}>{t('home.coursesCard')}</Text>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{t('home.coursesNotWatched', { n: 2 })}</Text>
              </View>
              {todaysSession && (
                <Text style={styles.cardSub}>{todaysSession.title}</Text>
              )}
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
  greeting: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 24,
  },
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
  weekLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 0.8,
    marginBottom: 4,
  },
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
    marginBottom: 6,
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
