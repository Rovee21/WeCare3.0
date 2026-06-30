import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { Colors } from '../constants/colors';

export default function ContactUsScreen() {
  const { t } = useTranslation();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.heading}>{t('contactUs.title')}</Text>

        {/* Coordinator card — navy */}
        <View style={styles.coordinatorCard}>
          <View style={styles.coordinatorInfo}>
            <Text style={styles.coordinatorTitle}>{t('contactUs.coordinator')}</Text>
            <Text style={styles.coordinatorPhone}>XXX-XXX-XXXX</Text>
          </View>
          <View style={styles.phoneCircle}>
            <Text style={styles.phoneIcon}>📞</Text>
          </View>
        </View>

        {/* Email card — white */}
        <TouchableOpacity
          style={styles.emailCard}
          onPress={() => Linking.openURL('mailto:wecaremason@gmail.com')}
          activeOpacity={0.8}
        >
          <View style={styles.emailIconCircle}>
            <Text style={styles.emailIcon}>✉️</Text>
          </View>
          <View style={styles.emailInfo}>
            <Text style={styles.emailTitle}>{t('contactUs.emailWecare')}</Text>
            <Text style={styles.emailAddress}>wecaremason@gmail.com</Text>
          </View>
          <Text style={styles.arrow}>→</Text>
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
    marginBottom: 24,
  },
  coordinatorCard: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  coordinatorInfo: { flex: 1 },
  coordinatorTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.white,
    marginBottom: 4,
  },
  coordinatorPhone: { fontSize: 14, color: 'rgba(255,255,255,0.75)' },
  phoneCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  phoneIcon: { fontSize: 22 },
  emailCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 1,
  },
  emailIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.accentLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  emailIcon: { fontSize: 20 },
  emailInfo: { flex: 1 },
  emailTitle: { fontSize: 15, fontWeight: '600', color: Colors.textPrimary, marginBottom: 2 },
  emailAddress: { fontSize: 13, color: Colors.textSecondary },
  arrow: { fontSize: 18, color: Colors.textSecondary },
});
