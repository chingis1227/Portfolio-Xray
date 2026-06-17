"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useReviewState } from "@/lib/reviewState";
import type { ClientFitInput } from "@/lib/generated/api-types";

type PresetId = NonNullable<ClientFitInput["preset_id"]>;
type Source = ClientFitInput["source"];

type Preset = {
  id: PresetId;
  label: string;
  returnRange: { min: number; max: number };
  volRange: { min: number; max: number };
  drawdown: number;
  horizon: number;
  note: string;
};

const PRESETS: Preset[] = [
  { id: "ultra_conservative", label: "Ultra Conservative", returnRange: { min: 0.02, max: 0.04 }, volRange: { min: 0.02, max: 0.05 }, drawdown: -0.10, horizon: 2, note: "Capital preservation is the first priority." },
  { id: "conservative", label: "Conservative", returnRange: { min: 0.03, max: 0.06 }, volRange: { min: 0.04, max: 0.07 }, drawdown: -0.15, horizon: 4, note: "Moderate growth with stability as the priority." },
  { id: "balanced", label: "Balanced", returnRange: { min: 0.05, max: 0.07 }, volRange: { min: 0.07, max: 0.10 }, drawdown: -0.20, horizon: 7, note: "Growth with drawdown control." },
  { id: "growth", label: "Growth", returnRange: { min: 0.07, max: 0.10 }, volRange: { min: 0.10, max: 0.14 }, drawdown: -0.275, horizon: 10, note: "Return-oriented profile with meaningful drawdown tolerance." },
  { id: "aggressive", label: "Aggressive", returnRange: { min: 0.10, max: 0.20 }, volRange: { min: 0.14, max: 0.20 }, drawdown: -0.35, horizon: 12, note: "Maximum growth profile with equity-like drawdowns accepted." }
];

const presetById = new Map(PRESETS.map((preset) => [preset.id, preset]));

function pct(value: number) {
  return (value * 100).toFixed(1).replace(/\.0$/, "");
}

function decimalFromPct(value: string) {
  const parsed = Number(value.replace(",", "."));
  return Number.isFinite(parsed) ? parsed / 100 : Number.NaN;
}

function pctInput(value: number) {
  return pct(Math.abs(value));
}

function suggestedPreset(objective: string, horizon: string): PresetId {
  if (objective === "preserve") return "conservative";
  if (objective === "maximum_growth") return "aggressive";
  if (objective === "high_growth") return horizon === "short" ? "balanced" : "growth";
  if (horizon === "short") return "conservative";
  if (horizon === "long") return "growth";
  return "balanced";
}

function sourceLabel(source: Source) {
  if (source === "manual_override") return "Manual targets";
  if (source === "preset_override") return "Preset override";
  return "Questionnaire confirmed";
}

export function ClientProfileScreen() {
  const router = useRouter();
  const { activeReview, saveClientFitProfile } = useReviewState();
  const saved = activeReview?.clientFitProfile;
  const savedPreset = saved?.preset_id && presetById.has(saved.preset_id) ? saved.preset_id : "balanced";
  const [objective, setObjective] = useState("balanced");
  const [horizonChoice, setHorizonChoice] = useState("medium");
  const [presetId, setPresetId] = useState<PresetId>(savedPreset as PresetId);
  const [source, setSource] = useState<Source>(saved?.source ?? "questionnaire");
  const preset = presetById.get(presetId) ?? PRESETS[2];
  const [returnMin, setReturnMin] = useState(pctInput(saved?.target_return_range?.min ?? preset.returnRange.min));
  const [returnMax, setReturnMax] = useState(pctInput(saved?.target_return_range?.max ?? preset.returnRange.max));
  const [volMin, setVolMin] = useState(pctInput(saved?.target_vol_range?.min ?? preset.volRange.min));
  const [volMax, setVolMax] = useState(pctInput(saved?.target_vol_range?.max ?? preset.volRange.max));
  const [drawdown, setDrawdown] = useState(pctInput(saved?.target_max_drawdown_pct ?? preset.drawdown));
  const [horizonYears, setHorizonYears] = useState(String(saved?.horizon_years ?? preset.horizon));

  const suggested = suggestedPreset(objective, horizonChoice);
  const values = useMemo(() => {
    const parsed = {
      returnMin: decimalFromPct(returnMin),
      returnMax: decimalFromPct(returnMax),
      volMin: decimalFromPct(volMin),
      volMax: decimalFromPct(volMax),
      drawdown: -Math.abs(decimalFromPct(drawdown)),
      horizonYears: Number(horizonYears.replace(",", "."))
    };
    const valid = parsed.returnMin >= 0
      && parsed.returnMax <= 1
      && parsed.returnMin < parsed.returnMax
      && parsed.volMin >= 0
      && parsed.volMax <= 1
      && parsed.volMin < parsed.volMax
      && parsed.drawdown <= 0
      && parsed.drawdown >= -1
      && parsed.horizonYears > 0;
    return { ...parsed, valid };
  }, [drawdown, horizonYears, returnMax, returnMin, volMax, volMin]);

  const applyPreset = (nextPresetId: PresetId, nextSource: Source = source) => {
    const next = presetById.get(nextPresetId) ?? PRESETS[2];
    setPresetId(next.id);
    setSource(nextSource);
    setReturnMin(pctInput(next.returnRange.min));
    setReturnMax(pctInput(next.returnRange.max));
    setVolMin(pctInput(next.volRange.min));
    setVolMax(pctInput(next.volRange.max));
    setDrawdown(pctInput(next.drawdown));
    setHorizonYears(String(next.horizon));
  };

  const saveProfile = () => {
    if (!values.valid) return;
    saveClientFitProfile({
      preset_id: presetId,
      source,
      source_quality: source === "manual_override" ? "high" : "medium",
      source_quality_reason: `${sourceLabel(source)} captured in the web Client Profile step.`,
      horizon_years: values.horizonYears,
      target_return_range: { min: values.returnMin, max: values.returnMax },
      target_vol_range: { min: values.volMin, max: values.volMax },
      target_max_drawdown_pct: values.drawdown
    });
    router.push("/portfolio-input");
  };

  return (
    <div>
      <PageHeader
        kicker="Advanced / Client Fit profile editor"
        title="Manual diagnostic context"
        description="Edit the stated planning profile used as non-binding context. The main product path now collects this through onboarding before Portfolio Input."
      >
        <StatusBadge tone={values.valid ? "green" : "amber"}>{values.valid ? "Profile ready" : "Profile incomplete"}</StatusBadge>
      </PageHeader>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <section className="pmri-card rounded-3xl p-5 md:p-6">
          <p className="pmri-label">Mandatory web questionnaire</p>
          <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">Planning answers</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <label>
              <span className="pmri-label block">Main objective</span>
              <select className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm font-medium text-pmri-text" value={objective} onChange={(event) => setObjective(event.target.value)}>
                <option value="preserve">Preserve capital</option>
                <option value="balanced">Balanced growth and risk</option>
                <option value="high_growth">High growth</option>
                <option value="maximum_growth">Maximum growth</option>
              </select>
            </label>
            <label>
              <span className="pmri-label block">Investment horizon</span>
              <select className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm font-medium text-pmri-text" value={horizonChoice} onChange={(event) => setHorizonChoice(event.target.value)}>
                <option value="short">Less than 5 years</option>
                <option value="medium">6-10 years</option>
                <option value="long">More than 10 years</option>
              </select>
            </label>
          </div>
          <div className="mt-5 rounded-2xl border border-pmri-border/55 bg-white/[0.025] p-4">
            <p className="pmri-label text-pmri-blueSoft">Suggested preset</p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">
              Questionnaire suggests <span className="font-semibold text-pmri-text">{presetById.get(suggested)?.label}</span>. You can accept it, choose another preset, or customize the target rows below.
            </p>
            <button type="button" onClick={() => applyPreset(suggested, "questionnaire")} className="pmri-focus mt-4 rounded-full border border-pmri-blue/35 bg-pmri-blue/[0.08] px-4 py-2 text-sm font-medium text-pmri-text transition hover:bg-pmri-blue/[0.12]">
              Use suggested profile
            </button>
          </div>
        </section>

        <aside className="pmri-card rounded-3xl p-5 md:p-6">
          <p className="pmri-label">Profile summary</p>
          <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">{preset.label}</h2>
          <p className="mt-2 text-sm leading-6 text-pmri-muted">{preset.note}</p>
          <div className="mt-5 space-y-3 text-sm text-pmri-text2">
            <p>Target return: {returnMin}-{returnMax}%</p>
            <p>Volatility comfort range: {volMin}-{volMax}%</p>
            <p>Maximum temporary loss: -{drawdown}%</p>
            <p>Horizon: {horizonYears} years</p>
            <p>Profile confidence: {source === "manual_override" ? "High" : "Medium"}</p>
          </div>
        </aside>
      </div>

      <section className="pmri-card mt-6 rounded-3xl p-5 md:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="pmri-label">Editable Client Fit limits</p>
            <h2 className="pmri-heading-section mt-2 text-xl text-pmri-text">Targets used as diagnostic context</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-muted">These fields become Client Fit display and test criteria. They are not hidden optimizer constraints.</p>
          </div>
          <label className="min-w-[240px]">
            <span className="pmri-label block">Profile preset</span>
            <select className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm font-medium text-pmri-text" value={presetId} onChange={(event) => applyPreset(event.target.value as PresetId, "preset_override")}>
              {PRESETS.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
            </select>
          </label>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-4">
          <label><span className="pmri-label block">Return min %</span><input className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm text-pmri-text" value={returnMin} onChange={(event) => { setSource("manual_override"); setReturnMin(event.target.value); }} /></label>
          <label><span className="pmri-label block">Return max %</span><input className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm text-pmri-text" value={returnMax} onChange={(event) => { setSource("manual_override"); setReturnMax(event.target.value); }} /></label>
          <label><span className="pmri-label block">Volatility min %</span><input className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm text-pmri-text" value={volMin} onChange={(event) => { setSource("manual_override"); setVolMin(event.target.value); }} /></label>
          <label><span className="pmri-label block">Volatility max %</span><input className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm text-pmri-text" value={volMax} onChange={(event) => { setSource("manual_override"); setVolMax(event.target.value); }} /></label>
          <label><span className="pmri-label block">Max temporary loss %</span><input className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm text-pmri-text" value={drawdown} onChange={(event) => { setSource("manual_override"); setDrawdown(event.target.value); }} /></label>
          <label><span className="pmri-label block">Horizon years</span><input className="pmri-focus mt-2 w-full rounded-xl border border-pmri-border/55 bg-pmri-secondary/80 px-3 py-2.5 text-sm text-pmri-text" value={horizonYears} onChange={(event) => { setSource("manual_override"); setHorizonYears(event.target.value); }} /></label>
          <div className="md:col-span-2 rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
            <StatusBadge tone={values.valid ? "green" : "amber"}>{sourceLabel(source)}</StatusBadge>
            <p className="mt-3 text-sm leading-6 text-pmri-muted">Source quality is shown on the Client Fit screen so the user can distinguish stated profile confidence from portfolio diagnosis quality.</p>
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
          <button type="button" disabled={!values.valid} onClick={saveProfile} className="pmri-focus pmri-primary-action rounded-full px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/10 disabled:text-pmri-muted">
            Save profile and continue to Portfolio Input
          </button>
          {!values.valid ? <p className="text-sm leading-6 text-pmri-amber">Check that ranges increase and percentages stay within realistic bounds.</p> : null}
        </div>
      </section>
    </div>
  );
}
