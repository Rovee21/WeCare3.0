import React, { useEffect, useState } from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';
import { useTranslation } from 'react-i18next';
import { getStoredToken } from '../services/authService';
import EnrollmentScreen from '../screens/EnrollmentScreen';
import HomeScreen from '../screens/HomeScreen';
import CoursesScreen from '../screens/CoursesScreen';
import DailySessionScreen from '../screens/DailySessionScreen';
import SettingsScreen from '../screens/SettingsScreen';
import ContactUsScreen from '../screens/ContactUsScreen';
import JournalPlaceholderScreen from '../screens/JournalPlaceholderScreen';
import { Colors } from '../constants/colors';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();
const CoursesStack = createNativeStackNavigator();
const SettingsStack = createNativeStackNavigator();

function CoursesNavigator() {
  return (
    <CoursesStack.Navigator screenOptions={{ headerShown: false }}>
      <CoursesStack.Screen name="CoursesList" component={CoursesScreen} />
      <CoursesStack.Screen name="DailySession" component={DailySessionScreen} />
    </CoursesStack.Navigator>
  );
}

function SettingsNavigator() {
  return (
    <SettingsStack.Navigator screenOptions={{ headerShown: false }}>
      <SettingsStack.Screen name="SettingsMain" component={SettingsScreen} />
      <SettingsStack.Screen name="ContactUs" component={ContactUsScreen} />
    </SettingsStack.Navigator>
  );
}

function MainTabs() {
  const { t } = useTranslation();
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: Colors.accent,
        tabBarInactiveTintColor: Colors.textSecondary,
        tabBarStyle: { backgroundColor: Colors.white, borderTopColor: Colors.border },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{ tabBarLabel: t('tabs.home'), tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>🏠</Text> }}
      />
      <Tab.Screen
        name="Courses"
        component={CoursesNavigator}
        options={{ tabBarLabel: t('tabs.courses'), tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>📖</Text> }}
      />
      <Tab.Screen
        name="Journal"
        component={JournalPlaceholderScreen}
        options={{ tabBarLabel: t('tabs.journal'), tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>🎙️</Text> }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsNavigator}
        options={{ tabBarLabel: t('tabs.settings'), tabBarIcon: ({ color }) => <Text style={{ fontSize: 18, color }}>⚙️</Text> }}
      />
    </Tab.Navigator>
  );
}

export default function RootNavigator() {
  const [initialRoute, setInitialRoute] = useState(null);

  useEffect(() => {
    getStoredToken().then(token => {
      setInitialRoute(token ? 'MainTabs' : 'Enrollment');
    });
  }, []);

  if (!initialRoute) return null;

  return (
    <Stack.Navigator initialRouteName={initialRoute} screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Enrollment" component={EnrollmentScreen} />
      <Stack.Screen name="MainTabs" component={MainTabs} />
    </Stack.Navigator>
  );
}
