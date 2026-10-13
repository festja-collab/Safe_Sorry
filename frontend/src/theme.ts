// Design tokens for this app. Light theme only (journal / paper personality).
// Keys match the "color" block of /app/design_guidelines.json.

import { useMemo } from "react";
import { Appearance, StyleSheet, useColorScheme } from "react-native";

export type ColorScheme = "light" | "dark";

const light = {
  surface: "#FDFBF7",
  onSurface: "#2C2A28",
  surfaceSecondary: "#F4F0EA",
  onSurfaceSecondary: "#3A3835",
  surfaceTertiary: "#EAE4D9",
  onSurfaceTertiary: "#4B4844",
  surfaceInverse: "#343D35",
  onSurfaceInverse: "#FDFBF7",
  muted: "#7D7973",

  brand: "#A2A995",
  onBrand: "#22251F",
  brandPrimary: "#D18E70",
  onBrandPrimary: "#FFFFFF",
  brandSecondary: "#96A192",
  onBrandSecondary: "#FFFFFF",
  brandTertiary: "#E2D9C8",
  onBrandTertiary: "#3A3835",

  success: "#7A9374",
  onSuccess: "#FFFFFF",
  warning: "#D9A05B",
  onWarning: "#FFFFFF",
  error: "#C06C62",
  onError: "#FFFFFF",
  info: "#8B9BA6",
  onInfo: "#FFFFFF",

  border: "#E1DBCF",
  borderStrong: "#C2B9A9",
  divider: "#EFEBE3",

  // Soft tints used behind status icons
  successTint: "#E7EDE4",
  warningTint: "#F6EAD9",
  errorTint: "#F3E1DD",
  infoTint: "#E4E8EB",
  highlight: "#F7EBC9", // highlighter-pen yellow for the story card
  scrim: "rgba(52,61,53,0)",
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
