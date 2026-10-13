import { Feather } from "@react-native-vector-icons/feather";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { Pressable, RefreshControl, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api } from "@/src/api";
import { ErrorState, Loading, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

type Row = { id: string; name: string; adviser_code: string; new: number; contacted: number; closed: number; clients: number; checks: number; leads: number };
type FirmStats = {
  totals: { leads: number; new: number; contacted: number; closed: number; clients: number; checks: number };
  advisers: Row[];
  by_source: { label: string; count: number }[];
};

export default function FirmDashboard() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const q = useQuery({ queryKey: ["firm-stats"], queryFn: () => api<FirmStats>("/firm/stats") });
  const t = q.data?.totals;
  const tiles = t
    ? [
        ["Clients", t.clients],
        ["Family checks", t.checks],
        ["Leads", t.leads],
        ["New", t.new],
        ["Contacted", t.contacted],
        ["Closed", t.closed],
      ]
    : [];

  return (
    <View style={s.root} testID="firm-dashboard-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="firm-dashboard-back" onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)"))} style={s.iconBtn}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
        <Txt variant="small">Firm dashboard</Txt>
        <View style={s.iconBtn} />
      </View>
      {q.isLoading ? (
        <Loading />
      ) : q.isError || !q.data ? (
        <ErrorState testID="firm-dashboard-error" message={(q.error as Error)?.message ?? "Couldn't load"} onRetry={() => q.refetch()} />
      ) : (
        <ScrollView
          contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, paddingBottom: insets.bottom + spacing.xl, gap: spacing.xl }}
          refreshControl={<RefreshControl refreshing={q.isRefetching} onRefresh={() => q.refetch()} tintColor={colors.brandPrimary} />}
        >
          <Txt variant="display">Across your firm</Txt>
          <View style={s.grid}>
            {tiles.map(([k, v]) => (
              <View key={k} style={s.tile} testID={`firm-total-${String(k).toLowerCase().replace(" ", "-")}`}>
                <Txt variant="display" color={colors.onSurfaceInverse}>
                  {v}
                </Txt>
                <Txt variant="small" color={colors.onSurfaceInverse} style={{ opacity: 0.75 }}>
                  {k}
                </Txt>
              </View>
            ))}
          </View>

          <View style={{ gap: spacing.md }}>
            <Txt variant="label">By adviser</Txt>
            {q.data.advisers.map((a) => (
              <View key={a.id} style={s.card} testID={`firm-adviser-row-${a.adviser_code}`}>
                <View style={{ flexDirection: "row", alignItems: "center" }}>
                  <Txt variant="title" style={{ flex: 1 }}>
                    {a.name}
                  </Txt>
                  <Txt variant="small">{a.adviser_code}</Txt>
                </View>
                <View style={{ flexDirection: "row", gap: spacing.md }}>
                  {[
                    ["Clients", a.clients],
                    ["Checks", a.checks],
                    ["Leads", a.leads],
                    ["New", a.new],
                    ["Closed", a.closed],
                  ].map(([k, v]) => (
                    <View key={k} style={{ flex: 1 }}>
                      <Txt variant="small">{k}</Txt>
                      <Txt style={{ color: colors.onSurface }}>{v}</Txt>
                    </View>
                  ))}
                </View>
              </View>
            ))}
          </View>

          {q.data.by_source.length ? (
            <View style={{ gap: spacing.sm }} testID="firm-lead-sources">
              <Txt variant="label">Where leads come from</Txt>
              {q.data.by_source.map((r) => (
                <View key={r.label} style={s.srcRow}>
                  <Txt style={{ flex: 1, color: colors.onSurface }}>{r.label}</Txt>
                  <Txt variant="title">{r.count}</Txt>
                </View>
              ))}
            </View>
          ) : null}
        </ScrollView>
      )}
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  tile: { width: "31%", flexGrow: 1, backgroundColor: c.surfaceInverse, borderRadius: radius.lg, padding: spacing.lg, gap: spacing.xs },
  card: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.lg, gap: spacing.md },
  srcRow: { flexDirection: "row", alignItems: "center", paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: c.divider },
}));
