import type { JourneyStep, JourneyStepStatus } from "./types";

export const journeySteps: JourneyStep[] = [
  {
    id: "portfolio-input",
    label: "Portfolio Input",
    shortLabel: "Input",
    href: "/portfolio-input",
    lockReason: "Portfolio Input is always available."
  },
  {
    id: "diagnosis",
    label: "Diagnosis",
    shortLabel: "Diagnosis",
    href: "/diagnosis",
    lockReason: "Complete Portfolio Input first to unlock Diagnosis."
  },
  {
    id: "evidence",
    label: "Evidence",
    shortLabel: "Evidence",
    href: "/evidence",
    lockReason: "Run portfolio diagnosis first to generate Evidence."
  },
  {
    id: "hypothesis",
    label: "Hypothesis",
    shortLabel: "Hypothesis",
    href: "/hypothesis",
    lockReason: "Review generated diagnosis and evidence before testing a hypothesis."
  },
  {
    id: "comparison",
    label: "Comparison",
    shortLabel: "Compare",
    href: "/comparison",
    lockReason: "Generate a candidate before comparing portfolios."
  },
  {
    id: "verdict",
    label: "Verdict",
    shortLabel: "Verdict",
    href: "/verdict",
    lockReason: "Complete the comparison before viewing the verdict."
  },
  {
    id: "report",
    label: "Report",
    shortLabel: "Report",
    href: "/report",
    lockReason: "Complete the decision workflow before generating the report."
  }
];

export type JourneyFlags = {
  inputCompleted: boolean;
  diagnosisGenerated: boolean;
  evidenceGenerated: boolean;
  improvementPathsAvailable: boolean;
  candidateReady: boolean;
  comparisonReady: boolean;
  verdictReady: boolean;
};

export type JourneyStepWithStatus = JourneyStep & {
  index: number;
  status: JourneyStepStatus;
};

export const emptyJourneyFlags: JourneyFlags = {
  inputCompleted: false,
  diagnosisGenerated: false,
  evidenceGenerated: false,
  improvementPathsAvailable: false,
  candidateReady: false,
  comparisonReady: false,
  verdictReady: false
};

export function getStepIndex(pathname: string): number {
  const index = journeySteps.findIndex((step) => pathname.startsWith(step.href));
  return index === -1 ? 0 : index;
}

export function getStepById(stepId: string) {
  return journeySteps.find((step) => step.id === stepId);
}

export function isStepUnlocked(stepId: string, flags: JourneyFlags): boolean {
  switch (stepId) {
    case "portfolio-input":
      return true;
    case "diagnosis":
      return flags.inputCompleted;
    case "evidence":
      return flags.diagnosisGenerated;
    case "hypothesis":
      return flags.diagnosisGenerated && flags.evidenceGenerated && flags.improvementPathsAvailable;
    case "comparison":
      return flags.candidateReady;
    case "verdict":
      return flags.comparisonReady;
    case "report":
      return flags.verdictReady;
    default:
      return false;
  }
}

export function buildJourneySteps(pathname: string, flags: JourneyFlags): JourneyStepWithStatus[] {
  const currentIndex = getStepIndex(pathname);

  return journeySteps.map((step, index) => {
    const unlocked = isStepUnlocked(step.id, flags);
    let status: JourneyStepStatus = "locked";

    if (unlocked && index === currentIndex) {
      status = "active";
    } else if (unlocked && index < currentIndex) {
      status = "completed";
    } else if (unlocked) {
      status = "available";
    }

    return { ...step, index, status };
  });
}
