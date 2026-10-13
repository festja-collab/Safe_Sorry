import { Feather } from "@react-native-vector-icons/feather";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, View } from "react-native";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { AdviserProfile, api } from "@/src/api";
import { Button, Field, Loading, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

export default function LinkAdviser() {
  const router = useRouter();
  const qc = useQueryClient();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const [code, setCode] = useState("");
  const q = useQuery({ queryKey: ["my-adviser"], queryFn: () => api<AdviserProfile>("/my-adviser") });
  const link = useMutation({
    mutationFn: () => api<AdviserProfile>("/me/adviser", { method: "POST", body: { code } }),
    onSuccess: (a) => {
      qc.setQueryData(["my-adviser"], a);
      setCode("");
    },
  });

  return (
    <View style={s.root} testID="link-adviser-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="link-adviser-back-button" onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/profile"))} style={s.iconBtn}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
      </View>
      <KeyboardAwareScrollView bottomOffset={24} keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, paddingBottom: insets.bottom + spacing.xl, gap: spacing.xl }}>
        <Txt variant="display">Your adviser</Txt>
        {q.isLoading ? (
          <View style={{ height: 100 }}>
            <Loading />
          </View>
        ) : q.data ? (
          <View style={s.card} testID="link-adviser-current">
            {q.data.photo_url ? <Image source={{ uri: q.data.photo_url }} style={s.photo} contentFit="cover" /> : null}
            <View style={{ flex: 1, gap: 2 }}>
              <Txt variant="title">{q.data.name}</Txt>
              <Txt variant="small">{q.data.title}</Txt>
              <Txt variant="small">{q.data.firm_name}</Txt>
            </View>
          </View>
        ) : null}
        {link.isSuccess ? (
          <Txt testID="link-adviser-success" color={colors.success}>
            You’re now connected to {link.data.name}.
          </Txt>
        ) : null}
        <View style={{ gap: spacing.md }}>
          <Txt>Been given a code by an adviser? Enter it here and your call-back requests will go to them.</Txt>
          <Field testID="link-adviser-code-input" label="Adviser code" value={code} onChangeText={(v) => setCode(v.toUpperCase())} placeholder="e.g. MARK-SFL" autoCapitalize="characters" />
          {link.isError ? (
            <Txt testID="link-adviser-error" color={colors.error}>
              {(link.error as Error).message}
            </Txt>
          ) : null}
          <Button testID="link-adviser-submit" title="Connect" icon="link" disabled={code.trim().length < 2} loading={link.isPending} onPress={() => link.mutate()} />
        </View>
      </KeyboardAwareScrollView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  card: { flexDirection: "row", gap: spacing.lg, alignItems: "center", backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.lg },
  photo: { width: 64, height: 64, borderRadius: radius.md },
}));
