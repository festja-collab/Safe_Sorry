import { Feather } from "@react-native-vector-icons/feather";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Image } from "expo-image";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import { useState } from "react";
import { Linking, Pressable, ScrollView, View } from "react-native";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, AdviserProfile, AssessmentSummary, logoUri } from "@/src/api";
import { useAuth } from "@/src/auth";
import { Button, Checkbox, Field, Txt } from "@/src/components/ui";
import { usesNativeTabs } from "@/src/navigation";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

type Config = AdviserProfile;
const TIMES = ["Mornings", "Afternoons", "Evenings", "Weekends", "Any time"];

export default function Adviser() {
  const { user } = useAuth();
  const params = useLocalSearchParams<{ assessment?: string }>();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const bottomChrome = usesNativeTabs ? insets.bottom : 0;
  const [name, setName] = useState(user?.name ?? "");
  const [phone, setPhone] = useState("");
  const [time, setTime] = useState("Any time");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [consent, setConsent] = useState(false);
  const router = useRouter();

  const config = useQuery({ queryKey: ["my-adviser"], queryFn: () => api<Config>("/my-adviser") });
  const adviser = config.data;
  const first = adviser?.name.split(" ")[0] ?? "your adviser";
  const list = useQuery({ queryKey: ["assessments"], queryFn: () => api<AssessmentSummary[]>("/assessments") });
  const assessmentId = params.assessment ?? list.data?.[0]?.id;

  const lead = useMutation({
    mutationFn: () =>
      api<{ id: string; email_sent: boolean }>("/leads", {
        method: "POST",
        body: { name, phone, preferred_time: time, message, assessment_id: assessmentId ?? null, consent },
      }),
    onError: (e: Error) => setError(e.message),
  });

  const submit = () => {
    setError("");
    if (!name.trim() || phone.trim().length < 6) {
      setError("Please add your name and a phone number we can reach you on.");
      return;
    }
    if (!consent) {
      setError("Please tick the box so we can pass your details to your adviser.");
      return;
    }
    lead.mutate();
  };

  return (
    <View style={s.root} testID="adviser-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.md }]}>
        <Txt variant="label">Talk to an adviser</Txt>
      </View>
      <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: bottomChrome + spacing.xl, gap: spacing.xl }}>
        <View style={s.intro}>
          {adviser?.photo_url ? (
            <Image source={{ uri: adviser.photo_url }} style={s.portrait} contentFit="cover" transition={300} testID="adviser-photo" />
          ) : (
            <View style={[s.portrait, s.monogram]} testID="adviser-photo">
              <Txt variant="display" color={colors.onBrandTertiary}>
                {(adviser?.name ?? "")
                  .split(" ")
                  .map((w) => w[0])
                  .join("")
                  .slice(0, 2)}
              </Txt>
            </View>
          )}
          <View style={{ flex: 1, gap: spacing.xs }}>
            <Txt variant="title" testID="adviser-name">
              {adviser ? `Hi, I’m ${first}.` : " "}
            </Txt>
            <Txt variant="small" testID="adviser-bio">
              {adviser?.bio ?? ""}
            </Txt>
          </View>
        </View>
        <Txt variant="display">Let’s close the gap together.</Txt>
        <Txt>
          Fifteen minutes on the phone is often all it takes. I’ll look at your story, find the cover that fits your
          budget, and help you put it in trust. As a dad myself, I know exactly why this matters.
        </Txt>

        {adviser?.calendly_url ? (
          <Button testID="adviser-book-call-button" title="Book a call" icon="calendar" onPress={() => WebBrowser.openBrowserAsync(adviser.calendly_url)} />
        ) : null}
        {adviser?.phone ? (
          <Button
            testID="adviser-call-now-button"
            title={`Call ${first} on ${adviser.phone}`}
            variant="secondary"
            icon="phone"
            onPress={() => Linking.openURL(`tel:${adviser.phone.replace(/[^0-9+]/g, "")}`)}
          />
        ) : null}

        {lead.isSuccess ? (
          <View style={s.success} testID="adviser-lead-success">
            <Feather name="check-circle" size={28} color={colors.success} />
            <Txt variant="title">Thank you, {name.split(" ")[0]}.</Txt>
            <Txt>
              Your request is with {first}. Expect a call {time === "Any time" ? "soon" : `in the ${time.toLowerCase()}`} — usually
              within one working day. Taking this step is the hardest part, and you’ve done it.
            </Txt>
          </View>
        ) : (
          <View style={s.form}>
            <Txt variant="title">Or ask {first} to call you</Txt>
            <Field testID="adviser-name-input" label="Your name" value={name} onChangeText={setName} placeholder="Your name" />
            <Field testID="adviser-phone-input" label="Phone number" value={phone} onChangeText={setPhone} placeholder="07700 900123" keyboardType="phone-pad" />
            <View style={{ gap: spacing.sm }}>
              <Txt variant="label">Best time to call</Txt>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ height: 56, flexGrow: 0 }} contentContainerStyle={{ gap: spacing.sm, alignItems: "center" }}>
                {TIMES.map((t) => (
                  <Pressable key={t} testID={`adviser-time-${t.toLowerCase().replace(" ", "-")}`} onPress={() => setTime(t)} style={[s.chip, time === t && s.chipOn]}>
                    <Txt variant="small" color={time === t ? colors.onSurfaceInverse : colors.onSurface}>
                      {t}
                    </Txt>
                  </Pressable>
                ))}
              </ScrollView>
            </View>
            <Field
              testID="adviser-message-input"
              label="Anything on your mind? (optional)"
              value={message}
              onChangeText={setMessage}
              placeholder="e.g. We’ve just had a baby…"
              multiline
              style={{ minHeight: 90, textAlignVertical: "top", flex: 1, fontSize: 16, paddingTop: 14 }}
            />
            {assessmentId ? (
              <View style={s.attach}>
                <Feather name="paperclip" size={14} color={colors.muted} />
                <Txt variant="small">Your latest family story will be shared with {first}.</Txt>
              </View>
            ) : null}
            <Checkbox testID="adviser-consent-checkbox" checked={consent} onToggle={() => setConsent(!consent)}>
              <Txt variant="small" style={{ color: colors.onSurfaceSecondary }}>
                I agree to my contact details and family report being shared with {adviser?.name ?? "my adviser"}
                {adviser?.firm_name ? ` at ${adviser.firm_name}` : ""} so they can contact me about protection.
              </Txt>
            </Checkbox>
            <Pressable testID="adviser-privacy-link" onPress={() => router.push("/privacy")}>
              <Txt variant="small" color={colors.accentText}>
                How we use your information
              </Txt>
            </Pressable>
            {error ? (
              <Txt testID="adviser-error" color={colors.error}>
                {error}
              </Txt>
            ) : null}
            <Button testID="adviser-submit-button" title="Request a call back" variant="secondary" icon="phone" loading={lead.isPending} onPress={submit} />
          </View>
        )}
        {adviser ? (
          <View style={[s.firm, { borderTopColor: adviser.brand_color || colors.surfaceInverse }]}>
            {adviser.logo_url ? <Image source={{ uri: logoUri(adviser.logo_url) }} style={s.logo} contentFit="contain" testID="adviser-firm-logo" /> : null}
            <Txt variant="small" style={{ textAlign: "center" }} testID="adviser-firm-info">
              {adviser.principal_name
                ? `${adviser.firm_name} (FRN ${adviser.fca_number}) is an Appointed Representative of ${adviser.principal_name}, which is authorised and regulated by the Financial Conduct Authority (FRN ${adviser.principal_fca_number}).`
                : `${adviser.firm_name} is authorised and regulated by the Financial Conduct Authority (FRN ${adviser.fca_number}).`}
            </Txt>
          </View>
        ) : null}
      </KeyboardAwareScrollView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.xl, paddingBottom: spacing.md, backgroundColor: c.surface },
  intro: { flexDirection: "row", alignItems: "center", gap: spacing.lg },
  portrait: { width: 88, height: 88, borderRadius: radius.lg, backgroundColor: c.surfaceTertiary },
  monogram: { backgroundColor: c.brandTertiary, alignItems: "center", justifyContent: "center" },
  form: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.lg },
  chip: { height: 36, flexShrink: 0, paddingHorizontal: spacing.lg, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, justifyContent: "center" },
  chipOn: { backgroundColor: c.surfaceInverse },
  attach: { flexDirection: "row", gap: spacing.sm, alignItems: "center" },
  firm: { borderTopWidth: 3, paddingTop: spacing.lg, gap: spacing.md, alignItems: "center" },
  logo: { width: 160, height: 56 },
  success: { backgroundColor: c.successTint, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md },
}));
