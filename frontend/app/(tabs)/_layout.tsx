import { Feather } from "@react-native-vector-icons/feather";
import { Redirect, Tabs } from "expo-router";
import { NativeTabs } from "expo-router/unstable-native-tabs";
import { Platform } from "react-native";

import { useAuth } from "@/src/auth";
import { usesNativeTabs } from "@/src/navigation";
import { colors, fonts } from "@/src/theme";

export default function TabsLayout() {
  const { user, loading } = useAuth();
  if (!loading && !user) return <Redirect href="/onboarding" />;
  const isAdviser = user?.role === "adviser";

  if (usesNativeTabs) {
    return (
      <NativeTabs tintColor={colors.brandPrimary}>
        <NativeTabs.Trigger name="index">
          <NativeTabs.Trigger.Icon sf="house.fill" />
          <NativeTabs.Trigger.Label>Home</NativeTabs.Trigger.Label>
        </NativeTabs.Trigger>
        <NativeTabs.Trigger name="leads" hidden={!isAdviser}>
          <NativeTabs.Trigger.Icon sf="tray.full.fill" />
          <NativeTabs.Trigger.Label>Leads</NativeTabs.Trigger.Label>
        </NativeTabs.Trigger>
        <NativeTabs.Trigger name="learn">
          <NativeTabs.Trigger.Icon sf="book.fill" />
          <NativeTabs.Trigger.Label>Learn</NativeTabs.Trigger.Label>
        </NativeTabs.Trigger>
        <NativeTabs.Trigger name="adviser" hidden={isAdviser}>
          <NativeTabs.Trigger.Icon sf="bubble.left.and.bubble.right.fill" />
          <NativeTabs.Trigger.Label>Adviser</NativeTabs.Trigger.Label>
        </NativeTabs.Trigger>
        <NativeTabs.Trigger name="profile">
          <NativeTabs.Trigger.Icon sf="person.crop.circle.fill" />
          <NativeTabs.Trigger.Label>Profile</NativeTabs.Trigger.Label>
        </NativeTabs.Trigger>
      </NativeTabs>
    );
  }

  const icon = (name: string) =>
    function TabIcon({ color }: { color: string }) {
      return <Feather name={name as any} size={22} color={color} />;
    };

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.onSurface,
        tabBarInactiveTintColor: colors.borderStrong,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          ...(Platform.OS === "web" ? { height: 64 } : {}),
        },
        tabBarItemStyle: { alignSelf: "center" },
        tabBarLabelStyle: { fontFamily: fonts.text, fontSize: 12 },
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Home", tabBarIcon: icon("home"), tabBarButtonTestID: "tab-home" } as any} />
      <Tabs.Screen name="leads" options={{ title: "Leads", tabBarIcon: icon("inbox"), tabBarButtonTestID: "tab-leads", href: isAdviser ? undefined : null } as any} />
      <Tabs.Screen name="learn" options={{ title: "Learn", tabBarIcon: icon("book-open"), tabBarButtonTestID: "tab-learn" } as any} />
      <Tabs.Screen name="adviser" options={{ title: "Adviser", tabBarIcon: icon("message-circle"), tabBarButtonTestID: "tab-adviser", href: isAdviser ? null : undefined } as any} />
      <Tabs.Screen name="profile" options={{ title: "Profile", tabBarIcon: icon("user"), tabBarButtonTestID: "tab-profile" } as any} />
    </Tabs>
  );
}
