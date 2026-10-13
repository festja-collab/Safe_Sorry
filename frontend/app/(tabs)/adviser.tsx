import { Feather } from "@react-native-vector-icons/feather";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Image } from "expo-image";
import { useLocalSearchParams } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import { useState } from "react";
import { Linking, Pressable, ScrollView, View } from "react-native";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, AssessmentSummary } from "@/src/api";
import { useAuth } from "@/src/auth";
import { Button, Field, Txt } from "@/src/components/ui";
import { usesNativeTabs } from "@/src/navigation";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

type Config = {
  calendly_url: string;
  adviser: { name: string; bio: string; photo_url: string; phone: string; firm_name: string; fca_number: string };
};
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

  const config = useQuery({ queryKey: ["config"], queryFn: () => api<Config>("/config") });
  const adviser = config.data?.adviser;
  const first = adviser?.name.split(" ")[0] ?? "your adviser";
  const list = useQuery({ queryKey: ["assessments"], queryFn: () => api<AssessmentSummary[]>("/assessments") });
  const assessmentId = params.assessment ?? list.data?.[0]?.id;

  const lead = useMutation({
    mutationFn: () =>
      api<{ id: string; email_sent: boolean }>("/leads", {
        method: "POST",
        body: { name, phone, preferred_time: time, message, assessment_id: assessmentId ?? null },
      }),
    onError: (e: Error) => setError(e.message),
  });

  const submit = () => {
    setError("");
    if (!name.trim() || phone.trim().length < 6) {
      setError("Please add your name and a phone number we can reach you on.");
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
          <Image source={adviser ? { uri: adviser.photo_url } : undefined} style={s.portrait} contentFit="cover" transition={300} testID="adviser-photo" />
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
          budget, and help you write it in trust.
        </Txt>

        <Button
          testID="adviser-book-call-button"
          title="Book a call"
          icon="calendar"
          disabled={!config.data}
          onPress={() => config.data && WebBrowser.openBrowserAsync(config.data.calendly_url)}
        />
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
            {error ? (
              <Txt testID="adviser-error" color={colors.error}>
                {error}
              </Txt>
            ) : null}
            <Button testID="adviser-submit-button" title="Request a call back" variant="secondary" icon="phone" loading={lead.isPending} onPress={submit} />
          </View>
        )}
        {adviser ? (
          <Txt variant="small" style={{ textAlign: "center" }} testID="adviser-firm-info">
            {adviser.firm_name} is authorised and regulated by the Financial Conduct Authority. FCA No. {adviser.fca_number}.
          </Txt>
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
  form: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.lg },
  chip: { height: 36, flexShrink: 0, paddingHorizontal: spacing.lg, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, justifyContent: "center" },
  chipOn: { backgroundColor: c.surfaceInverse },
  attach: { flexDirection: "row", gap: spacing.sm, alignItems: "center" },
  success: { backgroundColor: c.successTint, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md },
}));
