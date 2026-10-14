import { Feather } from "@react-native-vector-icons/feather";
import { ReactNode } from "react";
import { ActivityIndicator, Pressable, StyleProp, Text, TextInput, TextInputProps, TextStyle, View, ViewStyle } from "react-native";
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from "react-native-reanimated";

import { fonts, makeStyles, radius, spacing, useTheme } from "@/src/theme";

type TxtProps = {
  children: ReactNode;
  variant?: "hero" | "display" | "title" | "body" | "small" | "label";
  color?: string;
  style?: StyleProp<TextStyle>;
  testID?: string;
  numberOfLines?: number;
};

export function Txt({ children, variant = "body", color, style, testID, numberOfLines }: TxtProps) {
  const s = useStyles();
  return (
    <Text testID={testID} numberOfLines={numberOfLines} style={[s[variant], color ? { color } : null, style]}>
      {children}
    </Text>
  );
}

type BtnProps = {
  title: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "ghost" | "light";
  icon?: string;
  loading?: boolean;
  disabled?: boolean;
  testID: string;
  style?: StyleProp<ViewStyle>;
};

export function Notice({ text, testID, icon = "info" }: { text: string; testID: string; icon?: string }) {
  const { colors } = useTheme();
  return (
    <View testID={testID} style={{ flexDirection: "row", gap: spacing.md, padding: spacing.lg, borderRadius: radius.md, backgroundColor: colors.infoTint, borderLeftWidth: 4, borderLeftColor: colors.info }}>
      <Feather name={icon as any} size={18} color={colors.info} style={{ marginTop: 2 }} />
      <Txt variant="small" style={{ flex: 1, color: colors.onSurface }}>
        {text}
      </Txt>
    </View>
  );
}

export function Button({ title, onPress, variant = "primary", icon, loading, disabled, testID, style }: BtnProps) {
  const s = useStyles();
  const { colors } = useTheme();
  const scale = useSharedValue(1);
  const anim = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));
  const fg =
    variant === "primary" ? colors.onBrandPrimary : variant === "light" ? colors.onSurfaceInverse : colors.onSurface;
  const bg =
    variant === "primary" ? s.btnPrimary : variant === "secondary" ? s.btnSecondary : variant === "light" ? s.btnLight : s.btnGhost;
  return (
    <Animated.View style={[anim, style]}>
      <Pressable
        testID={testID}
        disabled={disabled || loading}
        onPressIn={() => (scale.value = withSpring(0.97))}
        onPressOut={() => (scale.value = withSpring(1))}
        onPress={onPress}
        style={[s.btn, bg, (disabled || loading) && { opacity: 0.5 }]}
      >
        {loading ? (
          <ActivityIndicator color={fg} />
        ) : (
          <>
            <Text style={[s.btnText, { color: fg }]}>{title}</Text>
            {icon ? <Feather name={icon as any} size={18} color={fg} /> : null}
          </>
        )}
      </Pressable>
    </Animated.View>
  );
}

export function Field({ label, prefix, ...props }: TextInputProps & { label?: string; prefix?: string }) {
  const s = useStyles();
  const { colors } = useTheme();
  return (
    <View style={{ gap: spacing.sm }}>
      {label ? <Txt variant="label">{label}</Txt> : null}
      <View style={s.inputWrap}>
        {prefix ? <Text style={s.prefix}>{prefix}</Text> : null}
        <TextInput placeholderTextColor={colors.muted} style={s.input} {...props} />
      </View>
    </View>
  );
}

export function Checkbox({ checked, onToggle, testID, children }: { checked: boolean; onToggle: () => void; testID: string; children: ReactNode }) {
  const { colors } = useTheme();
  return (
    <Pressable testID={testID} onPress={onToggle} style={{ flexDirection: "row", gap: spacing.md, alignItems: "flex-start", paddingVertical: spacing.xs }}>
      <View
        style={{
          width: 24,
          height: 24,
          borderRadius: radius.sm,
          borderWidth: 2,
          borderColor: checked ? colors.brandSecondary : colors.borderStrong,
          backgroundColor: checked ? colors.brandSecondary : "transparent",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {checked ? <Feather name="check" size={16} color={colors.onBrandSecondary} /> : null}
      </View>
      <View style={{ flex: 1 }}>{children}</View>
    </Pressable>
  );
}

export function Loading({ label, testID }: { label?: string; testID?: string }) {
  const { colors } = useTheme();
  return (
    <View testID={testID} style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.md, padding: spacing.xl }}>
      <ActivityIndicator color={colors.brandPrimary} />
      {label ? <Txt color={colors.muted}>{label}</Txt> : null}
    </View>
  );
}

export function ErrorState({ message, onRetry, testID }: { message: string; onRetry: () => void; testID: string }) {
  const s = useStyles();
  return (
    <View testID={testID} style={s.errorBox}>
      <Txt variant="title">Something got in the way</Txt>
      <Txt>{message}</Txt>
      <Button testID={`${testID}-retry`} title="Try again" variant="secondary" icon="refresh-cw" onPress={onRetry} />
    </View>
  );
}

export function IconBadge({ name, bg, fg, size = 40 }: { name: string; bg: string; fg: string; size?: number }) {
  return (
    <View style={{ width: size, height: size, borderRadius: radius.md, backgroundColor: bg, alignItems: "center", justifyContent: "center" }}>
      <Feather name={name as any} size={size * 0.45} color={fg} />
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  hero: { fontFamily: fonts.display, fontSize: 34, lineHeight: 40, color: c.onSurface, letterSpacing: -0.5 },
  display: { fontFamily: fonts.display, fontSize: 28, lineHeight: 34, color: c.onSurface, letterSpacing: -0.3 },
  title: { fontFamily: fonts.display, fontSize: 20, lineHeight: 26, color: c.onSurface },
  body: { fontFamily: fonts.text, fontSize: 16, lineHeight: 24, color: c.onSurfaceSecondary },
  small: { fontFamily: fonts.text, fontSize: 14, lineHeight: 20, color: c.muted },
  label: { fontFamily: fonts.text, fontSize: 12, lineHeight: 16, color: c.muted, letterSpacing: 1.2, textTransform: "uppercase" },
  btn: {
    minHeight: 54,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.xl,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.sm,
  },
  btnPrimary: { backgroundColor: c.brandPrimary },
  btnSecondary: { backgroundColor: c.brandTertiary },
  btnLight: { backgroundColor: "transparent", borderWidth: 1, borderColor: c.onSurfaceInverse },
  btnGhost: { backgroundColor: "transparent" },
  btnText: { fontFamily: fonts.text, fontSize: 16, fontWeight: "500" },
  inputWrap: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: c.surfaceTertiary,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    minHeight: 54,
  },
  prefix: { fontFamily: fonts.display, fontSize: 20, color: c.muted, marginRight: spacing.sm },
  input: { flex: 1, fontFamily: fonts.text, fontSize: 18, color: c.onSurface, paddingVertical: spacing.md },
  errorBox: { margin: spacing.xl, padding: spacing.xl, gap: spacing.md, borderRadius: radius.lg, backgroundColor: c.surfaceSecondary },
}));
