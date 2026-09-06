import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, Image, KeyboardAvoidingView, ScrollView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { enrollWithCode } from '../services/authService';
import { getUserProfile } from '../services/userService';
import { Colors } from '../constants/colors';
import { scaleFont } from '../constants/typography';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'zh', label: '中文 Chinese' },
];

export default function EnrollmentScreen({ navigation }) {
  const { t, i18n } = useTranslation();
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(false);

  async function handleSelectLanguage(langCode) {
    setLanguage(langCode);
    await i18n.changeLanguage(langCode);
  }

  async function handleEnroll() {
    if (!code.trim()) return;
    setLoading(true);
    try {
      await enrollWithCode(code.trim(), language);
      const { registerForPushNotifications, sendTokenToBackend } = await import('../services/notificationService');
      const pushToken = await registerForPushNotifications();
      if (pushToken) {
        sendTokenToBackend(pushToken);
      }

      // A brand-new enrollee can already be waitlisted (their cohort's program_start_date
      // hasn't arrived yet) — route them straight to the waitlist screen, same as a
      // returning waitlisted participant reopening the app.
      let route = 'MainTabs';
      try {
        const profile = await getUserProfile();
        if (profile?.is_waitlisted) {
          route = 'Waitlist';
        }
      } catch (e) {
        // fall back to MainTabs if the profile check fails
      }
      navigation.replace(route);
    } catch {
      Alert.alert('Invalid code', 'Please check your code and try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
        >
          <Image source={require('../../assets/logo.png')} style={styles.logo} resizeMode="contain" />

          <View style={styles.languageToggle}>
            {LANGUAGES.map(lang => (
              <TouchableOpacity
                key={lang.code}
                testID={`enrollment-language-${lang.code}`}
                style={[styles.languagePill, language === lang.code && styles.languagePillActive]}
                onPress={() => handleSelectLanguage(lang.code)}
              >
                <Text style={[styles.languagePillText, language === lang.code && styles.languagePillTextActive]}>
                  {lang.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.card}>
            <Text style={styles.title}>{t('enrollment.title')}</Text>
            <Text style={styles.subtitle}>{t('enrollment.subtitle')}</Text>

            <Text style={styles.inputLabel}>{t('enrollment.userIdLabel')}</Text>
            <TextInput
              testID="enrollment-code-input"
              style={styles.input}
              placeholder={t('enrollment.codePlaceholder')}
              placeholderTextColor={Colors.textSecondary}
              value={code}
              onChangeText={setCode}
              autoCapitalize="none"
              autoCorrect={false}
            />

            <TouchableOpacity
              testID="enrollment-submit-button"
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleEnroll}
              disabled={loading}
            >
              <Text style={styles.buttonText}>{t('enrollment.cta')}</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.privacy}>{t('enrollment.privacy')}</Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    flexGrow: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    paddingVertical: 24,
  },
  logo: {
    width: 120,
    height: 120,
    marginBottom: 24,
  },
  languageToggle: {
    flexDirection: 'row',
    backgroundColor: Colors.white,
    borderRadius: 10,
    padding: 4,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  languagePill: {
    paddingVertical: 8,
    paddingHorizontal: 18,
    borderRadius: 8,
  },
  languagePillActive: {
    backgroundColor: Colors.accentLight,
  },
  languagePillText: {
    fontSize: scaleFont(14),
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  languagePillTextActive: {
    color: Colors.accent,
    fontWeight: '700',
  },
  card: {
    width: '100%',
    backgroundColor: Colors.white,
    borderRadius: 20,
    padding: 28,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3,
  },
  title: {
    fontSize: scaleFont(26),
    fontWeight: '700',
    color: Colors.textPrimary,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: scaleFont(14),
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 28,
  },
  inputLabel: {
    fontSize: scaleFont(13),
    color: Colors.textSecondary,
    marginBottom: 6,
  },
  input: {
    width: '100%',
    height: 50,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 10,
    paddingHorizontal: 16,
    fontSize: scaleFont(16),
    color: Colors.textPrimary,
    backgroundColor: Colors.background,
    marginBottom: 20,
  },
  button: {
    width: '100%',
    height: 50,
    backgroundColor: Colors.accentLight,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.accent,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: {
    color: Colors.accent,
    fontSize: scaleFont(16),
    fontWeight: '600',
  },
  privacy: {
    fontSize: scaleFont(12),
    color: Colors.textSecondary,
    textAlign: 'center',
    paddingTop: 20,
    paddingHorizontal: 32,
  },
});
