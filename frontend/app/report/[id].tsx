import { Feather } from "@react-native-vector-icons/feather";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect } from "react";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";
import Animated, { FadeIn, FadeInDown, useAnimatedStyle, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, Assessment, Gap, gbp, Impact, Milestone, Story } from "@/src/api";
import { Button, ErrorState, IconBadge, Loading, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, ThemeColors, useTheme } from "@/src/theme";

const HERO = "https://images.unsplash.com/photo-1492269815085-88eb3ffe14e5?crop=entropy&cs=srgb&fm=jpg&q=80&w=1200";

function tone(c: ThemeColors, t: Impact["tone"]) {
  return {
    error: { bg: c.errorTint, fg: c.error },
    warning: { bg: c.warningTint, fg: c.warning },
    success: { bg: c.successTint, fg: c.success },
    info: { bg: c.infoTint, fg: c.info },
  }[t];
}

function WritingPulse() {
  const o = useSharedValue(0.35);
  useEffect(() => {
    o.value = withRepeat(withTiming(1, { duration: 900 }), -1, true);
  }, [o]);
  const st = useAnimatedStyle(() => ({ opacity: o.value }));
  return (
    <Animated.View style={st}>
      <Txt variant="title">Writing your family’s story…</Txt>
    </Animated.View>
  );
}

function StoryCard({ id, initial }: { id: string; initial: Story | null }) {
  const s = useStyles();
  const { colors } = useTheme();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["story", id],
    queryFn: () => api<Story>(`/assessments/${id}/story`, { method: "POST" }),
    enabled: !initial,
    retry: false,
    staleTime: Infinity,
  });
  useEffect(() => {
    if (q.data) qc.invalidateQueries({ queryKey: ["assessment", id] });
  }, [q.data, qc, id]);
  const story = initial ?? q.data;

  if (!story && q.isError)
    return <ErrorState testID="story-error" message="We couldn’t write your story just now." onRetry={() => q.refetch()} />;

  return (
    <View style={s.storyCard} testID="story-card">
      <View style={s.storyTape} />
      <Txt variant="label">A letter about your family</Txt>
      {!story ? (
        <View style={{ gap: spacing.md, paddingVertical: spacing.lg }} testID="story-loading">
          <WritingPulse />
          <Txt variant="small">Our writer is turning your answers into something real. This takes around 20 seconds.</Txt>
          {[90, 100, 70].map((w, i) => (
            <View key={i} style={[s.storyLine, { width: `${w}%` }]} />
          ))}
        </View>
      ) : (
        <Animated.View entering={FadeIn.duration(700)} style={{ gap: spacing.lg }}>
          <Txt variant="display" testID="story-title">
            {story.title}
          </Txt>
          {story.paragraphs.map((p, i) => (
            <Txt key={i} style={{ fontSize: 17, lineHeight: 28, color: colors.onSurface }} testID={`story-paragraph-${i}`}>
              {p}
            </Txt>
          ))}
          {story.closing ? (
            <View style={s.highlight}>
              <Txt style={{ fontFamily: "Fraunces", fontSize: 18, lineHeight: 26, color: colors.onSurface }}>{story.closing}</Txt>
            </View>
          ) : null}
        </Animated.View>
      )}
    </View>
  );
}

function Timeline({ milestones, runway, runoutDate }: { milestones: Milestone[]; runway: number | null; runoutDate: string | null }) {
  const s = useStyles();
  const { colors } = useTheme();
  const items = [{ month: 0, label: "Today", kind: "today", date: "Now", funded: true } as const, ...milestones];
  return (
    <View testID="report-timeline">
      {items.map((m, i) => {
        const last = i === items.length - 1;
        const isRun = m.kind === "runout";
        const nextFunded = !last && items[i + 1].funded && !isRun;
        return (
          <Animated.View key={`${m.label}-${i}`} entering={FadeInDown.delay(i * 90).duration(400)} style={s.tlRow}>
            <View style={s.tlRail}>
              <View
                style={[
                  s.tlDot,
                  { backgroundColor: isRun ? colors.error : m.funded ? colors.success : colors.surface, borderColor: isRun ? colors.error : m.funded ? colors.success : colors.borderStrong },
                  isRun && s.tlDotBig,
                ]}
              >
                {isRun ? <Feather name="alert-triangle" size={14} color={colors.onError} /> : null}
              </View>
              {!last ? (
                <View style={[s.tlLine, nextFunded ? { backgroundColor: colors.success } : { backgroundColor: "transparent", borderLeftWidth: 2, borderStyle: "dashed", borderColor: colors.error, opacity: 0.5 }]} />
              ) : null}
            </View>
            <View style={[s.tlBody, !m.funded && !isRun && { opacity: 0.55 }]}>
              <Txt variant="small">{m.date}</Txt>
              <Txt variant={isRun ? "title" : "body"} color={isRun ? colors.error : colors.onSurface}>
                {m.label}
              </Txt>
              {isRun ? (
                <Txt variant="small">Everything below this line, your family faces without you — and without money.</Txt>
              ) : !m.funded ? (
                <Txt variant="small" color={colors.error}>
                  Unfunded
                </Txt>
              ) : null}
            </View>
          </Animated.View>
        );
      })}
      {runway === null ? (
        <View style={[s.note, { backgroundColor: colors.successTint }]}>
          <Feather name="check-circle" size={16} color={colors.success} />
          <Txt variant="small" style={{ flex: 1, color: colors.onSurface }}>
            Every milestone above would still be funded.
          </Txt>
        </View>
      ) : null}
    </View>
  );
}

function GapCard({ title, icon, gap, desc, testID }: { title: string; icon: string; gap: Gap; desc: string; testID: string }) {
  const s = useStyles();
  const { colors } = useTheme();
  const pct = gap.need ? Math.min(100, (gap.have / gap.need) * 100) : 100;
  const unit = gap.monthly ? "/mo" : "";
  return (
    <View style={s.gapCard} testID={testID}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
        <IconBadge name={icon} bg={colors.brandTertiary} fg={colors.onBrandTertiary} />
        <View style={{ flex: 1 }}>
          <Txt variant="title">{title}</Txt>
          <Txt variant="small">{desc}</Txt>
        </View>
      </View>
      <View style={s.bar}>
        <View style={[s.barFill, { width: `${Math.max(3, pct)}%` }]} />
      </View>
      <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
        <View>
          <Txt variant="small">You have</Txt>
          <Txt style={{ color: colors.onSurface }}>
            {gbp(gap.have)}
            {unit}
          </Txt>
        </View>
        <View style={{ alignItems: "flex-end" }}>
          <Txt variant="small">Your family needs</Txt>
          <Txt style={{ color: colors.onSurface }}>
            {gbp(gap.need)}
            {unit}
          </Txt>
        </View>
      </View>
      <View style={[s.gapPill, { backgroundColor: gap.gap > 0 ? colors.errorTint : colors.successTint }]}>
        <Txt variant="small" color={gap.gap > 0 ? colors.error : colors.success} testID={`${testID}-gap`}>
          {gap.gap > 0 ? `Gap: ${gbp(gap.gap)}${unit}` : "No gap — well done"}
        </Txt>
      </View>
    </View>
  );
}

export default function Report() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const q = useQuery({ queryKey: ["assessment", id], queryFn: () => api<Assessment>(`/assessments/${id}`) });
  const back = () => (router.canGoBack() ? router.back() : router.replace("/(tabs)"));

  const header = (
    <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
      <Pressable testID="report-back-button" onPress={back} style={s.iconBtn}>
        <Feather name="arrow-left" size={22} color={colors.onSurface} />
      </Pressable>
      <Txt variant="small">Your family’s story</Txt>
      <View style={s.iconBtn} />
    </View>
  );

  if (q.isLoading)
    return (
      <View style={s.root}>
        {header}
        <Loading label="Gathering your family’s numbers…" testID="report-loading" />
      </View>
    );
  if (q.isError || !q.data)
    return (
      <View style={s.root}>
        {header}
        <ErrorState testID="report-error" message="We couldn’t load this report." onRetry={() => q.refetch()} />
      </View>
    );

  const { results: r, inputs: i } = q.data;
  const horizon = Math.max(r.runway_months ?? 0, ...r.milestones.map((m) => m.month), 12);
  const runwayPct = r.runway_months === null ? 100 : Math.max(4, (r.runway_months / horizon) * 100);
  const partner = i.partner_name || "your partner";

  return (
    <View style={s.root} testID="report-screen">
      {header}
      <ScrollView contentContainerStyle={{ paddingBottom: insets.bottom + spacing.xl }}>
        <View style={s.hero}>
          <Image source={{ uri: HERO }} style={StyleSheet.absoluteFill} contentFit="cover" transition={400} />
          <LinearGradient colors={[colors.scrim, colors.surfaceInverse]} locations={[0.2, 0.95]} style={StyleSheet.absoluteFill} />
          <Animated.View entering={FadeInDown.duration(600)} style={s.heroText}>
            <Txt variant="label" color={colors.onSurfaceInverse} style={{ opacity: 0.75 }}>
              If the worst happened tomorrow
            </Txt>
            <Txt variant="display" color={colors.onSurfaceInverse} testID="report-headline">
              {r.headline}
            </Txt>
          </Animated.View>
        </View>

        <View style={s.section}>
          {r.has_dependants ? (
            <View style={s.runwayCard} testID="report-runway">
              <Txt variant="label">Savings runway</Txt>
              <Txt variant="title">
                {r.runway_months === null ? "The money wouldn’t run out" : `Money lasts ${r.runway_label}`}
              </Txt>
              <View style={s.runTrack}>
                <LinearGradient
                  colors={[colors.success, colors.warning, colors.error]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={[s.runFill, { width: `${runwayPct}%` }]}
                />
              </View>
              <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                <Txt variant="small">Today</Txt>
                <Txt variant="small">{r.runout_date ?? "Beyond every milestone"}</Txt>
              </View>
              {r.monthly_gap_death > 0 ? (
                <Txt variant="small">
                  Each month, {partner} would be {gbp(r.monthly_gap_death)} short of the life your family lives today.
                </Txt>
              ) : null}
            </View>
          ) : null}

          {r.milestones.length ? (
            <View style={{ gap: spacing.md }}>
              <Txt variant="label">The moments ahead</Txt>
              <Timeline milestones={r.milestones} runway={r.runway_months} runoutDate={r.runout_date} />
            </View>
          ) : null}

          <View style={{ gap: spacing.md }}>
            <Txt variant="label">What it would mean, in real terms</Txt>
            {r.impacts.map((im, idx) => {
              const t = tone(colors, im.tone);
              return (
                <Animated.View key={idx} entering={FadeInDown.delay(idx * 70).duration(400)} style={s.impact} testID={`report-impact-${idx}`}>
                  <IconBadge name={im.icon} bg={t.bg} fg={t.fg} />
                  <View style={{ flex: 1, gap: spacing.xs }}>
                    <Txt variant="title" style={{ fontSize: 18, lineHeight: 24 }}>
                      {im.title}
                    </Txt>
                    <Txt variant="small" style={{ color: colors.onSurfaceSecondary }}>
                      {im.body}
                    </Txt>
                  </View>
                </Animated.View>
              );
            })}
          </View>

          <StoryCard id={q.data.id} initial={q.data.story} />

          <View style={{ gap: spacing.md }}>
            <Txt variant="label">Where the gaps are</Txt>
            <GapCard testID="gap-life" title="Life cover" icon="umbrella" gap={r.gaps.life} desc="Clears debts and replaces your income while they need you." />
            <GapCard testID="gap-income" title="Income protection" icon="activity" gap={r.gaps.income} desc={`If you couldn't work, savings last ${r.illness_runway_label}.`} />
            <GapCard testID="gap-critical" title="Critical illness" icon="heart" gap={r.gaps.critical} desc="A lump sum so recovery isn’t a money worry." />
          </View>

          <View style={s.cta}>
            <Txt variant="display" color={colors.onSurfaceInverse}>
              This is fixable. Often for less than a weekly takeaway.
            </Txt>
            <Txt color={colors.onSurfaceInverse} style={{ opacity: 0.8 }}>
              A friendly adviser can turn this story into a plan in one short call.
            </Txt>
            <Button
              testID="report-talk-adviser-button"
              title="Talk to someone who can help"
              icon="arrow-right"
              onPress={() => router.push({ pathname: "/(tabs)/adviser", params: { assessment: q.data.id } })}
            />
          </View>
          <Txt variant="small" style={{ textAlign: "center" }}>
            Estimates only, based on 2025/26 UK tax and benefit rates. Not financial advice.
          </Txt>
        </View>
      </ScrollView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: spacing.lg, paddingBottom: spacing.sm, backgroundColor: c.surface },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  hero: { height: 360, justifyContent: "flex-end", marginHorizontal: spacing.lg, borderRadius: radius.lg, overflow: "hidden", backgroundColor: c.surfaceInverse },
  heroText: { padding: spacing.xl, gap: spacing.sm },
  section: { padding: spacing.xl, gap: spacing["2xl"] },
  runwayCard: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md },
  runTrack: { height: 14, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, overflow: "hidden" },
  runFill: { height: 14, borderRadius: radius.pill },
  tlRow: { flexDirection: "row", gap: spacing.lg },
  tlRail: { width: 28, alignItems: "center" },
  tlDot: { width: 16, height: 16, borderRadius: 8, borderWidth: 2, marginTop: 4, alignItems: "center", justifyContent: "center" },
  tlDotBig: { width: 28, height: 28, borderRadius: 14, marginTop: 0 },
  tlLine: { flex: 1, width: 2, minHeight: 28, marginVertical: 2 },
  tlBody: { flex: 1, paddingBottom: spacing.xl, gap: 2 },
  note: { flexDirection: "row", gap: spacing.sm, alignItems: "center", padding: spacing.md, borderRadius: radius.md },
  impact: { flexDirection: "row", gap: spacing.lg, padding: spacing.lg, borderRadius: radius.lg, backgroundColor: c.surfaceSecondary },
  storyCard: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md, borderWidth: 1, borderColor: c.border },
  storyTape: { position: "absolute", top: -10, alignSelf: "center", width: 90, height: 20, backgroundColor: c.brandTertiary, opacity: 0.9, borderRadius: radius.sm, transform: [{ rotate: "-3deg" }] },
  storyLine: { height: 10, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary },
  highlight: { backgroundColor: c.highlight, padding: spacing.lg, borderRadius: radius.md },
  gapCard: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md },
  bar: { height: 8, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, overflow: "hidden" },
  barFill: { height: 8, borderRadius: radius.pill, backgroundColor: c.brandSecondary },
  gapPill: { alignSelf: "flex-start", paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: radius.pill },
  cta: { backgroundColor: c.surfaceInverse, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.lg },
}));
