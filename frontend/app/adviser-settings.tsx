import { Feather } from "@react-native-vector-icons/feather";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, View } from "react-native";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { AdviserProfile, api } from "@/src/api";
import { useAuth } from "@/src/auth";
import { Button, Field, Loading, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

type P = { name: string; title: string; bio: string; photo_url: string; phone: string; calendly_url: string; lead_email: string };
type F = { name: string; fca_number: string; principal_name: string; principal_fca_number: string };

export default function AdviserSettings() {
  const { user } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const q = useQuery({ queryKey: ["adviser-profile"], queryFn: () => api<AdviserProfile>("/adviser/profile") });
  const [p, setP] = useState<P | null>(null);
  const [f, setF] = useState<F | null>(null);

  useEffect(() => {
    if (q.data && !p) {
      const d = q.data;
      setP({ name: d.name, title: d.title, bio: d.bio, photo_url: d.photo_url, phone: d.phone, calendly_url: d.calendly_url, lead_email: d.email });
      setF({ name: d.firm_name, fca_number: d.fca_number, principal_name: d.principal_name, principal_fca_number: d.principal_fca_number });
    }
  }, [q.data, p]);

  const save = useMutation({
    mutationFn: async () => {
      await api("/adviser/profile", { method: "PUT", body: p });
      if (user?.is_firm_admin) await api("/firm", { method: "PUT", body: f });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["adviser-profile"] });
      qc.invalidateQueries({ queryKey: ["my-adviser"] });
    },
  });

  const field = (key: keyof P, label: string, extra: object = {}) => (
    <Field testID={`settings-${key}-input`} label={label} value={p?.[key] ?? ""} onChangeText={(v) => { setP((x) => (x ? { ...x, [key]: v } : x)); save.reset(); }} autoCapitalize="none" {...extra} />
  );
  const firmField = (key: keyof F, label: string) => (
    <Field testID={`settings-firm-${key}-input`} label={label} value={f?.[key] ?? ""} onChangeText={(v) => { setF((x) => (x ? { ...x, [key]: v } : x)); save.reset(); }} />
  );

  return (
    <View style={s.root} testID="adviser-settings-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="settings-back-button" onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/profile"))} style={s.iconBtn}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
        <Txt variant="small">Adviser settings</Txt>
        <View style={s.iconBtn} />
      </View>
      {!p ? (
        <Loading />
      ) : (
        <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, paddingBottom: insets.bottom + spacing.xl, gap: spacing.lg }}>
          <Txt variant="display">How clients see you</Txt>
          <View style={s.card}>
            {field("name", "Name", { autoCapitalize: "words" })}
            {field("title", "Job title", { autoCapitalize: "sentences" })}
            {field("bio", "Short bio", { autoCapitalize: "sentences", multiline: true })}
            {field("photo_url", "Photo link (https://…)")}
            {field("phone", "Phone number", { keyboardType: "phone-pad" })}
            {field("calendly_url", "Booking link (https://…)")}
            {field("lead_email", "Send call-back requests to", { keyboardType: "email-address" })}
          </View>
          {user?.is_firm_admin ? (
            <>
              <Txt variant="display">Firm details</Txt>
              <Txt variant="small">Shown to every client of your firm on the Adviser screen.</Txt>
              <View style={s.card}>
                {firmField("name", "Firm name")}
                {firmField("fca_number", "Firm FCA number")}
                {firmField("principal_name", "Principal firm (if Appointed Representative)")}
                {firmField("principal_fca_number", "Principal FCA number")}
              </View>
            </>
          ) : null}
          {save.isError ? (
            <Txt testID="settings-error" color={colors.error}>
              {(save.error as Error).message}
            </Txt>
          ) : null}
          {save.isSuccess ? (
            <Txt testID="settings-saved" color={colors.success}>
              Saved. Your clients will see the changes straight away.
            </Txt>
          ) : null}
          <Button testID="settings-save-button" title="Save changes" icon="check" loading={save.isPending} onPress={() => save.mutate()} />
        </KeyboardAwareScrollView>
      )}
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  card: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.lg },
}));
