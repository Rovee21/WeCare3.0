import React, { useEffect, useState, useMemo } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, SectionList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { getAllSessions } from '../services/sessionService';
import { Colors } from '../constants/colors';

function groupByWeek(sessions) {
  const map = {};
  for (const s of sessions) {
    if (!map[s.weekLabel]) map[s.weekLabel] = [];
    map[s.weekLabel].push(s);
  }
  return Object.entries(map).map(([title, data]) => ({ title, data }));
}

export default function CoursesScreen({ navigation }) {
  const { t } = useTranslation();
  const [sessions, setSessions] = useState([]);
  const [query, setQuery] = useState('');

  useEffect(() => { getAllSessions().then(setSessions); }, []);

  const sections = useMemo(() => {
    const filtered = query
      ? sessions.filter(s => s.title.toLowerCase().includes(query.toLowerCase()))
      : sessions;
    return groupByWeek(filtered);
  }, [sessions, query]);

  function renderItem({ item }) {
    return (
      <TouchableOpacity
        style={styles.courseRow}
        onPress={() => navigation.navigate('DailySession', { course: item })}
      >
        <View style={[styles.readIndicator, item.isRead && styles.readIndicatorFilled]} />
        <View style={styles.courseInfo}>
          <Text style={styles.courseTitle}>{item.title}</Text>
          <Text style={styles.courseMeta}>
            {[item.date, item.mediaTypes?.join(' · ')].filter(Boolean).join(' · ')}
          </Text>
        </View>
      </TouchableOpacity>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder={t('courses.searchPlaceholder')}
          placeholderTextColor={Colors.textSecondary}
          value={query}
          onChangeText={setQuery}
        />
      </View>
      <SectionList
        sections={sections}
        keyExtractor={item => item.id}
        renderItem={renderItem}
        renderSectionHeader={({ section }) => (
          <Text style={styles.sectionHeader}>{section.title}</Text>
        )}
        contentContainerStyle={styles.list}
        stickySectionHeadersEnabled={false}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  searchContainer: { padding: 16, paddingBottom: 8 },
  searchInput: {
    height: 44,
    backgroundColor: Colors.white,
    borderRadius: 10,
    paddingHorizontal: 14,
    fontSize: 15,
    color: Colors.textPrimary,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  list: { paddingHorizontal: 16, paddingBottom: 24 },
  sectionHeader: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 0.5,
    marginTop: 20,
    marginBottom: 8,
  },
  courseRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  readIndicator: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: Colors.accent,
    marginRight: 12,
  },
  readIndicatorFilled: {
    backgroundColor: Colors.accent,
  },
  courseInfo: { flex: 1 },
  courseTitle: { fontSize: 15, fontWeight: '600', color: Colors.textPrimary, marginBottom: 3 },
  courseMeta: { fontSize: 12, color: Colors.textSecondary },
});
