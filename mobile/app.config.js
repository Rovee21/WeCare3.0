module.exports = {
  expo: {
    name: "WeCare3.0",
    slug: "wecare3",
    icon: "./assets/icon.png",
    version: "1.0.0",
    orientation: "portrait",
    userInterfaceStyle: "light",
    icon: "./assets/icon.png",
    assetBundlePatterns: ["**/*"],
    newArchEnabled: true,
    updates: {
      url: "https://u.expo.dev/1edee5d5-fd18-4c6f-ba6d-96115a664d55"
    },
    runtimeVersion: {
      policy: "appVersion"
    },
    android: {
      package: "com.wecaremason.wecare",
      googleServicesFile: process.env.GOOGLE_SERVICES_JSON ?? "./google-services.json",
      permissions: [
        "android.permission.RECORD_AUDIO",
        "android.permission.MODIFY_AUDIO_SETTINGS"
      ]
    },
    ios: {
      bundleIdentifier: "com.wecaremason.wecare",
      supportsTablet: false,
      infoPlist: {
        ITSAppUsesNonExemptEncryption: false
      }
    },
    plugins: [
      "expo-secure-store",
      "expo-audio",
      "expo-video",
      // [
      //   "expo-notifications"
      // ]
    ],
    extra: {
      eas: {
        projectId: "1edee5d5-fd18-4c6f-ba6d-96115a664d55"
      }
    },
    owner: "lad_y"
  }
};