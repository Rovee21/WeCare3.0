import React, { useEffect, useState, useMemo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, SectionList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { getAllSessions } from '../services/sessionService';
import { Colors } from '../constants/colors';

function groupByWeek(sessions) {
  const map = {};
  for (const s of sessions) {
    const key = s.week_number ?? s.weekNumber ?? 1;
    if (!map[key]) map[key] = [];
    map[key].push(s);
  }
  return Object.keys(map)
    .sort((a, b) => Number(a) - Number(b))
    .map(week => ({ title: `WEEK ${week}`, data: map[week] }));
}

function CheckCircle({ isRead, isCurrent }) {
  if (isRead) {
    return (
      <View style={[styles.circle, styles.circleRead]}>
        <Text style={styles.checkmark}>✓</Text>
      </View>
    );
  }
  if (isCurrent) {
    return (
      <View style={[styles.circle, styles.circleCurrent]}>
        <View style={styles.circleDot} />
      </View>
    );
  }
  return <View style={[styles.circle, styles.circleEmpty]} />;
}

export default function CoursesScreen({ navigation }) {
  const { t } = useTranslation();
  const [sessions, setSessions] = useState([]);

  useEffect(() => { getAllSessions().then(setSessions); }, []);

  const sections = useMemo(() => groupByWeek(sessions), [sessions]);

  const totalSessions = sessions.length;
  const completedSessions = sessions.filter(s => s.is_read || s.isRead).length;
  const remaining = totalSessions - completedSessions;
  const firstUnreadId = sessions.find(s => !(s.is_read || s.isRead))?.id;

  function renderItem({ item }) {
    const isRead = item.is_read || item.isRead;
    const isCurrent = !isRead && item.id === firstUnreadId;
    const mediaTypes = item.media_types || item.mediaTypes || [];
    const meta = [mediaTypes[0], item.duration].filter(Boolean).join(' · ');

    return (
      <TouchableOpacity
        style={styles.courseRow}
        onPress={() => navigation.navigate('DailySession', { course: item })}
      >
        <CheckCircle isRead={isRead} isCurrent={isCurrent} />
        <View style={styles.courseInfo}>
          <Text style={styles.courseTitle}>{item.title}</Text>
          {meta ? <Text style={styles.courseMeta}>{meta}</Text> : null}
        </View>
      </TouchableOpacity>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <SectionList
        sections={sections}
        keyExtractor={item => String(item.id)}
        renderItem={renderItem}
        renderSectionHeader={({ section }) => (
          <Text style={styles.sectionHeader}>{section.title}</Text>
        )}
        ListHeaderComponent={() => (
          <View style={styles.header}>
            <Text style={styles.heading}>{t('courses.heading')}</Text>
            <Text style={styles.subheading}>
              {t('courses.subheadingPre')}
              <Text style={styles.subheadingAccent}> {remaining} </Text>
              {t('courses.subheadingPost')}
            </Text>
            {totalSessions > 0 && (
              <View style={styles.progressCard}>
                <Text style={styles.progressLabel}>{t('courses.progressLabel')}</Text>
                <Text style={styles.progressCount}>
                  {t('courses.progress', { completed: completedSessions, total: totalSessions })}
                </Text>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      { width: `${(completedSessions / totalSessions) * 100}%` },
                    ]}
                  />
                </View>
              </View>
            )}
          </View>
        )}
        contentContainerStyle={styles.list}
        stickySectionHeadersEnabled={false}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  list: { paddingHorizontal: 16, paddingBottom: 24 },
  header: { paddingTop: 8, paddingBottom: 4 },
  heading: {
    fontSize: 32,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 8,
  },
  subheading: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 16,
    lineHeight: 20,
  },
  subheadingAccent: {
    color: Colors.accent,
    fontWeight: '600',
  },
  progressCard: {
    backgroundColor: Colors.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 1,
  },
  progressLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  progressCount: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 10,
  },
  progressBar: {
    height: 4,
    backgroundColor: Colors.border,
    borderRadius: 2,
  },
  progressFill: {
    height: 4,
    backgroundColor: Colors.primary,
    borderRadius: 2,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 1,
    marginTop: 20,
    marginBottom: 8,
  },
  courseRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 13,
    paddingHorizontal: 4,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  circle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    marginRight: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  circleEmpty: {
    borderWidth: 2,
    borderColor: Colors.border,
  },
  circleRead: {
    backgroundColor: Colors.primary,
  },
  circleCurrent: {
    borderWidth: 2,
    borderColor: Colors.primary,
  },
  circleDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.primary,
  },
  checkmark: {
    color: Colors.white,
    fontSize: 12,
    fontWeight: '700',
  },
  courseInfo: { flex: 1 },
  courseTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: 2,
  },
  courseMeta: { fontSize: 12, color: Colors.textSecondary },
});
