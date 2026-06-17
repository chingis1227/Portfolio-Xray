"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useReviewState, type ReviewHolding } from "@/lib/reviewState";
import { useSupabaseAuth } from "@/lib/supabase/auth";
import { useSupabasePersistence, type SavedPortfolioRecord, type SavedReviewRecord } from "@/lib/supabase/persistence";

type Tone = "blue" | "gold" | "green" | "amber" | "red" | "slate";

const stageLabels: Record<string, string> = {
  input: "Input",
  data_load: "Data",
  xray: "Diagnosis",
  stress: "Stress",
  client_fit: "Client Fit",
  problem_classification: "Problem",
  launchpad_builder: "Launchpad",
  diagnosis: "Diagnosis",
  builder: "Builder",
  candidate: "Candidate",
  comparison: "Comparison",
  verdict: "Verdict",
  report: "Report"
};

function formatDate(value?: string) {
  if (!value) return "Not recorded";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function formatPercent(value: number) {
  return `${value.toFixed(value % 1 === 0 ? 0 : 1)}%`;
}

function totalWeight(holdings: ReviewHolding[]) {
  return holdings.reduce((sum, holding) => sum + holding.weight, 0);
}

function topHoldings(holdings: ReviewHolding[]) {
  return [...holdings].sort((a, b) => b.weight - a.weight).slice(0, 4);
}

function reviewTitle(review?: SavedReviewRecord | null) {
  if (!review) return "No active review yet";
  if (review.title) return review.title;
  if (typeof review.compactSummary.diagnosisHeadline === "string") return review.compactSummary.diagnosisHeadline;
  return "Saved review";
}

function reviewStatusTone(review?: SavedReviewRecord | null): Tone {
  if (!review) return "slate";
  if (review.status === "completed") return review.readOnlyHistory ? "amber" : "green";
  if (review.status === "failed") return "red";
  if (review.status === "draft") return "blue";
  return "slate";
}

function reviewStatusLabel(review?: SavedReviewRecord | null) {
  if (!review) return "No active review";
  if (review.status === "draft") return "Draft";
  if (review.readOnlyHistory) return "Read-only history";
  if (review.status === "completed") return review.lineageAvailable ? "Current review" : "Saved history";
  return review.status;
}

function nextHrefForReview(review?: SavedReviewRecord | null) {
  if (!review) return "/portfolio-input";
  if (review.status === "draft") return "/portfolio-input";
  if (review.stages.report) return "/report";
  if (review.stages.verdict) return "/verdict";
  if (review.stages.comparison) return "/comparison";
  if (review.stages.candidate) return "/comparison";
  if (review.stages.builder || review.stages.launchpad_builder) return "/hypothesis";
  if (review.stages.client_fit) return "/hypothesis";
  if (review.stages.stress || review.stages.xray || review.stages.diagnosis) return "/diagnosis";
  return "/portfolio-input";
}

function CardShell({ children }: { children: ReactNode }) {
  return <section className="pmri-card rounded-[1.75rem] p-5">{children}</section>;
}

function HoldingsPreview({ holdings }: { holdings: ReviewHolding[] }) {
  if (!holdings.length) {
    return <p className="mt-4 text-sm leading-6 text-pmri-muted">No holdings snapshot is available for this item.</p>;
  }
  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {topHoldings(holdings).map((holding) => (
        <span key={`${holding.ticker}-${holding.weight}`} className="rounded-full border border-pmri-border/45 bg-white/[0.025] px-3 py-1.5 text-xs text-pmri-text2">
          {holding.ticker} {formatPercent(holding.weight)}
        </span>
      ))}
    </div>
  );
}

function PortfolioCard({ portfolio, isActive, onLoad, onArchive }: { portfolio: SavedPortfolioRecord; isActive: boolean; onLoad: () => void; onArchive: () => void }) {
  return (
    <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold tracking-[-0.025em] text-pmri-text">{portfolio.name}</h3>
            {isActive ? <StatusBadge tone="blue">Active portfolio</StatusBadge> : null}
            {portfolio.versionNumber ? <StatusBadge tone="slate">Version {portfolio.versionNumber}</StatusBadge> : null}
          </div>
          <p className="mt-2 text-sm leading-6 text-pmri-muted">
            {portfolio.holdings.length} holdings, {formatPercent(totalWeight(portfolio.holdings))} total allocation, base currency {portfolio.baseCurrency}.
          </p>
          <p className="mt-1 text-xs text-pmri-muted">Updated {formatDate(portfolio.updatedAt)}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button type="button" onClick={onLoad} className="pmri-focus rounded-full border border-pmri-blue/45 bg-pmri-blue/[0.08] px-4 py-2 text-xs font-semibold text-pmri-blueSoft transition hover:bg-pmri-blue/[0.13]">
            Use for new review
          </button>
          <button type="button" onClick={onArchive} className="pmri-focus rounded-full border border-pmri-border/55 px-4 py-2 text-xs font-semibold text-pmri-muted transition hover:border-pmri-amber/45 hover:text-pmri-text2">
            Archive
          </button>
        </div>
      </div>
      <HoldingsPreview holdings={portfolio.holdings} />
    </article>
  );
}

function ReviewCard({ review, isActive, onOpen, onArchive }: { review: SavedReviewRecord; isActive: boolean; onOpen: () => void; onArchive: () => void }) {
  const stages = Object.keys(stageLabels).filter((stage) => Boolean(review.stages[stage as keyof typeof review.stages]));
  const holdings = review.portfolioSnapshot.holdings ?? [];
  return (
    <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.022] p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold tracking-[-0.02em] text-pmri-text">{reviewTitle(review)}</h3>
            {isActive ? <StatusBadge tone="blue">Active review</StatusBadge> : null}
            <StatusBadge tone={reviewStatusTone(review)}>{reviewStatusLabel(review)}</StatusBadge>
          </div>
          <p className="mt-2 text-sm leading-6 text-pmri-muted">
            {holdings.length} holdings saved from this review. Updated {formatDate(review.updatedAt ?? review.completedAt)}.
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button type="button" onClick={onOpen} className="pmri-focus rounded-full border border-pmri-blue/45 bg-pmri-blue/[0.08] px-4 py-2 text-xs font-semibold text-pmri-blueSoft transition hover:bg-pmri-blue/[0.13]">
            Open review
          </button>
          <button type="button" onClick={onArchive} className="pmri-focus rounded-full border border-pmri-border/55 px-4 py-2 text-xs font-semibold text-pmri-muted transition hover:border-pmri-amber/45 hover:text-pmri-text2">
            Archive
          </button>
        </div>
      </div>
      {stages.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {stages.slice(0, 9).map((stage) => (
            <span key={stage} className="rounded-full border border-pmri-border/35 px-2.5 py-1 text-[11px] text-pmri-muted">
              {stageLabels[stage]}
            </span>
          ))}
        </div>
      ) : <HoldingsPreview holdings={holdings} />}
    </article>
  );
}

export function WorkspaceScreen() {
  const router = useRouter();
  const { enabled, status, user } = useSupabaseAuth();
  const { activeReview, hydrateCloudReview, loadCloudPortfolioInput } = useReviewState();
  const {
    signedIn,
    savedPortfolios,
    savedReviews,
    workspaceState,
    portfoliosLoading,
    reviewsLoading,
    workspaceLoading,
    refreshSavedPortfolios,
    refreshSavedReviews,
    refreshWorkspaceState,
    deletePortfolio,
    archiveReview,
    setNotice
  } = useSupabasePersistence();

  const activeReviewRow = savedReviews.find((review) => review.id === workspaceState?.activeReviewRowId)
    ?? savedReviews.find((review) => review.id === workspaceState?.lastOpenedReviewRowId)
    ?? null;
  const activePortfolio = savedPortfolios.find((portfolio) => portfolio.id === workspaceState?.activePortfolioId)
    ?? savedPortfolios.find((portfolio) => portfolio.id === activeReviewRow?.portfolioId)
    ?? null;
  const latestReview = activeReviewRow ?? savedReviews[0] ?? null;
  const loading = portfoliosLoading || reviewsLoading || workspaceLoading;

  function refreshWorkspace() {
    void refreshSavedPortfolios();
    void refreshSavedReviews();
    void refreshWorkspaceState();
  }

  function openReview(review: SavedReviewRecord) {
    hydrateCloudReview(review);
    setNotice("success", review.readOnlyHistory ? "Opened read-only review history." : "Opened saved review.");
    router.push(nextHrefForReview(review));
  }

  function loadPortfolio(portfolio: SavedPortfolioRecord) {
    loadCloudPortfolioInput({
      portfolioId: portfolio.id,
      name: portfolio.name,
      investorCurrency: portfolio.baseCurrency,
      holdings: portfolio.holdings,
      versionId: portfolio.latestVersionId,
      versionNumber: portfolio.versionNumber
    });
    setNotice("info", "Loaded the saved portfolio. Editing it starts a new review and does not change past reviews.");
    router.push("/portfolio-input");
  }

  if (!enabled) {
    return (
      <div>
        <PageHeader kicker="Workspace" title="Account saving is not configured" description="You can still enter a portfolio in this browser, but saved portfolios and review history are unavailable." />
        <CardShell><Link href="/portfolio-input" className="pmri-focus pmri-primary-action inline-flex rounded-full px-5 py-2.5 text-sm font-semibold">Go to Portfolio Input</Link></CardShell>
      </div>
    );
  }

  if (status !== "signed_in" || !signedIn) {
    return (
      <div>
        <PageHeader kicker="Workspace" title="Sign in to open your workspace" description="Your saved portfolios and past reviews are tied to your account." />
        <CardShell><Link href="/onboarding/sign-in" className="pmri-focus pmri-primary-action inline-flex rounded-full px-5 py-2.5 text-sm font-semibold">Sign in</Link></CardShell>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        kicker="Workspace"
        title="Your investment workspace"
        description="Keep your saved portfolios, past reviews, and current analysis in one place."
      >
        <StatusBadge tone="green">Signed in</StatusBadge>
      </PageHeader>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-5">
          <CardShell>
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="pmri-label text-pmri-blueSoft">Current review</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em] text-pmri-text">{reviewTitle(latestReview)}</h2>
                <p className="mt-3 max-w-3xl text-sm leading-6 text-pmri-muted">
                  {latestReview ? "Continue the latest saved review, or start a new one from a saved portfolio." : "Start by adding your portfolio. Once the diagnosis is complete, it will appear here."}
                </p>
              </div>
              <div className="flex shrink-0 flex-wrap gap-2">
                <StatusBadge tone={reviewStatusTone(latestReview)}>{reviewStatusLabel(latestReview)}</StatusBadge>
              </div>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl border border-pmri-border/40 bg-white/[0.02] p-4">
                <p className="pmri-label text-pmri-text2">Account</p>
                <p className="mt-2 truncate text-sm text-pmri-text" title={user?.email ?? undefined}>{user?.email ?? "Signed-in user"}</p>
              </div>
              <div className="rounded-2xl border border-pmri-border/40 bg-white/[0.02] p-4">
                <p className="pmri-label text-pmri-text2">Active portfolio</p>
                <p className="mt-2 text-sm text-pmri-text">{activePortfolio?.name ?? activeReview?.cloudPortfolio?.name ?? "Not selected"}</p>
              </div>
              <div className="rounded-2xl border border-pmri-border/40 bg-white/[0.02] p-4">
                <p className="pmri-label text-pmri-text2">Saved reviews</p>
                <p className="mt-2 text-sm text-pmri-text">{savedReviews.length}</p>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-3">
              {latestReview ? (
                <button type="button" onClick={() => openReview(latestReview)} className="pmri-focus pmri-primary-action rounded-full px-5 py-2.5 text-sm font-semibold">
                  Continue review
                </button>
              ) : null}
              <Link href="/portfolio-input" className="pmri-focus rounded-full border border-pmri-border/60 px-5 py-2.5 text-sm font-semibold text-pmri-text2 transition hover:border-pmri-blue/40 hover:text-pmri-text">
                {latestReview ? "Start new review" : "Start portfolio review"}
              </Link>
              <button type="button" onClick={refreshWorkspace} className="pmri-focus rounded-full border border-pmri-border/60 px-5 py-2.5 text-sm font-semibold text-pmri-muted transition hover:border-pmri-border hover:text-pmri-text2">
                {loading ? "Refreshing..." : "Refresh workspace"}
              </button>
            </div>
          </CardShell>

          <CardShell>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="pmri-label text-pmri-blueSoft">Portfolio library</p>
                <h2 className="mt-2 text-xl font-semibold tracking-[-0.025em] text-pmri-text">Saved portfolios</h2>
                <p className="mt-2 text-sm leading-6 text-pmri-muted">Saved portfolios can be reused as a starting point for a new diagnosis.</p>
              </div>
              <StatusBadge tone="slate">Archive hides items</StatusBadge>
            </div>
            <div className="mt-5 space-y-3">
              {savedPortfolios.map((portfolio) => (
                <PortfolioCard
                  key={portfolio.id}
                  portfolio={portfolio}
                  isActive={portfolio.id === workspaceState?.activePortfolioId}
                  onLoad={() => loadPortfolio(portfolio)}
                  onArchive={() => void deletePortfolio(portfolio.id)}
                />
              ))}
              {!savedPortfolios.length ? (
                <div className="rounded-2xl border border-pmri-border/40 bg-white/[0.02] p-4">
                  <p className="text-sm text-pmri-muted">No saved portfolios yet. Add your portfolio to save it here for future reviews.</p>
                  <Link href="/portfolio-input" className="pmri-focus mt-4 inline-flex rounded-full border border-pmri-blue/45 bg-pmri-blue/[0.08] px-4 py-2 text-xs font-semibold text-pmri-blueSoft transition hover:bg-pmri-blue/[0.13]">
                    Add portfolio
                  </Link>
                </div>
              ) : null}
            </div>
          </CardShell>
        </div>

        <aside className="space-y-5">
          <CardShell>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="pmri-label text-pmri-blueSoft">Review history</p>
                <h2 className="mt-2 text-xl font-semibold tracking-[-0.025em] text-pmri-text">Past reviews</h2>
              </div>
              <StatusBadge tone="slate">{reviewsLoading ? "Loading" : `${savedReviews.length}`}</StatusBadge>
            </div>
            <div className="mt-5 space-y-3">
              {savedReviews.map((review) => (
                <ReviewCard
                  key={review.id}
                  review={review}
                  isActive={review.id === workspaceState?.activeReviewRowId}
                  onOpen={() => openReview(review)}
                  onArchive={() => void archiveReview(review.id)}
                />
              ))}
              {!savedReviews.length ? <p className="rounded-2xl border border-pmri-border/40 bg-white/[0.02] p-4 text-sm text-pmri-muted">No completed reviews yet. Run your first diagnosis to create review history.</p> : null}
            </div>
          </CardShell>

          <CardShell>
            <p className="pmri-label text-pmri-blueSoft">How it works</p>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-pmri-muted">
              <li>Saved portfolios can be reused for new reviews.</li>
              <li>Completed reviews do not change after they are created.</li>
              <li>Archiving hides items from your main list without deleting them.</li>
            </ul>
          </CardShell>
        </aside>
      </div>
    </div>
  );
}
