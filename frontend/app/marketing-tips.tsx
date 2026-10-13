import { Feather } from "@react-native-vector-icons/feather";
import { useRouter } from "expo-router";
import { Pressable, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { IconBadge, Txt } from "@/src/components/ui";
import { TIP_SECTIONS } from "@/src/marketing-tips";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

export default function MarketingTips() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  return (
    <View style={s.root} testID="marketing-tips-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <Pressable testID="marketing-tips-back-button" onPress={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)"))} style={s.iconBtn}>
          <Feather name="arrow-left" size={22} color={colors.onSurface} />
        </Pressable>
        <Txt variant="small">Marketing tips</Txt>
        <View style={s.iconBtn} />
      </View>
      <ScrollView contentContainerStyle={{ padding: spacing.xl, paddingTop: spacing.sm, paddingBottom: insets.bottom + spacing.xl, gap: spacing.lg }}>
        <Txt variant="display">Bring in more families</Txt>
        <Txt>Practical ideas for social media and Google ads, written for UK protection advisers. This is general guidance, not compliance or legal advice.</Txt>
        {TIP_SECTIONS.map((sec) => (
          <View key={sec.id} style={s.card} testID={`marketing-tips-${sec.id}`}>
            <View style={s.titleRow}>
              <IconBadge name={sec.icon} bg={colors.brandTertiary} fg={colors.onBrandTertiary} size={36} />
              <Txt variant="title" style={{ flex: 1 }}>
                {sec.title}
              </Txt>
            </View>
            {sec.intro ? <Txt variant="small">{sec.intro}</Txt> : null}
            {sec.points.map((p) => (
              <View key={p} style={s.point}>
                <View style={s.dot} />
                <Txt style={{ flex: 1 }}>{p}</Txt>
              </View>
            ))}
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: spacing.lg, backgroundColor: c.surface },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  card: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md },
  titleRow: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  point: { flexDirection: "row", gap: spacing.md, alignItems: "flex-start" },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: c.brandPrimary, marginTop: 10 },
}));
