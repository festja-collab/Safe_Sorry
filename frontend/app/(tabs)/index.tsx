import { Feather } from "@react-native-vector-icons/feather";
import { useQuery } from "@tanstack/react-query";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { Pressable, RefreshControl, ScrollView, View } from "react-native";
import Animated, { FadeInDown } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, ArticleSummary, AssessmentSummary, gbp } from "@/src/api";
import { useAuth } from "@/src/auth";
import { AdviserHome } from "@/src/components/adviser-home";
import { Button, IconBadge, Loading, Txt } from "@/src/components/ui";
import { usesNativeTabs } from "@/src/navigation";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

const FAMILY = "https://images.unsplash.com/photo-1492269815085-88eb3ffe14e5?crop=entropy&cs=srgb&fm=jpg&q=80&w=900";

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

function ClientHome() {
  const { user } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const bottomChrome = usesNativeTabs ? insets.bottom : 0;
  const list = useQuery({ queryKey: ["assessments"], queryFn: () => api<AssessmentSummary[]>("/assessments") });
  const articles = useQuery({ queryKey: ["articles"], queryFn: () => api<ArticleSummary[]>("/articles") });
  const latest = list.data?.[0];

  return (
    <View style={s.root} testID="home-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.md }]}>
        <Txt variant="label">{greeting()}</Txt>
        <Txt variant="display" testID="home-greeting">
          {user?.name ?? "Friend"}
        </Txt>
      </View>
      <ScrollView
        contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, paddingBottom: bottomChrome + spacing.xl, gap: spacing.xl }}
        refreshControl={<RefreshControl refreshing={list.isRefetching} onRefresh={() => list.refetch()} tintColor={colors.brandPrimary} />}
      >
        {list.isLoading ? (
          <View style={{ height: 240 }}>
            <Loading />
          </View>
        ) : latest ? (
          <Animated.View entering={FadeInDown.duration(500)}>
            <Pressable testID="home-latest-story-card" onPress={() => router.push(`/report/${latest.id}`)} style={s.storyCard}>
              <Txt variant="label" color={colors.onSurfaceInverse} style={{ opacity: 0.7 }}>
                Your family’s story
              </Txt>
              <Txt variant="display" color={colors.onSurfaceInverse} testID="home-latest-headline">
                {latest.headline}
              </Txt>
              <View style={s.statRow}>
                <View style={{ flex: 1 }}>
                  <Txt variant="small" color={colors.onSurfaceInverse} style={{ opacity: 0.7 }}>
                    Protected today
                  </Txt>
                  <Txt variant="title" color={colors.onSurfaceInverse}>
                    {latest.protected_pct}%
                  </Txt>
                </View>
                <View style={{ flex: 1 }}>
                  <Txt variant="small" color={colors.onSurfaceInverse} style={{ opacity: 0.7 }}>
                    Life cover gap
                  </Txt>
                  <Txt variant="title" color={colors.onSurfaceInverse}>
                    {gbp(latest.life_gap)}
                  </Txt>
                </View>
              </View>
              <View style={s.pctTrack}>
                <View style={[s.pctFill, { width: `${Math.max(4, latest.protected_pct)}%` }]} />
              </View>
              <View style={s.readRow}>
                <Txt color={colors.onSurfaceInverse}>Read your story</Txt>
                <Feather name="arrow-right" size={18} color={colors.onSurfaceInverse} />
              </View>
            </Pressable>
          </Animated.View>
        ) : (
          <Animated.View entering={FadeInDown.duration(500)} style={s.startCard}>
            <Image source={{ uri: FAMILY }} style={s.startImg} contentFit="cover" transition={300} />
            <View style={{ padding: spacing.xl, gap: spacing.md }}>
              <Txt variant="display">If tomorrow didn’t come, would they be okay?</Txt>
              <Txt>
                Most of us never ask. A few gentle questions will show you exactly what your family would face — in
                months, milestones and moments, not just numbers.
              </Txt>
              <Button testID="home-start-assessment-button" title="Start your family check" icon="arrow-right" onPress={() => router.push("/assessment")} />
            </View>
          </Animated.View>
        )}

        {latest ? (
          <Button testID="home-retake-button" title="Life changed? Update your check" variant="secondary" icon="refresh-cw" onPress={() => router.push("/assessment")} />
        ) : null}

        <Pressable testID="home-adviser-card" onPress={() => router.push("/(tabs)/adviser")} style={s.adviserRow}>
          <IconBadge name="message-circle" bg={colors.brandTertiary} fg={colors.onBrandTertiary} size={48} />
          <View style={{ flex: 1 }}>
            <Txt variant="title">Talk it through with a human</Txt>
            <Txt variant="small">Free, friendly, no pressure.</Txt>
          </View>
          <Feather name="chevron-right" size={20} color={colors.muted} />
        </Pressable>

        <View style={{ gap: spacing.md }}>
          <Txt variant="label">Worth a read</Txt>
          {(articles.data ?? []).slice(0, 2).map((a) => (
            <Pressable key={a.slug} testID={`home-article-${a.slug}`} onPress={() => router.push(`/article/${a.slug}`)} style={s.article}>
              <Txt variant="small" color={colors.accentText}>
                {a.category}
              </Txt>
              <Txt variant="title">{a.title}</Txt>
            </Pressable>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

export default function Home() {
  const { user } = useAuth();
  return user?.role === "adviser" ? <AdviserHome /> : <ClientHome />;
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.xl, paddingBottom: spacing.md, backgroundColor: c.surface, gap: spacing.xs },
  storyCard: { backgroundColor: c.surfaceInverse, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.lg },
  statRow: { flexDirection: "row", gap: spacing.lg },
  pctTrack: { height: 8, borderRadius: radius.pill, backgroundColor: c.inverseTrack, overflow: "hidden" },
  pctFill: { height: 8, borderRadius: radius.pill, backgroundColor: c.brandPrimary },
  readRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  startCard: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, overflow: "hidden" },
  startImg: { width: "100%", height: 200 },
  adviserRow: { flexDirection: "row", alignItems: "center", gap: spacing.lg, padding: spacing.lg, borderRadius: radius.lg, backgroundColor: c.surfaceSecondary, minHeight: 72 },
  article: { paddingVertical: spacing.lg, borderTopWidth: 1, borderTopColor: c.divider, gap: spacing.xs },
}));
