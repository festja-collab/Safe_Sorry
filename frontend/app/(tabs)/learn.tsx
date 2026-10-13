import { Feather } from "@react-native-vector-icons/feather";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { FlatList, Pressable, RefreshControl, View } from "react-native";
import Animated, { FadeInDown } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, ArticleSummary } from "@/src/api";
import { ErrorState, Txt } from "@/src/components/ui";
import { usesNativeTabs } from "@/src/navigation";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

export default function Learn() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { colors } = useTheme();
  const s = useStyles();
  const bottomChrome = usesNativeTabs ? insets.bottom : 0;
  const q = useQuery({ queryKey: ["articles"], queryFn: () => api<ArticleSummary[]>("/articles") });

  return (
    <View style={s.root} testID="learn-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.md }]}>
        <Txt variant="label">Learn</Txt>
        <Txt variant="display">Plain-English guides</Txt>
      </View>
      {q.isError ? (
        <ErrorState testID="learn-error" message={(q.error as Error).message} onRetry={() => q.refetch()} />
      ) : (
        <FlatList
          data={q.data ?? []}
          keyExtractor={(a) => a.slug}
          contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: bottomChrome + spacing.xl }}
          refreshControl={<RefreshControl refreshing={q.isRefetching} onRefresh={() => q.refetch()} tintColor={colors.brandPrimary} />}
          ListEmptyComponent={
            q.isLoading ? (
              <View style={{ gap: spacing.lg, paddingTop: spacing.lg }}>
                {[0, 1, 2].map((i) => (
                  <View key={i} style={s.skeleton} />
                ))}
              </View>
            ) : (
              <Txt testID="learn-empty">No articles found</Txt>
            )
          }
          renderItem={({ item, index }) => (
            <Animated.View entering={FadeInDown.delay(index * 80).duration(400)}>
              <Pressable testID={`learn-article-${item.slug}`} onPress={() => router.push(`/article/${item.slug}`)} style={s.item}>
                <View style={s.metaRow}>
                  <Txt variant="small" color={colors.accentText}>
                    {item.category}
                  </Txt>
                  <Txt variant="small">· {item.read_minutes} min read</Txt>
                </View>
                <Txt variant="display" style={{ fontSize: 24, lineHeight: 30 }}>
                  {item.title}
                </Txt>
                <Txt>{item.excerpt}</Txt>
                <View style={s.metaRow}>
                  <Txt variant="small" color={colors.onSurface}>
                    Read
                  </Txt>
                  <Feather name="arrow-right" size={14} color={colors.onSurface} />
                </View>
              </Pressable>
            </Animated.View>
          )}
        />
      )}
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.xl, paddingBottom: spacing.md, gap: spacing.xs, backgroundColor: c.surface },
  item: { paddingVertical: spacing.xl, borderBottomWidth: 1, borderBottomColor: c.divider, gap: spacing.sm },
  metaRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  skeleton: { height: 120, borderRadius: radius.md, backgroundColor: c.surfaceSecondary },
}));
