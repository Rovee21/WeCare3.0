// Stub: replace with real API calls when backend is ready

const MOCK_COURSES = [
  {
    id: '1-1', week_number: 1, day_number: 1, weekLabel: 'WEEK 1 - INTRO AND ADRD',
    title: 'Course 1.1: Intro to ADRD', date: 'May 5', media_types: ['Video'],
    is_read: true,
  },
  {
    id: '1-2', week_number: 1, day_number: 3, weekLabel: 'WEEK 1 - INTRO AND ADRD',
    title: 'Course 1.2: What is ADRD?', date: 'Today', media_types: ['Video'],
    is_read: false,
  },
  {
    id: '1-3', week_number: 1, day_number: 4, weekLabel: 'WEEK 1 - INTRO AND ADRD',
    title: 'Course 1.3: Caregiver Role', date: null, media_types: ['Video', 'Audio', 'Text'],
    is_read: false,
  },
  {
    id: '1-4', week_number: 1, day_number: 5, weekLabel: 'WEEK 1 - INTRO AND ADRD',
    title: 'Course 1.4: Daily Routines', date: null, media_types: ['Video', 'Audio', 'Text'],
    is_read: false,
  },
  {
    id: '2-1', week_number: 2, day_number: 1, weekLabel: 'WEEK 2 - MANAGING BEHAVIORS',
    title: 'Course 2.1: Sleep & Rest', date: null, media_types: ['Video', 'Text'],
    is_read: false,
  },
  {
    id: '2-2', week_number: 2, day_number: 2, weekLabel: 'WEEK 2 - MANAGING BEHAVIORS',
    title: 'Course 2.2: Nutrition Tips', date: null, media_types: ['Video', 'Text'],
    is_read: false,
  },
  {
    id: '2-3', week_number: 2, day_number: 3, weekLabel: 'WEEK 2 - MANAGING BEHAVIORS',
    title: 'Course 2.3: Behavior Triggers', date: null, media_types: ['Video', 'Audio', 'Text'],
    is_read: false,
  },
];

import { apiFetch } from './api';

export async function getTodaysSession() {
  return await apiFetch('/sessions/today/');
}

export async function getAllSessions() {
  return await apiFetch('/sessions/');
}

export async function markAsRead(courseId) {
  return await apiFetch(`/sessions/${courseId}/read/`, { method: 'POST' });
}

export async function logEngagement(eventData) {
  return await apiFetch('/engagement/', {
    method: 'POST',
    body: JSON.stringify(eventData),
  });
}
