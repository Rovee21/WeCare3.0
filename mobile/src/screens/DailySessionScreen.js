import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { logEngagement, markAsRead, markInProgress } from '../services/sessionService';
import { Colors } from '../constants/colors';
import { scaleFont } from '../constants/typography';
import { useVideoPlayer, VideoView } from 'expo-video';
import { Linking } from 'react-native';

export default function DailySessionScreen({ route, navigation }) {
  const { t } = useTranslation();
  const { course } = route.params;
  const [activeTab, setActiveTab] = useState('Video');
  const [commentsExpanded, setCommentsExpanded] = useState(false);
  const [liked, setLiked] = useState(false);

  const tabStartTimeRef = React.useRef(Date.now());
  const activeTabRef = React.useRef('Video');
  const videoTimeRef = React.useRef(0);
  const textTimeRef = React.useRef(0);
  const videoOpenRef = React.useRef(course?.video_url ? 1 : 0);

  // Actual playback time (from pressing play to pausing/stopping), separate from
  // videoTimeRef which measures time the Video tab was merely active/visible.
  const videoWatchSecondsRef = React.useRef(0);
  const playStartTimeRef = React.useRef(null);

  const player = useVideoPlayer(course?.video_url || '', p => { p.loop = false; });

  // Banks the current in-progress play segment into videoWatchSecondsRef and clears
  // playStartTimeRef, so it's safe to call this on pause, tab-away, or unmount alike.
  function stopWatchClock() {
    if (playStartTimeRef.current != null) {
      const elapsed = Math.round((Date.now() - playStartTimeRef.current) / 1000);
      if (elapsed > 0) videoWatchSecondsRef.current += elapsed;
      playStartTimeRef.current = null;
    }
  }

  useEffect(() => {
    const subscription = player.addListener('playingChange', ({ isPlaying }) => {
      if (isPlaying) {
        playStartTimeRef.current = Date.now();
      } else {
        stopWatchClock();
      }
    });
    return () => subscription.remove();
  }, [player]);

  // TODO: `course` comes straight from the typed API client now, which is consistently
  // snake_case (see README > API Contract & Codegen). The `?? course.xxxCamelCase` fallbacks
  // in this file (here and below) are dead code from before that fix and can be removed.
  useEffect(() => {
    if (course?.id) markInProgress(course.id).catch(() => {});
    tabStartTimeRef.current = Date.now();
    activeTabRef.current = 'Video';

    return () => {
      const secondsOnTab = Math.round((Date.now() - tabStartTimeRef.current) / 1000);
      if (secondsOnTab > 0) {
        if (activeTabRef.current === 'Video') videoTimeRef.current += secondsOnTab;
        else if (activeTabRef.current === 'Text') textTimeRef.current += secondsOnTab;
      }

      stopWatchClock(); // bank any in-progress play segment before leaving the screen

      const total = videoTimeRef.current + textTimeRef.current;
      if (total > 3) {
        // "Completed" requires meeting a meaningful engagement threshold (60s) on every
        // tab that actually has content for this session — a tab with no content for
        // this session doesn't block completion. Falling short leaves it "in progress"
        // (see markInProgress above), not completed.
        const hasVideo = !!course?.video_url;
        const hasText = !!course?.text_content;
        const videoThresholdMet = !hasVideo || videoWatchSecondsRef.current >= 60;
        const textThresholdMet = !hasText || textTimeRef.current >= 60;
        if (course?.id && videoThresholdMet && textThresholdMet) {
          markAsRead(course.id).catch(() => {});
        }
        logEngagement({
          session_id: course?.id,
          course_title: course?.title || '',
          week_number: course?.week_number || course?.weekNumber || 1,
          video_time_seconds: videoTimeRef.current,
          video_watch_seconds: videoWatchSecondsRef.current,
          text_time_seconds: textTimeRef.current,
          video_open_count: videoOpenRef.current,
        }).then(() => console.log('Engagement logged'))
          .catch((e) => console.log('Engagement FAILED:', e.message));
      }
    };
  }, [course?.id]);

  const tabs = [
    t('session.tabs.video'),
    t('session.tabs.text'),
  ];
  const tabKeys = ['Video', 'Text'];

  async function handleEmoji(emoji) {
    await logEngagement({
      course_title: course.title,
      week_number: course.week_number ?? course.weekNumber,
      interactive_feature_count: 1,
    });
  }

  async function handleTabChange(tabKey) {
    const secondsOnTab = Math.round((Date.now() - tabStartTimeRef.current) / 1000);
    if (activeTabRef.current === 'Video') videoTimeRef.current += secondsOnTab;
    else if (activeTabRef.current === 'Text') textTimeRef.current += secondsOnTab;

    // Leaving Video while playing stops the watch-time clock, same as a pause — the
    // player itself isn't paused, so if it's still playing once Video is reopened,
    // restart the clock below (no playingChange event fires in that case, since
    // isPlaying never actually changed).
    if (activeTabRef.current === 'Video' && tabKey !== 'Video') {
      stopWatchClock();
    }

    tabStartTimeRef.current = Date.now();
    activeTabRef.current = tabKey;
    setActiveTab(tabKey);

    if (tabKey === 'Video') {
      videoOpenRef.current += 1;
      if (player.playing) {
        playStartTimeRef.current = Date.now();
      }
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backText}>← {t('session.courseList')}</Text>
        </TouchableOpacity>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <TouchableOpacity onPress={() => navigation.navigate('Home')} style={styles.backButton}>
            <Text style={styles.backText}>🏠</Text>
          </TouchableOpacity>
          <Text style={styles.overflow}>⋯</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.meta}>Week {course?.week_number ?? course?.weekNumber} · {course?.date ?? ''}</Text>
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
            course?.video_url ? (
              <VideoView
                style={styles.videoPlayer}
                player={player}
                allowsFullscreen
                allowsPictureInPicture
                nativeControls
              />
            ) : (
              <View style={styles.videoPlaceholder}>
                <Text style={styles.playIcon}>▶</Text>
                <Text style={styles.videoDuration}>No video available</Text>
              </View>
            )
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
                  onPress={() => {
                    logEngagement({ infographic_open_count: 1, course_title: course.title });
                    Linking.openURL(r.url);
                  }}
                >
                  <View style={styles.resourceThumb}>
                    <Text style={{ fontSize: scaleFont(32), textAlign: 'center', marginTop: 10 }}>
                      {r.resource_type === 'PDF' ? '📄' : r.resource_type === 'Video' ? '🎬' : '🔗'}
                    </Text>
                  </View>
                  <Text style={styles.resourceTitle}>{r.title}</Text>
                  <Text style={styles.resourceType}>{r.resource_type}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </>
        )}
      </ScrollView>

      <View style={styles.bottomBar}>
        {['👍', '❤️', '💬'].map(emoji => (
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
  backText: { fontSize: scaleFont(18), color: Colors.accent, fontWeight: '500' },
  overflow: { fontSize: scaleFont(20), color: Colors.textSecondary },
  scroll: { paddingHorizontal: 16, paddingBottom: 24 },
  meta: { fontSize: scaleFont(13), color: Colors.textSecondary, marginBottom: 6 },
  courseTitle: { fontSize: scaleFont(22), fontWeight: '700', color: Colors.textPrimary, marginBottom: 16 },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: Colors.cardBackground,
    borderRadius: 10,
    padding: 4,
    marginBottom: 16,
  },
  tab: { flex: 1, paddingVertical: 8, alignItems: 'center', borderRadius: 8 },
  tabActive: { backgroundColor: Colors.white },
  tabText: { fontSize: scaleFont(14), color: Colors.textSecondary, fontWeight: '500' },
  tabTextActive: { color: Colors.textPrimary, fontWeight: '600' },
  mediaArea: { marginBottom: 24 },
  videoPlaceholder: {
    height: 200,
    backgroundColor: Colors.primary,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  videoPlayer: {
    height: 220,
    borderRadius: 12,
    backgroundColor: '#000',
  },
  playIcon: { fontSize: 40, color: Colors.white, marginBottom: 8 }, // decorative icon glyph, not reading text — left unscaled
  videoDuration: { fontSize: scaleFont(13), color: 'rgba(255,255,255,0.7)' },
  audioPlaceholder: {
    height: 120,
    backgroundColor: Colors.cardBackground,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderLabel: { fontSize: scaleFont(14), color: Colors.textSecondary, marginTop: 8 },
  textContent: { padding: 4 },
  textBody: { fontSize: scaleFont(15), color: Colors.textPrimary, lineHeight: 29 },
  sectionLabel: { fontSize: scaleFont(15), fontWeight: '600', color: Colors.textPrimary, marginBottom: 12 },
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
  resourceTitle: { fontSize: scaleFont(12), fontWeight: '600', color: Colors.textPrimary, marginBottom: 2 },
  resourceType: { fontSize: scaleFont(11), color: Colors.textSecondary },
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
  emoji: { fontSize: scaleFont(28) },
});