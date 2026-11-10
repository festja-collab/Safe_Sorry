import { Feather } from "@react-native-vector-icons/feather";
import { useQuery } from "@tanstack/react-query";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Pressable, RefreshControl, ScrollView, Share, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { AdviserProfile, api, Lead, logoUri } from "@/src/api";
import { useAuth } from "@/src/auth";
import { LeadCard } from "@/src/components/lead-card";
import { Button, Loading, Txt } from "@/src/components/ui";
import { usesNativeTabs } from "@/src/navigation";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

type Count = { label: string; count: number };
type Stats = { new: number; contacted: number; closed: number; total: number; clients: number; by_source: Count[]; by_heard: Count[] };
const CAMPAIGNS = ["FB", "IG", "GOOGLE", "TIKTOK", "FLYER"];

export function AdviserHome() {
  const { user } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const bottomChrome = usesNativeTabs ? insets.bottom : 0;
  const stats = useQuery({ queryKey: ["adviser-stats"], queryFn: () => api<Stats>("/adviser/stats") });
  const leads = useQuery({ queryKey: ["adviser-leads", "new"], queryFn: () => api<Lead[]>("/adviser/leads?status=new") });
  const profile = useQuery({ queryKey: ["adviser-profile"], queryFn: () => api<AdviserProfile>("/adviser/profile") });
  const trialLeft = profile.data?.trial_days_left;
  const [campaign, setCampaign] = useState(CAMPAIGNS[0]);
  const adLink = `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/start/${user?.adviser_code}?src=${campaign}`;
  const refresh = () => {
    stats.refetch();
    leads.refetch();
  };

  const tiles = [
    { label: "New leads", value: stats.data?.new, id: "new" },
    { label: "Contacted", value: stats.data?.contacted, id: "contacted" },
    { label: "Clients", value: stats.data?.clients, id: "clients" },
  ];

  return (
    <View style={s.root} testID="adviser-home-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.md, borderBottomColor: profile.data?.brand_color || colors.surfaceInverse }]}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
          <View style={{ flex: 1, gap: spacing.xs }}>
            <Txt variant="label">{profile.data?.firm_name || "Adviser dashboard"}</Txt>
            <Txt variant="display">{user?.name}</Txt>
          </View>
          {profile.data?.logo_url ? <Image source={{ uri: logoUri(profile.data.logo_url) }} style={s.logo} contentFit="contain" testID="adviser-home-logo" /> : null}
        </View>
      </View>
      <ScrollView
        contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, paddingBottom: bottomChrome + spacing.xl, gap: spacing.xl }}
        refreshControl={<RefreshControl refreshing={stats.isRefetching || leads.isRefetching} onRefresh={refresh} tintColor={colors.brandPrimary} />}
      >
        {trialLeft != null ? (
          <View style={[s.trial, trialLeft === 0 && { backgroundColor: colors.errorTint }]} testID="adviser-trial-banner">
            <Feather name="clock" size={18} color={trialLeft === 0 ? colors.error : colors.onBrandTertiary} />
            <Txt style={{ flex: 1, color: trialLeft === 0 ? colors.error : colors.onBrandTertiary }}>
              {trialLeft === 0
                ? "Your free trial has ended. We’ll be in touch about plans. Everything keeps working for now."
                : `Free trial: ${trialLeft} day${trialLeft === 1 ? "" : "s"} left`}
            </Txt>
          </View>
        ) : null}
        <View style={s.tiles}>
          {tiles.map((t) => (
            <View key={t.id} style={s.tile} testID={`adviser-stat-${t.id}`}>
              <Txt variant="display" color={colors.onSurfaceInverse}>
                {t.value ?? "–"}
              </Txt>
              <Txt variant="small" color={colors.onSurfaceInverse} style={{ opacity: 0.75 }}>
                {t.label}
              </Txt>
            </View>
          ))}
        </View>

        <View style={s.codeCard}>
          <Txt variant="label">Your adviser code</Txt>
          <Txt variant="display" testID="adviser-code" color={colors.accentText}>
            {user?.adviser_code}
          </Txt>
          <Txt variant="small">Clients who enter this code when they sign up are linked to you, and their call-back requests come straight to your inbox.</Txt>
          <Button testID="adviser-invite-client-button" title="Invite a client" icon="send" onPress={() => router.push("/invite")} />
          {user?.is_firm_admin ? (
            <Button testID="adviser-firm-dashboard-button" title="Firm dashboard" variant="secondary" icon="bar-chart-2" onPress={() => router.push("/firm-dashboard")} />
          ) : null}
          <Button
            testID="adviser-share-code-button"
            title="Share my code"
            variant="secondary"
            icon="share-2"
            onPress={() =>
              Share.share({
                message: `See what your family would face if the worst happened, in 5 minutes. It's free and there's nothing to download: ${process.env.EXPO_PUBLIC_BACKEND_URL}/api/start/${user?.adviser_code} – ${user?.name}`,
              })
            }
          />
        </View>

        <View style={s.codeCard} testID="adviser-ad-links">
          <Txt variant="label">Ad links</Txt>
          <Txt variant="small">Use a different link for each ad or campaign. People who sign up from it get a code like {user?.adviser_code}-{campaign}, so you can see which ads bring in leads.</Txt>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ height: 56, flexGrow: 0 }} contentContainerStyle={{ gap: spacing.sm, alignItems: "center" }}>
            {CAMPAIGNS.map((c) => (
              <Pressable key={c} testID={`adviser-campaign-${c.toLowerCase()}`} onPress={() => setCampaign(c)} style={[s.chip, campaign === c && s.chipOn]}>
                <Txt variant="small" color={campaign === c ? colors.onSurfaceInverse : colors.onSurface}>
                  {c}
                </Txt>
              </Pressable>
            ))}
          </ScrollView>
          <Txt variant="small" testID="adviser-ad-link" style={{ color: colors.onSurface }}>
            {adLink}
          </Txt>
          <Button testID="adviser-share-ad-link" title="Share ad link" variant="secondary" icon="link" onPress={() => Share.share({ message: adLink })} />
          <Button testID="adviser-marketing-tips-button" title="Marketing tips" variant="ghost" icon="book-open" onPress={() => router.push("/marketing-tips")} />
        </View>

        {stats.data && stats.data.total > 0 ? (
          <View style={{ gap: spacing.sm }} testID="adviser-lead-sources">
            <Txt variant="label">Where your leads come from</Txt>
            {[...stats.data.by_source, ...stats.data.by_heard.map((h) => ({ label: `Heard via ${h.label}`, count: h.count }))].map((r) => (
              <View key={r.label} style={s.srcRow}>
                <Txt style={{ flex: 1, color: colors.onSurface }}>{r.label}</Txt>
                <Txt variant="title">{r.count}</Txt>
              </View>
            ))}
          </View>
        ) : null}

        <View style={{ gap: spacing.md }}>
          <Txt variant="label">New leads</Txt>
          {leads.isLoading ? (
            <View style={{ height: 100 }}>
              <Loading />
            </View>
          ) : leads.data?.length ? (
            leads.data.slice(0, 5).map((l) => <LeadCard key={l.id} lead={l} />)
          ) : (
            <Txt testID="adviser-home-no-leads">No new leads right now. Share your code to start the conversation.</Txt>
          )}
          <Button testID="adviser-view-all-leads" title="View all leads" variant="ghost" icon="arrow-right" onPress={() => router.push("/(tabs)/leads")} />
        </View>
      </ScrollView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.xl, paddingBottom: spacing.md, gap: spacing.xs, backgroundColor: c.surface, borderBottomWidth: 3 },
  logo: { width: 96, height: 48 },
  trial: { flexDirection: "row", alignItems: "center", gap: spacing.md, backgroundColor: c.brandTertiary, borderRadius: radius.md, padding: spacing.lg },
  tiles: { flexDirection: "row", gap: spacing.md },
  tile: { flex: 1, backgroundColor: c.surfaceInverse, borderRadius: radius.lg, padding: spacing.lg, gap: spacing.xs },
  codeCard: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md },
  chip: { height: 36, flexShrink: 0, paddingHorizontal: spacing.lg, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, justifyContent: "center" },
  chipOn: { backgroundColor: c.surfaceInverse },
  srcRow: { flexDirection: "row", alignItems: "center", paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: c.divider },
}));
