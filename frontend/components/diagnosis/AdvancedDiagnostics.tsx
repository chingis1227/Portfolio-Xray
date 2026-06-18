import type { XRaySummary } from "@/lib/reviewState";
import type { MetricMatrixGroup } from "@/components/ui/MetricMatrix";
import { MetricCard } from "@/components/ui/MetricCard";
import { MetricMatrix } from "@/components/ui/MetricMatrix";
import { AdvancedDisclosure } from "@/components/ui/AdvancedDisclosure";
import { Surface } from "@/components/ui/Surface";
import type { DiagnosisDisplayModel } from "@/components/diagnosis/diagnosisPresentation";
import {
  CompositionPanel,
  FactorExposurePanel,
  HiddenRiskAlertsGrid,
  RiskBudgetPanel,
  WeaknessMapGrid
} from "@/components/diagnosis/PortfolioXRayBlocks";

export function AdvancedDiagnostics({ model, metricGroups, xraySummary }: { model: DiagnosisDisplayModel; metricGroups: MetricMatrixGroup[]; xraySummary?: XRaySummary }) {
  return (
    <AdvancedDisclosure
      id="advanced-diagnostics"
      title="Advanced diagnostics and technical evidence"
      summary="Metric matrix, professional measures, evidence notes, and full x-ray stay below the main diagnostic answer."
    >
      <MetricMatrix
        title="Compact metric matrix"
        description="Secondary metrics are grouped here after the primary diagnosis is understood."
        groups={metricGroups}
      />

      {model.advancedMetrics.length ? (
        <Surface tone="default" radius="3xl" padding="md">
          <h3 className="text-sm font-semibold text-pmri-text">Professional metrics</h3>
          <p className="mt-2 text-sm leading-6 text-pmri-text2">
            These metrics support the case file but do not lead the first-read diagnosis.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {model.advancedMetrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
          </div>
        </Surface>
      ) : null}

      {model.technicalEvidence.length || model.limitations.length ? (
        <Surface tone="default" radius="3xl" padding="md">
          <h3 className="text-sm font-semibold text-pmri-text">Evidence chain notes</h3>
          {model.technicalEvidence.length ? (
            <ul className="mt-3 space-y-2 text-sm leading-6 text-pmri-text2">
              {model.technicalEvidence.map((item) => <li key={item}>- {item}</li>)}
            </ul>
          ) : null}
          {model.limitations.length ? (
            <div className="mt-4 border-t border-white/[0.06] pt-4">
              <p className="text-xs font-semibold text-pmri-muted">Limitations</p>
              <ul className="mt-2 space-y-2 text-sm leading-6 text-pmri-text2">
                {model.limitations.map((item) => <li key={item}>- {item}</li>)}
              </ul>
            </div>
          ) : null}
        </Surface>
      ) : null}

      {xraySummary ? (
        <details className="rounded-2xl border border-white/[0.07] bg-black/10 p-4">
          <summary className="pmri-focus cursor-pointer list-none rounded-xl text-sm font-semibold text-pmri-text2 transition hover:text-pmri-text">
            Full portfolio x-ray detail
          </summary>
          <div className="mt-5 space-y-5">
            <CompositionPanel xray={xraySummary} />
            <FactorExposurePanel xray={xraySummary} />
            <HiddenRiskAlertsGrid xray={xraySummary} />
            <RiskBudgetPanel xray={xraySummary} />
            <WeaknessMapGrid xray={xraySummary} />
          </div>
        </details>
      ) : null}
    </AdvancedDisclosure>
  );
}
