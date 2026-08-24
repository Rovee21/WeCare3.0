import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { getJournalHistory } from '../services/journalService';
import { Colors } from '../constants/colors';
import { scaleFont } from '../constants/typography';

export default function VoiceJournalHistoryScreen({ navigation }) {
  const [entries, setEntries] = useState(null); // null = still loading
  const [playingId, setPlayingId] = useState(null);
  const [playingUrl, setPlayingUrl] = useState(null);

  const player = useAudioPlayer(playingUrl || undefined);
  const status = useAudioPlayerStatus(player);

  useFocusEffect(
    useCallback(() => {
      getJournalHistory()
        .then(setEntries)
        .catch(() => setEntries([]));
    }, [])
  );

  // A new playingUrl swaps in a freshly-loaded player instance (expo-audio recreates the
  // player whenever its source changes) — auto-play it once it's ready. Toggling the same
  // entry's play/pause is handled directly in handleTogglePlay instead, since the player
  // identity doesn't change in that case.
  useEffect(() => {
    if (playingUrl) player.play();
  }, [player]);

  function handleTogglePlay(entry) {
    if (!entry.audio_url) return;
    if (playingId === entry.id) {
      if (status.playing) player.pause();
      else player.play();
    } else {
      setPlayingId(entry.id);
      setPlayingUrl(entry.audio_url);
    }
  }

  function formatDate(iso) {
    if (!iso) return '';
    return new Date(iso).toLocaleDateString('en-US', {
      weekday: 'long', month: 'short', day: 'numeric', year: 'numeric',
    });
  }

  const renderItem = ({ item }) => {
    const isThisPlaying = playingId === item.id && status.playing;
    return (
      <View style={styles.entryCard}>
        <View style={styles.entryHeader}>
          <Text style={styles.entryDate}>{formatDate(item.submitted_at)}</Text>
          <Text style={styles.entryWeek}>Week {item.week_number}</Text>
        </View>
        <View style={styles.entryBody}>
          <View style={styles.entryMetaRow}>
            <View style={styles.entryMeta}>
              <Text style={styles.entryMetaLabel}>Emotion</Text>
              <Text style={styles.entryMetaValue}>{item.emotion_label || '—'}</Text>
            </View>
            <View style={styles.entryMeta}>
              <Text style={styles.entryMetaLabel}>Stress</Text>
              <Text style={styles.entryMetaValue}>
                {item.vj_stress_level != null ? `${item.vj_stress_level}/10` : '—'}
              </Text>
            </View>
          </View>
          <TouchableOpacity
            testID={`vj-history-play-${item.id}`}
            style={[styles.playButton, !item.audio_url && styles.playButtonDisabled]}
            onPress={() => handleTogglePlay(item)}
            disabled={!item.audio_url}
          >
            <Text style={styles.playButtonText}>{isThisPlaying ? '⏸' : '▶'}</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.heading}>Voice Journal History</Text>
      </View>

      {entries === null ? (
        <View style={styles.centerState}>
          <Text style={styles.emptyText}>Loading...</Text>
        </View>
      ) : entries.length === 0 ? (
        <View style={styles.centerState}>
          <Text style={styles.emptyEmoji}>🎙️</Text>
          <Text style={styles.emptyText}>No past entries yet.</Text>
          <Text style={styles.emptySubtext}>Record your first Voice Journal to see it here.</Text>
        </View>
      ) : (
        <FlatList
          data={entries}
          keyExtractor={item => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  header: { paddingHorizontal: 20, paddingTop: 8, paddingBottom: 12 },
  backButton: { alignSelf: 'flex-start', marginBottom: 8 },
  backText: { fontSize: scaleFont(18), color: Colors.accent, fontWeight: '500' },
  heading: { fontSize: scaleFont(26), fontWeight: '700', color: Colors.textPrimary },
  list: { paddingHorizontal: 20, paddingBottom: 24 },
  centerState: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 40 },
  emptyEmoji: { fontSize: 48, marginBottom: 12 }, // decorative icon glyph, not reading text — left unscaled
  emptyText: { fontSize: scaleFont(16), fontWeight: '600', color: Colors.textPrimary, textAlign: 'center' },
  emptySubtext: { fontSize: scaleFont(14), color: Colors.textSecondary, textAlign: 'center', marginTop: 4 },
  entryCard: {
    backgroundColor: Colors.white,
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  entryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  entryDate: { fontSize: scaleFont(14), fontWeight: '600', color: Colors.textPrimary },
  entryWeek: { fontSize: scaleFont(12), color: Colors.textSecondary, fontWeight: '500' },
  entryBody: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  entryMetaRow: { flexDirection: 'row', gap: 24 },
  entryMeta: {},
  entryMetaLabel: { fontSize: scaleFont(11), color: Colors.textSecondary, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 2 },
  entryMetaValue: { fontSize: scaleFont(15), fontWeight: '600', color: Colors.textPrimary },
  playButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  playButtonDisabled: { backgroundColor: Colors.border },
  playButtonText: { fontSize: scaleFont(16), color: Colors.white },
});
