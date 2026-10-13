import { Feather } from "@react-native-vector-icons/feather";
import { useRouter } from "expo-router";
import { Pressable, View } from "react-native";

import { gbp, Lead, timeAgo } from "@/src/api";
import { Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

export const STATUS_LABEL = { new: "New", contacted: "Contacted", closed: "Closed" } as const;

export function StatusPill({ status }: { status: Lead["status"] }) {
  const { colors } = useTheme();
  const map = {
    new: { bg: colors.brandTertiary, fg: colors.onBrandTertiary },
    contacted: { bg: colors.infoTint, fg: colors.info },
    closed: { bg: colors.surfaceTertiary, fg: colors.muted },
  }[status];
  return (
    <View style={{ backgroundColor: map.bg, paddingHorizontal: spacing.md, paddingVertical: 2, borderRadius: radius.pill }}>
      <Txt variant="small" color={map.fg}>
        {STATUS_LABEL[status]}
      </Txt>
    </View>
  );
}

export function LeadCard({ lead }: { lead: Lead }) {
  const router = useRouter();
  const { colors } = useTheme();
  const s = useStyles();
  return (
    <Pressable testID={`lead-card-${lead.id}`} onPress={() => router.push(`/lead/${lead.id}`)} style={s.card}>
      <View style={s.row}>
        <Txt variant="title" style={{ flex: 1 }} numberOfLines={1}>
          {lead.name}
        </Txt>
        <StatusPill status={lead.status} />
      </View>
      {lead.summary ? (
        <Txt variant="small" numberOfLines={2} style={{ color: colors.onSurfaceSecondary }}>
          {lead.summary.headline}
        </Txt>
      ) : null}
      <View style={s.row}>
        <Txt variant="small">
          {timeAgo(lead.created_at)} · {lead.source_label}
        </Txt>
        <View style={{ flex: 1 }} />
        {lead.summary ? (
          <Txt variant="small" color={colors.accentText}>
            Life gap {gbp(lead.summary.life_gap)}
          </Txt>
        ) : null}
        <Feather name="chevron-right" size={18} color={colors.muted} />
      </View>
    </Pressable>
  );
}

const useStyles = makeStyles((c) => ({
  card: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.lg, gap: spacing.sm },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
}));
