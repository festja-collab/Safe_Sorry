import { Feather } from "@react-native-vector-icons/feather";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useEffect, useState } from "react";
import { Platform, Pressable, View } from "react-native";

import { Button, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

const KEY = "home_tip_dismissed";

// Android Chrome fires this so we can show the browser's own "Add to home screen" dialog.
let deferredPrompt: any = null;
if (Platform.OS === "web" && typeof window !== "undefined") {
  window.addEventListener("beforeinstallprompt", (e: any) => {
    e.preventDefault();
    deferredPrompt = e;
  });
}

type Kind = "ios" | "android" | null;

function detect(): Kind {
  if (Platform.OS !== "web" || typeof window === "undefined") return null;
  const standalone = window.matchMedia?.("(display-mode: standalone)").matches || (window.navigator as any).standalone;
  if (standalone) return null;
  const ua = window.navigator.userAgent;
  if (/iPhone|iPad|iPod/i.test(ua)) return "ios";
  if (/Android/i.test(ua)) return "android";
  return null; // desktop: no tip
}

/** Gentle, dismissible tip on the report (mobile web only) to keep Safe > Sorry on the home screen. */
export function HomeScreenTip() {
  const { colors } = useTheme();
  const s = useStyles();
  const [kind, setKind] = useState<Kind>(null);

  useEffect(() => {
    const k = detect();
    if (!k) return;
    AsyncStorage.getItem(KEY).then((v) => !v && setKind(k));
  }, []);

  if (!kind) return null;

  const dismiss = () => {
    setKind(null);
    AsyncStorage.setItem(KEY, "1");
  };
  const install = async () => {
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    dismiss();
  };

  return (
    <View style={s.card} testID="home-screen-tip">
      <View style={s.head}>
        <Feather name="smartphone" size={20} color={colors.onBrandTertiary} />
        <Txt variant="title" style={{ flex: 1, color: colors.onBrandTertiary }}>
          Keep your report close
        </Txt>
        <Pressable testID="home-screen-tip-close" onPress={dismiss} hitSlop={12} accessibilityLabel="Close tip">
          <Feather name="x" size={20} color={colors.onBrandTertiary} />
        </Pressable>
      </View>
      <Txt variant="small" style={{ color: colors.onBrandTertiary }}>
        Add Safe &gt; Sorry to your home screen to come back to your family report any time. It opens like an app, with nothing to download.
      </Txt>
      {kind === "ios" ? (
        <Txt variant="small" style={{ color: colors.onBrandTertiary }} testID="home-screen-tip-ios">
          In Safari, tap the Share button <Feather name="share" size={13} /> at the bottom of the screen, then choose “Add to Home Screen”.
        </Txt>
      ) : deferredPrompt ? (
        <Button testID="home-screen-tip-add" title="Add to home screen" icon="plus" variant="secondary" onPress={install} />
      ) : (
        <Txt variant="small" style={{ color: colors.onBrandTertiary }} testID="home-screen-tip-android">
          In Chrome, tap the menu ⋮ at the top right, then choose “Add to Home screen”.
        </Txt>
      )}
      <Pressable testID="home-screen-tip-dismiss" onPress={dismiss} style={s.later}>
        <Txt variant="small" style={{ color: colors.onBrandTertiary, textDecorationLine: "underline" }}>
          No thanks
        </Txt>
      </Pressable>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  card: { backgroundColor: c.brandTertiary, borderRadius: radius.lg, padding: spacing.md, gap: spacing.sm },
  head: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  later: { alignSelf: "flex-start", minHeight: 44, justifyContent: "center" },
}));
