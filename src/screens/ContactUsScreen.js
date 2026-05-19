import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { Colors } from '../constants/colors';

export default function ContactUsScreen({ navigation }) {
  const { t } = useTranslation();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backText}>← {t('settings.settingsTitle')}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.content}>
        <Text style={styles.header}>{t('contactUs.title')}</Text>
        <Text style={styles.intro}>{t('contactUs.intro')}</Text>

        <View style={styles.card}>
          <Text style={styles.label}>{t('contactUs.emailLabel')}</Text>
          <TouchableOpacity onPress={() => Linking.openURL('mailto:wecaremason@gmail.com')}>
            <Text style={styles.link}>wecaremason@gmail.com</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>{t('contactUs.phoneLabel')}</Text>
          <Text style={styles.value}>XXX-XX-XXXX</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  topBar: { paddingHorizontal: 16, paddingVertical: 12 },
  backButton: { padding: 4, alignSelf: 'flex-start' },
  backText: { fontSize: 15, color: Colors.accent, fontWeight: '500' },
  content: { paddingHorizontal: 20, paddingTop: 8 },
  header: { fontSize: 24, fontWeight: '700', color: Colors.textPrimary, marginBottom: 8 },
  intro: { fontSize: 15, color: Colors.textSecondary, marginBottom: 24, lineHeight: 22 },
  card: {
    backgroundColor: Colors.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: 16,
    marginBottom: 12,
  },
  label: { fontSize: 12, color: Colors.textSecondary, fontWeight: '600', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 },
  link: { fontSize: 16, color: Colors.accent, fontWeight: '500' },
  value: { fontSize: 16, color: Colors.textPrimary, fontWeight: '500' },
});
