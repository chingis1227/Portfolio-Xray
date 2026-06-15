import type { SiteExplanationBundle, StatusTone } from "@/lib/types";
import { buildPublicSiteExplanationDisplayModel } from "@/lib/siteExplanationPresenter";
import { formatStressPercent } from "./stressLabModel";
import type { StressLabModel, StressScenarioDetail } from "./stressLabTypes";

export type StressStoryState =
  | "material_vulnerability"
  | "meaningful_stress"
  | "evidence_limited"
  | "stress_acceptable";

export type StressStoryFact = {
  label: string;
  value: string;
  detail: string;
  tone: StatusTone;
};

export type StressStoryMetric = {
  label: string;
  value: string;
  detail: string;
  tone: StatusTone;
};

export type StressStoryViewModel = {
  state: StressStoryState;
  eyebrow: string;
  title: string;
  answer: string;
  statusLabel: string;
  statusTone: StatusTone;
  confidenceLabel: string;
  confidenceTone: StatusTone;
  confidenceDetail: string;
  facts: StressStoryFact[];
  metrics: StressStoryMetric[];
  whatThisMeans: string;
  primaryScenarioId: string;
  evidenceTraceCount: number;
};

const RAW_TERM_PATTERN = /\b(?:stress_report|portfolio_xray|candidate_generation|current_vs_candidate|decision_verdict|schema_version|field_path|source_refs|artifact|frontend_review|true|false|null|n\/a|buy|sell|trade now|must rebalance|best portfolio|suitability approved)\b/i;

function clampText(value: string, fallback: string) {
  const text = value.replace(/\s+/g, " ").trim();
  if (!text || RAW_TERM_PATTERN.test(text)) return fallback;
  return text;
}

function firstAvailableSynthetic(model: StressLabModel) {
  return model.syntheticScenarios.find((scenario) => scenario.id === model.selectedScenarioId)
    ?? model.syntheticScenarios.find((scenario) => scenario.isWorst && scenario.availability === "available")
    ?? model.syntheticScenarios.find((scenario) => scenario.availability === "available")
    ?? model.syntheticScenarios[0];
}

function impactValue(scenario: StressScenarioDetail | undefined) {
  if (!scenario) return null;
  return scenario.kind === "historical" ? scenario.drawdownPct ?? scenario.portfolioLossPct : scenario.portfolioLossPct;
}

function joinTickers(rows: StressScenarioDetail["assetsHurt"], fallback: string) {
  const labels = rows.slice(0, 3).map((row) => row.ticker).filter(Boolean);
  return labels.length ? labels.join(", ") : fallback;
}

function deriveState({
  worstLoss,
  offset,
  confidenceLabel
}: {
  worstLoss: number | null;
  offset: number | null;
  confidenceLabel: string;
}): StressStoryState {
  const limited = /limited|insufficient|missing|unavailable/i.test(confidenceLabel);
  if (limited && worstLoss === null) return "evidence_limited";
  if (typeof worstLoss === "number" && worstLoss <= -0.15 && (offset === null || offset < 0.1)) {
    return "material_vulnerability";
  }
  if (typeof worstLoss === "number" && worstLoss <= -0.08) return "meaningful_stress";
  if (limited) return "evidence_limited";
  return "stress_acceptable";
}

function statePresentation(state: StressStoryState): { title: string; statusLabel: string; tone: StatusTone } {
  if (state === "material_vulnerability") {
    return { title: "Material stress vulnerability detected", statusLabel: "Material vulnerability", tone: "red" };
  }
  if (state === "meaningful_stress") {
    return { title: "Meaningful stress loss detected", statusLabel: "Stress loss", tone: "amber" };
  }
  if (state === "evidence_limited") {
    return { title: "Stress evidence is limited", statusLabel: "Evidence limited", tone: "amber" };
  }
  return { title: "No severe stress break detected", statusLabel: "Stress acceptable", tone: "green" };
}

function confidenceDetail(model: StressLabModel) {
  const syntheticAvailable = model.syntheticScenarios.filter((scenario) => scenario.availability === "available").length;
  const historicalAvailable = model.historicalScenarios.filter((scenario) => scenario.availability === "available").length;
  const limitedHistorical = model.historicalScenarios
    .filter((scenario) => scenario.availability !== "available")
    .map((scenario) => scenario.displayName);

  if (limitedHistorical.length) {
    return `${syntheticAvailable}/${model.syntheticScenarios.length} synthetic scenarios available; historical replay limited for ${limitedHistorical.join(", ")}.`;
  }
  return `${syntheticAvailable}/${model.syntheticScenarios.length} synthetic scenarios and ${historicalAvailable}/${model.historicalScenarios.length} historical episodes available.`;
}

function buildAnswer({
  state,
  scenario,
  offsetText,
  lossText
}: {
  state: StressStoryState;
  scenario: StressScenarioDetail | undefined;
  offsetText: string;
  lossText: string;
}) {
  const scenarioName = scenario?.displayName ?? "the available stress set";
  if (state === "material_vulnerability") {
    return `The current portfolio is most vulnerable to ${scenarioName}: estimated loss is ${lossText}, and assets that helped offset only ${offsetText} of losses.`;
  }
  if (state === "meaningful_stress") {
    return `The current portfolio shows a meaningful stress loss in ${scenarioName}: estimated loss is ${lossText}, with offset coverage of ${offsetText}.`;
  }
  if (state === "evidence_limited") {
    return "Stress evidence is usable only with limitations: review the available synthetic stress facts, but do not over-read incomplete historical replay.";
  }
  return `Available stress evidence does not show a severe current-portfolio break; the worst visible stress result is ${lossText} in ${scenarioName}.`;
}

function metricFromScorecard(model: StressLabModel, label: string) {
  return model.scorecard.find((item) => item.label === label);
}

function buildMetrics(model: StressLabModel, scenario: StressScenarioDetail | undefined): StressStoryMetric[] {
  const worstHistorical = metricFromScorecard(model, "Worst historical episode");
  const lossDrivers = joinTickers(scenario?.assetsHurt ?? [], "Unavailable");
  const metrics: StressStoryMetric[] = [
    {
      label: "Worst scenario",
      value: scenario?.displayName ?? "Unavailable",
      detail: `Estimated loss: ${formatStressPercent(impactValue(scenario))}`,
      tone: scenario?.severityTone ?? "slate"
    },
    {
      label: "Loss drivers",
      value: lossDrivers,
      detail: scenario?.assetsHurt.length ? "Largest hurt positions in the worst visible stress." : "Asset-level loss contribution is unavailable.",
      tone: scenario?.assetsHurt.length ? "red" : "slate"
    },
    {
      label: "Protection",
      value: model.hedgeGap.statusLabel,
      detail: `Offset coverage: ${formatStressPercent(model.hedgeGap.offsetCoverageRatio)}`,
      tone: model.hedgeGap.statusTone
    },
    {
      label: "Evidence",
      value: model.limitations.evidenceQualityLabel,
      detail: worstHistorical?.detail ?? confidenceDetail(model),
      tone: model.limitations.evidenceTone
    }
  ];
  return metrics.slice(0, 4);
}

function buildFacts(model: StressLabModel, scenario: StressScenarioDetail | undefined): StressStoryFact[] {
  const worstHistorical = metricFromScorecard(model, "Worst historical episode");
  const facts: StressStoryFact[] = [];

  if (scenario) {
    facts.push({
      label: "Worst synthetic stress",
      value: `${scenario.displayName}: ${formatStressPercent(scenario.portfolioLossPct)}`,
      detail: "This is the main current-portfolio stress result shown first.",
      tone: scenario.severityTone
    });
  }

  if (scenario?.assetsHurt.length) {
    facts.push({
      label: "Main loss drivers",
      value: joinTickers(scenario.assetsHurt, "Unavailable"),
      detail: "These holdings drive most of the selected stress loss.",
      tone: "red"
    });
  }

  facts.push({
    label: "Offset behavior",
    value: `${formatStressPercent(model.hedgeGap.offsetCoverageRatio)} offset coverage`,
    detail: model.hedgeGap.offsetCoverageRatio === null
      ? "Offset coverage is unavailable in the returned stress detail."
      : "This compares helped assets with losses from hurt assets.",
    tone: model.hedgeGap.statusTone
  });

  if (worstHistorical) {
    facts.push({
      label: "Historical replay",
      value: worstHistorical.value,
      detail: worstHistorical.detail,
      tone: worstHistorical.tone
    });
  }

  return facts.slice(0, 3);
}

function evidenceTraceCount(bundle?: SiteExplanationBundle) {
  const display = buildPublicSiteExplanationDisplayModel(bundle, "evidence", "Evidence trace");
  if (!display) return 0;
  return display.executiveItems.length + display.evidenceItems.length + display.technicalItems.length;
}

export function buildStressStoryViewModel(
  model: StressLabModel,
  siteExplanation?: SiteExplanationBundle
): StressStoryViewModel {
  const scenario = firstAvailableSynthetic(model);
  const worstLoss = impactValue(scenario);
  const offset = model.hedgeGap.offsetCoverageRatio;
  const state = deriveState({
    worstLoss,
    offset,
    confidenceLabel: model.limitations.evidenceQualityLabel
  });
  const presentation = statePresentation(state);
  const lossText = formatStressPercent(worstLoss);
  const offsetText = formatStressPercent(offset);

  return {
    state,
    eyebrow: "Current portfolio stress answer",
    title: presentation.title,
    answer: clampText(buildAnswer({ state, scenario, offsetText, lossText }), "Stress evidence is available for the current portfolio."),
    statusLabel: presentation.statusLabel,
    statusTone: presentation.tone,
    confidenceLabel: model.limitations.evidenceQualityLabel,
    confidenceTone: model.limitations.evidenceTone,
    confidenceDetail: clampText(confidenceDetail(model), "Evidence coverage is available in the stress details."),
    facts: buildFacts(model, scenario),
    metrics: buildMetrics(model, scenario),
    whatThisMeans: "Stress Test Lab does not create a rebalance verdict. It identifies the current portfolio's stress weak point so the next step can check whether that risk fits the provided profile.",
    primaryScenarioId: scenario?.id ?? model.selectedScenarioId,
    evidenceTraceCount: evidenceTraceCount(siteExplanation)
  };
}

export function assertPublicStressStoryLimits(story: StressStoryViewModel) {
  return {
    hasSingleAnswer: Boolean(story.answer && story.title),
    factCountOk: story.facts.length <= 3,
    metricCountOk: story.metrics.length <= 4,
    noRawTerms: !RAW_TERM_PATTERN.test(JSON.stringify(story))
  };
}
