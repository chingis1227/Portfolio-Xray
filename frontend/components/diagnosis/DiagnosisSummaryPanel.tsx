import Link from "next/link";
import type { Metric } from "@/lib/types";
import type { XRaySummary } from "@/lib/reviewState";
import {
  evidenceQualityLabel,
  evidenceTone,
  normalizeDisplayLabel,
  normalizeDisplaySentence,
  riskSeverityLabel,
  riskSeverityTone
} from "@/lib/displayLabels";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  CompositionPanel,
  DiagnosisSectionNav,
  FactorExposurePanel,
  HiddenRiskAlertsGrid,
  RiskBudgetPanel,
  RiskProfilePanel,
  SectionHeader,
  WeaknessMapGrid
} from "@/components/diagnosis/PortfolioXRayBlocks";

type DiagnosisSummaryPanelProps = {
  status: string;
  headline: string;
  evidenceQuality: string;
  nextStep: string;
  boundaryNote: string;
  drivers: string[];
  metrics: Metric[];
  xraySummary?: XRaySummary;
};

function clientSafeNote(note: string) {
  return normalizeDisplaySentence(note, "Supporting evidence is unavailable.");
}

function isUserRelevantLimitation(note: string) {
  const normalized = note.toLowerCase();
  if (normalized.includes("normalized for product contract")) return false;
  if (normalized.includes("factor names normalized")) return false;
  if (normalized.includes("usd->usd") || normalized.includes("vix->")) return false;
  return true;
}

function findMetric(metrics: Metric[], label: string) {
  return metrics.find((metric) => metric.label.toLowerCase() === label.toLowerCase());
}

function metricText(metric?: Metric, fallback = "Unavailable") {
  if (!metric) return fallback;
  const detail = metric.detail && metric.detail !== "n/a" ? ` ${metric.detail}` : "";
  return normalizeDisplayLabel(`${metric.value}${detail}`, fallback);
}

function parsePercent(value?: string) {
  if (!value) return null;
  const parsed = Number(value.replace("%", "").trim());
  return Number.isFinite(parsed) ? parsed : null;
}

function concentrationSeverity(value?: string) {
  const parsed = parsePercent(value);
  if (parsed === null) return "Unavailable";
  if (parsed >= 65) return "High risk";
  if (parsed >= 50) return "Medium risk";
  return "Low risk";
}

function mainDiagnosis(headline: string, xraySummary?: XRaySummary) {
  const metrics = xraySummary?.snapshotCards ?? [];
  const exposure = findMetric(metrics, "Dominant exposure")?.value;
  const top3 = parsePercent(findMetric(metrics, "Top 3 concentration")?.value);

  if (exposure && top3 !== null) {
    const concentrationText = top3 >= 50 ? "and concentrated in the top holdings" : "with capital spread across the leading holdings";
    return `The portfolio is ${normalizeDisplayLabel(exposure).toLowerCase()}-led ${concentrationText}.`;
  }

  return clientSafeNote(headline);
}

function primaryEvidence(xraySummary?: XRaySummary) {
  const metrics = xraySummary?.snapshotCards ?? [];
  const top3 = findMetric(metrics, "Top 3 concentration");
  const dominant = findMetric(metrics, "Dominant exposure");
  const topHolding = findMetric(metrics, "Top holding");
  const weakness = findMetric(metrics, "Worst pre-stress weakness") ?? findMetric(metrics, "Primary weakness");

  return [
    top3 ? `Top 3 holdings: ${normalizeDisplayLabel(top3.value)}` : "",
    dominant ? `Dominant exposure: ${metricText(dominant)}` : "",
    topHolding ? `Largest holding: ${normalizeDisplayLabel(topHolding.value)}` : "",
    weakness ? `Main pre-stress weakness: ${normalizeDisplayLabel(weakness.value)}` : ""
  ].filter(Boolean);
}

function nextReviewStep(nextStep: string, xraySummary?: XRaySummary) {
  const weakness = findMetric(xraySummary?.snapshotCards ?? [], "Worst pre-stress weakness")?.value;
  if (weakness && weakness !== "n/a") {
    const weaknessLabel = normalizeDisplayLabel(weakness).toLowerCase();
    const pairedStress = weaknessLabel.includes("severe recession") ? "equity sell-off" : "severe recession";
    return `Review stress evidence for ${weaknessLabel} and ${pairedStress} before testing a candidate.`;
  }
  return clientSafeNote(nextStep);
}

function dataCoverageLabel(evidenceQuality: string) {
  const quality = evidenceQualityLabel(evidenceQuality);
  if (quality === "Strong evidence") return "Strong";
  if (quality === "Moderate evidence") return "Moderate";
  if (quality === "Limited evidence") return "Limited";
  return "Insufficient data";
}

function DiagnosisHero({
  headline,
  evidenceQuality,
  nextStep,
  xraySummary
}: Pick<DiagnosisSummaryPanelProps, "headline" | "evidenceQuality" | "nextStep" | "boundaryNote"> & { xraySummary?: XRaySummary }) {
  const evidence = primaryEvidence(xraySummary);
  const quality = evidenceQualityLabel(evidenceQuality);

  return (
    <section className="pmri-card pmri-animated-border-panel pmri-section-reveal relative overflow-hidden rounded-3xl p-5 md:p-6">
      <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-pmri-blue/[0.04] blur-3xl" aria-hidden="true" />
      <div className="relative">
        <div className="flex flex-wrap gap-2">
          <StatusBadge tone="slate">Current portfolio review</StatusBadge>
          <StatusBadge tone={evidenceTone(quality)}>Data coverage: {dataCoverageLabel(quality)}</StatusBadge>
          <StatusBadge tone="slate">Candidate not tested</StatusBadge>
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <p className="pmri-label text-pmri-text2">Executive diagnosis</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-pmri-text md:text-3xl">Main diagnosis</h2>
            <p className="mt-3 max-w-3xl text-base leading-7 text-pmri-text2">{mainDiagnosis(headline, xraySummary)}</p>
          </div>

          <div className="rounded-2xl border border-pmri-border/60 bg-white/[0.024] p-4">
            <h3 className="text-sm font-semibold text-pmri-text">Primary evidence</h3>
            <div className="mt-3 space-y-2">
              {(evidence.length ? evidence : ["Primary evidence is unavailable in the compact review."]).map((item) => (
                <p key={item} className="flex gap-2 text-sm leading-6 text-pmri-text2">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-pmri-blueSoft/70" aria-hidden="true" />
                  <span>{clientSafeNote(item)}</span>
                </p>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl border border-pmri-border/55 bg-white/[0.02] p-4">
            <p className="pmri-label text-pmri-text2">Next review step</p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">{nextReviewStep(nextStep, xraySummary)}</p>
          </div>
          <div className="rounded-2xl border border-pmri-border/55 bg-white/[0.02] p-4">
            <p className="pmri-label text-pmri-text2">Decision boundary</p>
            <p className="mt-2 text-sm leading-6 text-pmri-text2">This is a diagnostic review of the current portfolio, not a rebalance recommendation.</p>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/evidence" className="pmri-focus pmri-primary-action rounded-full px-5 py-2.5 text-sm font-medium transition">
            Review supporting evidence
          </Link>
          <Link href="/hypothesis" className="pmri-focus rounded-full border border-pmri-border bg-white/[0.035] px-5 py-2.5 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/45 hover:text-pmri-text">
            Test a candidate hypothesis
          </Link>
        </div>
      </div>
    </section>
  );
}

type SummaryCard = {
  title: string;
  value: string;
  explanation: string;
  badge?: string;
};

function summaryCards(xraySummary: XRaySummary | undefined, fallbackMetrics: Metric[]): SummaryCard[] {
  const metrics = xraySummary?.snapshotCards?.length ? xraySummary.snapshotCards : fallbackMetrics;
  const top3 = findMetric(metrics, "Top 3 concentration");
  const exposure = findMetric(metrics, "Dominant exposure") ?? findMetric(metrics, "Equity sleeve");
  const drawdown = findMetric(metrics, "Max drawdown");
  const weakness = findMetric(metrics, "Worst pre-stress weakness") ?? findMetric(metrics, "Primary weakness");
  const top3Severity = concentrationSeverity(top3?.value);

  return [
    {
      title: "Capital concentration",
      value: top3 ? `Top 3 = ${normalizeDisplayLabel(top3.value)}` : "Unavailable",
      explanation: "The largest holdings dominate capital allocation.",
      badge: top3Severity
    },
    {
      title: "Economic exposure",
      value: exposure ? metricText(exposure) : "Unavailable",
      explanation: "The portfolio is primarily exposed to the dominant economic risk sleeve.",
      badge: exposure?.tone === "amber" || exposure?.tone === "red" ? "Medium risk" : "Strong evidence"
    },
    {
      title: "Risk behavior",
      value: drawdown ? normalizeDisplayLabel(drawdown.value) : "Unavailable",
      explanation: "The portfolio has experienced material downside in the diagnostic window.",
      badge: drawdown?.tone === "red" ? "High risk" : drawdown?.tone === "amber" ? "Medium risk" : "Low risk"
    },
    {
      title: "Main pre-stress weakness",
      value: weakness ? normalizeDisplayLabel(weakness.value) : "Unavailable",
      explanation: "This is the main weakness to review in Stress Lab before testing a candidate.",
      badge: weakness?.tone === "red" ? "High risk" : weakness?.tone === "amber" ? "Medium risk" : "Data limitation"
    }
  ];
}

function ExecutiveSummaryCard({ card }: { card: SummaryCard }) {
  const isEvidence = card.badge?.includes("evidence");
  const isReviewState = card.badge === "Data limitation";
  const tone = isReviewState ? "slate" : isEvidence ? evidenceTone(card.badge) : riskSeverityTone(card.badge);
  const badgeLabel = isReviewState ? "Data limitation" : isEvidence ? evidenceQualityLabel(card.badge) : riskSeverityLabel(card.badge);

  return (
    <article className="pmri-card pmri-interactive-card rounded-2xl p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-pmri-text">{card.title}</h3>
        {card.badge ? <StatusBadge tone={tone}>{badgeLabel}</StatusBadge> : null}
      </div>
      <p className="data-figure mt-5 text-2xl font-medium text-pmri-text">{card.value}</p>
      <p className="mt-2 text-sm leading-6 text-pmri-text2">{card.explanation}</p>
    </article>
  );
}

export function DiagnosisSummaryPanel({
  headline,
  evidenceQuality,
  nextStep,
  drivers,
  metrics,
  xraySummary
}: DiagnosisSummaryPanelProps) {
  const visibleLimitations = (xraySummary?.unavailableNotes ?? []).filter(isUserRelevantLimitation);

  return (
    <div className="space-y-6">
      <DiagnosisHero
        headline={headline}
        evidenceQuality={evidenceQuality}
        nextStep={nextStep}
        boundaryNote="This is a diagnostic review of the current portfolio, not a rebalance recommendation."
        xraySummary={xraySummary}
      />

      <DiagnosisSectionNav />

      <section id="summary" className="pmri-card pmri-section-reveal scroll-mt-28 rounded-3xl p-5 [--pmri-reveal-delay:60ms] md:p-6">
        <SectionHeader
          eyebrow="Summary"
          title="What matters first"
          insight="Four decision-useful facts summarize capital concentration, economic exposure, risk behavior, and the main pre-stress weakness."
        />
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {summaryCards(xraySummary, metrics).map((card) => <ExecutiveSummaryCard key={card.title} card={card} />)}
        </div>
        {!xraySummary && drivers.length ? (
          <div className="mt-5 grid gap-3 md:grid-cols-3">
            {drivers.slice(0, 3).map((driver) => (
              <article key={driver} className="rounded-2xl border border-pmri-border/55 bg-white/[0.025] p-4">
                <p className="text-sm leading-6 text-pmri-text2">{clientSafeNote(driver)}</p>
              </article>
            ))}
          </div>
        ) : null}
      </section>

      <CompositionPanel xray={xraySummary} />
      <RiskProfilePanel xray={xraySummary} />
      <FactorExposurePanel xray={xraySummary} />
      <HiddenRiskAlertsGrid xray={xraySummary} />
      <RiskBudgetPanel xray={xraySummary} />
      <WeaknessMapGrid xray={xraySummary} />

      {visibleLimitations.length ? (
        <section className="pmri-boundary-note rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-pmri-text">Data limitations to review</h2>
          <div className="mt-3 grid gap-2">
            {visibleLimitations.map((note) => <p key={note} className="text-sm leading-6 text-pmri-text2">• {clientSafeNote(note)}</p>)}
          </div>
        </section>
      ) : null}

      <section className="pmri-card rounded-3xl p-5 md:p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="pmri-label">Next step</p>
            <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text">Review supporting evidence before testing a hypothesis</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-pmri-muted">
              Diagnosis explains the current portfolio. Evidence provides supporting data; a hypothesis tests one candidate idea without implying a recommendation.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/evidence" className="pmri-focus pmri-primary-action rounded-full px-5 py-2.5 text-sm font-medium transition">
              Review supporting evidence
            </Link>
            <Link href="/hypothesis" className="pmri-focus rounded-full border border-pmri-border bg-white/[0.035] px-5 py-2.5 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/45 hover:text-pmri-text">
              Test a candidate hypothesis
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
