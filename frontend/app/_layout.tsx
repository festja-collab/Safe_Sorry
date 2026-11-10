import { QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import Head from "expo-router/head";
import { StatusBar } from "expo-status-bar";
import { LogBox, Platform, StyleSheet, View } from "react-native";
import { KeyboardProvider } from "react-native-keyboard-controller";

import { AuthProvider } from "@/src/auth";
import { ErrorBoundary } from "@/src/components/error-boundary";
import { queryClient } from "@/src/query-client";
import { colors } from "@/src/theme";

// Disable logbox errors etc so that users can see the app
// and agent works as expected.
LogBox.ignoreAllLogs(true);

export default function RootLayout() {
  const [loaded] = useFonts({
    Fraunces: require("../assets/fonts/Fraunces.ttf"),
    Quicksand: require("../assets/fonts/Quicksand.ttf"),
  });
  if (!loaded) return null;

  return (
    <ErrorBoundary>
      <Head>
        <title>Safe &gt; Sorry · Free family protection check</title>
        <meta name="description" content="A free 5-minute check that shows what your family would face if the worst happened. Estimates only, not regulated advice." />
        <meta name="theme-color" content="#223342" />
        <meta property="og:title" content="Safe > Sorry · Would your family be okay?" />
        <meta property="og:description" content="A free 5-minute family protection check. Nothing to download." />
        <link rel="manifest" href="/manifest.json" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-title" content="Safe > Sorry" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      </Head>
      <QueryClientProvider client={queryClient}>
        <KeyboardProvider>
          <AuthProvider>
            <StatusBar style="dark" />
            <View style={styles.page}>
              <View style={styles.column}>
                <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.surface } }}>
                  <Stack.Screen name="assessment" options={{ presentation: "fullScreenModal", gestureEnabled: false }} />
                </Stack>
              </View>
            </View>
          </AuthProvider>
        </KeyboardProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

// On laptops/desktops (web), keep the phone design in a centred column on a navy page so text and
// buttons stay a comfortable size. Phones and narrow windows are unchanged (the column is full width).
const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.brand, alignItems: "center" },
  column: {
    flex: 1,
    width: "100%",
    maxWidth: Platform.OS === "web" ? 640 : undefined,
    overflow: "hidden",
    backgroundColor: colors.surface,
    ...(Platform.OS === "web" ? { boxShadow: "0 0 40px rgba(0,0,0,0.25)" } : {}),
  },
});
