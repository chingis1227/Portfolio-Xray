"use client";

import { type MouseEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { Metric, StatusTone } from "@/lib/types";
import type {
  XRayBreakdown,
  XRayFactor,
  XRayHoldingRow,
  XRayHiddenRiskAlert,
  XRayRiskContribution,
  XRaySummary,
  XRayWeaknessTile
} from "@/lib/reviewState";
import {
  evidenceQualityLabel,
  evidenceTone,
  normalizeDisplayLabel,
  normalizeDisplaySentence,
  riskSeverityLabel,
  riskSeverityTone
} from "@/lib/displayLabels";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreIndicator } from "@/components/ui/ScoreIndicator";

const CHART_COLORS = [
  "rgba(236,239,243,0.9)",
  "rgba(193,209,224,0.72)",
  "rgba(148,155,166,0.72)",
  "rgba(111,191,155,0.62)",
  "rgba(201,166,107,0.66)",
  "rgba(215,122,122,0.58)"
];

const softPanel = "rounded-2xl border border-pmri-border/60 bg-white/[0.026]";
const raisedPanel = "rounded-2xl border border-white/[0.07] bg-[rgba(23,24,27,0.78)] shadow-decision";

function cleanLabel(value?: string | number | null, fallback = "Unavailable") {
  return normalizeMetricText(normalizeDisplayLabel(value, fallback));
}

function formatEmbeddedPercent(value: string) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return value;
  return `${numeric.toFixed(2).replace(/\.0+$/, "")}%`;
}

function formatEmbeddedRatio(value: string) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(2) : value;
}

function normalizeMetricText(value: string) {
  return value
    .replace(/\b([+-]?\d+\.\d{2,})\s+percentage points\b/gi, (_match, number) => `${formatEmbeddedRatio(number)} percentage points`)
    .replace(/\b(-?\d+\.\d{3,})%/g, (_match, number) => formatEmbeddedPercent(number))
    .replace(/\b(-?0?\.\d+)\s+CAGR\b/gi, (_match, number) => `${formatEmbeddedPercent(String(Number(number) * 100))} CAGR`)
    .replace(/\bCAGR\s+(-?0?\.\d+)\b/gi, (_match, number) => `CAGR ${formatEmbeddedPercent(String(Number(number) * 100))}`)
    .replace(/\bannualized volatility\s+(-?0?\.\d+)\b/gi, (_match, number) => `annualized volatility ${formatEmbeddedPercent(String(Number(number) * 100))}`)
    .replace(/\bmaximum drawdown\s+(-?0?\.\d+)\b/gi, (_match, number) => `maximum drawdown ${formatEmbeddedPercent(String(Number(number) * 100))}`)
    .replace(/\bSharpe ratio\s+(-?\d+\.\d+)\b/gi, (_match, number) => `Sharpe ratio ${formatEmbeddedRatio(number)}`)
    .replace(/\bSortino\s+(-?\d+\.\d+)\b/gi, (_match, number) => `Sortino ${formatEmbeddedRatio(number)}`);
}

function sentence(value?: string | null, fallback = "Evidence limitation.") {
  return normalizeMetricText(normalizeDisplaySentence(value, fallback));
}

function pct(value?: number) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "Unavailable";
  const normalized = Math.abs(value) <= 1 ? value * 100 : value;
  return `${normalized.toFixed(1).replace(/\.0$/, "")}%`;
}

function numberText(value?: number) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "Unavailable";
  return value.toFixed(2).replace(/\.0+$/, "");
}

function severityTone(level?: string): StatusTone {
  return riskSeverityTone(level);
}

function severityLabel(level?: string) {
  return riskSeverityLabel(level);
}

function maxWeight(items: Array<{ weightPct?: number }>) {
  return Math.max(1, ...items.map((item) => Math.abs(item.weightPct ?? 0)));
}

function polarToCartesian(cx: number, cy: number, radius: number, angleInDegrees: number) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180;
  return {
    x: cx + (radius * Math.cos(angleInRadians)),
    y: cy + (radius * Math.sin(angleInRadians))
  };
}

function describeArc(cx: number, cy: number, radius: number, startAngle: number, endAngle: number) {
  const safeEndAngle = endAngle - startAngle >= 359.99 ? startAngle + 359.99 : endAngle;
  const start = polarToCartesian(cx, cy, radius, safeEndAngle);
  const end = polarToCartesian(cx, cy, radius, startAngle);
  const largeArcFlag = safeEndAngle - startAngle <= 180 ? "0" : "1";
  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
}

export function SectionHeader({ eyebrow, title, insight, action }: { eyebrow: string; title: string; insight: string; action?: string }) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="pmri-label text-pmri-text2">{cleanLabel(eyebrow)}</p>
        <h2 className="pmri-heading-section mt-2 text-2xl text-pmri-text md:text-3xl">{title}</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-pmri-text2">{sentence(insight)}</p>
      </div>
      {action ? (
        <Link href="/evidence" className="pmri-focus inline-flex w-fit rounded-full border border-pmri-borderSoft/55 bg-white/[0.035] px-4 py-2 text-sm font-medium text-pmri-text2 transition hover:border-pmri-blue/45 hover:text-pmri-text">{action}</Link>
      ) : null}
    </div>
  );
}

function UnavailableState({ title = "Insufficient evidence", message }: { title?: string; message: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-pmri-borderSoft/55 bg-white/[0.018] p-5">
      <StatusBadge tone="slate">Unavailable</StatusBadge>
      <h3 className="mt-3 text-sm font-semibold text-pmri-text">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-pmri-text2">{sentence(message)}</p>
    </div>
  );
}

function TooltipHint({ label, text }: { label: string; text: string }) {
  return <span title={text} data-tooltip={text} tabIndex={0} className="pmri-info-hint inline-flex h-5 w-5 cursor-help items-center justify-center rounded-full border border-pmri-borderSoft/45 bg-white/[0.035] text-[11px] font-semibold text-pmri-text2" aria-label={`${label}: ${text}`}>i</span>;
}

function EvidenceChip({ children, href = "/evidence" }: { children: string; href?: string }) {
  return <Link href={href} className="pmri-focus pmri-evidence-chip inline-flex rounded-full border border-pmri-border/70 bg-white/[0.025] px-3 py-1.5 text-xs font-medium text-pmri-text2">{sentence(children)}</Link>;
}

function MiniFacts({ facts, limit = 5 }: { facts: string[]; limit?: number }) {
  const visible = facts.map((fact) => sentence(fact)).filter(Boolean).slice(0, limit);
  if (!visible.length) return <UnavailableState message="Key facts are unavailable for this module." />;
  return (
    <div className="grid gap-3">
      {visible.map((fact, index) => (
        <div key={`${fact}-${index}`} className="pmri-hover-panel flex gap-3 rounded-xl border border-pmri-border/55 bg-white/[0.024] p-3">
          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-pmri-blueSoft/75" aria-hidden="true" />
          <p className="text-sm font-normal leading-6 text-[#DDE6F0]">{fact}</p>
        </div>
      ))}
    </div>
  );
}

function findBreakdown(xray: XRaySummary, title: string) {
  return xray.composition.breakdowns.find((breakdown) => breakdown.title.toLowerCase() === title.toLowerCase());
}

function topBreakdownItem(breakdown?: XRayBreakdown) {
  return breakdown?.items.slice().sort((a, b) => b.weightPct - a.weightPct)[0];
}

function compositionInsight(xray?: XRaySummary) {
  if (!xray) return "Allocation breakdown unavailable because composition evidence is incomplete.";
  const assetClass = topBreakdownItem(findBreakdown(xray, "Asset class"));
  const mainFactor = topBreakdownItem(findBreakdown(xray, "Main risk factor"));
  if (assetClass && mainFactor) {
    return `Capital is weighted toward ${cleanLabel(assetClass.name)} (${pct(assetClass.weightPct)}), with main risk factor exposure at ${cleanLabel(mainFactor.name)} (${pct(mainFactor.weightPct)}).`;
  }
  return "Capital allocation and economic risk evidence are available for review.";
}

function DonutChart({ breakdown }: { breakdown?: XRayBreakdown }) {
  const items = breakdown?.items ?? [];
  const total = items.reduce((sum, item) => sum + Math.max(0, item.weightPct), 0) || 1;
  const topIndex = items.reduce((largestIndex, item, index, allItems) => item.weightPct > allItems[largestIndex].weightPct ? index : largestIndex, 0);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const activeIndex = hoveredIndex ?? topIndex;
  const activeItem = items[activeIndex] ?? items[topIndex];
  const segments = useMemo(() => {
    let cursor = 0;
    return items.map((item, index) => {
      const span = (Math.max(0, item.weightPct) / total) * 360;
      const segment = {
        item,
        index,
        start: cursor,
        end: cursor + span
      };
      cursor += span;
      return segment;
    });
  }, [items, total]);
  if (!breakdown?.items.length || !activeItem) return <UnavailableState message="Allocation donut unavailable because this exposure split is missing." />;
  return (
    <article className={`${raisedPanel} pmri-interactive-card p-5`}>
      <div className="flex items-center justify-between gap-3"><div><p className="pmri-label text-pmri-text2">Economic allocation</p><h3 className="mt-1 text-lg font-semibold text-pmri-text">{cleanLabel(breakdown.title)}</h3></div><StatusBadge tone="slate">Capital view</StatusBadge></div>
      <div className="mt-6 grid gap-5 sm:grid-cols-[220px_1fr] sm:items-center">
        <div
          className="relative mx-auto h-52 w-52"
          onMouseLeave={() => setHoveredIndex(null)}
          onBlur={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget)) setHoveredIndex(null);
          }}
        >
          <svg viewBox="0 0 220 220" role="img" aria-label={`${cleanLabel(breakdown.title)} allocation donut`} className="h-full w-full overflow-visible">
            <circle cx="110" cy="110" r="84" fill="none" stroke="rgba(255,255,255,0.055)" strokeWidth="24" />
            {segments.map((segment) => {
              const isActive = segment.index === activeIndex;
              const isDimmed = hoveredIndex !== null && !isActive;
              const color = CHART_COLORS[segment.index % CHART_COLORS.length];
              return (
                <path
                  key={`${breakdown.title}-${segment.item.name}`}
                  d={describeArc(110, 110, isActive ? 86 : 84, segment.start, segment.end)}
                  fill="none"
                  stroke={color}
                  strokeWidth={isActive ? 27 : 22}
                  strokeLinecap="butt"
                  className="pmri-donut-segment cursor-pointer outline-none"
                  style={{ opacity: isDimmed ? 0.34 : isActive ? 1 : 0.78 }}
                  tabIndex={0}
                  role="button"
                  aria-label={`${cleanLabel(segment.item.name)} ${pct(segment.item.weightPct)}`}
                  onMouseEnter={() => setHoveredIndex(segment.index)}
                  onFocus={() => setHoveredIndex(segment.index)}
                  onClick={() => setHoveredIndex(segment.index)}
                />
              );
            })}
          </svg>
          <div className="pointer-events-none absolute inset-8 rounded-full border border-white/[0.06] bg-pmri-surface shadow-inner" />
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center px-8 text-center">
            <p className="text-xs text-pmri-text2">{hoveredIndex === null ? "Largest sleeve" : "Selected sleeve"}</p>
            <p className="mt-1 max-w-32 truncate text-lg font-semibold text-pmri-text">{cleanLabel(activeItem.name)}</p>
            <p className="data-figure text-sm text-pmri-text2">{pct(activeItem.weightPct)}</p>
          </div>
        </div>
        <div className="pmri-linked-group space-y-2">
          {breakdown.items.slice(0, 6).map((item, index) => {
            const isActive = index === activeIndex;
            const isDimmed = hoveredIndex !== null && !isActive;
            return (
              <button
                key={`${breakdown.title}-${item.name}`}
                type="button"
                data-active={isActive}
                className="pmri-chart-legend-row pmri-focus flex w-full cursor-pointer items-center justify-between gap-3 rounded-xl border border-transparent px-2.5 py-2 text-left text-sm"
                style={{ opacity: isDimmed ? 0.48 : 1 }}
                onMouseEnter={() => setHoveredIndex(index)}
                onFocus={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
                onBlur={() => setHoveredIndex(null)}
              >
                <span className="flex min-w-0 items-center gap-2 text-pmri-text2">
                  <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: CHART_COLORS[index % CHART_COLORS.length] }} />
                  <span className="truncate">{cleanLabel(item.name)}</span>
                </span>
                <span className={`data-figure ${isActive ? "font-semibold text-pmri-text" : "text-pmri-text2"}`}>{pct(item.weightPct)}</span>
              </button>
            );
          })}
        </div>
      </div>
    </article>
  );
}

function StackedExposureBar({ breakdown, label }: { breakdown?: XRayBreakdown; label: string }) {
  const items = breakdown?.items ?? [];
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  if (!breakdown?.items.length) return <UnavailableState message={`${label} exposure split is unavailable.`} />;
  const total = items.reduce((sum, item) => sum + Math.max(0, item.weightPct), 0) || 1;
  return (
    <article className={`${softPanel} pmri-interactive-card p-4`} onMouseLeave={() => setActiveIndex(null)}>
      <div className="flex items-center justify-between gap-3"><h3 className="text-sm font-semibold text-pmri-text">{label}</h3><span className="text-xs text-pmri-text2">{breakdown.items.length} groups</span></div>
      <div className="mt-4 flex h-4 overflow-hidden rounded-full bg-white/[0.055]">
        {items.slice(0, 6).map((item, index) => {
          const isActive = index === activeIndex;
          const isDimmed = activeIndex !== null && !isActive;
          return (
            <div
              key={`${breakdown.title}-${item.name}`}
              title={`${cleanLabel(item.name)}: ${pct(item.weightPct)}`}
              className="pmri-bar-fill h-full min-w-[3px] cursor-pointer border-r border-black/25 last:border-r-0"
              style={{ width: `${(Math.max(0, item.weightPct) / total) * 100}%`, background: CHART_COLORS[index % CHART_COLORS.length], opacity: isDimmed ? 0.36 : 1 }}
              onMouseEnter={() => setActiveIndex(index)}
            />
          );
        })}
      </div>
      <div className="pmri-linked-group mt-4 grid gap-2">
        {items.slice(0, 4).map((item, index) => {
          const isActive = index === activeIndex;
          return (
            <button
              key={`${label}-${item.name}`}
              type="button"
              data-active={isActive}
              className="pmri-linked-chart-row pmri-focus flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-transparent px-2 py-1.5 text-left text-xs"
              onMouseEnter={() => setActiveIndex(index)}
              onFocus={() => setActiveIndex(index)}
              onBlur={() => setActiveIndex(null)}
            >
              <span className="flex min-w-0 items-center gap-2 text-pmri-text2"><span className="h-2 w-2 shrink-0 rounded-full" style={{ background: CHART_COLORS[index % CHART_COLORS.length] }} /><span className="truncate">{cleanLabel(item.name)}</span></span>
              <span className={`data-figure ${isActive ? "font-semibold text-pmri-text" : "text-pmri-text2"}`}>{pct(item.weightPct)}</span>
            </button>
          );
        })}
      </div>
    </article>
  );
}

function ExposureBars({ breakdown, title }: { breakdown?: XRayBreakdown; title: string }) {
  const items = breakdown?.items ?? [];
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  if (!breakdown?.items.length) return <UnavailableState message={`${title} evidence is unavailable.`} />;
  const max = maxWeight(items);
  return (
    <article className={`${softPanel} pmri-interactive-card p-4`} onMouseLeave={() => setActiveIndex(null)}>
      <h3 className="text-sm font-semibold text-pmri-text">{title}</h3>
      <div className="pmri-bar-group mt-4 space-y-2">
        {items.slice(0, 6).map((item, index) => {
          const isActive = index === activeIndex;
          return (
            <button
              key={`${title}-${item.name}`}
              type="button"
              data-active={isActive}
              className="pmri-interactive-bar-row pmri-focus w-full cursor-pointer rounded-xl border border-transparent px-2 py-2 text-left"
              onMouseEnter={() => setActiveIndex(index)}
              onFocus={() => setActiveIndex(index)}
              onBlur={() => setActiveIndex(null)}
            >
              <div className="flex items-center justify-between gap-3 text-xs"><span className={`truncate ${isActive ? "font-medium text-pmri-text" : "text-pmri-text2"}`}>{cleanLabel(item.name)}</span><span className={`data-figure ${isActive ? "font-semibold text-pmri-text" : "text-pmri-text2"}`}>{pct(item.weightPct)}</span></div>
              <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-white/[0.055]"><div className="pmri-bar-fill h-full rounded-full" style={{ width: `${Math.min(100, Math.max(4, (Math.abs(item.weightPct) / max) * 100))}%`, background: CHART_COLORS[index % CHART_COLORS.length] }} /></div>
            </button>
          );
        })}
      </div>
    </article>
  );
}

function HoldingsTable({ holdings }: { holdings: XRayHoldingRow[] }) {
  if (!holdings.length) return <UnavailableState message="Holdings table unavailable because current portfolio holdings were not stored in the review state." />;

  return (
    <article className={`${raisedPanel} p-5`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="pmri-label text-pmri-text2">Capital allocation breakdown</p>
          <h3 className="mt-1 text-lg font-semibold text-pmri-text">Holdings table</h3>
        </div>
        <StatusBadge tone="slate">Current portfolio review</StatusBadge>
      </div>
      <div className="mt-5 overflow-x-auto">
        <table className="min-w-[720px] w-full border-separate border-spacing-0 text-left text-sm">
          <thead>
            <tr className="text-xs uppercase tracking-[0.14em] text-pmri-muted">
              <th className="border-b border-pmri-border/70 px-3 py-3 font-medium">Holding</th>
              <th className="border-b border-pmri-border/70 px-3 py-3 font-medium">Weight</th>
              <th className="border-b border-pmri-border/70 px-3 py-3 font-medium">Asset class</th>
              <th className="border-b border-pmri-border/70 px-3 py-3 font-medium">Risk role</th>
              <th className="border-b border-pmri-border/70 px-3 py-3 font-medium">Main risk factor</th>
            </tr>
          </thead>
          <tbody>
            {holdings.slice(0, 8).map((holding) => (
              <tr key={holding.holding} className="pmri-table-row">
                <td className="border-b border-pmri-border/35 px-3 py-3 font-medium text-pmri-text">{cleanLabel(holding.holding)}</td>
                <td className="data-figure border-b border-pmri-border/35 px-3 py-3 text-pmri-text2">{pct(holding.weightPct)}</td>
                <td className="border-b border-pmri-border/35 px-3 py-3 text-pmri-text2">{cleanLabel(holding.assetClass)}</td>
                <td className="border-b border-pmri-border/35 px-3 py-3 text-pmri-text2">{cleanLabel(holding.riskRole)}</td>
                <td className="border-b border-pmri-border/35 px-3 py-3 text-pmri-text2">{cleanLabel(holding.mainRiskFactor)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

function ConcentrationCards({ xray }: { xray: XRaySummary }) {
  const flags = xray.composition.flags.slice(0, 4);
  if (!flags.length) return <UnavailableState message="No concentration signals were available for this review." />;
  return <div className="grid gap-3 sm:grid-cols-2">{flags.map((flag) => { const tone = severityTone(flag.severity); return <article key={`${flag.label}-${flag.message}`} className={`${softPanel} pmri-interactive-card p-4`}><div className="flex items-start justify-between gap-3"><h3 className="text-sm font-semibold text-pmri-text">{cleanLabel(flag.label)}</h3><StatusBadge tone={tone}>{severityLabel(flag.severity)}</StatusBadge></div><p className="mt-3 text-sm leading-6 text-pmri-text2">{sentence(flag.message)}</p></article>; })}</div>;
}

export function CompositionPanel({ xray }: { xray?: XRaySummary }) {
  return (
    <section id="composition" className="pmri-card pmri-animated-border-panel pmri-section-reveal scroll-mt-28 rounded-3xl p-5 [--pmri-reveal-delay:90ms] md:p-6">
      <SectionHeader eyebrow="Portfolio composition" title="What the portfolio owns economically" insight={compositionInsight(xray)} action="Review supporting evidence" />
      {!xray ? <div className="mt-5"><UnavailableState message="Allocation breakdown unavailable because taxonomy data is incomplete or not stored in the current review." /></div> : (
        <div className="mt-6 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <DonutChart breakdown={findBreakdown(xray, "Asset class")} />
          <div className="grid gap-4"><MiniFacts facts={xray.composition.keyFacts} limit={4} /><article className={`${softPanel} p-4`}><h3 className="text-sm font-semibold text-pmri-text">Capital view vs economic risk view</h3><p className="mt-2 text-sm leading-6 text-pmri-text2">Capital weights show where money is allocated. Economic risk view groups those holdings by risk role, region, currency, and main factor so hidden concentration is easier to review.</p></article><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2"><StackedExposureBar breakdown={findBreakdown(xray, "Region")} label="Region exposure" /><StackedExposureBar breakdown={findBreakdown(xray, "Currency")} label="Currency exposure" /></div></div>
          <div className="grid gap-4 xl:col-span-2 lg:grid-cols-[1fr_1fr]"><ExposureBars breakdown={findBreakdown(xray, "Risk role")} title="Risk role exposure" /><ExposureBars breakdown={findBreakdown(xray, "Main risk factor")} title="Main risk factor exposure" /></div>
          <div className="xl:col-span-2"><HoldingsTable holdings={xray.composition.holdings ?? []} /></div>
          <div className="xl:col-span-2"><ConcentrationCards xray={xray} /></div>
        </div>
      )}
    </section>
  );
}

function DrawdownUnavailablePanel({ facts }: { facts: string[] }) {
  return (
    <article className={`${raisedPanel} pmri-interactive-card relative overflow-hidden p-5`}>
      <div className="absolute inset-x-5 top-20 h-px bg-white/[0.05]" aria-hidden="true" />
      <div className="absolute inset-x-5 top-32 h-px bg-white/[0.04]" aria-hidden="true" />
      <div className="absolute inset-x-5 top-44 h-px bg-white/[0.035]" aria-hidden="true" />
      <div className="relative">
        <div className="flex items-start justify-between gap-3"><div><p className="pmri-label text-pmri-text2">Drawdown / rolling behavior</p><h3 className="mt-1 text-lg font-semibold text-pmri-text">Rolling chart not shown</h3></div><StatusBadge tone="slate">Chart unavailable</StatusBadge></div>
        <div className="mt-8 h-40 rounded-2xl border border-dashed border-pmri-borderSoft/45 bg-black/10 p-4">
          <p className="max-w-sm text-sm leading-6 text-pmri-text2">The current compact review includes risk metrics, but not enough time-series points to draw a client-safe chart here.</p>
          <div className="mt-5 flex flex-wrap gap-2"><EvidenceChip>Review drawdown evidence</EvidenceChip><EvidenceChip>Check rolling volatility</EvidenceChip></div>
        </div>
        <div className="mt-4"><MiniFacts facts={facts} limit={3} /></div>
      </div>
    </article>
  );
}

const riskMetricGroups: Array<{ title: string; labels: string[]; interpretation: string }> = [
  { title: "Return profile", labels: ["CAGR"], interpretation: "Realized growth over the primary diagnostic window." },
  { title: "Risk level", labels: ["Annual volatility", "Vol of vol"], interpretation: "How much total portfolio movement the user has lived through." },
  { title: "Downside pain", labels: ["Max drawdown", "Time to recovery", "Time underwater", "Drawdowns >10%"], interpretation: "How severe and persistent past losses were in this review window." },
  { title: "Tail risk", labels: ["VaR 95", "ES 95", "Skewness", "Kurtosis"], interpretation: "How bad-loss days and return-shape evidence look historically." },
  { title: "Market dependence", labels: ["Beta", "Downside beta", "Upside beta", "Benchmark correlation"], interpretation: "How closely the portfolio moves with the benchmark, especially in down markets." },
  { title: "Risk-adjusted efficiency", labels: ["Sharpe", "Sortino", "Treynor"], interpretation: "Downside-adjusted efficiency can differ from total-volatility efficiency." }
];

function metricByLabel(metrics: Metric[], label: string) {
  return metrics.find((metric) => metric.label.toLowerCase() === label.toLowerCase());
}

function RiskMetricGroupCard({ title, metrics, interpretation }: { title: string; metrics: Metric[]; interpretation: string }) {
  if (!metrics.length) return null;
  const mainMetric = metrics[0];
  const tone = title === "Downside pain" || title === "Tail risk" || title === "Market dependence"
    ? mainMetric.tone
    : "slate";

  return (
    <article className={`${softPanel} pmri-interactive-card p-4`}>
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-pmri-text">{title}</h3>
        {tone ? <StatusBadge tone={tone}>{tone === "red" || tone === "amber" || tone === "green" ? severityLabel(tone === "red" ? "high" : tone === "amber" ? "medium" : "low") : "Strong evidence"}</StatusBadge> : null}
      </div>
      <div className="mt-4 grid gap-3">
        {metrics.map((metric) => (
          <div key={metric.label} className="flex items-baseline justify-between gap-3 rounded-xl border border-pmri-border/45 bg-white/[0.018] px-3 py-2.5">
            <span className="text-xs font-medium text-pmri-text2">{cleanLabel(metric.label)}</span>
            <span className="data-figure text-sm font-semibold text-pmri-text">{cleanLabel(metric.value)}</span>
          </div>
        ))}
      </div>
      <p className="mt-3 text-sm leading-6 text-pmri-text2">{interpretation}</p>
    </article>
  );
}

function RiskProfileGroups({ metrics }: { metrics: Metric[] }) {
  const visibleGroups = riskMetricGroups
    .map((group) => ({
      ...group,
      metrics: group.labels.map((label) => metricByLabel(metrics, label)).filter((metric): metric is Metric => Boolean(metric))
    }))
    .filter((group) => group.metrics.length);

  if (!visibleGroups.length) return <UnavailableState message="Risk metrics are unavailable for this review." />;

  return (
    <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visibleGroups.map((group) => (
          <RiskMetricGroupCard key={group.title} title={group.title} metrics={group.metrics} interpretation={group.interpretation} />
        ))}
      </div>
      <details className="mt-5 rounded-2xl border border-pmri-border/60 bg-white/[0.02] p-4">
        <summary className="pmri-focus cursor-pointer list-none rounded-xl text-sm font-medium text-pmri-text2 transition hover:text-pmri-text">View full diagnostics</summary>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {metrics.map((metric) => <MetricCard key={metric.label} metric={{ ...metric, detail: sentence(metric.detail ?? "") }} />)}
        </div>
      </details>
      <div className="mt-4 rounded-2xl border border-dashed border-pmri-borderSoft/50 bg-white/[0.018] p-4">
        <StatusBadge tone="slate">Data limitation</StatusBadge>
        <p className="mt-3 text-sm leading-6 text-pmri-text2">Rolling charts are not shown in this compact diagnosis view. Available point-in-time risk metrics are shown above; review supporting evidence for time-series detail when available.</p>
      </div>
    </>
  );
}

export function RiskProfilePanel({ xray }: { xray?: XRaySummary }) {
  return (
    <section id="risk-profile" className="pmri-card pmri-section-reveal scroll-mt-28 rounded-3xl p-5 [--pmri-reveal-delay:120ms] md:p-6">
      <SectionHeader eyebrow="Risk profile" title="How the current portfolio behaves" insight={xray?.riskProfile.insight ?? "Risk profile unavailable because portfolio metrics were not available for this review."} action="Review supporting evidence" />
      {!xray ? <div className="mt-5"><UnavailableState message="Risk diagnostics unavailable because metric evidence is missing." /></div> : (
        <div className="mt-6"><RiskProfileGroups metrics={xray.riskProfile.metrics} /></div>
      )}
    </section>
  );
}

function FactorCard({ factor, maxValue }: { factor: XRayFactor; maxValue: number }) {
  const magnitude = Math.max(Math.abs(factor.beta ?? 0), Math.abs(factor.contributionPct ?? 0));
  const width = magnitude > 0 ? Math.min(100, Math.max(5, (magnitude / maxValue) * 100)) : 5;
  const evidence = evidenceQualityLabel(factor.confidence);
  const exposure = factorExposureLevel(factor);
  return (
    <article className={`${softPanel} pmri-interactive-card p-4`}>
      <div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="text-sm font-semibold text-pmri-text">{cleanLabel(factor.factor)}</p><p className="mt-1 text-xs text-pmri-text2">Exposure level: {exposure}</p></div><StatusBadge tone={evidenceTone(factor.confidence)}>{evidence}</StatusBadge></div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/[0.055]"><div className="pmri-bar-fill h-full rounded-full bg-pmri-blueSoft/75" style={{ width: `${width}%` }} /></div>
      <dl className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-xl border border-pmri-border/45 bg-white/[0.018] p-3"><dt className="text-pmri-muted">Sensitivity</dt><dd className="data-figure mt-1 text-pmri-text">{numberText(factor.beta)}</dd></div>
        <div className="rounded-xl border border-pmri-border/45 bg-white/[0.018] p-3"><dt className="text-pmri-muted">Contribution</dt><dd className="data-figure mt-1 text-pmri-text">{pct(factor.contributionPct)}</dd></div>
      </dl>
      <p className="mt-3 text-sm leading-6 text-pmri-text2">{factorInterpretation(factor)}</p>
    </article>
  );
}

function factorExposureLevel(factor: XRayFactor) {
  const contribution = Math.abs(factor.contributionPct ?? 0);
  const beta = Math.abs(factor.beta ?? 0);
  if (factor.beta === undefined && factor.contributionPct === undefined) return "Unavailable";
  if (contribution >= 50 || beta >= 0.6) return "High";
  if (contribution >= 10 || beta >= 0.25) return "Medium";
  return "Low";
}

function factorInterpretation(factor: XRayFactor) {
  const name = cleanLabel(factor.factor);
  const exposure = factorExposureLevel(factor).toLowerCase();
  const contribution = factor.contributionPct ?? 0;

  if (name === "Equity" && (exposure === "high" || contribution >= 50)) {
    return "Equity is the dominant factor explaining portfolio behavior in this review.";
  }
  if (name === "Interest-rate sensitivity") {
    return contribution >= 10
      ? "Rate sensitivity is a visible driver and should be reviewed alongside bond exposure."
      : "The portfolio has visible rate sensitivity, but other factors explain more of overall behavior.";
  }
  if (name === "USD") {
    return contribution >= 10
      ? "USD sensitivity is material enough to review as part of currency exposure."
      : "USD sensitivity is present but not a dominant driver in this review.";
  }
  if (name === "Commodity") {
    return contribution >= 10
      ? "Commodity exposure is a visible diversifier and stress area to review."
      : "Commodity sensitivity is visible but not a main behavior driver here.";
  }
  if (exposure === "unavailable") return "Factor evidence is unavailable for this review.";
  if (exposure === "high") return `${name} is a major behavior driver in the current portfolio evidence.`;
  if (exposure === "medium") return `${name} is visible, but it is not the only driver of portfolio behavior.`;
  return `${name} sensitivity is present but limited in this review.`;
}

function FactorMatrix({ factors }: { factors: XRayFactor[] }) {
  const visibleFactors = factors.filter((factor) => factor.beta !== undefined || factor.contributionPct !== undefined);
  if (!visibleFactors.length) return <UnavailableState message="Market factor exposure unavailable: insufficient factor evidence." />;
  const maxValue = Math.max(0.01, ...visibleFactors.map((factor) => Math.max(Math.abs(factor.beta ?? 0), Math.abs(factor.contributionPct ?? 0))));
  return <div className="grid gap-3 md:grid-cols-2">{visibleFactors.slice(0, 8).map((factor) => <FactorCard key={factor.factor} factor={factor} maxValue={maxValue} />)}</div>;
}

export function FactorExposurePanel({ xray }: { xray?: XRaySummary }) {
  return (
    <section id="factors" className="pmri-card pmri-section-reveal scroll-mt-28 rounded-3xl p-5 [--pmri-reveal-delay:150ms] md:p-6">
      <SectionHeader eyebrow="Market factor exposure" title="Which market forces may drive returns" insight={xray?.factors.insight ?? "Factor exposure unavailable: insufficient factor evidence."} action="Review supporting evidence" />
      {!xray ? <div className="mt-5"><UnavailableState message="Factor exposure unavailable: insufficient factor data." /></div> : (
        <div className="mt-6 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
          <article className={`${raisedPanel} pmri-interactive-card p-5`}>
            <div className="flex items-center justify-between gap-3"><h3 className="text-sm font-semibold text-pmri-text">Top factor drivers</h3><StatusBadge tone="slate">Top 3 drivers</StatusBadge></div>
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-[620px] w-full border-separate border-spacing-0 text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase tracking-[0.14em] text-pmri-muted">
                    <th className="border-b border-pmri-border/70 px-3 py-3 font-medium">Rank</th>
                    <th className="border-b border-pmri-border/70 px-3 py-3 font-medium">Factor</th>
                    <th className="border-b border-pmri-border/70 px-3 py-3 font-medium">Sensitivity</th>
                    <th className="border-b border-pmri-border/70 px-3 py-3 font-medium">Contribution</th>
                    <th className="border-b border-pmri-border/70 px-3 py-3 font-medium">Evidence quality</th>
                  </tr>
                </thead>
                <tbody>
                  {(xray.factors.topFactors.length ? xray.factors.topFactors : xray.factors.factorCards.slice(0, 3)).slice(0, 3).map((factor, index) => (
                    <tr key={`${factor.factor}-${index}`} className="pmri-table-row">
                      <td className="border-b border-pmri-border/35 px-3 py-3 text-pmri-text2">{index + 1}</td>
                      <td className="border-b border-pmri-border/35 px-3 py-3 font-medium text-pmri-text">{cleanLabel(factor.factor)}</td>
                      <td className="data-figure border-b border-pmri-border/35 px-3 py-3 text-pmri-text2">{numberText(factor.beta)}</td>
                      <td className="data-figure border-b border-pmri-border/35 px-3 py-3 text-pmri-text2">{pct(factor.contributionPct)}</td>
                      <td className="border-b border-pmri-border/35 px-3 py-3"><StatusBadge tone={evidenceTone(factor.confidence)}>{evidenceQualityLabel(factor.confidence)}</StatusBadge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 space-y-2">{(xray.factors.topFactors.length ? xray.factors.topFactors : xray.factors.factorCards.slice(0, 3)).slice(0, 3).map((factor, index) => <p key={`${factor.factor}-interpretation-${index}`} className="text-sm leading-6 text-pmri-text2"><span className="font-medium text-pmri-text">{cleanLabel(factor.factor)}:</span> {factorInterpretation(factor)}</p>)}</div>
            {xray.factors.caveat ? <p className="mt-4 rounded-xl border border-pmri-border/55 bg-white/[0.02] p-3 text-xs leading-5 text-pmri-text2">{sentence(xray.factors.caveat, "Some factor evidence is limited and should be reviewed before interpretation.")}</p> : null}
          </article>
          <FactorMatrix factors={xray.factors.factorCards} />
        </div>
      )}
    </section>
  );
}

function HiddenAlertCard({ alert }: { alert: XRayHiddenRiskAlert }) {
  const tone = severityTone(alert.level);
  const evidence = alert.evidence.length ? alert.evidence : ["Insufficient evidence for this alert."];
  const evidenceLabel = evidenceQualityLabel(alert.confidence);
  return (
    <article className={`${softPanel} pmri-interactive-card p-4`}>
      <div className="flex items-start justify-between gap-3"><div><h3 className="text-base font-semibold text-pmri-text">{cleanLabel(alert.title)}</h3><div className="mt-2 flex flex-wrap gap-2"><StatusBadge tone={tone}>Risk level: {severityLabel(alert.level)}</StatusBadge><StatusBadge tone={evidenceTone(alert.confidence)}>Evidence quality: {evidenceLabel}</StatusBadge></div></div>{alert.score !== undefined ? <ScoreIndicator score={alert.score} tone={tone} size="xs" /> : null}</div>
      <div className="mt-4 grid gap-3">
        <div>
          <p className="text-xs font-medium text-pmri-text">What was detected</p>
          <p className="mt-1 text-sm leading-6 text-pmri-text2">{hiddenDetectedText(alert)}</p>
        </div>
        <div className="rounded-xl border border-pmri-border/45 bg-black/10 p-3">
          <p className="text-xs font-medium text-pmri-text">Why it matters</p>
          <p className="mt-1 text-xs leading-5 text-pmri-text2">{hiddenWhyItMatters(alert)}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-pmri-text">Key evidence</p>
          <div className="mt-2 space-y-1.5">{evidence.slice(0, 3).map((item) => <p key={item} className="text-xs leading-5 text-pmri-text2">• {sentence(item)}</p>)}</div>
        </div>
      </div>
      <div className="mt-4"><p className="text-xs font-medium text-pmri-text">Linked assets</p><div className="mt-2 flex flex-wrap gap-2">{alert.linkedAssets.length ? alert.linkedAssets.slice(0, 3).map((asset) => <StatusBadge key={asset} tone="slate">{cleanLabel(asset)}</StatusBadge>) : <StatusBadge tone="slate">Assets unavailable</StatusBadge>}</div></div>
      <div className="mt-4"><p className="text-xs font-medium text-pmri-text">Next stress tests</p><div className="mt-2 flex flex-wrap gap-2">{(alert.nextTests.length ? alert.nextTests : ["Stress review needed"]).slice(0, 3).map((test) => <EvidenceChip key={test}>{test}</EvidenceChip>)}</div></div>
    </article>
  );
}

function hiddenDetectedText(alert: XRayHiddenRiskAlert) {
  if (alert.id === "hidden_equity_beta") return "The portfolio may behave more equity-like than its allocation labels suggest.";
  if (alert.id === "duration_concentration") return "A meaningful part of portfolio behavior may come from rate-sensitive holdings.";
  if (alert.id === "credit_liquidity_risk") return "Some holdings may carry credit or liquidity risk that is not obvious from headline allocation.";
  if (alert.id === "correlation_concentration") return "Several holdings may move together in stress rather than diversify each other.";
  if (alert.id === "weak_hedge_behavior") return "Defensive sleeves may not fully offset losses in the main stress areas.";
  if (alert.id === "tail_risk") return "The portfolio may have downside tail behavior that deserves stress review.";
  return sentence(alert.diagnosis, "A hidden risk signal is visible in the current portfolio evidence.");
}

function hiddenWhyItMatters(alert: XRayHiddenRiskAlert) {
  if (alert.id === "hidden_equity_beta") return "In risk-off markets, equity-linked holdings may dominate losses.";
  if (alert.id === "duration_concentration") return "Interest-rate shocks can affect defensive holdings and reduce diversification when rates move sharply.";
  if (alert.id === "credit_liquidity_risk") return "Credit or liquidity stress can create losses even when headline asset-class weights look diversified.";
  if (alert.id === "correlation_concentration") return "Diversification can weaken when holdings share the same economic driver.";
  if (alert.id === "weak_hedge_behavior") return "The portfolio may have less protection than expected when the main risk factor sells off.";
  if (alert.id === "tail_risk") return "Large-loss periods can matter more for decisions than average volatility.";
  return "This risk should be reviewed before using the diagnosis to test a candidate.";
}

export function HiddenRiskAlertsGrid({ xray }: { xray?: XRaySummary }) {
  return (
    <section id="hidden-risks" className="pmri-card pmri-section-reveal scroll-mt-28 rounded-3xl p-5 [--pmri-reveal-delay:180ms] md:p-6">
      <SectionHeader eyebrow="Hidden risk alerts" title="Risks that may not be obvious from tickers" insight={xray ? "The review highlights risks that may be hidden behind ticker labels, allocation categories, or diversification assumptions." : "Hidden risk alerts unavailable because supporting evidence is missing."} action="Review supporting evidence" />
      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{xray?.hiddenRisks.alerts.length ? xray.hiddenRisks.alerts.map((alert) => <HiddenAlertCard key={alert.id} alert={alert} />) : <UnavailableState message="Hidden risk alerts unavailable: insufficient evidence." />}</div>
    </section>
  );
}

function RiskContributionBars({ rows }: { rows: XRayRiskContribution[] }) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  if (!rows.length) return <UnavailableState message="Risk contribution rows are unavailable." />;
  const max = Math.max(1, ...rows.map((row) => Math.max(row.weightPct ?? 0, row.riskContributionPct ?? 0)));
  return (
    <div className="pmri-bar-group space-y-4" onMouseLeave={() => setActiveIndex(null)}>
      {rows.map((row, index) => {
        const gap = row.gapPp ?? ((row.riskContributionPct ?? 0) - (row.weightPct ?? 0));
        const gapTone: StatusTone = gap > 5 ? "amber" : gap < -5 ? "green" : "slate";
        const isActive = index === activeIndex;
        return (
          <button
            key={row.name}
            type="button"
            data-active={isActive}
            className={`pmri-interactive-bar-row pmri-focus w-full cursor-pointer rounded-xl border border-pmri-border/60 bg-white/[0.024] p-4 text-left ${gap > 5 ? "pmri-risk-overweight" : ""}`}
            onMouseEnter={() => setActiveIndex(index)}
            onFocus={() => setActiveIndex(index)}
            onBlur={() => setActiveIndex(null)}
          >
            <div className="flex items-center justify-between gap-3"><p className={`text-sm font-semibold ${isActive ? "text-pmri-text" : "text-pmri-text2"}`}>{cleanLabel(row.name)}</p><span className="pmri-gap-pill"><StatusBadge tone={gapTone}>Gap: {gap > 0 ? "+" : ""}{numberText(gap)} percentage points</StatusBadge></span></div>
            <div className="mt-3 space-y-2">
              <div><div className="flex justify-between text-xs text-pmri-text2"><span>Capital weight</span><span className={isActive ? "font-semibold text-pmri-text" : ""}>{pct(row.weightPct)}</span></div><div className="mt-1 h-2 overflow-hidden rounded-full bg-white/[0.055]"><div className="pmri-bar-fill h-full rounded-full bg-pmri-blueSoft/70" style={{ width: `${Math.min(100, ((row.weightPct ?? 0) / max) * 100)}%` }} /></div></div>
              <div><div className="flex justify-between text-xs text-pmri-text2"><span>Risk contribution</span><span className={isActive ? "font-semibold text-pmri-text" : ""}>{pct(row.riskContributionPct)}</span></div><div className="mt-1 h-2 overflow-hidden rounded-full bg-white/[0.055]"><div className="pmri-bar-fill pmri-risk-bar-fill h-full rounded-full bg-pmri-amber/75" style={{ width: `${Math.min(100, ((row.riskContributionPct ?? 0) / max) * 100)}%` }} /></div></div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

function RiskDriverLeaderboard({ rows }: { rows: XRayRiskContribution[] }) {
  if (!rows.length) return <UnavailableState message="Top risk drivers are unavailable." />;
  const max = Math.max(1, ...rows.map((row) => row.riskContributionPct ?? 0));
  return <div className="pmri-bar-group space-y-3">{rows.slice(0, 3).map((row) => <div key={row.name} className="pmri-interactive-bar-row rounded-xl border border-pmri-border/60 bg-white/[0.024] p-3"><div className="flex items-center justify-between gap-3"><span className="text-sm font-semibold text-pmri-text">{cleanLabel(row.name)}</span><span className="data-figure text-sm text-pmri-text">{pct(row.riskContributionPct)}</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-white/[0.055]"><div className="pmri-bar-fill h-full rounded-full bg-pmri-text/75" style={{ width: `${Math.min(100, ((row.riskContributionPct ?? 0) / max) * 100)}%` }} /></div></div>)}</div>;
}

function riskBudgetInsight(xray?: XRaySummary) {
  const top = xray?.riskBudget.topContributor;
  if (!top?.name) return "Risk budget unavailable because contribution evidence is missing.";
  const gap = top.gapPp ?? ((top.riskContributionPct ?? 0) - (top.weightPct ?? 0));
  return `${cleanLabel(top.name)} drives ${pct(top.riskContributionPct)} of normal risk versus ${pct(top.weightPct)} of capital. Gap: ${gap > 0 ? "+" : ""}${numberText(gap)} percentage points.`;
}

export function RiskBudgetPanel({ xray }: { xray?: XRaySummary }) {
  const top = xray?.riskBudget.topContributor;
  return (
    <section id="risk-budget" className="pmri-card pmri-animated-border-panel pmri-section-reveal scroll-mt-28 rounded-3xl p-5 [--pmri-reveal-delay:210ms] md:p-6">
      <SectionHeader eyebrow="Who drives portfolio risk" title="Capital weight versus risk contribution" insight={riskBudgetInsight(xray)} action="Review supporting evidence" />
      {!xray ? <div className="mt-5"><UnavailableState message="Risk budget unavailable because risk contribution data is missing." /></div> : (
        <div className="mt-6 flex flex-col items-start gap-5 xl:flex-row">
          <article className={`${raisedPanel} pmri-interactive-card w-full p-5 xl:w-[55%]`} style={{ alignSelf: "flex-start", height: "auto" }}><div className="mb-4 flex items-center justify-between gap-3"><h3 className="text-sm font-semibold text-pmri-text">Weight vs risk contribution</h3><TooltipHint label="Risk contribution" text="Normal portfolio risk contribution, not stress loss contribution." /></div><RiskContributionBars rows={xray.riskBudget.contributors} /></article>
          <div className="w-full space-y-4 xl:w-[45%]">
            <article className={`${raisedPanel} pmri-interactive-card p-5`}><p className="pmri-label text-pmri-text2">Top contributor</p><p className="mt-3 text-2xl font-semibold text-pmri-text">{top?.name ? cleanLabel(top.name) : "Unavailable"}</p><p className="mt-2 text-sm leading-6 text-pmri-text2">{top ? `${cleanLabel(top.name)} is ${pct(top.weightPct)} of capital and ${pct(top.riskContributionPct)} of normal portfolio risk.` : "Top risk contributor unavailable."}</p><p className="mt-4 text-sm text-pmri-text2">Top 3 risk share: <span className="data-figure text-pmri-text">{pct(xray.riskBudget.top3Share)}</span></p></article>
            <article className={`${softPanel} pmri-interactive-card p-4`}><h3 className="text-sm font-semibold text-pmri-text">Top 3 risk drivers</h3><div className="mt-4"><RiskDriverLeaderboard rows={xray.riskBudget.contributors} /></div></article>
            {xray.riskBudget.buckets.length ? <article className={`${softPanel} pmri-interactive-card p-4`}><h3 className="text-sm font-semibold text-pmri-text">Risk bucket contribution</h3><p className="mt-1 text-xs leading-5 text-pmri-text2">Normal portfolio risk contribution by bucket.</p><div className="mt-4"><RiskDriverLeaderboard rows={xray.riskBudget.buckets} /></div></article> : null}
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
              <article className={`${softPanel} pmri-interactive-card p-4`}><h3 className="text-sm font-semibold text-pmri-text">Risk-overweight assets</h3><div className="mt-3"><MiniFacts facts={xray.riskBudget.riskOverweight.map((row) => `${cleanLabel(row.name)}: ${pct(row.weightPct)} weight vs ${pct(row.riskContributionPct)} risk.`)} limit={3} /></div></article>
              <article className={`${softPanel} pmri-interactive-card p-4`}><h3 className="text-sm font-semibold text-pmri-text">Risk-underweight assets</h3><div className="mt-3"><MiniFacts facts={xray.riskBudget.riskUnderweight.map((row) => `${cleanLabel(row.name)}: ${pct(row.weightPct)} weight vs ${pct(row.riskContributionPct)} risk.`)} limit={3} /></div></article>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function WeaknessTile({ tile }: { tile: XRayWeaknessTile }) {
  const tone = severityTone(tile.severity);
  const evidence = tile.evidence.length ? tile.evidence : ["Insufficient evidence for this weakness tile."];
  const drivers = tile.linkedAssets.length ? tile.linkedAssets.slice(0, 3).map((asset) => cleanLabel(asset)).join(", ") : "Assets unavailable";
  const nextTest = tile.nextTests[0] ? cleanLabel(tile.nextTests[0]) : "Stress review needed";
  return (
    <article className={`${softPanel} pmri-interactive-card pmri-weakness-tile ${tile.score === undefined ? "opacity-80" : ""} p-4`}>
      <div className="flex items-start justify-between gap-3"><div><h3 className="text-base font-semibold text-pmri-text">{cleanLabel(tile.title)}</h3><p className="mt-1 text-xs text-pmri-text2">{severityLabel(tile.severity)}</p></div><StatusBadge tone={tone}>{severityLabel(tile.severity)}</StatusBadge></div>
      <div className="mt-4 flex items-center justify-between rounded-2xl border border-pmri-border/50 bg-black/10 px-3 py-2"><span className="text-xs font-medium text-pmri-text2">Score</span><ScoreIndicator score={tile.score} tone={tone} /></div>
      <div className="mt-4 space-y-2 text-xs leading-5 text-pmri-text2">
        <p><span className="font-medium text-pmri-text">Main drivers:</span> {drivers}</p>
        <p><span className="font-medium text-pmri-text">Next stress test:</span> {nextTest}</p>
      </div>
      {tile.score === undefined ? <p className="mt-3 rounded-xl border border-dashed border-pmri-borderSoft/45 bg-black/10 p-3 text-xs leading-5 text-pmri-text2">Data limitation: review supporting evidence before treating this as a live weakness.</p> : null}
      <details className="mt-4"><summary className="pmri-focus cursor-pointer list-none rounded-lg text-xs font-medium text-pmri-text2 transition hover:text-pmri-text">Supporting evidence</summary><div className="mt-3 space-y-2"><p className="text-xs leading-5 text-pmri-text2">{sentence(tile.diagnosis)}</p>{evidence.slice(0, 3).map((item) => <p key={item} className="text-xs leading-5 text-pmri-text2">• {sentence(item)}</p>)}<div className="flex flex-wrap gap-2 pt-1">{(tile.nextTests.length ? tile.nextTests.slice(0, 3) : ["Stress review needed"]).map((test) => <EvidenceChip key={test}>{test}</EvidenceChip>)}</div></div></details>
    </article>
  );
}

export function WeaknessMapGrid({ xray }: { xray?: XRaySummary }) {
  const topWeaknesses = xray?.weaknessMap.tiles
    .slice()
    .sort((a, b) => (b.score ?? -1) - (a.score ?? -1))
    .slice(0, 3) ?? [];

  return (
    <section id="weakness-map" className="pmri-card pmri-animated-border-panel pmri-section-reveal scroll-mt-28 rounded-3xl p-5 [--pmri-reveal-delay:240ms] md:p-6">
      <SectionHeader eyebrow="Potential stress weaknesses" title="Where the portfolio may break under stress" insight={xray ? "The map ranks pre-stress areas to review before any candidate test." : "Weakness map unavailable because pre-stress signals are missing."} action="Review supporting evidence" />
      {topWeaknesses.length ? <div className="mt-6 grid gap-3 md:grid-cols-3">{topWeaknesses.map((tile, index) => <article key={`${tile.id}-summary`} className={`${raisedPanel} p-4`}><p className="pmri-label text-pmri-text2">Top weakness {index + 1}</p><h3 className="mt-2 text-base font-semibold text-pmri-text">{cleanLabel(tile.title)}</h3><div className="mt-3"><ScoreIndicator score={tile.score} tone={severityTone(tile.severity)} /></div></article>)}</div> : null}
      <div className="pmri-weakness-grid mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">{xray?.weaknessMap.tiles.length ? xray.weaknessMap.tiles.map((tile) => <WeaknessTile key={tile.id} tile={tile} />) : <UnavailableState message="Portfolio Weakness Map unavailable: insufficient evidence." />}</div>
    </section>
  );
}

export const diagnosisSections = [
  { id: "summary", label: "Summary" },
  { id: "composition", label: "Composition" },
  { id: "risk-profile", label: "Risk Profile" },
  { id: "factors", label: "Factors" },
  { id: "hidden-risks", label: "Hidden Risks" },
  { id: "risk-budget", label: "Risk Budget" },
  { id: "weakness-map", label: "Weakness Map" }
];

export function DiagnosisSectionNav() {
  const [activeSection, setActiveSection] = useState(diagnosisSections[0].id);

  useEffect(() => {
    const targets = diagnosisSections
      .map((section) => document.getElementById(section.id))
      .filter((element): element is HTMLElement => Boolean(element));
    if (!targets.length) return undefined;

    const observer = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible?.target.id) setActiveSection(visible.target.id);
    }, { rootMargin: "-18% 0px -68% 0px", threshold: [0.1, 0.35, 0.6] });

    targets.forEach((target) => observer.observe(target));
    return () => observer.disconnect();
  }, []);

  function handleSectionClick(event: MouseEvent<HTMLAnchorElement>, id: string) {
    const target = document.getElementById(id);
    if (!target) return;
    event.preventDefault();
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    target.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
    window.history.replaceState(null, "", `#${id}`);
    setActiveSection(id);
  }

  return (
    <nav className="sticky top-4 z-20 -mx-1 overflow-x-auto rounded-2xl border border-pmri-border/70 bg-pmri-bg/88 p-1 shadow-decision backdrop-blur-xl" aria-label="Portfolio Diagnosis sections">
      <div className="flex min-w-max gap-1">{diagnosisSections.map((section) => <a key={section.id} href={`#${section.id}`} aria-current={activeSection === section.id ? "true" : undefined} onClick={(event) => handleSectionClick(event, section.id)} className="pmri-focus pmri-section-nav-link rounded-xl border border-transparent px-3.5 py-2 text-sm font-medium text-pmri-text2 hover:bg-white/[0.055] hover:text-pmri-text">{section.label}</a>)}</div>
    </nav>
  );
}
