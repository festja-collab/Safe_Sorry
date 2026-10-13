import { Feather } from "@react-native-vector-icons/feather";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { Pressable, RefreshControl, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, AssessmentSummary, niceDate } from "@/src/api";
import { useAuth } from "@/src/auth";
import { Button, ErrorState, IconBadge, Loading, Txt } from "@/src/components/ui";
import { usesNativeTabs } from "@/src/navigation";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

export default function Profile() {
  const { user, signOut } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const bottomChrome = usesNativeTabs ? insets.bottom : 0;
  const q = useQuery({ queryKey: ["assessments"], queryFn: () => api<AssessmentSummary[]>("/assessments") });

  return (
    <View style={s.root} testID="profile-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.md }]}>
        <Txt variant="label">Profile</Txt>
        <Txt variant="display" testID="profile-name">
          {user?.name}
        </Txt>
        <Txt variant="small" testID="profile-email">
          {user?.email}
        </Txt>
      </View>
      <ScrollView
        contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: bottomChrome + spacing.xl, gap: spacing.lg }}
        refreshControl={<RefreshControl refreshing={q.isRefetching} onRefresh={() => q.refetch()} tintColor={colors.brandPrimary} />}
      >
        <Txt variant="label" style={{ marginTop: spacing.md }}>
          Saved family checks
        </Txt>
        {q.isLoading ? (
          <View style={{ height: 120 }}>
            <Loading />
          </View>
        ) : q.isError ? (
          <ErrorState testID="profile-error" message={(q.error as Error).message} onRetry={() => q.refetch()} />
        ) : q.data && q.data.length ? (
          q.data.map((a) => (
            <Pressable key={a.id} testID={`profile-assessment-${a.id}`} onPress={() => router.push(`/report/${a.id}`)} style={s.row}>
              <IconBadge name="file-text" bg={colors.brandTertiary} fg={colors.onBrandTertiary} />
              <View style={{ flex: 1, gap: 2 }}>
                <Txt numberOfLines={2} style={{ color: colors.onSurface }}>
                  {a.headline}
                </Txt>
                <Txt variant="small">
                  {niceDate(a.created_at)} · {a.protected_pct}% protected
                </Txt>
              </View>
              <Feather name="chevron-right" size={20} color={colors.muted} />
            </Pressable>
          ))
        ) : (
          <View style={s.empty} testID="profile-empty">
            <Feather name="folder" size={36} color={colors.borderStrong} />
            <Txt variant="title">No saved assessments yet</Txt>
            <Txt variant="small">Your family’s story will live here once you’ve done your first check.</Txt>
            <Button testID="profile-start-button" title="Start your family check" onPress={() => router.push("/assessment")} />
          </View>
        )}
        <Pressable testID="profile-new-check" onPress={() => router.push("/assessment")} style={s.row}>
          <IconBadge name="plus" bg={colors.successTint} fg={colors.success} />
          <Txt style={{ flex: 1, color: colors.onSurface }}>New family check</Txt>
          <Feather name="chevron-right" size={20} color={colors.muted} />
        </Pressable>
        {user?.role === "adviser" ? (
          <Pressable testID="profile-adviser-settings" onPress={() => router.push("/adviser-settings")} style={s.row}>
            <IconBadge name="briefcase" bg={colors.brandTertiary} fg={colors.onBrandTertiary} />
            <Txt style={{ flex: 1, color: colors.onSurface }}>Adviser {user.is_firm_admin ? "& firm " : ""}settings</Txt>
            <Feather name="chevron-right" size={20} color={colors.muted} />
          </Pressable>
        ) : (
          <Pressable testID="profile-link-adviser" onPress={() => router.push("/link-adviser")} style={s.row}>
            <IconBadge name="user-check" bg={colors.brandTertiary} fg={colors.onBrandTertiary} />
            <Txt style={{ flex: 1, color: colors.onSurface }}>Your adviser</Txt>
            <Feather name="chevron-right" size={20} color={colors.muted} />
          </Pressable>
        )}
        <Pressable testID="profile-change-password" onPress={() => router.push("/change-password")} style={s.row}>
          <IconBadge name="lock" bg={colors.surfaceTertiary} fg={colors.onSurfaceTertiary} />
          <Txt style={{ flex: 1, color: colors.onSurface }}>Change password</Txt>
          <Feather name="chevron-right" size={20} color={colors.muted} />
        </Pressable>
        <Pressable testID="profile-privacy" onPress={() => router.push("/privacy")} style={s.row}>
          <IconBadge name="shield" bg={colors.surfaceTertiary} fg={colors.onSurfaceTertiary} />
          <Txt style={{ flex: 1, color: colors.onSurface }}>Privacy notice</Txt>
          <Feather name="chevron-right" size={20} color={colors.muted} />
        </Pressable>
        <Button testID="profile-logout-button" title="Log out" variant="ghost" icon="log-out" onPress={async () => { await signOut(); router.replace("/onboarding"); }} />
      </ScrollView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.xl, paddingBottom: spacing.md, gap: spacing.xs, backgroundColor: c.surface },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.lg, minHeight: 64, padding: spacing.md, borderRadius: radius.lg, backgroundColor: c.surfaceSecondary },
  empty: { alignItems: "center", gap: spacing.md, padding: spacing.xl, borderRadius: radius.lg, backgroundColor: c.surfaceSecondary },
}));
