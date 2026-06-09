import { evidenceQualityLabel, evidenceTone, normalizeDisplayLabel } from "@/lib/displayLabels";
import type { StatusTone } from "@/lib/types";
import type {
  ContributionRow,
  FactorContributionRow,
  HedgeGapSummary,
  StressLabModel,
  StressLimitations,
  StressScenarioDetail,
  StressScorecardItem,
  XRayConfirmationRow
} from "./stressLabTypes";

const SYNTHETIC_ORDER = [
  "equity_shock",
  "credit_shock",
  "rates_shock",
  "inflation_stagflation",
  "liquidity_shock",
  "usd_shock",
  "commodity_shock",
  "recession_severe"
];

const HISTORICAL_ORDER = ["dotcom", "2008", "2020", "2022", "banking_2023"];

const SCENARIO_LABELS: Record<string, string> = {
  equity_shock: "Equity sell-off",
  credit_shock: "Credit shock",
  rates_shock: "Interest-rate shock",
  inflation_stagflation: "Inflation / stagflation",
  liquidity_shock: "Liquidity shock",
  usd_shock: "USD shock",
  commodity_shock: "Commodity shock",
  recession_severe: "Severe recession",
  dotcom: "Dot-com",
  "2008": "2008",
  "2020": "2020",
  "2022": "2022-like drawdown",
  banking_2023: "Banking 2023"
};

const PROTECTION_LABELS: Record<string, string> = {
  equity_crash_protection: "Equity sell-off protection",
  rates_up_shock_protection: "Interest-rate shock protection",
  stagflation_protection: "Inflation / stagflation protection",
  liquidity_shock_protection: "Liquidity shock protection",
  usd_spike_protection: "USD shock protection",
  credit_shock_protection: "Credit shock protection",
  commodity_inflation_shock_protection: "Commodity shock protection",
  recession_severe_protection: "Severe recession protection"
};

const FACTOR_LABELS: Record<string, string> = {
  eq: "Equity",
  equity: "Equity",
  beta_eq: "Equity",
  rr: "Interest-rate sensitivity",
  real_rates: "Interest-rate sensitivity",
  beta_rr: "Interest-rate sensitivity",
  inf: "Inflation",
  inflation: "Inflation",
  beta_inf: "Inflation",
  credit: "Credit",
  beta_credit: "Credit",
  usd: "USD",
  beta_usd: "USD",
  cmd: "Commodity",
  commodity: "Commodity",
  beta_cmd: "Commodity",
  vix: "Volatility",
  beta_vix: "Volatility",
  us_growth: "Growth",
  beta_us_growth: "Growth"
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function record(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function array(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function text(value: unknown, fallback = "") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function number(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function firstNumber(...values: unknown[]) {
  for (const value of values) {
    const parsed = number(value);
    if (parsed !== null) return parsed;
  }
  return null;
}

export function formatStressPercent(value: number | null | undefined, options: { signed?: boolean; digits?: number } = {}) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "Unavailable";
  const digits = options.digits ?? 1;
  const pct = value * 100;
  const sign = options.signed && pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(digits).replace(/\.0$/, "")}%`;
}

function scenarioLabel(id: unknown) {
  const key = text(id);
  return SCENARIO_LABELS[key] ?? normalizeDisplayLabel(key, "Unavailable");
}

function protectionLabel(id: unknown) {
  const key = text(id);
  return PROTECTION_LABELS[key] ?? normalizeDisplayLabel(key, "Stress protection");
}

function factorLabel(id: unknown, fallback = "Factor") {
  const key = text(id);
  return FACTOR_LABELS[key] ?? normalizeDisplayLabel(key, fallback);
}

function statusToneFromLoss(value: number | null, isWorst: boolean): StatusTone {
  if (value === null) return "slate";
  if (isWorst || value <= -0.12) return "red";
  if (value <= -0.05) return "amber";
  if (value < 0) return "slate";
  return "green";
}

function scenarioSeverity(value: number | null, isWorst: boolean) {
  if (value === null) return "Unavailable";
  if (isWorst) return "Most damaging";
  const magnitude = Math.abs(value);
  if (magnitude >= 0.1) return "Material loss";
  if (magnitude >= 0.03) return "Moderate loss";
  return "Less damaging";
}

function scenarioEvidenceQuality(row: Record<string, unknown>, rawRow?: Record<string, unknown>) {
  const syntheticAssumptions = record(rawRow?.synthetic_assumptions);
  const syntheticConfidence = syntheticAssumptions.beta_confidence;
  const historicalQuality = row.data_quality;
  const availability = text(row.availability);
  if (availability === "unavailable") return "Insufficient data";
  if (syntheticConfidence !== undefined) return evidenceQualityLabel(syntheticConfidence);
  if (historicalQuality !== undefined) {
    const quality = text(historicalQuality).toLowerCase();
    if (quality === "reliable") return "Strong evidence";
    if (quality === "usable_with_gaps") return "Moderate evidence";
    if (quality.includes("insufficient")) return "Insufficient data";
    return evidenceQualityLabel(quality);
  }
  return availability === "available" ? "Strong evidence" : "Limited evidence";
}

function mapContributionRows(value: unknown): ContributionRow[] {
  const source = record(value);
  return Object.entries(source)
    .map(([ticker, raw]) => {
      const parsed = number(raw);
      if (parsed === null) return null;
      const status = parsed > 0 ? "Helped" : parsed < 0 ? "Hurt" : "Neutral";
      return { ticker, value: parsed, status } satisfies ContributionRow;
    })
    .filter((item): item is ContributionRow => Boolean(item))
    .sort((a, b) => {
      if (a.status !== b.status) {
        if (a.status === "Hurt") return -1;
        if (b.status === "Hurt") return 1;
        if (a.status === "Helped") return 1;
        if (b.status === "Helped") return -1;
      }
      return Math.abs(b.value) - Math.abs(a.value) || a.ticker.localeCompare(b.ticker);
    });
}

function assetRowsFromList(value: unknown, status: ContributionRow["status"]): ContributionRow[] {
  return array(value)
    .map(record)
    .map((item) => {
      const ticker = text(item.ticker);
      const parsed = number(item.pnl_pct);
      if (!ticker || parsed === null) return null;
      if (status === "Helped" && parsed <= 0) return null;
      if (status === "Hurt" && parsed >= 0) return null;
      return { ticker, value: parsed, status } satisfies ContributionRow;
    })
    .filter((item): item is ContributionRow => Boolean(item));
}

function splitContributions(rows: ContributionRow[]) {
  const hurt = rows.filter((row) => row.value < 0).sort((a, b) => a.value - b.value || a.ticker.localeCompare(b.ticker));
  const helped = rows.filter((row) => row.value > 0).sort((a, b) => b.value - a.value || a.ticker.localeCompare(b.ticker));
  return { hurt, helped };
}

function factorRowsFromMap(value: unknown): FactorContributionRow[] {
  return Object.entries(record(value))
    .map(([factor, raw]) => {
      const parsed = number(raw);
      if (parsed === null || parsed === 0) return null;
      return {
        factor: factorLabel(factor),
        value: parsed,
        status: parsed < 0 ? "Loss driver" : "Offset"
      } satisfies FactorContributionRow;
    })
    .filter((item): item is FactorContributionRow => Boolean(item))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value) || a.factor.localeCompare(b.factor));
}

function factorRowsFromLists(driverRows: unknown, helpedRows: unknown): FactorContributionRow[] {
  return [...array(driverRows), ...array(helpedRows)]
    .map(record)
    .map((item) => {
      const parsed = number(item.pnl_pct);
      if (parsed === null || parsed === 0) return null;
      return {
        factor: factorLabel(item.factor_short ?? item.beta_key ?? item.factor, "Factor"),
        value: parsed,
        status: parsed < 0 ? "Loss driver" : "Offset"
      } satisfies FactorContributionRow;
    })
    .filter((item): item is FactorContributionRow => Boolean(item))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value) || a.factor.localeCompare(b.factor));
}

function syntheticScenarioFromRow({
  row,
  rawRow,
  worstScenarioId
}: {
  row: Record<string, unknown>;
  rawRow?: Record<string, unknown>;
  worstScenarioId: string;
}): StressScenarioDetail {
  const id = text(row.scenario_id);
  const portfolioLossPct = firstNumber(row.portfolio_loss_pct, row.portfolio_pnl_pct);
  const isWorst = Boolean(id && id === worstScenarioId);
  const lossContribution = record(row.loss_contribution);
  const contributionMap = lossContribution.pnl_by_asset_pct ?? row.pnl_by_asset_pct;
  const rows = mapContributionRows(contributionMap);
  const split = splitContributions(rows);
  const assetsHurt = assetRowsFromList(lossContribution.assets_hurt, "Hurt");
  const assetsHelped = assetRowsFromList(row.assets_helped ?? lossContribution.assets_helped, "Helped");
  const factorAttribution = record(row.factor_attribution);
  const factors = factorRowsFromMap(factorAttribution.pnl_by_factor_pct).length
    ? factorRowsFromMap(factorAttribution.pnl_by_factor_pct)
    : factorRowsFromLists(factorAttribution.top_factor_drivers, factorAttribution.helped_factors);
  const helped = assetsHelped.length ? assetsHelped : split.helped;
  const hurt = assetsHurt.length ? assetsHurt : split.hurt;
  const quality = scenarioEvidenceQuality(row, rawRow);
  const availability = text(row.availability, portfolioLossPct === null ? "unavailable" : "available");

  return {
    id,
    displayName: scenarioLabel(id),
    groupLabel: "Synthetic shock",
    kind: "synthetic",
    portfolioLossPct,
    drawdownPct: firstNumber(row.drawdown_pct),
    availability,
    severityLabel: scenarioSeverity(portfolioLossPct, isWorst),
    severityTone: statusToneFromLoss(portfolioLossPct, isWorst),
    evidenceQualityLabel: quality,
    evidenceTone: evidenceTone(quality),
    isWorst,
    lossContributions: rows,
    assetsHurt: hurt,
    assetsHelped: helped,
    factorAttribution: factors,
    interpretation: buildScenarioInterpretation({
      displayName: scenarioLabel(id),
      portfolioLossPct,
      assetsHurt: hurt,
      assetsHelped: helped,
      kind: "synthetic"
    }),
    limitation: availability === "available" ? undefined : "Scenario result is unavailable for this stress run."
  };
}

function historicalScenarioFromRow({
  row,
  worstEpisode
}: {
  row: Record<string, unknown>;
  worstEpisode: string;
}): StressScenarioDetail {
  const id = text(row.episode ?? row.scenario_id);
  const portfolioLossPct = firstNumber(row.portfolio_loss_pct, row.pnl_real_episode);
  const drawdownPct = firstNumber(row.drawdown_pct, row.max_dd);
  const isWorst = Boolean(id && id === worstEpisode);
  const lossContribution = record(row.loss_contribution);
  const rows = mapContributionRows(lossContribution.pnl_by_asset_pct ?? row.pnl_by_asset_pct);
  const split = splitContributions(rows);
  const assetsHurt = assetRowsFromList(lossContribution.assets_hurt, "Hurt");
  const assetsHelped = assetRowsFromList(row.assets_helped ?? lossContribution.assets_helped, "Helped");
  const factorAttribution = record(row.factor_attribution);
  const factors = factorRowsFromMap(factorAttribution.pnl_by_factor_pct).length
    ? factorRowsFromMap(factorAttribution.pnl_by_factor_pct)
    : factorRowsFromLists(factorAttribution.top_factor_drivers, factorAttribution.helped_factors);
  const quality = scenarioEvidenceQuality(row);
  const availability = text(row.availability, drawdownPct === null ? "unavailable" : "available");
  const limitation = availability === "available"
    ? undefined
    : text(row.limitation_summary ?? row.user_note, "Historical replay is limited for this episode.");

  return {
    id,
    displayName: scenarioLabel(id),
    groupLabel: "Historical episode",
    kind: "historical",
    portfolioLossPct,
    drawdownPct,
    availability,
    severityLabel: scenarioSeverity(drawdownPct ?? portfolioLossPct, isWorst),
    severityTone: statusToneFromLoss(drawdownPct ?? portfolioLossPct, isWorst),
    evidenceQualityLabel: quality,
    evidenceTone: evidenceTone(quality),
    isWorst,
    dataNote: limitation,
    lossContributions: rows,
    assetsHurt: assetsHurt.length ? assetsHurt : split.hurt,
    assetsHelped: assetsHelped.length ? assetsHelped : split.helped,
    factorAttribution: factors,
    interpretation: buildScenarioInterpretation({
      displayName: scenarioLabel(id),
      portfolioLossPct: drawdownPct ?? portfolioLossPct,
      assetsHurt: assetsHurt.length ? assetsHurt : split.hurt,
      assetsHelped: assetsHelped.length ? assetsHelped : split.helped,
      kind: "historical"
    }),
    limitation
  };
}

function buildScenarioInterpretation({
  displayName,
  portfolioLossPct,
  assetsHurt,
  assetsHelped,
  kind
}: {
  displayName: string;
  portfolioLossPct: number | null;
  assetsHurt: ContributionRow[];
  assetsHelped: ContributionRow[];
  kind: "synthetic" | "historical";
}) {
  if (portfolioLossPct === null) {
    return kind === "historical"
      ? `${displayName} replay is limited because the current holdings do not have enough usable history for this period.`
      : `${displayName} is in the Scenario Library, but the portfolio result is unavailable for this run.`;
  }
  const hurt = assetsHurt.slice(0, 3).map((item) => item.ticker).join(", ");
  const helped = assetsHelped.slice(0, 3).map((item) => item.ticker).join(", ");
  const offset = helped
    ? `${helped} helped offset part of the loss.`
    : "No meaningful helped assets were detected in this scenario.";
  return `${displayName} shows ${formatStressPercent(portfolioLossPct)} stress impact for the current portfolio. ${hurt ? `${hurt} drove the largest losses. ` : ""}${offset}`;
}

function rowById(rows: unknown[], field: "scenario_id" | "episode", id: string) {
  return rows.map(record).find((row) => text(row[field]) === id);
}

function buildSyntheticScenarios(stress: Record<string, unknown>) {
  const stressResults = record(stress.stress_results_v1);
  const envelope = record(stressResults.envelope);
  const worstSynthetic = record(envelope.worst_synthetic ?? record(stress.current_portfolio_stress_scorecard_v1).worst_synthetic_scenario);
  const worstScenarioId = text(worstSynthetic.scenario_id, "recession_severe");
  const rows = array(stressResults.synthetic_scenarios ?? stressResults.synthetic);
  const rawRows = array(stress.scenario_results);
  return SYNTHETIC_ORDER.map((id) => {
    const row = rowById(rows, "scenario_id", id);
    if (!row) return unavailableScenario(id, "synthetic", id === worstScenarioId);
    const rawRow = rowById(rawRows, "scenario_id", id);
    return syntheticScenarioFromRow({ row, rawRow, worstScenarioId });
  });
}

function buildHistoricalScenarios(stress: Record<string, unknown>) {
  const stressResults = record(stress.stress_results_v1);
  const envelope = record(stressResults.envelope);
  const worstHistorical = record(envelope.worst_historical ?? record(stress.current_portfolio_stress_scorecard_v1).worst_historical_scenario);
  const worstEpisode = text(worstHistorical.episode, "2022");
  const rows = array(stressResults.historical_episodes ?? stressResults.historical);
  return HISTORICAL_ORDER.map((id) => {
    const row = rowById(rows, "episode", id) ?? rowById(rows, "scenario_id", id);
    if (!row) return unavailableScenario(id, "historical", id === worstEpisode);
    return historicalScenarioFromRow({ row, worstEpisode });
  });
}

function unavailableScenario(id: string, kind: "synthetic" | "historical", isWorst = false): StressScenarioDetail {
  return {
    id,
    displayName: scenarioLabel(id),
    groupLabel: kind === "synthetic" ? "Synthetic shock" : "Historical episode",
    kind,
    portfolioLossPct: null,
    drawdownPct: null,
    availability: "unavailable",
    severityLabel: "Unavailable",
    severityTone: "slate",
    evidenceQualityLabel: "Insufficient data",
    evidenceTone: "slate",
    isWorst,
    dataNote: kind === "historical" ? "Replay limited" : "Scenario result unavailable",
    lossContributions: [],
    assetsHurt: [],
    assetsHelped: [],
    factorAttribution: [],
    interpretation: kind === "historical"
      ? `${scenarioLabel(id)} replay is limited for the current portfolio.`
      : `${scenarioLabel(id)} is in the Scenario Library, but this run did not return a usable result.`,
    limitation: kind === "historical"
      ? "Historical replay is limited because asset-level history is incomplete."
      : "Synthetic stress result is unavailable for this run."
  };
}

function protectionStatusLabel(value: unknown) {
  const status = text(value).toLowerCase();
  if (status === "strong_protection") return "Strong offset";
  if (status === "partial_protection") return "Partial offset";
  if (status === "weak_protection") return "Weak offset";
  if (status === "no_protection") return "No meaningful offset";
  if (status === "not_needed_or_no_loss") return "Less damaging";
  return "Unavailable";
}

function protectionTone(value: unknown): StatusTone {
  const label = protectionStatusLabel(value);
  if (label === "Strong offset") return "green";
  if (label === "Partial offset") return "amber";
  if (label === "Weak offset" || label === "No meaningful offset") return "red";
  return "slate";
}

function buildHedgeGap(stress: Record<string, unknown>, scenarios: StressScenarioDetail[]): HedgeGapSummary {
  const hedge = record(stress.hedge_gap_analysis_v1);
  const summary = record(hedge.summary);
  const scorecard = record(stress.current_portfolio_stress_scorecard_v1);
  const scorecardOffset = record(scorecard.offset_coverage_summary);
  const mainGap = record(summary.main_hedge_gap ?? record(scorecard.main_hedge_gap).main_hedge_gap);
  const riskType = text(mainGap.risk_type ?? mainGap.protection_type ?? scorecardOffset.risk_type ?? summary.weakest_protection_area);
  const scenarioId = text(mainGap.linked_scenario_id ?? mainGap.scenario_id ?? scorecardOffset.linked_scenario_id);
  const row = array(hedge.by_risk_type).map(record).find((item) => {
    return text(item.risk_type) === riskType || text(item.linked_scenario_id) === scenarioId;
  });
  const grossLoss = firstNumber(row?.gross_loss_from_assets_hurt, scorecardOffset.gross_loss_from_assets_hurt);
  const positive = firstNumber(row?.positive_contribution_from_assets_helped, scorecardOffset.positive_contribution_from_assets_helped);
  const offset = firstNumber(row?.offset_coverage_ratio, mainGap.offset_coverage_ratio, scorecardOffset.offset_coverage_ratio);
  const scenario = scenarios.find((item) => item.id === scenarioId);
  const hurt = row ? assetRowsFromList(row.assets_hurt, "Hurt") : scenario?.assetsHurt ?? [];
  const helped = row ? assetRowsFromList(row.assets_helped, "Helped") : scenario?.assetsHelped ?? [];
  const statusLabel = protectionStatusLabel(row?.protection_status ?? mainGap.protection_status);
  const grossText = formatStressPercent(grossLoss ? -Math.abs(grossLoss) : grossLoss);
  const helpedText = formatStressPercent(positive, { signed: true });
  const offsetText = formatStressPercent(offset);

  return {
    displayName: protectionLabel(riskType),
    scenarioDisplayName: scenarioLabel(scenarioId),
    grossLossFromHurt: grossLoss,
    positiveContributionFromHelped: positive,
    offsetCoverageRatio: offset,
    statusLabel,
    statusTone: protectionTone(row?.protection_status ?? mainGap.protection_status),
    assetsHurt: hurt,
    assetsHelped: helped,
    interpretation: offset === null
      ? "Offset coverage is unavailable because the stress run did not return enough asset contribution detail."
      : `Only ${offsetText} of losses from hurt assets were offset by assets that helped in ${scenarioLabel(scenarioId)}. Hurt assets contributed ${grossText}; helped assets contributed ${helpedText}.`
  };
}

function joinTickers(rows: ContributionRow[], fallback: string) {
  const labels = rows.slice(0, 3).map((row) => row.ticker);
  return labels.length ? labels.join(", ") : fallback;
}

function buildScorecard({
  stress,
  selectedScenario,
  synthetic,
  historical,
  hedgeGap
}: {
  stress: Record<string, unknown>;
  selectedScenario: StressScenarioDetail;
  synthetic: StressScenarioDetail[];
  historical: StressScenarioDetail[];
  hedgeGap: HedgeGapSummary;
}): StressScorecardItem[] {
  const scorecard = record(stress.current_portfolio_stress_scorecard_v1);
  const diagnosis = record(scorecard.stress_diagnosis);
  const coverage = record(scorecard.stress_coverage);
  const worstSynthetic = synthetic.find((item) => item.isWorst) ?? selectedScenario;
  const worstHistorical = historical.find((item) => item.isWorst) ?? historical.find((item) => item.drawdownPct !== null);
  const syntheticAvailable = firstNumber(coverage.n_synthetic_available) ?? synthetic.filter((item) => item.availability === "available").length;
  const syntheticTotal = firstNumber(coverage.n_synthetic_total) ?? synthetic.length;
  const historicalAvailable = firstNumber(coverage.n_historical_available) ?? historical.filter((item) => item.availability === "available").length;
  const historicalTotal = firstNumber(coverage.n_historical_total) ?? historical.length;
  const quality = evidenceQualityLabel(diagnosis.diagnosis_confidence ?? scorecard.block_status ?? "partial");

  return [
    {
      label: "Worst synthetic scenario",
      value: worstSynthetic.displayName,
      detail: `Estimated portfolio loss: ${formatStressPercent(worstSynthetic.portfolioLossPct)}`,
      tone: worstSynthetic.severityTone
    },
    {
      label: "Worst historical episode",
      value: worstHistorical?.drawdownPct !== null && worstHistorical?.drawdownPct !== undefined ? worstHistorical.displayName : "Historical replay limited",
      detail: worstHistorical?.drawdownPct !== null && worstHistorical?.drawdownPct !== undefined
        ? `Max drawdown: ${formatStressPercent(worstHistorical.drawdownPct)}`
        : "Older episodes have incomplete holding history.",
      tone: worstHistorical?.drawdownPct !== null && worstHistorical?.drawdownPct !== undefined ? worstHistorical.severityTone : "amber"
    },
    {
      label: "Main loss drivers",
      value: joinTickers(selectedScenario.assetsHurt, "Unavailable"),
      detail: selectedScenario.assetsHurt.length
        ? "These positions drive most of the selected stress loss."
        : "Asset-level loss contribution is unavailable.",
      tone: selectedScenario.assetsHurt.length ? "red" : "slate"
    },
    {
      label: "Assets that helped",
      value: joinTickers(selectedScenario.assetsHelped, "No meaningful offset detected"),
      detail: selectedScenario.assetsHelped.length
        ? "Only positive stress contributions are counted as helped."
        : "No assets had positive contribution in the selected scenario.",
      tone: selectedScenario.assetsHelped.length ? "green" : "amber"
    },
    {
      label: "Main hedge gap",
      value: hedgeGap.displayName,
      detail: `Offset coverage: ${formatStressPercent(hedgeGap.offsetCoverageRatio)}`,
      tone: hedgeGap.statusTone
    },
    {
      label: "Data coverage",
      value: quality,
      detail: `${syntheticAvailable}/${syntheticTotal} synthetic scenarios and ${historicalAvailable}/${historicalTotal} historical episodes available.`,
      tone: evidenceTone(quality)
    }
  ];
}

function confirmationDetail(row: Record<string, unknown>) {
  const scenario = scenarioLabel(row.linked_scenario_id ?? row.risk_type);
  const status = protectionStatusLabel(row.protection_status).toLowerCase();
  const offset = formatStressPercent(firstNumber(row.offset_coverage_ratio));
  const loss = formatStressPercent(firstNumber(row.portfolio_loss_pct));
  return `${scenario} stress shows ${status} with ${offset} offset coverage and ${loss} portfolio stress impact.`;
}

function buildXRayConfirmation(stress: Record<string, unknown>, historical: StressScenarioDetail[]) {
  const scorecard = record(stress.current_portfolio_stress_scorecard_v1);
  const preStress = record(scorecard.pre_stress_confirmation_summary);
  const weaknessMap = record(preStress.weakness_map);
  const rows = array(weaknessMap.confirmation_rows).map(record);
  const confirmed: XRayConfirmationRow[] = rows
    .filter((row) => ["confirmed", "partially_confirmed"].includes(text(row.confirmation_status)))
    .slice(0, 4)
    .map((row) => ({
      label: scenarioLabel(row.linked_scenario_id ?? row.risk_type),
      detail: confirmationDetail(row),
      tone: text(row.confirmation_status) === "confirmed" ? "amber" : "slate"
    }));

  const lessMaterial: XRayConfirmationRow[] = rows
    .filter((row) => ["not_confirmed", "not_applicable"].includes(text(row.confirmation_status)))
    .slice(0, 4)
    .map((row) => ({
      label: scenarioLabel(row.linked_scenario_id ?? row.risk_type),
      detail: text(row.confirmation_status) === "not_confirmed"
        ? `${scenarioLabel(row.linked_scenario_id ?? row.risk_type)} did not confirm the pre-stress weakness in this review.`
        : `${scenarioLabel(row.linked_scenario_id ?? row.risk_type)} was less material in the pre-stress weakness review.`,
      tone: "slate"
    }));

  const insufficientData: XRayConfirmationRow[] = historical
    .filter((item) => item.availability !== "available")
    .slice(0, 3)
    .map((item) => ({
      label: item.displayName,
      detail: item.limitation ?? "Historical replay is limited for this episode.",
      tone: "amber"
    }));

  return {
    confirmed,
    lessMaterial,
    insufficientData,
    note: rows.length
      ? "Stress confirmation is based on available scenario results. Some X-Ray weaknesses still require more evidence before a candidate test."
      : "Stress confirmation mapping was not returned for this run. Review scenario results before treating pre-stress weaknesses as confirmed."
  };
}

function buildLimitations(stress: Record<string, unknown>, historical: StressScenarioDetail[], synthetic: StressScenarioDetail[]): StressLimitations {
  const scorecard = record(stress.current_portfolio_stress_scorecard_v1);
  const diagnosis = record(scorecard.stress_diagnosis);
  const unavailableHistorical = historical.filter((item) => item.availability !== "available");
  const syntheticAvailable = synthetic.filter((item) => item.availability === "available").length;
  const quality = evidenceQualityLabel(diagnosis.diagnosis_confidence ?? scorecard.block_status ?? "partial");
  const episodeNames = unavailableHistorical.map((item) => item.displayName).join(", ");

  return {
    headline: unavailableHistorical.length
      ? "Historical replay is limited for older episodes."
      : "Stress data coverage is usable for this review.",
    evidenceQualityLabel: quality,
    evidenceTone: evidenceTone(quality),
    whatLimited: unavailableHistorical.length
      ? [`Older historical episodes have incomplete asset-level coverage: ${episodeNames}.`]
      : ["No older historical replay limitation was surfaced in the available stress summary."],
    whyItMatters: unavailableHistorical.length
      ? ["The portfolio-level stress view may be unavailable for those older episodes, and asset-level contribution may be less reliable."]
      : ["Available stress results can be reviewed without relying on unavailable historical replays."],
    stillUsable: [
      `${syntheticAvailable}/${synthetic.length} synthetic stress scenarios remain available.`,
      "Current Portfolio X-Ray diagnostics remain available as pre-stress context.",
      "Use these results as supporting evidence before testing any candidate hypothesis."
    ]
  };
}

export function buildStressLabModelFromOutputs(outputs: unknown): StressLabModel | null {
  const outputRecord = record(outputs);
  const stress = record(outputRecord.stress_report);
  if (!Object.keys(stress).length) return null;

  const syntheticScenarios = buildSyntheticScenarios(stress);
  const historicalScenarios = buildHistoricalScenarios(stress);
  const selectedScenario = syntheticScenarios.find((item) => item.isWorst && item.availability === "available")
    ?? syntheticScenarios.find((item) => item.availability === "available")
    ?? syntheticScenarios[0];
  const hedgeGap = buildHedgeGap(stress, syntheticScenarios);
  const scorecard = buildScorecard({
    stress,
    selectedScenario,
    synthetic: syntheticScenarios,
    historical: historicalScenarios,
    hedgeGap
  });

  return {
    headerStatusLabel: "Current portfolio review",
    scorecard,
    syntheticScenarios,
    historicalScenarios,
    selectedScenarioId: selectedScenario.id,
    hedgeGap,
    xrayConfirmation: buildXRayConfirmation(stress, historicalScenarios),
    limitations: buildLimitations(stress, historicalScenarios, syntheticScenarios)
  };
}

export function ensureStressLabModel(value: unknown): StressLabModel {
  return value as StressLabModel;
}
