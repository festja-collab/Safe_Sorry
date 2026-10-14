import { File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";
import { Platform } from "react-native";

import { TOKEN_KEY } from "@/src/api";
import { storage } from "@/src/utils/storage";

/** Downloads the CRM CSV: browser download on web, share sheet (Save to Files, email…) on phones. */
export async function downloadLeadsCsv(status?: string) {
  const token = await storage.secureGet<string | null>(TOKEN_KEY, null);
  const qs = status && status !== "all" ? `?status=${status}` : "";
  const res = await fetch(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/adviser/leads/export${qs}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("We couldn't create the file. Please try again.");
  const name = `safe-sorry-leads-${new Date().toISOString().slice(0, 10)}.csv`;
  // res.text() strips the UTF-8 BOM; add it back so Excel shows £ and accented names correctly
  const text = "\ufeff" + (await res.text()).replace(/^\ufeff/, "");
  if (Platform.OS === "web") {
    const url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
    return;
  }
  const file = new File(Paths.cache, name);
  if (file.exists) file.delete();
  file.create();
  file.write(text);
  await Sharing.shareAsync(file.uri, { mimeType: "text/csv", UTI: "public.comma-separated-values-text", dialogTitle: "Save leads for your CRM" });
}
