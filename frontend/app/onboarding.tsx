import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import { Pressable, StyleSheet, View } from "react-native";
import Animated, { FadeInDown } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Button, Txt } from "@/src/components/ui";
import { spacing, useTheme } from "@/src/theme";

const HERO =
  "https://images.unsplash.com/photo-1770871821382-60ea99b0a941?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85&w=1200";

export default function Onboarding() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  return (
    <View testID="onboarding-screen" style={{ flex: 1, backgroundColor: colors.surfaceInverse }}>
      <Image source={{ uri: HERO }} style={StyleSheet.absoluteFill} contentFit="cover" transition={400} />
      <LinearGradient
        colors={[colors.scrim, colors.scrim, colors.surfaceInverse]}
        locations={[0, 0.4, 0.78]}
        style={StyleSheet.absoluteFill}
      />
      <LinearGradient colors={[colors.surfaceInverse, colors.scrim]} style={{ position: "absolute", top: 0, left: 0, right: 0, height: insets.top + 96, opacity: 0.6 }} />
      <View style={{ paddingTop: insets.top + spacing.lg, paddingHorizontal: spacing.xl }}>
        <View style={{ alignSelf: "flex-start", backgroundColor: colors.surface, borderRadius: 16, padding: spacing.sm }}>
          <Image source={require("../assets/images/logo-full.png")} style={{ width: 92, height: 97 }} contentFit="contain" accessibilityLabel="Safe > Sorry" testID="onboarding-logo" />
        </View>
      </View>
      <View style={{ flex: 1 }} />
      <View style={{ paddingHorizontal: spacing.xl, paddingBottom: insets.bottom + spacing.xl, gap: spacing.lg }}>
        <Animated.View entering={FadeInDown.duration(600)}>
          <Txt variant="hero" color={colors.onSurfaceInverse}>
            The people you love deserve more than “it’ll be fine”.
          </Txt>
        </Animated.View>
        <Animated.View entering={FadeInDown.delay(150).duration(600)}>
          <Txt color={colors.onSurfaceInverse} style={{ opacity: 0.85 }}>
            In five gentle minutes, see what life would really look like for your family if you weren’t there — and
            how to make sure they’re okay.
          </Txt>
        </Animated.View>
        <Animated.View entering={FadeInDown.delay(300).duration(600)} style={{ gap: spacing.sm }}>
          <Button
            testID="onboarding-begin-button"
            title="Begin your family check"
            icon="arrow-right"
            onPress={() => router.push({ pathname: "/auth", params: { mode: "register" } })}
          />
          <Button
            testID="onboarding-login-button"
            title="I already have an account"
            variant="light"
            onPress={() => router.push({ pathname: "/auth", params: { mode: "login" } })}
          />
          <Pressable testID="onboarding-firm-signup-link" onPress={() => router.push("/firm-signup")} style={{ paddingVertical: spacing.md, alignItems: "center" }}>
            <Txt variant="small" color={colors.onSurfaceInverse}>
              Are you an adviser? <Txt variant="small" color={colors.brandPrimary}>Set up your firm</Txt>
            </Txt>
          </Pressable>
        </Animated.View>
      </View>
    </View>
  );
}
