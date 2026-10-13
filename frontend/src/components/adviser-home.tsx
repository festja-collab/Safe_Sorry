import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { RefreshControl, ScrollView, Share, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, Lead } from "@/src/api";
import { useAuth } from "@/src/auth";
import { LeadCard } from "@/src/components/lead-card";
import { Button, Loading, Txt } from "@/src/components/ui";
import { usesNativeTabs } from "@/src/navigation";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

type Stats = { new: number; contacted: number; closed: number; total: number; clients: number };

export function AdviserHome() {
  const { user } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const bottomChrome = usesNativeTabs ? insets.bottom : 0;
  const stats = useQuery({ queryKey: ["adviser-stats"], queryFn: () => api<Stats>("/adviser/stats") });
  const leads = useQuery({ queryKey: ["adviser-leads", "new"], queryFn: () => api<Lead[]>("/adviser/leads?status=new") });
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
      <View style={[s.header, { paddingTop: insets.top + spacing.md }]}>
        <Txt variant="label">Adviser dashboard</Txt>
        <Txt variant="display">{user?.name}</Txt>
      </View>
      <ScrollView
        contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, paddingBottom: bottomChrome + spacing.xl, gap: spacing.xl }}
        refreshControl={<RefreshControl refreshing={stats.isRefetching || leads.isRefetching} onRefresh={refresh} tintColor={colors.brandPrimary} />}
      >
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
          <Button
            testID="adviser-share-code-button"
            title="Share my code"
            variant="secondary"
            icon="share-2"
            onPress={() =>
              Share.share({
                message: `See what your family would face if the worst happened, in 5 minutes. Download Safe > Sorry and use my adviser code ${user?.adviser_code} when you sign up. – ${user?.name}`,
              })
            }
          />
        </View>

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
  header: { paddingHorizontal: spacing.xl, paddingBottom: spacing.md, gap: spacing.xs, backgroundColor: c.surface },
  tiles: { flexDirection: "row", gap: spacing.md },
  tile: { flex: 1, backgroundColor: c.surfaceInverse, borderRadius: radius.lg, padding: spacing.lg, gap: spacing.xs },
  codeCard: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md },
}));
