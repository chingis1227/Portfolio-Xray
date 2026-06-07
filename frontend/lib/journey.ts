import type { JourneyStep } from "./types";

export const journeySteps: JourneyStep[] = [
  { id: "portfolio-input", label: "Portfolio Input", shortLabel: "Input", href: "/portfolio-input" },
  { id: "diagnosis", label: "Diagnosis", shortLabel: "Diagnosis", href: "/diagnosis" },
  { id: "evidence", label: "Evidence", shortLabel: "Evidence", href: "/evidence" },
  { id: "hypothesis", label: "Hypothesis", shortLabel: "Hypothesis", href: "/hypothesis" },
  { id: "comparison", label: "Comparison", shortLabel: "Compare", href: "/comparison" },
  { id: "verdict", label: "Verdict", shortLabel: "Verdict", href: "/verdict" },
  { id: "report", label: "Report", shortLabel: "Report", href: "/report" }
];

export function getStepIndex(pathname: string): number {
  const index = journeySteps.findIndex((step) => pathname.startsWith(step.href));
  return index === -1 ? 0 : index;
}
