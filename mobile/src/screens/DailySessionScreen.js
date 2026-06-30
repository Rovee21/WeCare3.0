import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { logEngagement, markAsRead } from '../services/sessionService';
import { Colors } from '../constants/colors';

export default function DailySessionScreen({ route, navigation }) {
  const { t } = useTranslation();
  const { course } = route.params;
  const [commentsExpanded, setCommentsExpanded] = useState(false);
  const [liked, setLiked] = useState(false);

  useEffect(() => {
    if (course?.id) markAsRead(course.id).catch(() => {});
  }, [course?.id]);

  async function handleLike() {
    setLiked(l => !l);
    await logEngagement({
      course_title: course.title,
      week_number: course.week_number ?? course.weekNumber,
      interactive_feature_count: 1,
    });
  }

  const weekNum = course?.week_number ?? course?.weekNumber ?? '—';
  const dayNum = course?.day_number ?? course?.dayNumber ?? '—';
  const mediaTypes = course?.media_types || course?.mediaTypes || [];
  const primaryType = mediaTypes[0] ?? 'Video';

  return (
    <SafeAreaView style={styles.container}>
      {/* Top bar */}
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <View style={styles.topCenter}>
          <Text style={styles.courseLabel}>COURSE {weekNum}.{dayNum}</Text>
          <Text style={styles.courseTitle} numberOfLines={1}>{course?.title}</Text>
        </View>
        <TouchableOpacity style={styles.overflowButton}>
          <Text style={styles.overflow}>···</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Video player */}
        <View style={styles.videoPlayer}>
          <TouchableOpacity style={styles.playButton}>
            <Text style={styles.playIcon}>▶</Text>
          </TouchableOpacity>
          <View style={styles.durationBadge}>
            <Text style={styles.durationText}>{course?.duration ?? '8:24'}</Text>
          </View>
        </View>

        {/* Video meta */}
        <Text style={styles.videoTitle}>{course?.title}</Text>
        <Text style={styles.videoMeta}>
          Week {weekNum} · {course?.duration ?? '8 min'} · {primaryType}
        </Text>

        {/* Reactions */}
        <View style={styles.reactionsRow}>
          <TouchableOpacity style={styles.reactionBadge} onPress={handleLike}>
            <Text style={styles.reactionIcon}>{liked ? '♥' : '♡'}</Text>
            <Text style={styles.reactionCount}>{liked ? 1 : 0}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.reactionBadge}>
            <Text style={styles.reactionIcon}>💬</Text>
            <Text style={styles.reactionCount}>0</Text>
          </TouchableOpacity>
        </View>

        {/* Text content */}
        {(course?.text_content || course?.textContent) ? (
          <Text style={styles.textBody}>
            {course?.text_content ?? course?.textContent}
          </Text>
        ) : null}

        {/* Additional resources */}
        {course?.resources?.length > 0 && (
          <View style={styles.resourcesSection}>
            <Text style={styles.resourcesLabel}>
              {t('session.additionalResources').toUpperCase()} (DOWNLOADABLE)
            </Text>
            {course.resources.map(r => (
              <TouchableOpacity
                key={r.id}
                style={styles.resourceRow}
                onPress={() => logEngagement({ infographic_open_count: 1, course_title: course.title })}
              >
                <View style={styles.resourceIcon}>
                  <Text style={styles.resourceIconText}>📄</Text>
                </View>
                <View style={styles.resourceInfo}>
                  <Text style={styles.resourceTitle}>{r.title}</Text>
                  <Text style={styles.resourceType}>{r.resource_type}</Text>
                </View>
                <Text style={styles.downloadIcon}>⬇</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Comments */}
        <TouchableOpacity
          style={styles.commentsHeader}
          onPress={() => setCommentsExpanded(e => !e)}
        >
          <Text style={styles.commentsTitle}>{t('session.comments')} 0</Text>
          <Text style={styles.commentsChevron}>{commentsExpanded ? '∧' : '∨'}</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  backButton: { padding: 4 },
  backArrow: { fontSize: 22, color: Colors.textPrimary },
  topCenter: { flex: 1 },
  courseLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 0.8,
  },
  courseTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  overflowButton: { padding: 4 },
  overflow: { fontSize: 18, color: Colors.textSecondary, letterSpacing: 2 },
  scroll: { paddingHorizontal: 16, paddingBottom: 32 },
  videoPlayer: {
    height: 200,
    backgroundColor: '#C0C0C0',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  playButton: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: 'rgba(255,255,255,0.85)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  playIcon: { fontSize: 20, color: Colors.textPrimary, marginLeft: 4 },
  durationBadge: {
    position: 'absolute',
    bottom: 10,
    right: 10,
    backgroundColor: 'rgba(0,0,0,0.55)',
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  durationText: { color: Colors.white, fontSize: 11, fontWeight: '600' },
  videoTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  videoMeta: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginBottom: 16,
  },
  reactionsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  reactionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 7,
    gap: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  reactionIcon: { fontSize: 16 },
  reactionCount: { fontSize: 14, fontWeight: '600', color: Colors.textPrimary },
  textBody: {
    fontSize: 15,
    color: Colors.textPrimary,
    lineHeight: 24,
    marginBottom: 24,
  },
  resourcesSection: { marginBottom: 8 },
  resourcesLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  resourceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  resourceIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: Colors.accentLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  resourceIconText: { fontSize: 18 },
  resourceInfo: { flex: 1 },
  resourceTitle: { fontSize: 14, fontWeight: '600', color: Colors.textPrimary },
  resourceType: { fontSize: 12, color: Colors.textSecondary },
  downloadIcon: { fontSize: 18, color: Colors.primary },
  commentsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    marginTop: 8,
  },
  commentsTitle: { fontSize: 15, fontWeight: '600', color: Colors.textPrimary },
  commentsChevron: { fontSize: 14, color: Colors.textSecondary },
});
