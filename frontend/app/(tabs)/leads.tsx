import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { FlatList, Pressable, RefreshControl, ScrollView, useWindowDimensions, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, Lead } from "@/src/api";
import { downloadLeadsCsv } from "@/src/export-leads";
import { LeadCard } from "@/src/components/lead-card";
import { Button, ErrorState, Loading, Txt } from "@/src/components/ui";
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
  const { width } = useWindowDimensions();
  const wide = width >= 900; // laptop / desktop browser
  const cols = width >= 1280 ? 3 : wide ? 2 : 1;
  const bottomChrome = usesNativeTabs ? insets.bottom : 0;
  const [filter, setFilter] = useState("all");
  const q = useQuery({
    queryKey: ["adviser-leads", filter],
    queryFn: () => api<Lead[]>(`/adviser/leads${filter === "all" ? "" : `?status=${filter}`}`),
  });
  const exp = useMutation({ mutationFn: () => downloadLeadsCsv(filter) });

  return (
    <View style={s.root} testID="leads-screen">
      <View style={[s.header, wide && s.headerWide, { paddingTop: insets.top + spacing.md }]}>
        <View style={{ flex: 1, gap: spacing.xs }}>
          <Txt variant="label">Lead inbox</Txt>
          <Txt variant="display">Families who want to talk</Txt>
        </View>
        <View style={{ gap: spacing.xs, alignItems: wide ? "flex-end" : "stretch" }}>
          <Button
            testID="leads-export-button"
            title="Download for CRM"
            icon="download"
            variant="secondary"
            loading={exp.isPending}
            onPress={() => exp.mutate()}
          />
          <Txt variant="small" testID="leads-export-hint">
            {exp.isError ? (exp.error as Error).message : "CSV file: contact details and consent, ready to import into Greenlight or any CRM"}
          </Txt>
        </View>
      </View>
      <View style={[{ height: 56 }, wide && s.wideBox]}>
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
          key={`cols-${cols}`}
          numColumns={cols}
          data={q.data ?? []}
          keyExtractor={(l) => l.id}
          style={wide ? s.wideBox : undefined}
          columnWrapperStyle={cols > 1 ? { gap: spacing.md } : undefined}
          contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingTop: spacing.sm, paddingBottom: bottomChrome + spacing.xl, gap: spacing.md }}
          refreshControl={<RefreshControl refreshing={q.isRefetching} onRefresh={() => q.refetch()} tintColor={colors.brandPrimary} />}
          renderItem={({ item }) => (
            <View style={{ flex: 1 / cols }}>
              <LeadCard lead={item} />
            </View>
          )}
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
  header: { paddingHorizontal: spacing.xl, paddingBottom: spacing.sm, gap: spacing.md, backgroundColor: c.surface },
  headerWide: { flexDirection: "row", alignItems: "flex-end", width: "100%", maxWidth: 1240, alignSelf: "center" },
  wideBox: { width: "100%", maxWidth: 1240, alignSelf: "center" },
  chips: { gap: spacing.sm, paddingHorizontal: spacing.xl, alignItems: "center" },
  chip: { height: 36, flexShrink: 0, paddingHorizontal: spacing.lg, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, justifyContent: "center" },
  chipOn: { backgroundColor: c.surfaceInverse },
  empty: { padding: spacing.xl, gap: spacing.sm, borderRadius: radius.lg, backgroundColor: c.surfaceSecondary },
}));
