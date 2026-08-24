import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useFocusEffect } from '@react-navigation/native';
import { getUserProfile } from '../services/userService';
import { Colors } from '../constants/colors';
import { scaleFont } from '../constants/typography';

function formatProgramStartDate(isoDate) {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-US', {
    month: 'long', day: 'numeric', year: 'numeric',
  });
}

export default function WaitlistScreen({ navigation }) {
  const { t } = useTranslation();
  const [programStartDate, setProgramStartDate] = useState(null);

  useFocusEffect(
    useCallback(() => {
      getUserProfile()
        .then(p => setProgramStartDate(p.program_start_date ?? null))
        .catch(() => {});
    }, [])
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.emoji}>🕓</Text>
        <Text style={styles.title}>{t('waitlist.title')}</Text>
        <Text style={styles.message}>
          {programStartDate
            ? t('waitlist.messageWithDate', { date: formatProgramStartDate(programStartDate) })
            : t('waitlist.messageSoon')}
        </Text>
        <TouchableOpacity
          style={styles.contactButton}
          onPress={() => navigation.navigate('Contact')}
          activeOpacity={0.85}
        >
          <Text style={styles.contactButtonText}>{t('home.contactUs')}</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  emoji: { fontSize: 48, marginBottom: 16 }, // decorative icon glyph, not reading text — left unscaled
  title: {
    fontSize: scaleFont(22),
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 12,
    textAlign: 'center',
  },
  message: {
    fontSize: scaleFont(15),
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 26,
    marginBottom: 28,
  },
  contactButton: {
    backgroundColor: Colors.primary,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 28,
  },
  contactButtonText: { color: Colors.white, fontWeight: '600', fontSize: scaleFont(15) },
});
