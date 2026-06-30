import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert, Switch } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { getStoredProfile, deleteAccount } from '../services/authService';
import { Colors } from '../constants/colors';

export default function SettingsScreen({ navigation }) {
  const { t } = useTranslation();
  const [profile, setProfile] = useState(null);
  const [dailyReminders, setDailyReminders] = useState(true);
  const [largerText, setLargerText] = useState(false);

  useEffect(() => { getStoredProfile().then(setProfile); }, []);

  function handleDeleteData() {
    Alert.alert(
      t('settings.deleteConfirmTitle'),
      t('settings.deleteConfirmMessage'),
      [
        { text: t('settings.cancel'), style: 'cancel' },
        {
          text: t('settings.deleteConfirm'),
          style: 'destructive',
          onPress: async () => {
            await deleteAccount();
            navigation.replace('Enrollment');
          },
        },
      ]
    );
  }

  const currentLanguage = profile?.language ?? 'en';

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.heading}>{t('settings.settingsTitle')}</Text>

        {/* Profile card */}
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarIcon}>👤</Text>
          </View>
          <View>
            <Text style={styles.profileName}>{profile?.label ?? '—'}</Text>
            <Text style={styles.profileId}>User ID: {profile?.participantId ?? '—'}</Text>
          </View>
        </View>

        {/* Language section */}
        <Text style={styles.sectionLabel}>{t('settings.language').toUpperCase()}</Text>
        <View style={styles.settingsCard}>
          <View style={styles.row}>
            <Text style={styles.rowLabel}>{t('settings.languageEnglish')}</Text>
            <View style={[styles.radioCircle, currentLanguage === 'en' && styles.radioCircleSelected]}>
              {currentLanguage === 'en' && <Text style={styles.radioCheck}>✓</Text>}
            </View>
          </View>
          <View style={[styles.row, styles.rowLast]}>
            <Text style={styles.rowLabel}>{t('settings.languageChinese')}  Chinese</Text>
            <View style={[styles.radioCircle, currentLanguage === 'zh' && styles.radioCircleSelected]}>
              {currentLanguage === 'zh' && <Text style={styles.radioCheck}>✓</Text>}
            </View>
          </View>
        </View>

        {/* Preferences section */}
        <Text style={styles.sectionLabel}>{t('settings.preferences').toUpperCase()}</Text>
        <View style={styles.settingsCard}>
          <View style={styles.row}>
            <Text style={styles.rowLabel}>{t('settings.dailyReminders')}</Text>
            <Switch
              value={dailyReminders}
              onValueChange={setDailyReminders}
              trackColor={{ false: Colors.border, true: Colors.primary }}
              thumbColor={Colors.white}
            />
          </View>
          <View style={[styles.row, styles.rowLast]}>
            <Text style={styles.rowLabel}>{t('settings.largerText')}</Text>
            <Switch
              value={largerText}
              onValueChange={setLargerText}
              trackColor={{ false: Colors.border, true: Colors.primary }}
              thumbColor={Colors.white}
            />
          </View>
        </View>

        {/* Delete data */}
        <TouchableOpacity style={styles.deleteRow} onPress={handleDeleteData}>
          <Text style={styles.deleteText}>{t('settings.deleteMyData')}</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { paddingHorizontal: 20, paddingTop: 16 },
  heading: {
    fontSize: 32,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 20,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
    gap: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 1,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarIcon: { fontSize: 22 },
  profileName: { fontSize: 16, fontWeight: '700', color: Colors.textPrimary },
  profileId: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  settingsCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    marginBottom: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 1,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  rowLast: { borderBottomWidth: 0 },
  rowLabel: { fontSize: 15, color: Colors.textPrimary },
  radioCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioCircleSelected: {
    borderColor: Colors.primary,
    backgroundColor: Colors.primary,
  },
  radioCheck: { color: Colors.white, fontSize: 12, fontWeight: '700' },
  deleteRow: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 1,
  },
  deleteText: { fontSize: 15, color: Colors.destructive, fontWeight: '600' },
});
