module.exports = {
  expo: {
    name: "WeCare3.0",
    slug: "wecare3",
    version: "1.0.0",
    orientation: "portrait",
    userInterfaceStyle: "light",
    assetBundlePatterns: ["**/*"],
    newArchEnabled: true,
    android: {
      package: "com.wecaremason.wecare3",
      googleServicesFile: process.env.GOOGLE_SERVICES_JSON ?? "./google-services.json",
      permissions: [
        "android.permission.RECORD_AUDIO",
        "android.permission.MODIFY_AUDIO_SETTINGS"
      ]
    },
    ios: {
      bundleIdentifier: "com.wecaremason.wecare3"
    },
    plugins: [
      "expo-secure-store",
      "expo-audio",
      "expo-video",
      [
        "expo-notifications"
      ]
    ],
    extra: {
      eas: {
        projectId: "1edee5d5-fd18-4c6f-ba6d-96115a664d55"
      }
    }
  }
};