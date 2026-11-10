import { QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import Head from "expo-router/head";
import { StatusBar } from "expo-status-bar";
import { LogBox } from "react-native";
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
      </Head>
      <QueryClientProvider client={queryClient}>
        <KeyboardProvider>
          <AuthProvider>
            <StatusBar style="dark" />
            <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.surface } }}>
              <Stack.Screen name="assessment" options={{ presentation: "fullScreenModal", gestureEnabled: false }} />
            </Stack>
          </AuthProvider>
        </KeyboardProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
