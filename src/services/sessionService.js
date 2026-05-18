// Stub: replace with real API calls when backend is ready

const MOCK_COURSES = [
  {
    id: '1-1', weekNumber: 1, weekLabel: 'WEEK 1 - INTRO AND ADRD',
    title: 'Course 1.1: Intro to ADRD', date: 'May 5', mediaTypes: ['Video'],
    durationMin: 18, isRead: true,
  },
  {
    id: '1-2', weekNumber: 1, weekLabel: 'WEEK 1 - INTRO AND ADRD',
    title: 'Course 1.2: What is ADRD?', date: 'Today', mediaTypes: ['Video'],
    durationMin: null, isRead: false,
  },
  {
    id: '1-3', weekNumber: 1, weekLabel: 'WEEK 1 - INTRO AND ADRD',
    title: 'Course 1.3: Caregiver Role', date: null, mediaTypes: ['Video', 'Audio', 'Text'],
    durationMin: null, isRead: false,
  },
  {
    id: '1-4', weekNumber: 1, weekLabel: 'WEEK 1 - INTRO AND ADRD',
    title: 'Course 1.4: Daily Routines', date: null, mediaTypes: ['Video', 'Audio', 'Text'],
    durationMin: null, isRead: false,
  },
  {
    id: '2-1', weekNumber: 2, weekLabel: 'WEEK 2 - MANAGING BEHAVIORS',
    title: 'Course 2.1: Sleep & Rest', date: null, mediaTypes: ['Video', 'Text'],
    durationMin: null, isRead: false,
  },
  {
    id: '2-2', weekNumber: 2, weekLabel: 'WEEK 2 - MANAGING BEHAVIORS',
    title: 'Course 2.2: Nutrition Tips', date: null, mediaTypes: ['Video', 'Text'],
    durationMin: null, isRead: false,
  },
  {
    id: '2-3', weekNumber: 2, weekLabel: 'WEEK 2 - MANAGING BEHAVIORS',
    title: 'Course 2.3: Behavior Triggers', date: null, mediaTypes: ['Video', 'Audio', 'Text'],
    durationMin: null, isRead: false,
  },
];

export async function getTodaysSession() {
  // TODO: GET /api/sessions/today
  return MOCK_COURSES[1];
}

export async function getAllSessions() {
  // TODO: GET /api/sessions
  return MOCK_COURSES;
}

export async function markAsRead(courseId) {
  // TODO: POST /api/sessions/:id/read
  console.log('markAsRead', courseId);
}

export async function logEngagement(eventData) {
  // TODO: POST /api/engagement
  // eventData fields match tracking variables in CLAUDE.md
  console.log('logEngagement', eventData);
}
