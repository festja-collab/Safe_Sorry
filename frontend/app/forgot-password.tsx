import { Feather } from "@react-native-vector-icons/feather";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, View } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, User } from "@/src/api";
import { useAuth } from "@/src/auth";
import { Button, Field, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

export default function ForgotPassword() {
  const params = useLocalSearchParams<{ email?: string }>();
  const { applySession } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const [step, setStep] = useState<"email" | "code">("email");
  const [email, setEmail] = useState(params.email ?? "");
  const [code, setCode] = useState("");
  const [pw, setPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [info, setInfo] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const sendCode = async () => {
    setError("");
    setBusy(true);
    try {
      const r = await api<{ message: string }>("/auth/forgot-password", { method: "POST", body: { email: email.trim() } });
      setInfo(r.message);
      setStep("code");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const reset = async () => {
    setError("");
    if (!/^\d{6}$/.test(code)) return setError("Please enter the 6-digit code from the email.");
    if (pw.length < 10) return setError("Your new password needs at least 10 characters.");
    if (pw !== confirm) return setError("The new passwords don’t match.");
    setBusy(true);
    try {
      const r = await api<{ token: string; user: User }>("/auth/reset-password", {
        method: "POST",
        body: { email: email.trim(), code, new_password: pw },
      });
      await applySession(r);
      router.replace("/(tabs)");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={s.root} testID="forgot-password-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="forgot-back" onPress={() => (step === "code" ? setStep("email") : router.canGoBack() ? router.back() : router.replace("/auth"))} style={s.iconBtn}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
      </View>
      <KeyboardAwareScrollView bottomOffset={110} keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, gap: spacing.lg }}>
        <Txt variant="display">{step === "email" ? "Reset your password" : "Check your email"}</Txt>
        {step === "email" ? (
          <>
            <Txt>Enter the email you signed up with and we’ll send you a 6-digit code.</Txt>
            <Field testID="forgot-email-input" label="Email" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" placeholder="you@example.com" />
          </>
        ) : (
          <>
            <Txt testID="forgot-info">{info}</Txt>
            <Field testID="forgot-code-input" label="6-digit code" value={code} onChangeText={(v) => setCode(v.replace(/[^0-9]/g, ""))} keyboardType="number-pad" maxLength={6} placeholder="123456" />
            <Field testID="forgot-new-password" label="New password" value={pw} onChangeText={setPw} secureTextEntry placeholder="At least 10 characters" />
            <Field testID="forgot-confirm-password" label="Confirm new password" value={confirm} onChangeText={setConfirm} secureTextEntry />
            <Pressable testID="forgot-resend" onPress={sendCode} disabled={busy}>
              <Txt variant="small" color={colors.accentText}>
                Didn’t get it? Send a new code
              </Txt>
            </Pressable>
          </>
        )}
        {error ? (
          <View style={s.error} testID="forgot-error">
            <Txt color={colors.error}>{error}</Txt>
          </View>
        ) : null}
      </KeyboardAwareScrollView>
      <KeyboardStickyView offset={{ opened: insets.bottom - spacing.md }}>
        <View style={[s.footer, { paddingBottom: insets.bottom + spacing.lg }]}>
          {step === "email" ? (
            <Button testID="forgot-send-code" title="Send code" icon="mail" loading={busy} disabled={!email.includes("@")} onPress={sendCode} />
          ) : (
            <Button testID="forgot-reset-submit" title="Set new password" icon="lock" loading={busy} onPress={reset} />
          )}
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
