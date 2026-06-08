"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { EvidenceCenter } from "@/components/evidence/EvidenceCenter";
import { StatusBadge } from "@/components/ui/StatusBadge";
import data from "@/data/demo/evidence-center.json";
import { useReviewState } from "@/lib/reviewState";
import type { EvidenceItem, Metric, StatusTone } from "@/lib/types";

type EvidencePayload = {
  headline: string;
  quality: string;
  boundaryNote: string;
  items: EvidenceItem[];
  metrics: Metric[];
};

const sampleEvidence = data as EvidencePayload;

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function record(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function array(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function text(value: unknown, fallback = "n/a") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function number(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatPercent(value: unknown, mode: "raw" | "decimal" = "raw") {
  const parsed = number(value);
  if (parsed === null) return "n/a";
  const pct = mode === "decimal" ? parsed * 100 : parsed;
  return `${pct.toFixed(1).replace(/\.0$/, "")}%`;
}

function toneForLoss(value: unknown): StatusTone {
  const parsed = number(value);
  if (parsed === null) return "slate";
  if (parsed <= -0.12) return "red";
  if (parsed <= -0.06) return "amber";
  return "blue";
}

function firstWarning(...sources: unknown[]) {
  for (const source of sources) {
    const warnings = array(source).filter((item): item is string => typeof item === "string" && Boolean(item.trim()));
    if (warnings.length) return warnings[0];
  }
  return null;
}

function buildRealEvidence(activeReview: ReturnType<typeof useReviewState>["activeReview"]): EvidencePayload | null {
  if (activeReview?.reviewSummary?.evidence) return activeReview.reviewSummary.evidence;

  const outputs = record(activeReview?.reviewResult?.outputs);
  const xray = record(outputs.portfolio_xray);
  const stress = record(outputs.stress_report);
  if (!Object.keys(xray).length || !Object.keys(stress).length) return null;

  const allocation = record(xray.block_2_1_asset_allocation);
  const composition = record(allocation.portfolio_composition_snapshot);
  const riskBudget = record(xray.block_2_5_risk_budget_view);
  const metricsBlock = record(xray.block_2_2_portfolio_metrics);
  const drawdown = record(metricsBlock.drawdown_diagnostics);
  const weaknessMap = record(xray.block_2_6_portfolio_weakness_map);
  const stressConclusions = record(stress.stress_conclusions);
  const worstScenario = record(stressConclusions.worst_synthetic_scenario);
  const hedgeSummary = record(record(stress.hedge_gap_analysis_v1).summary);
  const mainHedgeGap = record(hedgeSummary.main_hedge_gap);

  const dominantAssetClass = record(composition.dominant_asset_class);
  const dominantRiskFactor = record(composition.dominant_main_risk_factor);
  const topHolding = record(composition.top1_holding);
  const topRiskContributors = array(riskBudget.top3_rc_assets).map(record).slice(0, 3);
  const topRiskContributor = record(riskBudget.top1_rc_asset);
  const riskTypes = array(weaknessMap.risk_types)
    .map(record)
    .filter((item) => Boolean(text(item.risk_title, "") || text(item.risk_type, "")))
    .sort((a, b) => (number(b.score_0_100) ?? 0) - (number(a.score_0_100) ?? 0));
  const dataWarning = firstWarning(
    allocation.data_quality_warnings,
    metricsBlock.data_quality_warnings,
    weaknessMap.data_quality_warnings,
    stressConclusions.data_quality_warnings,
    hedgeSummary.data_quality_warnings
  );

  const holdingsCount = number(composition.total_holdings) ?? activeReview?.reviewSummary?.holdingsCount ?? activeReview?.holdings.length ?? 0;
  const dominantExposureName = text(dominantRiskFactor.name, text(dominantAssetClass.name, "Dominant exposure"));
  const dominantExposureWeight = formatPercent(dominantRiskFactor.weight_pct ?? dominantAssetClass.weight_pct);
  const worstScenarioId = text(worstScenario.scenario_id ?? stress.failed_scenario, "Worst stress scenario");
  const worstStressLoss = worstScenario.portfolio_pnl_pct ?? stress.worst_scenario_loss_pct;
  const maxDrawdown = drawdown.max_drawdown;
  const hedgeCoverage = mainHedgeGap.offset_coverage_ratio ?? hedgeSummary.main_hedge_gap_offset_coverage_ratio;
  const hedgeArea = text(mainHedgeGap.protection_type ?? hedgeSummary.weakest_protection_area, "hedge gap");
  const riskContributorText = topRiskContributors.length
    ? topRiskContributors
      .map((item) => `${text(item.ticker, "Asset")} ${formatPercent(item.rc_pct ?? item.risk_contribution_pct)}`)
      .join(" · ")
    : "Top risk contributors were not returned.";

  const items: EvidenceItem[] = [
    {
      type: "X-Ray",
      title: "Portfolio composition",
      status: `${holdingsCount} holdings`,
      summary: topHolding.ticker
        ? `Largest holding is ${text(topHolding.ticker)} at ${formatPercent(topHolding.weight_pct)}.`
        : "Portfolio composition was returned for the current portfolio.",
      source: "Portfolio X-Ray",
      tone: "blue"
    },
    {
      type: "X-Ray",
      title: "Dominant exposure",
      status: `${dominantExposureName} · ${dominantExposureWeight}`,
      summary: `The current portfolio is most exposed to ${dominantExposureName}.`,
      source: "Portfolio X-Ray",
      tone: number(dominantRiskFactor.weight_pct ?? dominantAssetClass.weight_pct) !== null && (number(dominantRiskFactor.weight_pct ?? dominantAssetClass.weight_pct) ?? 0) >= 50 ? "amber" : "blue"
    },
    {
      type: "X-Ray",
      title: "Top risk contributors",
      status: topRiskContributor.ticker ? `${text(topRiskContributor.ticker)} leads risk` : "Not available",
      summary: riskContributorText,
      source: "Portfolio X-Ray",
      tone: topRiskContributors.length ? "amber" : "slate"
    },
    {
      type: "Stress",
      title: "Worst stress scenario",
      status: worstScenarioId,
      summary: `Estimated portfolio loss: ${formatPercent(worstStressLoss, "decimal")}.`,
      source: "Stress Test Lab",
      tone: toneForLoss(worstStressLoss)
    },
    {
      type: "Stress",
      title: "Hedge / offset coverage",
      status: hedgeCoverage !== undefined ? `${formatPercent(hedgeCoverage, "decimal")} offset coverage` : "Not available",
      summary: hedgeCoverage !== undefined
        ? `Weakest protection area: ${hedgeArea}.`
        : "Stress result did not return hedge or offset coverage.",
      source: "Stress Test Lab",
      tone: hedgeCoverage !== undefined ? ((number(hedgeCoverage) ?? 0) < 0.25 ? "amber" : "blue") : "slate"
    }
  ];

  if (riskTypes[0]) {
    items.splice(3, 0, {
      type: "X-Ray",
      title: "Primary weakness",
      status: `${text(riskTypes[0].severity, "Risk")} · score ${text(String(riskTypes[0].score_0_100 ?? "n/a"))}`,
      summary: text(riskTypes[0].short_diagnosis, text(riskTypes[0].risk_title, "Primary weakness returned by X-Ray.")),
      source: "Portfolio X-Ray",
      tone: (number(riskTypes[0].score_0_100) ?? 0) >= 70 ? "red" : "amber"
    });
  }

  if (dataWarning) {
    items.push({
      type: "Data quality",
      title: "Data quality warning",
      status: "Review with caution",
      summary: dataWarning,
      source: "Input and diagnostic data checks",
      tone: "amber"
    });
  }

  return {
    headline: "Evidence is based on the latest completed real review.",
    quality: `Real run · ${text(stressConclusions.overall_confidence, "confidence n/a")} stress confidence`,
    boundaryNote: "Evidence is diagnostic and comes from Portfolio X-Ray plus Stress Test Lab for the submitted current portfolio.",
    metrics: [
      {
        label: "Holdings",
        value: String(holdingsCount),
        detail: topHolding.ticker ? `Largest: ${text(topHolding.ticker)} ${formatPercent(topHolding.weight_pct)}` : "Current portfolio",
        tone: "blue"
      },
      {
        label: "Dominant exposure",
        value: dominantExposureName,
        detail: dominantExposureWeight,
        tone: "amber"
      },
      {
        label: "Worst stress loss",
        value: formatPercent(worstStressLoss, "decimal"),
        detail: worstScenarioId,
        tone: toneForLoss(worstStressLoss)
      },
      {
        label: "Max drawdown",
        value: formatPercent(maxDrawdown, "decimal"),
        detail: "Portfolio X-Ray drawdown",
        tone: toneForLoss(maxDrawdown)
      },
      {
        label: "Offset coverage",
        value: hedgeCoverage !== undefined ? formatPercent(hedgeCoverage, "decimal") : "n/a",
        detail: hedgeArea,
        tone: hedgeCoverage !== undefined ? "amber" : "slate"
      }
    ],
    items
  };
}

function LockedEvidenceState() {
  return (
    <section className="pmri-card rounded-2xl p-6 md:p-8">
      <StatusBadge tone="amber">Evidence locked</StatusBadge>
      <h2 className="mt-4 text-2xl font-semibold tracking-[-0.02em] text-pmri-text">
        Complete Portfolio Input first to unlock Evidence.
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-pmri-muted">
        Run a real portfolio diagnosis first. Evidence will then be filled from Portfolio X-Ray and Stress Test Lab.
      </p>
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-6 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-pmri-blueSoft"
      >
        Go to Portfolio Input
      </Link>
    </section>
  );
}

function MissingRawEvidenceState() {
  return (
    <section className="pmri-card rounded-2xl border-pmri-risk/30 p-6 md:p-8">
      <StatusBadge tone="red">Real run incomplete</StatusBadge>
      <h2 className="mt-4 text-2xl font-semibold tracking-[-0.02em] text-pmri-text">
        Evidence summary is not available for this completed review.
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-pmri-muted">
        The browser keeps compact summaries instead of full raw JSON. Please rerun Portfolio Input if this older saved review has no compact evidence summary.
      </p>
      <Link
        href="/portfolio-input"
        className="pmri-focus mt-6 inline-flex rounded-full border border-pmri-blue/50 bg-pmri-blue px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-pmri-blueSoft"
      >
        Rerun Portfolio Input
      </Link>
    </section>
  );
}

function EvidencePageContent() {
  const { activeReview, hydrated } = useReviewState();
  const searchParams = useSearchParams();
  const sampleMode = searchParams.get("sample") === "1";
  const completedRealReview = Boolean(
    activeReview?.submitted
    && activeReview.runMode === "real_run"
    && activeReview.runStatus === "completed"
    && activeReview.reviewSummary
  );
  const realEvidence = completedRealReview ? buildRealEvidence(activeReview) ?? activeReview?.reviewSummary?.evidence ?? null : null;
  const payload = realEvidence ?? (sampleMode ? sampleEvidence : null);
  const stateLabel = realEvidence ? "Real run" : sampleMode ? "Sample fallback" : "Evidence locked";

  return (
    <div>
      <PageHeader
        kicker="Step 03 / Evidence"
        title="Evidence Center"
        description="Key X-Ray and stress evidence for the current portfolio, before any candidate or verdict."
      >
        <StatusBadge tone={realEvidence ? "green" : sampleMode ? "amber" : "slate"}>{stateLabel}</StatusBadge>
      </PageHeader>
      {!hydrated ? null : payload ? (
        <EvidenceCenter {...payload} />
      ) : completedRealReview ? (
        <MissingRawEvidenceState />
      ) : (
        <LockedEvidenceState />
      )}
    </div>
  );
}

export default function EvidencePage() {
  return (
    <Suspense fallback={null}>
      <EvidencePageContent />
    </Suspense>
  );
}
