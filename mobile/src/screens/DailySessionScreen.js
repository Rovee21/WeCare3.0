import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { logEngagement, markAsRead } from '../services/sessionService';
import { Colors } from '../constants/colors';

export default function DailySessionScreen({ route, navigation }) {
  const { t } = useTranslation();
  const { course } = route.params;
  const [activeTab, setActiveTab] = useState('Video');

  useEffect(() => {
    // Mark as read when the screen is opened
    if (course?.id) markAsRead(course.id).catch(() => {});
  }, [course?.id]);

  const tabs = [
    t('session.tabs.video'),
    t('session.tabs.audio'),
    t('session.tabs.text'),
  ];
  const tabKeys = ['Video', 'Audio', 'Text'];

  async function handleEmoji(emoji) {
    await logEngagement({
      course_title: course.title,
      week_number: course.weekNumber,
      interactive_feature_count: 1,
    });
  }

  async function handleTabChange(tabKey) {
    setActiveTab(tabKey);
    if (tabKey === 'Video') {
      await logEngagement({
        course_title: course.title,
        week_number: course.weekNumber,
        video_open_count: 1,
      });
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backText}>← {t('session.courseList')}</Text>
        </TouchableOpacity>
        <Text style={styles.overflow}>⋯</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.meta}>Week {course?.weekNumber} · Sent {course?.date ?? '—'}</Text>
        <Text style={styles.courseTitle}>{course?.title}</Text>

        <View style={styles.tabBar}>
          {tabKeys.map((key, i) => (
            <TouchableOpacity
              key={key}
              style={[styles.tab, activeTab === key && styles.tabActive]}
              onPress={() => handleTabChange(key)}
            >
              <Text style={[styles.tabText, activeTab === key && styles.tabTextActive]}>
                {tabs[i]}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.mediaArea}>
          {activeTab === 'Video' && (
            <View style={styles.videoPlaceholder}>
              <Text style={styles.playIcon}>▶</Text>
              <Text style={styles.videoDuration}>00:00 / 18:00</Text>
            </View>
          )}
          {activeTab === 'Audio' && (
            <View style={styles.audioPlaceholder}>
              <Text style={styles.playIcon}>🎧</Text>
              <Text style={styles.placeholderLabel}>Audio player coming soon</Text>
            </View>
          )}
          {activeTab === 'Text' && (
            <View style={styles.textContent}>
              <Text style={styles.textBody}>
                {course?.text_content || course?.textContent || ''}
              </Text>
            </View>
          )}
        </View>

        {course?.resources?.length > 0 && (
          <>
            <Text style={styles.sectionLabel}>{t('session.additionalResources')}</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.resourcesRow}>
              {course.resources.map(r => (
                <TouchableOpacity
                  key={r.id}
                  style={styles.resourceCard}
                  onPress={() => logEngagement({ infographic_open_count: 1, course_title: course.title })}
                >
                  <View style={styles.resourceThumb} />
                  <Text style={styles.resourceTitle}>{r.title}</Text>
                  <Text style={styles.resourceType}>{r.resource_type}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </>
        )}
      </ScrollView>

      <View style={styles.bottomBar}>
        {['😊', '😐', '😢'].map(emoji => (
          <TouchableOpacity key={emoji} onPress={() => handleEmoji(emoji)} style={styles.emojiButton}>
            <Text style={styles.emoji}>{emoji}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: { padding: 4 },
  backText: { fontSize: 15, color: Colors.accent, fontWeight: '500' },
  overflow: { fontSize: 20, color: Colors.textSecondary },
  scroll: { paddingHorizontal: 16, paddingBottom: 24 },
  meta: { fontSize: 13, color: Colors.textSecondary, marginBottom: 6 },
  courseTitle: { fontSize: 22, fontWeight: '700', color: Colors.textPrimary, marginBottom: 16 },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: Colors.cardBackground,
    borderRadius: 10,
    padding: 4,
    marginBottom: 16,
  },
  tab: { flex: 1, paddingVertical: 8, alignItems: 'center', borderRadius: 8 },
  tabActive: { backgroundColor: Colors.white },
  tabText: { fontSize: 14, color: Colors.textSecondary, fontWeight: '500' },
  tabTextActive: { color: Colors.textPrimary, fontWeight: '600' },
  mediaArea: { marginBottom: 24 },
  videoPlaceholder: {
    height: 200,
    backgroundColor: Colors.primary,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  playIcon: { fontSize: 40, color: Colors.white, marginBottom: 8 },
  videoDuration: { fontSize: 13, color: 'rgba(255,255,255,0.7)' },
  audioPlaceholder: {
    height: 120,
    backgroundColor: Colors.cardBackground,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderLabel: { fontSize: 14, color: Colors.textSecondary, marginTop: 8 },
  textContent: { padding: 4 },
  textBody: { fontSize: 15, color: Colors.textPrimary, lineHeight: 24 },
  sectionLabel: { fontSize: 15, fontWeight: '600', color: Colors.textPrimary, marginBottom: 12 },
  resourcesRow: { marginBottom: 16 },
  resourceCard: {
    width: 120,
    backgroundColor: Colors.white,
    borderRadius: 10,
    padding: 10,
    marginRight: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  resourceThumb: {
    height: 64,
    backgroundColor: Colors.cardBackground,
    borderRadius: 6,
    marginBottom: 6,
  },
  resourceTitle: { fontSize: 12, fontWeight: '600', color: Colors.textPrimary, marginBottom: 2 },
  resourceType: { fontSize: 11, color: Colors.textSecondary },
  bottomBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    backgroundColor: Colors.white,
  },
  emojiButton: { padding: 6 },
  emoji: { fontSize: 28 },
});
