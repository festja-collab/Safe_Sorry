import { Redirect } from "expo-router";

import { useAuth } from "@/src/auth";
import { Loading } from "@/src/components/ui";

export default function Index() {
  const { user, loading } = useAuth();
  if (loading) return <Loading testID="app-loading" />;
  return <Redirect href={user ? "/(tabs)" : "/onboarding"} />;
}
