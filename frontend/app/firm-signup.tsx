import { Feather } from "@react-native-vector-icons/feather";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, View } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, uploadFile, User } from "@/src/api";
import { useAuth } from "@/src/auth";
import { ColorPicker, LogoBox, PickedLogo, pickLogo, BRAND_COLORS } from "@/src/components/firm-branding";
import { Button, Checkbox, Field, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

type Form = {
  firm_name: string;
  fca_number: string;
  principal_name: string;
  principal_fca_number: string;
  name: string;
  title: string;
  phone: string;
  email: string;
  password: string;
};

const EMPTY: Form = { firm_name: "", fca_number: "", principal_name: "", principal_fca_number: "", name: "", title: "", phone: "", email: "", password: "" };

export default function FirmSignup() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const { applySession } = useAuth();
  const [f, setF] = useState<Form>(EMPTY);
  const [isAR, setIsAR] = useState(false);
  const [color, setColor] = useState(BRAND_COLORS[0].hex);
  const [logo, setLogo] = useState<PickedLogo | null>(null);
  const [agree, setAgree] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k: keyof Form) => (v: string) => setF((x) => ({ ...x, [k]: v }));
  const field = (k: keyof Form, label: string, extra: object = {}) => (
    <Field testID={`firm-signup-${k.replace(/_/g, "-")}-input`} label={label} value={f[k]} onChangeText={set(k)} {...extra} />
  );

  const submit = async () => {
    setError("");
    if (!f.firm_name.trim() || !f.name.trim() || !f.email.trim()) return setError("Please add your firm name, your name and your email.");
    if (!/^\d{6,7}$/.test(f.fca_number.trim())) return setError("Please enter your firm’s FCA number (6 or 7 digits).");
    if (isAR && (!f.principal_name.trim() || !/^\d{6,7}$/.test(f.principal_fca_number.trim())))
      return setError("Please add your principal firm’s name and FCA number.");
    if (f.password.length < 10) return setError("Please choose a password of at least 10 characters.");
    if (!agree) return setError("Please read and accept the privacy notice to continue.");
    setBusy(true);
    try {
      const body = {
        ...f,
        fca_number: f.fca_number.trim(),
        principal_name: isAR ? f.principal_name.trim() : "",
        principal_fca_number: isAR ? f.principal_fca_number.trim() : "",
        email: f.email.trim(),
        brand_color: color,
        privacy_accepted: true,
      };
      const r = await api<{ token: string; user: User }>("/firms/register", { method: "POST", body });
      await applySession(r);
      if (logo) await uploadFile("/firm/logo", logo).catch(() => null); // can be retried from settings
      router.replace("/(tabs)");
    } catch (e: any) {
      setError(e.message ?? "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={s.root} testID="firm-signup-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="firm-signup-back-button" onPress={() => (router.canGoBack() ? router.back() : router.replace("/onboarding"))} style={s.back}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
      </View>
      <KeyboardAwareScrollView bottomOffset={110} keyboardShouldPersistTaps="handled" contentContainerStyle={s.content}>
        <Txt variant="label">For advisers & firms</Txt>
        <Txt variant="display">Set up your firm</Txt>
        <Txt>Give your clients a branded family check that sends call-back requests straight to you. Free for 14 days, no card needed.</Txt>

        <Txt variant="title">1. Your firm</Txt>
        <View style={s.card}>
          {field("firm_name", "Firm name", { autoCapitalize: "words", placeholder: "e.g. Acme Wealth Ltd" })}
          {field("fca_number", "Firm FCA number (FRN)", { keyboardType: "number-pad", placeholder: "6 or 7 digits" })}
          <Checkbox testID="firm-signup-ar-checkbox" checked={isAR} onToggle={() => setIsAR(!isAR)}>
            <Txt variant="small" style={{ color: colors.onSurfaceSecondary }}>
              We’re an Appointed Representative of a principal firm
            </Txt>
          </Checkbox>
          {isAR ? (
            <>
              {field("principal_name", "Principal firm name", { autoCapitalize: "words" })}
              {field("principal_fca_number", "Principal FCA number", { keyboardType: "number-pad" })}
            </>
          ) : null}
        </View>

        <Txt variant="title">2. Your branding</Txt>
        <View style={s.card}>
          <ColorPicker value={color} onChange={setColor} />
          <View style={[s.preview, { backgroundColor: color }]} testID="firm-signup-color-preview">
            <Txt variant="title" color={colors.onSurfaceInverse}>
              {f.firm_name.trim() || "Your firm"}
            </Txt>
            <Txt variant="small" color={colors.onSurfaceInverse}>
              How your invite pages will look
            </Txt>
          </View>
          <LogoBox testID="firm-signup-logo-button" uri={logo?.uri ?? ""} onPick={async () => setLogo((await pickLogo()) ?? logo)} />
        </View>

        <Txt variant="title">3. You (firm admin)</Txt>
        <View style={s.card}>
          {field("name", "Your full name", { autoCapitalize: "words" })}
          {field("title", "Job title (optional)", { autoCapitalize: "words", placeholder: "e.g. Protection Adviser" })}
          {field("phone", "Phone (optional)", { keyboardType: "phone-pad" })}
          {field("email", "Work email", { autoCapitalize: "none", keyboardType: "email-address", autoComplete: "email" })}
          {field("password", "Password", { secureTextEntry: true, placeholder: "At least 10 characters" })}
        </View>

        <Checkbox testID="firm-signup-privacy-checkbox" checked={agree} onToggle={() => setAgree(!agree)}>
          <Txt variant="small" style={{ color: colors.onSurfaceSecondary }}>
            I’ve read the privacy notice. I confirm my firm will get its own compliance sign-off before promoting the app to clients.
          </Txt>
        </Checkbox>
        <Pressable testID="firm-signup-open-privacy" onPress={() => router.push("/privacy")}>
          <Txt variant="small" color={colors.accentText}>
            Read the privacy notice
          </Txt>
        </Pressable>
        {error ? (
          <View testID="firm-signup-error" style={s.error}>
            <Feather name="alert-circle" size={16} color={colors.error} />
            <Txt color={colors.error} style={{ flex: 1 }}>
              {error}
            </Txt>
          </View>
        ) : null}
      </KeyboardAwareScrollView>
      <KeyboardStickyView offset={{ opened: insets.bottom - spacing.md }}>
        <View style={[s.footer, { paddingBottom: insets.bottom + spacing.lg }]}>
          <Button testID="firm-signup-submit-button" title="Start 14-day free trial" icon="arrow-right" loading={busy} onPress={submit} />
        </View>
      </KeyboardStickyView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  back: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  content: { paddingHorizontal: spacing.xl, paddingTop: spacing.md, paddingBottom: spacing.xl, gap: spacing.lg },
  card: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.lg },
  preview: { borderRadius: radius.md, padding: spacing.lg, gap: spacing.xs },
  error: { flexDirection: "row", gap: spacing.sm, alignItems: "center", backgroundColor: c.errorTint, padding: spacing.md, borderRadius: radius.md },
  footer: { paddingHorizontal: spacing.xl, paddingTop: spacing.md, backgroundColor: c.surface },
}));
