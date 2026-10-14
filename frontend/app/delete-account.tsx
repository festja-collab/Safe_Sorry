import { Feather } from "@react-native-vector-icons/feather";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, View } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api } from "@/src/api";
import { useAuth } from "@/src/auth";
import { Button, Checkbox, Field, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

type Done = { reference: string; completed_at: string; deleted: { assessments: number; callback_requests: number; account: number } };

export default function DeleteAccount() {
  const { signOut } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const [password, setPassword] = useState("");
  const [sure, setSure] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<Done | null>(null);

  const submit = async () => {
    setError("");
    setBusy(true);
    try {
      setDone(await api<Done>("/auth/delete-account", { method: "POST", body: { password } }));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const finish = async () => {
    await signOut().catch(() => null);
    router.replace("/onboarding");
  };

  if (done)
    return (
      <View style={[s.root, { paddingTop: insets.top + spacing["2xl"], padding: spacing.xl, gap: spacing.lg }]} testID="delete-account-done">
        <Feather name="check-circle" size={48} color={colors.success} />
        <Txt variant="display">Your data has been deleted</Txt>
        <Txt>
          Your account, {done.deleted.assessments} family check{done.deleted.assessments === 1 ? "" : "s"} and letter
          {done.deleted.assessments === 1 ? "" : "s"}, and {done.deleted.callback_requests} call-back request
          {done.deleted.callback_requests === 1 ? "" : "s"} have been permanently removed from the app.
        </Txt>
        <View style={s.ref}>
          <Txt variant="label">Your confirmation reference</Txt>
          <Txt variant="title" testID="delete-account-reference">
            {done.reference}
          </Txt>
          <Txt variant="small">Completed {new Date(done.completed_at).toLocaleString("en-GB")}. Keep this if you’d like proof it’s done.</Txt>
        </View>
        <Button testID="delete-account-finish" title="Done" onPress={finish} />
      </View>
    );

  return (
    <View style={s.root} testID="delete-account-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="delete-account-back" onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/profile"))} style={s.iconBtn}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
      </View>
      <KeyboardAwareScrollView bottomOffset={110} keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, gap: spacing.lg }}>
        <Txt variant="display">Delete my account and data</Txt>
        <Txt>This permanently removes, straight away:</Txt>
        {["Your account and sign-in details", "Every family check, report and AI letter", "Any call-back requests you’ve sent to your adviser"].map((t) => (
          <Txt key={t} style={{ color: colors.onSurfaceSecondary }}>
            • {t}
          </Txt>
        ))}
        <Txt variant="small">This can’t be undone. If you’ve already spoken to an adviser, any advice records they hold outside this app are kept under their own regulatory duties. You can ask them about those directly.</Txt>
        <Field testID="delete-account-password" label="Enter your password to confirm" value={password} onChangeText={setPassword} secureTextEntry />
        <Checkbox testID="delete-account-confirm" checked={sure} onToggle={() => setSure(!sure)}>
          <Txt variant="small" style={{ color: colors.onSurfaceSecondary }}>
            I understand my data will be permanently deleted
          </Txt>
        </Checkbox>
        {error ? (
          <View style={s.error} testID="delete-account-error">
            <Txt color={colors.error}>{error}</Txt>
          </View>
        ) : null}
      </KeyboardAwareScrollView>
      <KeyboardStickyView offset={{ opened: insets.bottom - spacing.md }}>
        <View style={[s.footer, { paddingBottom: insets.bottom + spacing.lg }]}>
          <Button testID="delete-account-submit" title="Permanently delete everything" icon="trash-2" loading={busy} disabled={!password || !sure} onPress={submit} />
        </View>
      </KeyboardStickyView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  error: { backgroundColor: c.errorTint, padding: spacing.md, borderRadius: radius.md },
  ref: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.xs },
  footer: { paddingHorizontal: spacing.xl, paddingTop: spacing.md, backgroundColor: c.surface },
}));
