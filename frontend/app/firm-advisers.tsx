import { Feather } from "@react-native-vector-icons/feather";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, Share, View } from "react-native";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api } from "@/src/api";
import { Button, Field, Loading, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

type FirmAdviser = { id: string; name: string; email: string; title: string; adviser_code: string; is_firm_admin: boolean; pending_setup: boolean; leads: number };
type Created = { name: string; email: string; adviser_code: string; temporary_password: string };

export default function FirmAdvisers() {
  const router = useRouter();
  const qc = useQueryClient();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [title, setTitle] = useState("Protection Adviser");
  const q = useQuery({ queryKey: ["firm-advisers"], queryFn: () => api<FirmAdviser[]>("/firm/advisers") });
  const add = useMutation({
    mutationFn: () => api<Created>("/firm/advisers", { method: "POST", body: { name, email, title } }),
    onSuccess: () => {
      setName("");
      setEmail("");
      qc.invalidateQueries({ queryKey: ["firm-advisers"] });
    },
  });
  const created = add.data;

  return (
    <View style={s.root} testID="firm-advisers-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="firm-advisers-back" onPress={() => (router.canGoBack() ? router.back() : router.replace("/adviser-settings"))} style={s.iconBtn}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
        <Txt variant="small">Your firm’s advisers</Txt>
        <View style={s.iconBtn} />
      </View>
      <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, paddingBottom: insets.bottom + spacing.xl, gap: spacing.lg }}>
        <Txt variant="display">Advisers</Txt>
        {q.isLoading ? (
          <View style={{ height: 80 }}>
            <Loading />
          </View>
        ) : (
          (q.data ?? []).map((a) => (
            <View key={a.id} style={s.row} testID={`firm-adviser-${a.adviser_code}`}>
              <View style={{ flex: 1, gap: 2 }}>
                <Txt style={{ color: colors.onSurface }}>
                  {a.name}
                  {a.is_firm_admin ? " · Admin" : ""}
                </Txt>
                <Txt variant="small">
                  {a.adviser_code} · {a.leads} lead{a.leads === 1 ? "" : "s"}
                  {a.pending_setup ? " · Awaiting first sign-in" : ""}
                </Txt>
              </View>
            </View>
          ))
        )}

        {created ? (
          <View style={s.created} testID="firm-adviser-created">
            <Txt variant="title">{created.name} is set up</Txt>
            <Txt variant="small">Share these sign-in details privately. The temporary password is shown only once; they’ll choose their own the first time they sign in.</Txt>
            <Txt style={{ color: colors.onSurface }}>Email: {created.email}</Txt>
            <Txt style={{ color: colors.onSurface }} testID="firm-adviser-temp-password">
              Temporary password: {created.temporary_password}
            </Txt>
            <Txt style={{ color: colors.onSurface }}>Adviser code: {created.adviser_code}</Txt>
            <Button
              testID="firm-adviser-share-details"
              title="Share sign-in details"
              variant="secondary"
              icon="share-2"
              onPress={() =>
                Share.share({
                  message: `Your Safe > Sorry adviser account is ready.\nEmail: ${created.email}\nTemporary password: ${created.temporary_password}\nYour adviser code: ${created.adviser_code}\nYou'll be asked to choose your own password when you first sign in.`,
                })
              }
            />
          </View>
        ) : null}

        <View style={s.card}>
          <Txt variant="title">Add an adviser</Txt>
          <Field testID="firm-adviser-name-input" label="Full name" value={name} onChangeText={setName} placeholder="e.g. Jane Smith" autoCapitalize="words" />
          <Field testID="firm-adviser-email-input" label="Work email" value={email} onChangeText={setEmail} placeholder="jane@yourfirm.co.uk" autoCapitalize="none" keyboardType="email-address" />
          <Field testID="firm-adviser-title-input" label="Job title" value={title} onChangeText={setTitle} />
          {add.isError ? (
            <Txt testID="firm-adviser-error" color={colors.error}>
              {(add.error as Error).message}
            </Txt>
          ) : null}
          <Button testID="firm-adviser-add-button" title="Add adviser" icon="user-plus" loading={add.isPending} disabled={!name.trim() || !email.trim()} onPress={() => add.mutate()} />
        </View>
      </KeyboardAwareScrollView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  row: { flexDirection: "row", alignItems: "center", padding: spacing.lg, borderRadius: radius.lg, backgroundColor: c.surfaceSecondary },
  card: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.lg },
  created: { backgroundColor: c.successTint, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.sm },
}));
