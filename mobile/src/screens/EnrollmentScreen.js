import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { enrollWithCode } from '../services/authService';
import { Colors } from '../constants/colors';

export default function EnrollmentScreen({ navigation }) {
  const { t } = useTranslation();
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleEnroll() {
    if (!code.trim()) return;
    setLoading(true);
    try {
      await enrollWithCode(code.trim());
      navigation.replace('MainTabs');
    } catch {
      Alert.alert('Invalid code', 'Please check your code and try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Image source={require('../../assets/logo.png')} style={styles.logo} resizeMode="contain" />

        <View style={styles.card}>
          <Text style={styles.title}>{t('enrollment.title')}</Text>
          <Text style={styles.subtitle}>{t('enrollment.subtitle')}</Text>

          <Text style={styles.inputLabel}>{t('enrollment.userIdLabel')}</Text>
          <TextInput
            style={styles.input}
            placeholder={t('enrollment.codePlaceholder')}
            placeholderTextColor={Colors.textSecondary}
            value={code}
            onChangeText={setCode}
            autoCapitalize="none"
            autoCorrect={false}
          />

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleEnroll}
            disabled={loading}
          >
            <Text style={styles.buttonText}>{t('enrollment.cta')}</Text>
          </TouchableOpacity>
        </View>
      </View>

      <Text style={styles.privacy}>{t('enrollment.privacy')}</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    justifyContent: 'space-between',
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  logo: {
    width: 120,
    height: 120,
    marginBottom: 32,
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
    fontSize: 26,
    fontWeight: '700',
    color: Colors.textPrimary,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 28,
  },
  inputLabel: {
    fontSize: 13,
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
    fontSize: 16,
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
    fontSize: 16,
    fontWeight: '600',
  },
  privacy: {
    fontSize: 12,
    color: Colors.textSecondary,
    textAlign: 'center',
    paddingBottom: 16,
    paddingHorizontal: 32,
  },
});
