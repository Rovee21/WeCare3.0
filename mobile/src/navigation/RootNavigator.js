import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';
import { useTranslation } from 'react-i18next';
import EnrollmentScreen from '../screens/EnrollmentScreen';
import HomeScreen from '../screens/HomeScreen';
import CoursesScreen from '../screens/CoursesScreen';
import DailySessionScreen from '../screens/DailySessionScreen';
import SettingsScreen from '../screens/SettingsScreen';
import ContactUsScreen from '../screens/ContactUsScreen';
import VoiceJournalScreen from '../screens/VoiceJournalScreen';
import SurveyScreen from '../screens/SurveyScreen';
import WaitlistScreen from '../screens/WaitlistScreen';
import { Colors } from '../constants/colors';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();
const CoursesStack = createNativeStackNavigator();
const JournalStack = createNativeStackNavigator();
const WaitlistStack = createNativeStackNavigator();

function CoursesNavigator() {
  return (
    <CoursesStack.Navigator screenOptions={{ headerShown: false }}>
      <CoursesStack.Screen name="CoursesList" component={CoursesScreen} />
      <CoursesStack.Screen name="DailySession" component={DailySessionScreen} />
    </CoursesStack.Navigator>
  );
}

function JournalNavigator() {
  return (
    <JournalStack.Navigator screenOptions={{ headerShown: false }}>
      <JournalStack.Screen name="VoiceJournal" component={VoiceJournalScreen} />
      <JournalStack.Screen name="Survey" component={SurveyScreen} />
    </JournalStack.Navigator>
  );
}

function WaitlistNavigator() {
  return (
    <WaitlistStack.Navigator screenOptions={{ headerShown: false }}>
      <WaitlistStack.Screen name="WaitlistHome" component={WaitlistScreen} />
      <WaitlistStack.Screen name="Contact" component={ContactUsScreen} />
    </WaitlistStack.Navigator>
  );
}

function MainTabs() {
  const { t } = useTranslation();
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.textSecondary,
        tabBarStyle: {
          backgroundColor: Colors.white,
          borderTopColor: Colors.border,
        },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarLabel: t('tabs.home'),
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>🏠</Text>,
        }}
      />
      <Tab.Screen
        name="Courses"
        component={CoursesNavigator}
        options={{
          tabBarLabel: t('tabs.courses'),
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>📚</Text>,
        }}
      />
      <Tab.Screen
        name="Journal"
        component={JournalNavigator}
        options={{
          tabBarLabel: t('tabs.journal'),
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>🎙️</Text>,
        }}
      />
      <Tab.Screen
        name="Contact"
        component={ContactUsScreen}
        options={{
          tabBarLabel: t('tabs.contact'),
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>📞</Text>,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarLabel: t('tabs.settings'),
          tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>⚙️</Text>,
        }}
      />
    </Tab.Navigator>
  );
}

export default function RootNavigator() {
  const [initialRoute, setInitialRoute] = React.useState(null);

  React.useEffect(() => {
    import('../services/authService').then(({ getStoredToken }) => {
      getStoredToken().then(async token => {
        if (!token) {
          setInitialRoute('Enrollment');
          return;
        }

        // Waitlisted participants get a dedicated screen instead of the normal tab
        // experience — check the live profile before deciding where to route.
        let route = 'MainTabs';
        try {
          const { getUserProfile } = await import('../services/userService');
          const profile = await getUserProfile();
          if (profile?.is_waitlisted) {
            route = 'Waitlist';
          }
        } catch (e) {
          // If the profile check fails (e.g. transient network error), fall back to
          // MainTabs rather than blocking app access entirely.
        }
        setInitialRoute(route);

        const { registerForPushNotifications, sendTokenToBackend } = await import('../services/notificationService');
        const pushToken = await registerForPushNotifications();
        if (pushToken) {
          sendTokenToBackend(pushToken);
        }
      });
    });
  }, []);

  if (!initialRoute) return null;

  return (
    <Stack.Navigator initialRouteName={initialRoute} screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Enrollment" component={EnrollmentScreen} />
      <Stack.Screen name="MainTabs" component={MainTabs} />
      <Stack.Screen name="Waitlist" component={WaitlistNavigator} />
    </Stack.Navigator>
  );
}
