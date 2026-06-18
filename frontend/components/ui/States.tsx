import type { ReactNode } from "react";
import { ButtonLink } from "@/components/ui/Button";
import { Surface } from "@/components/ui/Surface";
import { StatusBadge } from "@/components/ui/StatusBadge";

type ProductStateTone = "default" | "risk" | "warning" | "info" | "neutral";

type ProductStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
  missing?: string[];
  details?: string[];
};

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <StateShell title={title} description={description} action={action} />;
}

export function LoadingState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <StateShell title={title} description={description} action={action} loading badge="Preparing" tone="info" />;
}

export function ErrorState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <StateShell title={title} description={description} action={action} tone="risk" badge="Needs attention" />;
}

export function LockedState({ title, description, action, missing }: ProductStateProps) {
  return <StateShell title={title} description={description} action={action} tone="warning" badge="Locked" missing={missing} />;
}

export function PartialEvidenceState({ title, description, action, details }: ProductStateProps) {
  return <StateShell title={title} description={description} action={action} tone="warning" badge="Partial evidence" details={details} />;
}

export function ReadOnlyHistoryState({ title, description, action }: ProductStateProps) {
  return <StateShell title={title} description={description} action={action} tone="neutral" badge="Read-only history" />;
}

export function StaleLineageState({ title, description, action, details }: ProductStateProps) {
  return <StateShell title={title} description={description} action={action} tone="warning" badge="Previous result ignored" details={details} />;
}

export function EvidenceInsufficientState({ title, description, action, details }: ProductStateProps) {
  return <StateShell title={title} description={description} action={action} tone="warning" badge="Evidence insufficient" details={details} />;
}

export function CandidateUnavailableState({ title, description, action, details }: ProductStateProps) {
  return <StateShell title={title} description={description} action={action} tone="warning" badge="Test candidate unavailable" details={details} />;
}

export function GenerationFailedState({ title, description, action, details }: ProductStateProps) {
  return <StateShell title={title} description={description} action={action} tone="risk" badge="Generation failed" details={details} />;
}

function StateShell({
  title,
  description,
  action,
  loading,
  tone = "default",
  badge,
  missing,
  details
}: {
  title: string;
  description: string;
  action?: ReactNode;
  loading?: boolean;
  tone?: ProductStateTone;
  badge?: string;
  missing?: string[];
  details?: string[];
}) {
  const surfaceTone = tone === "risk" ? "risk" : tone === "warning" ? "warning" : "glass";
  const badgeTone = tone === "risk" ? "red" : tone === "warning" ? "amber" : tone === "info" ? "blue" : "slate";
  const list = missing?.length ? missing : details;

  return (
    <Surface tone={surfaceTone} radius="3xl" padding="lg">
      <div className="flex flex-wrap items-center gap-3">
        {loading ? <span className="pmri-spinner" aria-hidden="true" /> : null}
        {badge ? <StatusBadge tone={badgeTone}>{badge}</StatusBadge> : null}
      </div>
      <h2 className="mt-4 pmri-type-section-title text-pmri-text">{title}</h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-pmri-text2">{description}</p>
      {list?.length ? (
        <div className="mt-5 rounded-2xl border border-white/[0.08] bg-black/15 p-4">
          <p className="pmri-type-meta text-pmri-muted">{missing?.length ? "What is missing" : "What this means"}</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-pmri-text2">
            {list.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-pmri-blueSoft/70" aria-hidden="true" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {action ? <div className="mt-6 flex flex-wrap gap-3">{action}</div> : null}
    </Surface>
  );
}

export function PortfolioInputAction() {
  return <ButtonLink href="/portfolio-input" variant="primary">Go to Portfolio Input</ButtonLink>;
}

export function BackToPortfolioInputAction() {
  return <ButtonLink href="/portfolio-input" variant="secondary">Back to Portfolio Input</ButtonLink>;
}
