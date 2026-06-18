import type { ReactNode } from "react";
import type { StatusTone } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";

type ActiveDiagnosticTestContextProps = {
  testName?: ReactNode;
  purpose?: ReactNode;
  candidateName?: ReactNode;
  evidenceQuality?: ReactNode;
  limitation?: ReactNode;
  tone?: StatusTone;
};

function textOrFallback(value: ReactNode | undefined, fallback: string) {
  return value ?? fallback;
}

export function ActiveDiagnosticTestContext({
  testName,
  purpose,
  candidateName,
  evidenceQuality,
  limitation,
  tone = "slate"
}: ActiveDiagnosticTestContextProps) {
  const safeTestName = textOrFallback(testName, "Diagnostic test not selected");

  return (
    <section className="rounded-3xl border border-pmri-border/55 bg-white/[0.024] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.035)]">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="pmri-type-meta text-pmri-blueSoft">Active diagnostic test</p>
            <StatusBadge tone={tone}>{evidenceQuality ?? "Context"}</StatusBadge>
          </div>
          <h2 className="mt-2 pmri-type-card-title text-pmri-text">{safeTestName}</h2>
          {purpose ? <p className="mt-2 max-w-4xl text-sm leading-6 text-pmri-text2">{purpose}</p> : null}
        </div>
        {candidateName ? (
          <div className="rounded-2xl border border-white/[0.08] bg-black/15 px-4 py-3 lg:max-w-xs">
            <p className="pmri-type-meta text-pmri-muted">Generated test candidate</p>
            <p className="mt-1 text-sm font-medium leading-6 text-pmri-text">{candidateName}</p>
          </div>
        ) : null}
      </div>
      {limitation ? (
        <p className="mt-4 rounded-2xl border border-pmri-amber/25 bg-pmri-amber/[0.07] px-4 py-3 text-sm leading-6 text-pmri-text2">
          <span className="font-medium text-pmri-amber">Boundary:</span> {limitation}
        </p>
      ) : null}
    </section>
  );
}
