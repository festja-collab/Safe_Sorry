import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { FlatList, Pressable, RefreshControl, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, Lead } from "@/src/api";
import { LeadCard } from "@/src/components/lead-card";
import { ErrorState, Loading, Txt } from "@/src/components/ui";
import { usesNativeTabs } from "@/src/navigation";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

const FILTERS = [
  { id: "all", label: "All" },
  { id: "new", label: "New" },
  { id: "contacted", label: "Contacted" },
  { id: "closed", label: "Closed" },
];

export default function Leads() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const bottomChrome = usesNativeTabs ? insets.bottom : 0;
  const [filter, setFilter] = useState("all");
  const q = useQuery({
    queryKey: ["adviser-leads", filter],
    queryFn: () => api<Lead[]>(`/adviser/leads${filter === "all" ? "" : `?status=${filter}`}`),
  });

  return (
    <View style={s.root} testID="leads-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.md }]}>
        <Txt variant="label">Lead inbox</Txt>
        <Txt variant="display">Families who want to talk</Txt>
      </View>
      <View style={{ height: 56 }}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.chips}>
          {FILTERS.map((f) => (
            <Pressable key={f.id} testID={`leads-filter-${f.id}`} onPress={() => setFilter(f.id)} style={[s.chip, filter === f.id && s.chipOn]}>
              <Txt variant="small" color={filter === f.id ? colors.onSurfaceInverse : colors.onSurface}>
                {f.label}
              </Txt>
            </Pressable>
          ))}
        </ScrollView>
      </View>
      {q.isLoading ? (
        <Loading />
      ) : q.isError ? (
        <ErrorState testID="leads-error" message={(q.error as Error).message} onRetry={() => q.refetch()} />
      ) : (
        <FlatList
          data={q.data ?? []}
          keyExtractor={(l) => l.id}
          contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingTop: spacing.sm, paddingBottom: bottomChrome + spacing.xl, gap: spacing.md }}
          refreshControl={<RefreshControl refreshing={q.isRefetching} onRefresh={() => q.refetch()} tintColor={colors.brandPrimary} />}
          renderItem={({ item }) => <LeadCard lead={item} />}
          ListEmptyComponent={
            <View style={s.empty} testID="leads-empty">
              <Txt variant="title">Nothing here yet</Txt>
              <Txt variant="small">When a family asks you to call, they’ll appear here with their story.</Txt>
            </View>
          }
        />
      )}
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.xl, paddingBottom: spacing.sm, gap: spacing.xs, backgroundColor: c.surface },
  chips: { gap: spacing.sm, paddingHorizontal: spacing.xl, alignItems: "center" },
  chip: { height: 36, flexShrink: 0, paddingHorizontal: spacing.lg, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, justifyContent: "center" },
  chipOn: { backgroundColor: c.surfaceInverse },
  empty: { padding: spacing.xl, gap: spacing.sm, borderRadius: radius.lg, backgroundColor: c.surfaceSecondary },
}));
