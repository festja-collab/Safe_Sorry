import { Feather } from "@react-native-vector-icons/feather";
import { Image } from "expo-image";
import * as ImagePicker from "expo-image-picker";
import { Pressable, View } from "react-native";

import { Txt } from "@/src/components/ui";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

// Firm brand colours are firm data (not app theme). All are dark enough for white text on top.
export const BRAND_COLORS = [
  { hex: "#223342", name: "Navy" },
  { hex: "#1F4D3A", name: "Forest" },
  { hex: "#1D4E5F", name: "Teal" },
  { hex: "#1F3A93", name: "Royal" },
  { hex: "#4A2C5A", name: "Plum" },
  { hex: "#6B2737", name: "Burgundy" },
  { hex: "#2E2E33", name: "Charcoal" },
];

export type PickedLogo = { uri: string; name: string; type: string };

/** Opens the system photo picker (no permission prompt is needed for picking a single image). */
export async function pickLogo(): Promise<PickedLogo | null> {
  const r = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], allowsEditing: false, quality: 0.8 });
  if (r.canceled || !r.assets?.[0]) return null;
  const a = r.assets[0];
  const type = a.mimeType && ["image/png", "image/jpeg", "image/webp"].includes(a.mimeType) ? a.mimeType : "image/jpeg";
  return { uri: a.uri, name: a.fileName ?? `logo.${type.split("/")[1]}`, type };
}

export function ColorPicker({ value, onChange }: { value: string; onChange: (hex: string) => void }) {
  const s = useStyles();
  const { colors } = useTheme();
  return (
    <View style={{ gap: spacing.sm }}>
      <Txt variant="label">Brand colour</Txt>
      <View style={s.swatches}>
        {BRAND_COLORS.map((c) => (
          <Pressable key={c.hex} testID={`brand-color-${c.name.toLowerCase()}`} accessibilityLabel={c.name} onPress={() => onChange(c.hex)} style={[s.swatch, { backgroundColor: c.hex }, value === c.hex && s.swatchOn]}>
            {value === c.hex ? <Feather name="check" size={18} color={colors.onSurfaceInverse} /> : null}
          </Pressable>
        ))}
      </View>
    </View>
  );
}

export function LogoBox({ uri, onPick, busy, testID }: { uri: string; onPick: () => void; busy?: boolean; testID: string }) {
  const s = useStyles();
  const { colors } = useTheme();
  return (
    <View style={{ gap: spacing.sm }}>
      <Txt variant="label">Firm logo (optional)</Txt>
      <Pressable testID={testID} onPress={onPick} disabled={busy} style={s.logoBox}>
        {uri ? (
          <Image source={{ uri }} style={s.logo} contentFit="contain" testID={`${testID}-preview`} />
        ) : (
          <Feather name="image" size={26} color={colors.muted} />
        )}
        <Txt variant="small" color={colors.accentText}>
          {busy ? "Uploading…" : uri ? "Change logo" : "Choose a logo (PNG or JPG, up to 2 MB)"}
        </Txt>
      </Pressable>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  swatches: { flexDirection: "row", flexWrap: "wrap", gap: spacing.md },
  swatch: { width: 44, height: 44, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
  swatchOn: { borderWidth: 3, borderColor: c.brandPrimary },
  logoBox: { minHeight: 110, borderRadius: radius.md, borderWidth: 1, borderStyle: "dashed", borderColor: c.borderStrong, backgroundColor: c.surface, alignItems: "center", justifyContent: "center", gap: spacing.sm, padding: spacing.lg },
  logo: { width: 180, height: 60 },
}));
