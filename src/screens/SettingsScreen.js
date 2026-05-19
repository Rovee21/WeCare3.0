import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { getStoredProfile, deleteAccount } from '../services/authService';
import { Colors } from '../constants/colors';

export default function SettingsScreen({ navigation }) {
  const { t } = useTranslation();
  const [profile, setProfile] = useState(null);

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

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.profileHeader}>
        <View style={styles.avatar}>
          <Text style={styles.avatarIcon}>👤</Text>
        </View>
        <View>
          <Text style={styles.participantId}>
            Participant #{profile?.participantId ?? '—'}
          </Text>
          <Text style={styles.participantMeta}>
            Week {profile?.weekNumber ?? '—'} · {profile?.group ?? '—'} group
          </Text>
        </View>
      </View>

      <View style={styles.section}>
        <TouchableOpacity style={[styles.row, styles.rowLast]} onPress={() => navigation.navigate('ContactUs')}>
          <Text style={styles.rowLabel}>{t('settings.contactUs')}</Text>
          <Text style={styles.rowArrow}>›</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.deleteRow} onPress={handleDeleteData}>
        <Text style={styles.deleteText}>{t('settings.deleteMyData')}</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    padding: 20,
    paddingBottom: 24,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.cardBackground,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  avatarIcon: { fontSize: 26 },
  participantId: { fontSize: 17, fontWeight: '700', color: Colors.textPrimary },
  participantMeta: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  section: {
    backgroundColor: Colors.white,
    marginHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  rowLast: { borderBottomWidth: 0 },
  rowLabel: { fontSize: 15, color: Colors.textPrimary },
  rowArrow: { fontSize: 20, color: Colors.textSecondary },
  deleteRow: {
    marginHorizontal: 16,
    marginTop: 16,
    backgroundColor: Colors.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingVertical: 16,
    alignItems: 'center',
  },
  deleteText: { fontSize: 15, color: Colors.destructive, fontWeight: '600' },
});
