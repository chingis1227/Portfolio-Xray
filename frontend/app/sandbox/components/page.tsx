import { ActiveDiagnosticTestContext } from "@/components/ui/ActiveDiagnosticTestContext";
import { AdvancedDisclosure } from "@/components/ui/AdvancedDisclosure";
import { Button, ButtonLink } from "@/components/ui/Button";
import { EvidenceItem } from "@/components/ui/EvidenceItem";
import { EvidenceSummary } from "@/components/ui/EvidenceSummary";
import { MetricMatrix, ComparisonMetricMatrix } from "@/components/ui/MetricMatrix";
import { SectionHeader } from "@/components/ui/SectionHeader";
import {
  CandidateUnavailableState,
  EmptyState,
  ErrorState,
  EvidenceInsufficientState,
  GenerationFailedState,
  LoadingState,
  LockedState,
  PartialEvidenceState,
  ReadOnlyHistoryState,
  StaleLineageState
} from "@/components/ui/States";
import { Surface } from "@/components/ui/Surface";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { VerdictHero } from "@/components/ui/VerdictHero";
import { EvidenceStrip } from "@/components/diagnosis/EvidenceStrip";

const evidence = [
  { label: "Primary issue", value: "Top-heavy allocation" },
  { label: "Main exposure", value: "Equity-led" },
  { label: "Worst observed downside", value: "-22.4%", tone: "red" as const },
  { label: "Evidence quality", value: "Strong" }
];

export default function ComponentSandboxPage() {
  return (
    <div className="space-y-8 pb-12">
      <VerdictHero
        stepContext="Sandbox - Decision Room Foundation"
        headline="Reusable primitives shape the product before individual screens are polished."
        interpretation="This sandbox previews the isolated UI workflow for product states, diagnostic-test context, evidence summaries, and route-ready components."
        facts={[
          { label: "Workflow", value: "Sandbox first" },
          { label: "Storybook", value: "Deferred" },
          { label: "Benchmark", value: "/diagnosis" }
        ]}
        actions={(
          <>
            <ButtonLink href="/diagnosis" variant="primary">Open Diagnosis</ButtonLink>
            <ButtonLink href="/workspace" variant="secondary">Back to Workspace</ButtonLink>
          </>
        )}
      />

      <Surface tone="glass" radius="3xl" padding="md">
        <SectionHeader
          eyebrow="Primitive controls"
          title="Buttons, badges, and quiet hierarchy"
          description="Primary blue is reserved for the next safe action. Amber and red are evidence-backed, not decorative."
        />
        <div className="mt-5 flex flex-wrap gap-3">
          <Button variant="primary">Primary action</Button>
          <Button variant="secondary">Secondary action</Button>
          <Button variant="ghost">Ghost action</Button>
          <Button variant="danger">Risk action</Button>
          <Button variant="primary" disabled>Not ready yet</Button>
          <Button variant="secondary" className="max-w-xs whitespace-normal text-left leading-5">Long label that wraps on narrow screens without breaking the button rhythm</Button>
          <StatusBadge tone="blue">Active</StatusBadge>
          <StatusBadge tone="amber">Partial evidence</StatusBadge>
          <StatusBadge tone="red">Material issue</StatusBadge>
          <StatusBadge tone="slate">Neutral long state label</StatusBadge>
        </div>
      </Surface>

      <section className="grid gap-5 lg:grid-cols-3">
        <Surface tone="default" radius="3xl" padding="md">
          <SectionHeader eyebrow="Default" title="Case-file surface" description="Decision reading unit with calm graphite depth." />
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <EvidenceItem label="Metric value" value="52.8%" />
            <EvidenceItem label="Risk evidence" value="-18.6%" tone="red" detail="Muted red only when evidence-backed." />
          </div>
        </Surface>
        <Surface tone="raised" radius="3xl" padding="md">
          <SectionHeader eyebrow="Raised" title="Action console host" description="Use for focused canvases and route-side actions." />
          <p className="mt-5 text-sm leading-6 text-pmri-text2">Raised surfaces can hold setup controls without making the entire page feel like a form.</p>
        </Surface>
        <Surface tone="warning" radius="3xl" padding="md">
          <SectionHeader eyebrow="Warning" title="Evidence-required surface" description="Amber means partial, blocked, or evidence-required state." />
          <p className="mt-5 text-sm leading-6 text-pmri-text2">Use for valid states that need user recovery or more evidence.</p>
        </Surface>
      </section>

      <EvidenceStrip items={evidence} />

      <section className="space-y-5">
        <SectionHeader
          eyebrow="Evidence states"
          title="Evidence summaries stay compact"
          description="The first read promotes at most four facts; missing evidence stays explicit."
        />
        <div className="grid gap-5 lg:grid-cols-2">
          <EvidenceSummary
            title="Four-item summary"
            description="Normal, amber, red, and blue tones in one strip."
            items={[
              { label: "Diagnosis", value: "Concentration risk" },
              { label: "Stress", value: "Severe equity shock", tone: "amber" },
              { label: "Drawdown", value: "Material", tone: "red" },
              { label: "Next step", value: "Review Stress Lab", tone: "blue" }
            ]}
          />
          <EvidenceSummary
            title="Missing evidence"
            description="Empty summaries explain absence without looking broken."
            items={[]}
          />
        </div>
      </section>

      <section className="space-y-5">
        <SectionHeader
          eyebrow="Active context"
          title="Diagnostic-test context follows downstream routes"
          description="Comparison, Verdict, and Report should repeat what test is active without implying a recommendation."
        />
        <ActiveDiagnosticTestContext
          testName="Improve crisis resilience"
          purpose="Test whether a more defensive allocation lowers severe stress loss enough to justify further review."
          candidateName="Minimum CVaR test candidate"
          evidenceQuality="Limited evidence"
          limitation="This is a diagnostic comparison input, not a trade instruction or suitability approval."
          tone="amber"
        />
      </section>

      <section className="space-y-5">
        <SectionHeader
          eyebrow="Product states"
          title="Shared state family"
          description="These states should be reused before creating route-local shells."
        />
        <div className="grid gap-5 lg:grid-cols-3">
          <EmptyState title="Missing data state" description="Add holdings and weights to start the diagnosis." />
          <LoadingState title="Preparing evidence" description="Portfolio MRI is preparing the current review evidence." />
          <ErrorState title="Review needs attention" description="The review could not complete. The user should get a clear recovery path." />
          <LockedState title="Route locked" description="Complete the previous journey step first." missing={["Run Portfolio Diagnosis", "Open Stress Test Lab evidence"]} />
          <PartialEvidenceState title="Partial evidence" description="Only partial evidence is available, so conclusions are limited." details={["Stress evidence returned with limitations", "Comparison should disclose missing metrics"]} />
          <ReadOnlyHistoryState title="Saved review is read-only" description="The snapshot can be reviewed, but it cannot unlock new same-run actions." />
          <StaleLineageState title="Previous result ignored" description="The saved result does not match the active diagnostic test." details={["Generate fresh comparison evidence for the active test before continuing."]} />
          <EvidenceInsufficientState title="Evidence insufficient" description="Do not form a portfolio decision from this evidence yet." details={["Comparison evidence is incomplete", "Test another path or monitor until evidence improves"]} />
          <CandidateUnavailableState title="Test candidate unavailable" description="Generate one test candidate before comparing trade-offs." details={["Return to Hypothesis", "Review the selected setup and evidence limitations"]} />
          <GenerationFailedState title="Generation failed" description="The selected diagnostic test could not be built from the available evidence." details={["Adjust setup bounds", "Choose another diagnostic test path"]} />
        </div>
      </section>

      <section className="space-y-5">
        <SectionHeader
          eyebrow="Metric matrices"
          title="Matrices stay secondary to the first-read answer"
          description="Unavailable values are explicit and material rows sort first."
        />
        <MetricMatrix
          groups={[
            {
              title: "Risk diagnosis",
              rows: [
                { metric: "Top holding concentration", portfolioValue: "38%", reference: "Review above 25%", status: { label: "Watch", tone: "amber" }, meaning: "Single-name exposure may dominate stress behavior.", material: true },
                { metric: "Evidence quality", portfolioValue: "Not enough evidence yet", reference: "Review evidence", meaning: "The metric should not be inferred when evidence is missing." }
              ]
            }
          ]}
        />
        <ComparisonMetricMatrix
          groups={[
            {
              title: "Trade-off evidence",
              rows: [
                { metric: "Worst stress loss", currentPortfolio: "-22.4%", candidatePortfolio: "-16.8%", change: "Improved", status: { label: "Improved", tone: "blue" }, interpretation: "The test candidate reduced stress loss in this scenario.", material: true },
                { metric: "Turnover", currentPortfolio: "Current allocation", candidatePortfolio: "Test candidate", change: "Higher", status: { label: "Trade-off", tone: "amber" }, interpretation: "Potential implementation cost remains a limitation." }
              ]
            }
          ]}
        />
      </section>

      <AdvancedDisclosure title="Long and technical state" summary="Collapsed by default so advanced content never wins the first viewport.">
        <p className="text-sm leading-6 text-pmri-text2">
          This area is for metric matrices, raw limitations, provenance, and developer-oriented evidence. It remains available without dominating the diagnostic answer.
        </p>
      </AdvancedDisclosure>
    </div>
  );
}
