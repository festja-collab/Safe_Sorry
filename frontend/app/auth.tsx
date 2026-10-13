import { Feather } from "@react-native-vector-icons/feather";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, View } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuth } from "@/src/auth";
import { Button, Field, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

export default function AuthScreen() {
  const params = useLocalSearchParams<{ mode?: string }>();
  const [mode, setMode] = useState<"login" | "register">(params.mode === "login" ? "login" : "register");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { signIn, register } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();

  const submit = async () => {
    setError("");
    if (!email.trim() || !password || (mode === "register" && !name.trim())) {
      setError("Please fill in every field.");
      return;
    }
    setBusy(true);
    try {
      if (mode === "login") await signIn(email, password);
      else await register(name, email, password);
      router.replace(mode === "register" ? "/assessment" : "/(tabs)");
    } catch (e: any) {
      setError(e.message ?? "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={s.root}>
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="auth-back-button" onPress={() => (router.canGoBack() ? router.back() : router.replace("/onboarding"))} style={s.back}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
      </View>
      <KeyboardAwareScrollView bottomOffset={110} contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
        <Txt variant="label">{mode === "register" ? "Let's begin" : "Welcome back"}</Txt>
        <Txt variant="display" style={{ marginTop: spacing.sm }}>
          {mode === "register" ? "Somewhere safe to keep your family’s plan." : "Good to see you again."}
        </Txt>
        <Txt style={{ marginTop: spacing.md, marginBottom: spacing.xl }}>
          {mode === "register"
            ? "Create an account so your answers and story are saved for when you’re ready to act."
            : "Sign in to revisit your family’s story."}
        </Txt>
        <View style={{ gap: spacing.lg }}>
          {mode === "register" ? (
            <Field testID="auth-name-input" label="Your first name" value={name} onChangeText={setName} placeholder="e.g. Tom" autoCapitalize="words" />
          ) : null}
          <Field
            testID="auth-email-input"
            label="Email"
            value={email}
            onChangeText={setEmail}
            placeholder="you@example.com"
            autoCapitalize="none"
            keyboardType="email-address"
            autoComplete="email"
          />
          <Field
            testID="auth-password-input"
            label="Password"
            value={password}
            onChangeText={setPassword}
            placeholder="At least 6 characters"
            secureTextEntry
            onSubmitEditing={submit}
          />
          {error ? (
            <View testID="auth-error" style={s.error}>
              <Feather name="alert-circle" size={16} color={colors.error} />
              <Txt color={colors.error} style={{ flex: 1 }}>
                {error}
              </Txt>
            </View>
          ) : null}
          <Pressable testID="auth-toggle-mode" onPress={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }} style={{ paddingVertical: spacing.sm }}>
            <Txt variant="small">
              {mode === "login" ? "New here? " : "Already have an account? "}
              <Txt variant="small" color={colors.brandPrimary}>
                {mode === "login" ? "Create an account" : "Sign in"}
              </Txt>
            </Txt>
          </Pressable>
        </View>
      </KeyboardAwareScrollView>
      <KeyboardStickyView offset={{ opened: insets.bottom - spacing.md }}>
        <View style={[s.footer, { paddingBottom: insets.bottom + spacing.lg }]}>
          <Button testID="auth-submit-button" title={mode === "login" ? "Sign in" : "Create account"} icon="arrow-right" loading={busy} onPress={submit} />
        </View>
      </KeyboardStickyView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  back: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  content: { paddingHorizontal: spacing.xl, paddingTop: spacing.md, paddingBottom: spacing.xl },
  error: { flexDirection: "row", gap: spacing.sm, alignItems: "center", backgroundColor: c.errorTint, padding: spacing.md, borderRadius: radius.md },
  footer: { paddingHorizontal: spacing.xl, paddingTop: spacing.md, backgroundColor: c.surface },
}));
