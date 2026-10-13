import { Feather } from "@react-native-vector-icons/feather";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { Pressable, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api } from "@/src/api";
import { ErrorState, Loading, Txt } from "@/src/components/ui";
import { makeStyles, spacing, useTheme } from "@/src/theme";

type Privacy = { version: string; sections: { heading: string; body: string }[] };

export default function PrivacyScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const q = useQuery({ queryKey: ["privacy"], queryFn: () => api<Privacy>("/privacy") });

  return (
    <View style={s.root} testID="privacy-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="privacy-back" onPress={() => (router.canGoBack() ? router.back() : router.replace("/"))} style={s.iconBtn}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
      </View>
      {q.isLoading ? (
        <Loading />
      ) : q.isError || !q.data ? (
        <ErrorState testID="privacy-error" message="We couldn't load the privacy notice." onRetry={() => q.refetch()} />
      ) : (
        <ScrollView contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: insets.bottom + spacing.xl, gap: spacing.lg }}>
          <Txt variant="hero">Privacy notice</Txt>
          <Txt variant="small">Version {q.data.version}</Txt>
          {q.data.sections.map((sec) => (
            <View key={sec.heading} style={{ gap: spacing.sm }}>
              <Txt variant="title">{sec.heading}</Txt>
              <Txt>{sec.body}</Txt>
            </View>
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
}));
