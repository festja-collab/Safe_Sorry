// Design tokens for this app. Light theme only (journal / paper personality).
// Keys match the "color" block of /app/design_guidelines.json.

import { useMemo } from "react";
import { Appearance, StyleSheet, useColorScheme } from "react-native";

export type ColorScheme = "light" | "dark";

const light = {
  // SFL-inspired palette: white, navy (#223342) and gold (#BF9B30)
  surface: "#FFFFFF",
  onSurface: "#1E2B38",
  surfaceSecondary: "#F5F6F8",
  onSurfaceSecondary: "#38434F",
  surfaceTertiary: "#E9ECF0",
  onSurfaceTertiary: "#4A5562",
  surfaceInverse: "#223342",
  onSurfaceInverse: "#FFFFFF",
  muted: "#6C7683",

  brand: "#223342",
  onBrand: "#FFFFFF",
  brandPrimary: "#BF9B30",
  onBrandPrimary: "#1A2633",
  brandSecondary: "#223342",
  onBrandSecondary: "#FFFFFF",
  brandTertiary: "#F4EEDC",
  onBrandTertiary: "#6E5714",

  success: "#3E8E63",
  onSuccess: "#FFFFFF",
  warning: "#B98318",
  onWarning: "#FFFFFF",
  error: "#BF4A41",
  onError: "#FFFFFF",
  info: "#1890D7",
  onInfo: "#FFFFFF",

  border: "#E3E2E7",
  borderStrong: "#C3C9D2",
  divider: "#EEEFF2",

  // Soft tints used behind status icons
  successTint: "#E6F2EC",
  warningTint: "#F8EFDA",
  errorTint: "#F8E5E3",
  infoTint: "#E3F0FA",
  highlight: "#F6EED6", // soft gold highlight for the story card
  scrim: "rgba(34,51,66,0)",
  inverseTrack: "rgba(255,255,255,0.15)",
  accentText: "#8F7019", // readable gold for small text on white
};

export type ThemeColors = typeof light;

export const defaultScheme = "light" satisfies ColorScheme;

export const themes: { light: ThemeColors; dark?: ThemeColors } = { light };

export function setColorScheme(scheme: ColorScheme | null) {
  Appearance.setColorScheme?.(scheme ?? "unspecified");
}

setColorScheme?.(themes.dark ? null : defaultScheme);

export function useTheme(): { scheme: ColorScheme; colors: ThemeColors } {
  const system = useColorScheme();
  const scheme: ColorScheme = system && themes[system] ? system : defaultScheme;
  return { scheme, colors: themes[scheme] ?? themes.light };
}

export const colors = light;

export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, "2xl": 32, "3xl": 48 };
export const radius = { sm: 6, md: 12, lg: 20, pill: 999 };
export const fonts = { display: "Fraunces", text: "Quicksand" };

export function makeStyles<T extends StyleSheet.NamedStyles<T> | StyleSheet.NamedStyles<any>>(
  factory: (colors: ThemeColors) => T & StyleSheet.NamedStyles<any>,
): () => T {
  return function useStyles(): T {
    const { colors } = useTheme();
    return useMemo(() => StyleSheet.create(factory(colors)), [colors]);
  };
}
