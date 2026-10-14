import { Feather } from "@react-native-vector-icons/feather";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { ReactNode, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import Animated, { FadeInRight } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api, Assessment } from "@/src/api";
import { useAuth } from "@/src/auth";
import { Button, Field, IconBadge, Notice, Txt } from "@/src/components/ui";
import { NOT_ADVICE } from "@/src/compliance-text";
import { makeStyles, radius, spacing, useTheme } from "@/src/theme";

type Kid = { name: string; age: string };
type Form = {
  first_name: string;
  age: string;
  relationship: string;
  partner_name: string;
  partner_income: string;
  children: Kid[];
  employment: string;
  annual_income: string;
  monthly_outgoings: string;
  housing: string;
  mortgage_balance: string;
  monthly_housing: string;
  mortgage_years: string;
  other_debts: string;
  savings: string;
  life_cover: string;
  death_in_service: number;
  sick_pay_months: number;
  income_protection: string;
  critical_illness: string;
  worry: string;
};

const num = (v: string) => Number(String(v).replace(/[^0-9.]/g, "")) || 0;
const money = (v: string) => {
  const d = v.replace(/[^0-9]/g, "");
  return d ? d.replace(/\B(?=(\d{3})+(?!\d))/g, ",") : "";
};

function Choice({ label, desc, icon, selected, onPress, testID }: { label: string; desc?: string; icon: string; selected: boolean; onPress: () => void; testID: string }) {
  const s = useStyles();
  const { colors } = useTheme();
  return (
    <Pressable testID={testID} onPress={onPress} style={[s.choice, selected && s.choiceOn]}>
      <IconBadge name={icon} bg={selected ? colors.brandPrimary : colors.surfaceTertiary} fg={selected ? colors.onBrandPrimary : colors.onSurfaceTertiary} />
      <View style={{ flex: 1, gap: 2 }}>
        <Txt style={{ color: colors.onSurface }}>{label}</Txt>
        {desc ? <Txt variant="small">{desc}</Txt> : null}
      </View>
      {selected ? <Feather name="check" size={20} color={colors.brandPrimary} /> : null}
    </Pressable>
  );
}

function Chips<T extends string | number>({ options, value, onChange, testID }: { options: { label: string; value: T }[]; value: T; onChange: (v: T) => void; testID: string }) {
  const s = useStyles();
  const { colors } = useTheme();
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ height: 56, flexGrow: 0 }} contentContainerStyle={{ gap: spacing.sm, alignItems: "center" }}>
      {options.map((o) => (
        <Pressable key={String(o.value)} testID={`${testID}-${o.value}`} onPress={() => onChange(o.value)} style={[s.chip, value === o.value && s.chipOn]}>
          <Txt variant="small" color={value === o.value ? colors.onSurfaceInverse : colors.onSurface}>
            {o.label}
          </Txt>
        </Pressable>
      ))}
    </ScrollView>
  );
}

type Step = { key: string; title: string; subtitle?: string; show?: (f: Form) => boolean; valid?: (f: Form) => boolean; render: () => ReactNode };

export default function AssessmentScreen() {
  const { user } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const s = useStyles();
  const [f, setF] = useState<Form>({
    first_name: user?.name ?? "",
    age: "",
    relationship: "",
    partner_name: "",
    partner_income: "",
    children: [],
    employment: "employed",
    annual_income: "",
    monthly_outgoings: "",
    housing: "",
    mortgage_balance: "",
    monthly_housing: "",
    mortgage_years: "",
    other_debts: "",
    savings: "",
    life_cover: "",
    death_in_service: 0,
    sick_pay_months: 0,
    income_protection: "",
    critical_illness: "",
    worry: "",
  });
  const set = (patch: Partial<Form>) => setF((p) => ({ ...p, ...patch }));
  const hasPartner = f.relationship === "partner" || f.relationship === "married";
  const partner = f.partner_name.trim() || "your partner";

  const setKids = (n: number) =>
    set({ children: Array.from({ length: n }, (_, i) => f.children[i] ?? { name: "", age: "" }) });
  const setKid = (i: number, patch: Partial<Kid>) =>
    set({ children: f.children.map((k, j) => (j === i ? { ...k, ...patch } : k)) });

  const allSteps: Step[] = [
    {
      key: "you",
      title: "First, a little about you.",
      subtitle: "This is your family’s story — so let’s start with its author.",
      valid: (x) => !!x.first_name.trim() && num(x.age) >= 16 && num(x.age) <= 90,
      render: () => (
        <>
          <Field testID="q-first-name-input" label="Your first name" value={f.first_name} onChangeText={(v) => set({ first_name: v })} placeholder="Your name" />
          <Field testID="q-age-input" label="Your age" value={f.age} onChangeText={(v) => set({ age: v.replace(/[^0-9]/g, "") })} placeholder="e.g. 38" keyboardType="number-pad" maxLength={2} />
        </>
      ),
    },
    {
      key: "relationship",
      title: "Who shares your life?",
      subtitle: "It matters more than you’d think — the state treats couples very differently.",
      valid: (x) => !!x.relationship && (x.relationship === "single" || !!x.partner_name.trim()),
      render: () => (
        <>
          <Choice testID="q-rel-single" icon="user" label="Just me" selected={f.relationship === "single"} onPress={() => set({ relationship: "single" })} />
          <Choice testID="q-rel-partner" icon="users" label="Living with a partner" desc="Not married or in a civil partnership" selected={f.relationship === "partner"} onPress={() => set({ relationship: "partner" })} />
          <Choice testID="q-rel-married" icon="heart" label="Married or civil partnership" selected={f.relationship === "married"} onPress={() => set({ relationship: "married" })} />
          {hasPartner ? (
            <Field testID="q-partner-name-input" label="Their first name" value={f.partner_name} onChangeText={(v) => set({ partner_name: v })} placeholder="e.g. Sarah" autoCapitalize="words" />
          ) : null}
        </>
      ),
    },
    {
      key: "children",
      title: "Are there little (or not so little) ones?",
      subtitle: "Their names help us show what your plan means for them.",
      valid: (x) => x.children.every((k) => k.name.trim() && k.age !== ""),
      render: () => (
        <>
          <Chips
            testID="q-kids"
            value={f.children.length}
            onChange={setKids}
            options={[0, 1, 2, 3, 4, 5].map((n) => ({ label: n === 0 ? "No children" : String(n), value: n }))}
          />
          {f.children.map((k, i) => (
            <View key={i} style={s.kidRow}>
              <View style={{ flex: 2 }}>
                <Field testID={`q-child-${i}-name`} label={`Child ${i + 1}`} value={k.name} onChangeText={(v) => setKid(i, { name: v })} placeholder="Name" autoCapitalize="words" />
              </View>
              <View style={{ flex: 1 }}>
                <Field testID={`q-child-${i}-age`} label="Age" value={k.age} onChangeText={(v) => setKid(i, { age: v.replace(/[^0-9]/g, "") })} placeholder="0" keyboardType="number-pad" maxLength={2} />
              </View>
            </View>
          ))}
        </>
      ),
    },
    {
      key: "work",
      title: "How do you earn your living?",
      valid: (x) => num(x.annual_income) > 0,
      render: () => (
        <>
          <Choice testID="q-emp-employed" icon="briefcase" label="Employed" selected={f.employment === "employed"} onPress={() => set({ employment: "employed" })} />
          <Choice testID="q-emp-self" icon="tool" label="Self-employed" desc="No employer sick pay or death-in-service" selected={f.employment === "self_employed"} onPress={() => set({ employment: "self_employed", death_in_service: 0, sick_pay_months: 0 })} />
          <Field testID="q-income-input" label="Your yearly income before tax" prefix="£" value={f.annual_income} onChangeText={(v) => set({ annual_income: money(v) })} placeholder="45,000" keyboardType="number-pad" />
        </>
      ),
    },
    {
      key: "partner_income",
      title: `And what does ${partner} earn?`,
      subtitle: "Their income is what your family would be living on.",
      show: () => hasPartner,
      render: () => (
        <Field testID="q-partner-income-input" label="Yearly income before tax" prefix="£" value={f.partner_income} onChangeText={(v) => set({ partner_income: money(v) })} placeholder="0 if not working" keyboardType="number-pad" />
      ),
    },
    {
      key: "outgoings",
      title: "What does it cost to run your home each month?",
      subtitle: "Food, bills, childcare, cars, clubs, the little treats. Leave out the mortgage or rent — we’ll ask next.",
      valid: (x) => num(x.monthly_outgoings) > 0,
      render: () => (
        <Field testID="q-outgoings-input" label="Monthly household spending" prefix="£" value={f.monthly_outgoings} onChangeText={(v) => set({ monthly_outgoings: money(v) })} placeholder="2,000" keyboardType="number-pad" />
      ),
    },
    {
      key: "home",
      title: "Tell us about home.",
      valid: (x) => !!x.housing,
      render: () => (
        <>
          <Choice testID="q-home-mortgage" icon="home" label="We have a mortgage" selected={f.housing === "mortgage"} onPress={() => set({ housing: "mortgage" })} />
          <Choice testID="q-home-rent" icon="key" label="We rent" selected={f.housing === "rent"} onPress={() => set({ housing: "rent" })} />
          <Choice testID="q-home-own" icon="sun" label="We own it outright" selected={f.housing === "own"} onPress={() => set({ housing: "own" })} />
        </>
      ),
    },
    {
      key: "home_details",
      title: f.housing === "rent" ? "What’s the rent?" : "The mortgage, in a nutshell.",
      show: (x) => x.housing === "mortgage" || x.housing === "rent",
      valid: (x) => num(x.monthly_housing) > 0,
      render: () =>
        f.housing === "rent" ? (
          <Field testID="q-rent-input" label="Monthly rent" prefix="£" value={f.monthly_housing} onChangeText={(v) => set({ monthly_housing: money(v) })} placeholder="1,200" keyboardType="number-pad" />
        ) : (
          <>
            <Field testID="q-mortgage-balance-input" label="Amount left to pay" prefix="£" value={f.mortgage_balance} onChangeText={(v) => set({ mortgage_balance: money(v) })} placeholder="220,000" keyboardType="number-pad" />
            <Field testID="q-mortgage-monthly-input" label="Monthly payment" prefix="£" value={f.monthly_housing} onChangeText={(v) => set({ monthly_housing: money(v) })} placeholder="1,100" keyboardType="number-pad" />
            <Field testID="q-mortgage-years-input" label="Years remaining" value={f.mortgage_years} onChangeText={(v) => set({ mortgage_years: v.replace(/[^0-9]/g, "") })} placeholder="25" keyboardType="number-pad" maxLength={2} />
          </>
        ),
    },
    {
      key: "money",
      title: "What’s in the safety net?",
      subtitle: "Savings you could actually reach, and any loans or cards still owed.",
      render: () => (
        <>
          <Field testID="q-savings-input" label="Savings" prefix="£" value={f.savings} onChangeText={(v) => set({ savings: money(v) })} placeholder="0" keyboardType="number-pad" />
          <Field testID="q-debts-input" label="Other debts (loans, cards, car finance)" prefix="£" value={f.other_debts} onChangeText={(v) => set({ other_debts: money(v) })} placeholder="0" keyboardType="number-pad" />
        </>
      ),
    },
    {
      key: "cover_life",
      title: "Any cover already in place?",
      subtitle: "Don’t worry if you’re unsure — a best guess is fine. Zero is a perfectly honest answer.",
      render: () => (
        <>
          <Field testID="q-life-cover-input" label="Personal life insurance payout" prefix="£" value={f.life_cover} onChangeText={(v) => set({ life_cover: money(v) })} placeholder="0" keyboardType="number-pad" />
          {f.employment === "employed" ? (
            <View style={{ gap: spacing.sm }}>
              <Txt variant="label">Death-in-service from work</Txt>
              <Chips
                testID="q-dis"
                value={f.death_in_service}
                onChange={(v) => set({ death_in_service: v })}
                options={[0, 1, 2, 3, 4].map((n) => ({ label: n === 0 ? "None / not sure" : `${n}× salary`, value: n }))}
              />
            </View>
          ) : null}
        </>
      ),
    },
    {
      key: "cover_ill",
      title: "If illness kept you from work…",
      subtitle: "This is the risk most of us forget — and the most likely one to happen.",
      render: () => (
        <>
          {f.employment === "employed" ? (
            <View style={{ gap: spacing.sm }}>
              <Txt variant="label">Full sick pay from your employer</Txt>
              <Chips
                testID="q-sick"
                value={f.sick_pay_months}
                onChange={(v) => set({ sick_pay_months: v })}
                options={[0, 1, 3, 6, 12].map((n) => ({ label: n === 0 ? "Statutory only" : `${n} month${n > 1 ? "s" : ""}`, value: n }))}
              />
            </View>
          ) : null}
          <Field testID="q-ip-input" label="Income protection (monthly benefit)" prefix="£" value={f.income_protection} onChangeText={(v) => set({ income_protection: money(v) })} placeholder="0" keyboardType="number-pad" />
          <Field testID="q-ci-input" label="Critical illness cover (lump sum)" prefix="£" value={f.critical_illness} onChangeText={(v) => set({ critical_illness: money(v) })} placeholder="0" keyboardType="number-pad" />
        </>
      ),
    },
    {
      key: "worry",
      title: "Last one. What keeps you up at night?",
      subtitle: "We’ll keep this front of mind as we write your story.",
      valid: (x) => !!x.worry,
      render: () => (
        <>
          <Choice testID="q-worry-home" icon="home" label="Losing our home" selected={f.worry === "Losing our home"} onPress={() => set({ worry: "Losing our home" })} />
          <Choice testID="q-worry-kids" icon="star" label="The children’s future" selected={f.worry === "The children's future"} onPress={() => set({ worry: "The children's future" })} />
          <Choice testID="q-worry-partner" icon="heart" label={hasPartner ? `${partner} coping alone` : "Being a burden on family"} selected={f.worry === "Partner coping alone" || f.worry === "Being a burden on family"} onPress={() => set({ worry: hasPartner ? "Partner coping alone" : "Being a burden on family" })} />
          <Choice testID="q-worry-life" icon="coffee" label="Our everyday way of life" selected={f.worry === "Our everyday way of life"} onPress={() => set({ worry: "Our everyday way of life" })} />
        </>
      ),
    },
  ];

  const steps = allSteps.filter((st) => !st.show || st.show(f));
  const [idx, setIdx] = useState(0);
  const step = steps[Math.min(idx, steps.length - 1)];
  const isLast = idx >= steps.length - 1;
  const canContinue = !step.valid || step.valid(f);

  const submit = useMutation({
    mutationFn: () =>
      api<Assessment>("/assessments", {
        method: "POST",
        body: {
          first_name: f.first_name.trim(),
          age: num(f.age),
          relationship: f.relationship,
          partner_name: f.partner_name.trim(),
          partner_income: hasPartner ? num(f.partner_income) : 0,
          children: f.children.map((k) => ({ name: k.name.trim(), age: num(k.age) })),
          employment: f.employment,
          annual_income: num(f.annual_income),
          monthly_outgoings: num(f.monthly_outgoings),
          housing: f.housing,
          mortgage_balance: f.housing === "mortgage" ? num(f.mortgage_balance) : 0,
          monthly_housing: f.housing === "own" ? 0 : num(f.monthly_housing),
          mortgage_years: f.housing === "mortgage" ? num(f.mortgage_years) : 0,
          other_debts: num(f.other_debts),
          savings: num(f.savings),
          life_cover: num(f.life_cover),
          death_in_service: f.death_in_service,
          sick_pay_months: f.sick_pay_months,
          income_protection: num(f.income_protection),
          critical_illness: num(f.critical_illness),
          worry: f.worry,
        },
      }),
    onSuccess: (a) => {
      qc.invalidateQueries({ queryKey: ["assessments"] });
      router.replace(`/report/${a.id}`);
    },
  });

  const next = () => (isLast ? submit.mutate() : setIdx(idx + 1));
  const close = () => (router.canGoBack() ? router.back() : router.replace("/(tabs)"));

  return (
    <View style={s.root} testID="assessment-screen">
      <View style={[s.header, { paddingTop: insets.top + spacing.sm }]}>
        <View style={s.headerRow}>
          <Pressable testID="assessment-back-button" onPress={() => (idx === 0 ? close() : setIdx(idx - 1))} style={s.iconBtn}>
            <Feather name={idx === 0 ? "x" : "arrow-left"} size={22} color={colors.onSurface} />
          </Pressable>
          <Txt variant="small" testID="assessment-progress-label">
            {idx + 1} of {steps.length}
          </Txt>
          <View style={s.iconBtn} />
        </View>
        <View style={s.track}>
          <View style={[s.fill, { width: `${((idx + 1) / steps.length) * 100}%` }]} />
        </View>
      </View>
      <KeyboardAwareScrollView bottomOffset={120} keyboardShouldPersistTaps="handled" contentContainerStyle={s.content}>
        <Animated.View key={step.key} entering={FadeInRight.duration(350)} style={{ gap: spacing.lg }}>
          <Txt variant="display" testID="assessment-question-title">
            {step.title}
          </Txt>
          {step.subtitle ? <Txt>{step.subtitle}</Txt> : null}
          {idx === 0 ? <Notice testID="assessment-not-advice" text={NOT_ADVICE} icon="alert-circle" /> : null}
          <View style={{ gap: spacing.md, marginTop: spacing.sm }}>{step.render()}</View>
          {submit.isError ? (
            <Txt testID="assessment-error" color={colors.error}>
              {(submit.error as Error).message}
            </Txt>
          ) : null}
        </Animated.View>
      </KeyboardAwareScrollView>
      <KeyboardStickyView offset={{ opened: insets.bottom - spacing.md }}>
        <View style={[s.footer, { paddingBottom: insets.bottom + spacing.lg }]}>
          <Button
            testID="assessment-continue-button"
            title={isLast ? "Show me my family’s story" : "Continue"}
            icon="arrow-right"
            disabled={!canContinue}
            loading={submit.isPending}
            onPress={next}
          />
        </View>
      </KeyboardStickyView>
    </View>
  );
}

const useStyles = makeStyles((c) => ({
  root: { flex: 1, backgroundColor: c.surface },
  header: { paddingHorizontal: spacing.lg, paddingBottom: spacing.md, backgroundColor: c.surface, gap: spacing.sm },
  headerRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  iconBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  track: { height: 6, marginHorizontal: spacing.sm, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, overflow: "hidden" },
  fill: { height: 6, borderRadius: radius.pill, backgroundColor: c.brandSecondary },
  content: { paddingHorizontal: spacing.xl, paddingTop: spacing.lg, paddingBottom: spacing.xl },
  footer: { paddingHorizontal: spacing.xl, paddingTop: spacing.md, backgroundColor: c.surface },
  choice: { flexDirection: "row", alignItems: "center", gap: spacing.lg, minHeight: 72, padding: spacing.lg, borderRadius: radius.lg, backgroundColor: c.surfaceSecondary, borderWidth: 1.5, borderColor: c.surfaceSecondary },
  choiceOn: { borderColor: c.brandPrimary, backgroundColor: c.surface },
  chip: { height: 36, flexShrink: 0, paddingHorizontal: spacing.lg, borderRadius: radius.pill, backgroundColor: c.surfaceTertiary, justifyContent: "center" },
  chipOn: { backgroundColor: c.surfaceInverse },
  kidRow: { flexDirection: "row", gap: spacing.md },
}));
