import { Feather } from "@react-native-vector-icons/feather";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, View } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, User } from "@/src/api";
import { useAuth } from "@/src/auth";
import { Button, Field, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

export default function ChangePassword() {
  const { user, applySession, signOut } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const forced = !!user?.must_change_password;
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const submit = async () => {
    setError("");
    if (next.length < 10) return setError("Your new password needs at least 10 characters.");
    if (next !== confirm) return setError("The new passwords don’t match.");
    setBusy(true);
    try {
      const r = await api<{ token: string; user: User }>("/auth/change-password", {
        method: "POST",
        body: { current_password: current, new_password: next },
      });
      await applySession(r);
      setDone(true);
      if (forced) router.replace("/(tabs)");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={s.root} testID="change-password-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        {forced ? (
          <Pressable testID="change-password-logout" onPress={async () => { await signOut(); router.replace("/onboarding"); }} style={s.iconBtn}>
            <Feather name="log-out" size={20} color={colors.onSurface} />
          </Pressable>
        ) : (
          <Pressable testID="change-password-back" onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/profile"))} style={s.iconBtn}>
            <Feather name="arrow-left" size={22} color={colors.onSurface} />
          </Pressable>
        )}
      </View>
      <KeyboardAwareScrollView bottomOffset={110} keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, gap: spacing.lg }}>
        <Txt variant="display">{forced ? "Welcome! Set your own password" : "Change password"}</Txt>
        <Txt>
          {forced
            ? "You signed in with a temporary password from your firm. Choose a new one only you know."
            : "For your security, this signs you out on any other phones."}
        </Txt>
        <Field testID="change-password-current" label={forced ? "Temporary password" : "Current password"} value={current} onChangeText={setCurrent} secureTextEntry />
        <Field testID="change-password-new" label="New password" value={next} onChangeText={setNext} secureTextEntry placeholder="At least 10 characters" />
        <Field testID="change-password-confirm" label="Confirm new password" value={confirm} onChangeText={setConfirm} secureTextEntry onSubmitEditing={submit} />
        {error ? (
          <View style={s.error} testID="change-password-error">
            <Txt color={colors.error}>{error}</Txt>
          </View>
        ) : null}
        {done && !forced ? (
          <Txt testID="change-password-success" color={colors.success}>
            Password changed.
          </Txt>
        ) : null}
      </KeyboardAwareScrollView>
      <KeyboardStickyView offset={{ opened: insets.bottom - spacing.md }}>
        <View style={[s.footer, { paddingBottom: insets.bottom + spacing.lg }]}>
          <Button testID="change-password-submit" title="Save new password" icon="lock" loading={busy} disabled={!current || !next || !confirm} onPress={submit} />
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
  footer: { paddingHorizontal: spacing.xl, paddingTop: spacing.md, backgroundColor: c.surface },
}));
