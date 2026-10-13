import { Feather } from "@react-native-vector-icons/feather";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, ScrollView, Share, View } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuth } from "@/src/auth";
import { Button, Field, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

const TEMPLATES = [
  {
    id: "nudge",
    label: "Gentle nudge",
    text: (n: string) =>
      `Hi ${n}, no pressure at all, but if you've got five minutes this shows in plain terms what your family would face if the worst happened. It's a good way to see if there's a gap worth thinking about.`,
  },
  {
    id: "after-chat",
    label: "After our chat",
    text: (n: string) =>
      `Hi ${n}, lovely to chat earlier. As promised, here's the app I mentioned. It takes about five minutes and makes it much easier to see what cover, if any, would really help your family.`,
  },
  {
    id: "life-event",
    label: "Big life change",
    text: (n: string) =>
      `Hi ${n}, congratulations on the big news! When life changes it's worth a quick check that your family would still be okay if something happened. This app walks you through it in five minutes.`,
  },
];

export default function Invite() {
  const { user } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const [name, setName] = useState("");
  const [tpl, setTpl] = useState(TEMPLATES[0].id);
  const [note, setNote] = useState("");
  const [sent, setSent] = useState(false);

  const first = (user?.name ?? "").split(" ")[0];
  const clientName = name.trim() || "there";
  const link = `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/invite/${user?.adviser_code}${name.trim() ? `?name=${encodeURIComponent(name.trim())}` : ""}`;
  const body = TEMPLATES.find((t) => t.id === tpl)!.text(clientName);
  const message = `${body}${note.trim() ? `\n\n${note.trim()}` : ""}\n\n${link}\n\nUse my code ${user?.adviser_code}-INV when you sign up.\n${first}`;

  const send = async () => {
    const r = await Share.share({ message });
    if (r.action === Share.sharedAction) setSent(true);
  };

  return (
    <View style={s.root} testID="invite-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="invite-back-button" onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)"))} style={s.iconBtn}>
          <Feather name="x" size={22} color={colors.onSurface} />
        </Pressable>
        <Txt variant="small">Invite a client</Txt>
        <View style={s.iconBtn} />
      </View>
      <KeyboardAwareScrollView bottomOffset={110} keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, gap: spacing.lg }}>
        <Txt variant="display">Send a gentle nudge</Txt>
        <Txt>Perfect for someone who’s on the fence. They get a personal link with your photo and code, and when they sign up you’ll see them in your lead inbox if they ask for a call.</Txt>
        <Field testID="invite-name-input" label="Client’s first name" value={name} onChangeText={setName} placeholder="e.g. Sarah" autoCapitalize="words" />
        <View style={{ gap: spacing.sm }}>
          <Txt variant="label">Message</Txt>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ height: 56, flexGrow: 0 }} contentContainerStyle={{ gap: spacing.sm, alignItems: "center" }}>
            {TEMPLATES.map((t) => (
              <Pressable key={t.id} testID={`invite-template-${t.id}`} onPress={() => setTpl(t.id)} style={[s.chip, tpl === t.id && s.chipOn]}>
                <Txt variant="small" color={tpl === t.id ? colors.onSurfaceInverse : colors.onSurface}>
                  {t.label}
                </Txt>
              </Pressable>
            ))}
          </ScrollView>
        </View>
        <Field testID="invite-note-input" label="Add a personal line (optional)" value={note} onChangeText={setNote} placeholder="e.g. Give me a shout with any questions" multiline style={{ minHeight: 70, flex: 1, fontSize: 16, textAlignVertical: "top", paddingTop: 14 }} />
        <View style={s.preview} testID="invite-preview">
          <Txt variant="label">Preview</Txt>
          <Txt style={{ color: colors.onSurface }}>{message}</Txt>
        </View>
        {sent ? (
          <Txt testID="invite-sent" color={colors.success}>
            Sent. Nice one — a personal nudge is often what tips someone into acting.
          </Txt>
        ) : null}
      </KeyboardAwareScrollView>
      <KeyboardStickyView offset={{ opened: insets.bottom - spacing.md }}>
        <View style={[s.footer, { paddingBottom: insets.bottom + spacing.lg }]}>
          <Button testID="invite-send-button" title="Send via text, WhatsApp or email" icon="send" onPress={send} />
        </View>
      </KeyboardStickyView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  chip: { height: 36, flexShrink: 0, paddingHorizontal: spacing.lg, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, justifyContent: "center" },
  chipOn: { backgroundColor: c.surfaceInverse },
  preview: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.lg, gap: spacing.sm },
  footer: { paddingHorizontal: spacing.xl, paddingTop: spacing.md, backgroundColor: c.surface },
}));
