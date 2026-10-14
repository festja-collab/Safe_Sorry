import { Feather } from "@react-native-vector-icons/feather";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Linking, Pressable, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, gbp, Lead, LeadStatus, niceDate } from "@/src/api";
import { STATUS_LABEL, StatusPill } from "@/src/components/lead-card";
import { Button, ErrorState, Loading, Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

export default function LeadDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const q = useQuery({ queryKey: ["lead", id], queryFn: () => api<Lead>(`/adviser/leads/${id}`) });
  const setStatus = useMutation({
    mutationFn: (status: LeadStatus) => api(`/adviser/leads/${id}`, { method: "PATCH", body: { status } }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["lead", id] });
      qc.invalidateQueries({ queryKey: ["adviser-leads"] });
      qc.invalidateQueries({ queryKey: ["adviser-stats"] });
    },
  });

  const header = (
    <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
      <Pressable testID="lead-back-button" onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)/leads"))} style={s.iconBtn}>
        <Feather name="arrow-left" size={22} color={colors.onSurface} />
      </Pressable>
      <Txt variant="small">Lead</Txt>
      <View style={s.iconBtn} />
    </View>
  );
  if (q.isLoading)
    return (
      <View style={s.root}>
        {header}
        <Loading />
      </View>
    );
  if (q.isError || !q.data)
    return (
      <View style={s.root}>
        {header}
        <ErrorState testID="lead-error" message="We couldn't open this lead." onRetry={() => q.refetch()} />
      </View>
    );

  const l = q.data;
  const r = l.assessment?.results;
  const i = l.assessment?.inputs;
  const family = i
    ? [
        i.relationship === "single" ? "Single" : `${i.relationship === "married" ? "Married to" : "Lives with"} ${i.partner_name || "partner"}`,
        i.children?.length ? `${i.children.length} child${i.children.length > 1 ? "ren" : ""} (${i.children.map((c: any) => `${c.name} ${c.age}`).join(", ")})` : "No children",
        `Earns ${gbp(i.annual_income)}`,
        i.housing === "mortgage" ? `Mortgage ${gbp(i.mortgage_balance)}` : i.housing === "rent" ? "Renting" : "Owns home",
      ]
    : [];

  return (
    <View style={s.root} testID="lead-detail-screen">
      {header}
      <ScrollView contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, paddingBottom: insets.bottom + spacing.xl, gap: spacing.xl, width: "100%", maxWidth: 760, alignSelf: "center" }}>
        <View style={{ gap: spacing.sm }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
            <Txt variant="display" style={{ flex: 1 }} testID="lead-name">
              {l.name}
            </Txt>
            <StatusPill status={l.status} />
          </View>
          <Txt variant="small">
            Requested {niceDate(l.created_at)}
            {l.preferred_time ? ` · Prefers ${l.preferred_time.toLowerCase()}` : ""}
          </Txt>
          <Txt variant="small" testID="lead-source">
            Came from: {l.source_label}
            {l.source_code ? ` (code ${l.source_code})` : ""}
            {l.heard_from ? ` · Heard via ${l.heard_from}` : ""}
          </Txt>
        </View>

        <View style={{ gap: spacing.sm }}>
          <Button testID="lead-call-button" title={`Call ${l.phone}`} icon="phone" onPress={() => Linking.openURL(`tel:${l.phone.replace(/[^0-9+]/g, "")}`)} />
          <Button testID="lead-email-button" title={`Email ${l.email}`} variant="secondary" icon="mail" onPress={() => Linking.openURL(`mailto:${l.email}`)} />
        </View>

        {l.message ? (
          <View style={s.card}>
            <Txt variant="label">Their message</Txt>
            <Txt testID="lead-message">{l.message}</Txt>
          </View>
        ) : null}

        <View style={{ gap: spacing.sm }}>
          <Txt variant="label">Status</Txt>
          <View style={{ flexDirection: "row", gap: spacing.sm }}>
            {(["new", "contacted", "closed"] as LeadStatus[]).map((st) => (
              <Pressable key={st} testID={`lead-status-${st}`} disabled={setStatus.isPending} onPress={() => setStatus.mutate(st)} style={[s.statusBtn, l.status === st && s.statusOn]}>
                <Txt variant="small" color={l.status === st ? colors.onSurfaceInverse : colors.onSurface}>
                  {STATUS_LABEL[st]}
                </Txt>
              </Pressable>
            ))}
          </View>
        </View>

        {r ? (
          <View style={s.card} testID="lead-family-summary">
            <Txt variant="label">Their family story</Txt>
            <Txt variant="title">{r.headline}</Txt>
            {family.map((f) => (
              <Txt key={f} variant="small" style={{ color: colors.onSurfaceSecondary }}>
                • {f}
              </Txt>
            ))}
            <View style={s.table} testID="lead-cover-table">
              <View style={s.tr}>
                {["", "Needs", "Has", "Gap"].map((h) => (
                  <Txt key={h} variant="small" style={[s.td, h ? s.num : s.first]}>
                    {h}
                  </Txt>
                ))}
              </View>
              {(
                [
                  ["Life cover", r.gaps.life, ""],
                  ["Income protection", r.gaps.income, "/mo"],
                  ["Critical illness", r.gaps.critical, ""],
                ] as const
              ).map(([k, g, unit]) => (
                <View key={k} style={[s.tr, s.trLine]} testID={`lead-cover-${k.split(" ")[0].toLowerCase()}`}>
                  <Txt variant="small" style={[s.td, s.first, { color: colors.onSurface }]}>
                    {k}
                  </Txt>
                  <Txt variant="small" style={[s.td, s.num]}>{gbp(g.need) + unit}</Txt>
                  <Txt variant="small" style={[s.td, s.num]}>{gbp(g.have) + unit}</Txt>
                  <Txt variant="small" style={[s.td, s.num, { color: g.gap > 0 ? colors.error : colors.success, fontWeight: "700" }]}>
                    {gbp(g.gap) + unit}
                  </Txt>
                </View>
              ))}
            </View>
            {i ? (
              <View style={{ gap: spacing.xs }} testID="lead-existing-cover">
                <Txt variant="label">What they have now</Txt>
                {[
                  `Life insurance: ${Number(i.life_cover) ? gbp(i.life_cover) : "none"}`,
                  `Death in service: ${Number(i.death_in_service) ? `${i.death_in_service}× salary (${gbp(i.death_in_service * i.annual_income)})` : "none"}`,
                  `Income protection: ${Number(i.income_protection) ? `${gbp(i.income_protection)}/mo` : "none"}`,
                  `Critical illness: ${Number(i.critical_illness) ? gbp(i.critical_illness) : "none"}`,
                  `Employer sick pay: ${Number(i.sick_pay_months) ? `${i.sick_pay_months} month${Number(i.sick_pay_months) === 1 ? "" : "s"}` : "statutory only"}`,
                  `Savings: ${gbp(i.savings || 0)}`,
                ].map((t) => (
                  <Txt key={t} variant="small" style={{ color: colors.onSurfaceSecondary }}>
                    • {t}
                  </Txt>
                ))}
                <Txt variant="small">“Has” for life cover includes life insurance, death in service and savings.</Txt>
              </View>
            ) : null}
            {i?.worry ? <Txt variant="small">Biggest worry: {i.worry}</Txt> : null}
            <Button testID="lead-open-report-button" title="Open full family report" variant="secondary" icon="file-text" onPress={() => router.push(`/report/${l.assessment_id}`)} />
          </View>
        ) : (
          <Txt variant="small">This family hadn’t completed a check when they asked for a call.</Txt>
        )}
      </ScrollView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  card: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md },
  statusBtn: { flex: 1, height: 44, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, alignItems: "center", justifyContent: "center" },
  statusOn: { backgroundColor: c.surfaceInverse },
  table: { gap: 0 },
  tr: { flexDirection: "row", alignItems: "center", paddingVertical: spacing.sm, gap: spacing.xs },
  trLine: { borderTopWidth: 1, borderTopColor: c.border },
  td: { flex: 1 },
  first: { flex: 1.3 },
  num: { textAlign: "right" },
}));
