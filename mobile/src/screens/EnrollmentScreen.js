import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
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
        <View style={styles.iconContainer}>
          <Text style={styles.icon}>♥</Text>
        </View>

        <Text style={styles.title}>{t('enrollment.title')}</Text>
        <Text style={styles.subtitle}>{t('enrollment.subtitle')}</Text>

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
  iconContainer: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: Colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  icon: {
    fontSize: 32,
    color: Colors.white,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: Colors.accent,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 40,
    lineHeight: 22,
  },
  input: {
    width: '100%',
    height: 52,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 10,
    paddingHorizontal: 16,
    fontSize: 16,
    color: Colors.textPrimary,
    backgroundColor: Colors.white,
    marginBottom: 16,
  },
  button: {
    width: '100%',
    height: 52,
    backgroundColor: Colors.accent,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: Colors.white,
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
