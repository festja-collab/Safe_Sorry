import { Feather } from "@react-native-vector-icons/feather";
import { useQuery } from "@tanstack/react-query";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Pressable, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, Article } from "@/src/api";
import { Button, ErrorState, Loading, Txt } from "@/src/components/ui";
import { makeStyles, spacing, useTheme } from "@/src/theme";

export default function ArticleScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const q = useQuery({ queryKey: ["article", slug], queryFn: () => api<Article>(`/articles/${slug}`) });

  return (
    <View style={s.root} testID="article-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="article-back-button" onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/learn"))} style={s.back}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
      </View>
      {q.isLoading ? (
        <Loading />
      ) : q.isError || !q.data ? (
        <ErrorState testID="article-error" message="We couldn't open this guide." onRetry={() => q.refetch()} />
      ) : (
        <ScrollView contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: insets.bottom + spacing.xl, gap: spacing.lg }}>
          <Txt variant="small" color={colors.brandPrimary}>
            {q.data.category} · {q.data.read_minutes} min read
          </Txt>
          <Txt variant="hero" testID="article-title">
            {q.data.title}
          </Txt>
          <Txt style={{ fontSize: 18, lineHeight: 28, color: colors.muted }}>{q.data.excerpt}</Txt>
          <View style={s.divider} />
          {q.data.body.map((p, i) => (
            <Txt key={i} style={{ fontSize: 17, lineHeight: 28 }}>
              {p}
            </Txt>
          ))}
          <View style={s.divider} />
          <Button testID="article-start-check-button" title="See what this means for my family" icon="arrow-right" onPress={() => router.push("/assessment")} />
        </ScrollView>
      )}
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  back: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  divider: { height: 1, backgroundColor: c.divider, marginVertical: spacing.sm },
}));
