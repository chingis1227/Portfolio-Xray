const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const frontendRoot = path.resolve(__dirname, "..");

function read(relPath) {
  return fs.readFileSync(path.join(frontendRoot, relPath), "utf8");
}

function countMatches(source, pattern) {
  return [...source.matchAll(pattern)].length;
}

const primarySurfaceFiles = [
  "components/layout/PlatformTopHeader.tsx",
  "components/diagnosis/DiagnosisSummaryPanel.tsx",
  "components/diagnosis/DiagnosisHero.tsx",
  "components/diagnosis/DiagnosticCanvas.tsx",
  "components/diagnosis/StressLabCta.tsx",
  "components/evidence/EvidenceScreen.tsx",
  "components/evidence/StressTestLab.tsx",
  "components/client-fit/ClientFitScreen.tsx",
  "components/hypothesis/HypothesisScreen.tsx",
  "components/comparison/ComparisonScreen.tsx",
  "components/verdict/VerdictScreen.tsx",
  "components/report/ReportScreen.tsx"
];

const defensivePrimaryPatterns = [
  /current[- ]portfolio[- ]first/i,
  /current only/i,
  /scope:\s*current/i,
  /not a recommendation/i,
  /not a rebalance/i,
  /not.*rebalance recommendation/i,
  /before (?:any|testing|generating).*candidate/i,
  /only after .*candidate/i,
  /candidate testing/i,
  /diagnostic only/i,
  /decision-support evidence only/i
];

test("primary UI surfaces do not expose defensive IA guardrails as repeated copy", () => {
  for (const relPath of primarySurfaceFiles) {
    const source = read(relPath);
    for (const pattern of defensivePrimaryPatterns) {
      assert.doesNotMatch(source, pattern, `${relPath} contains defensive primary copy: ${pattern}`);
    }
  }
});

test("Diagnosis primary surface has a single quiet evidence-quality mention and no candidate boundary copy", () => {
  const diagnosisPrimary = [
    "components/diagnosis/DiagnosisSummaryPanel.tsx",
    "components/diagnosis/DiagnosisHero.tsx",
    "components/diagnosis/DiagnosticCanvas.tsx",
    "components/diagnosis/StressLabCta.tsx"
  ].map(read).join("\n");

  assert.ok(countMatches(diagnosisPrimary, /Evidence quality|Quality:/gi) <= 1, "Diagnosis repeats evidence quality in primary UI");
  assert.doesNotMatch(diagnosisPrimary, /Scope note|before .*candidate|candidate testing|Only after/i);
  assert.doesNotMatch(diagnosisPrimary, /Advanced diagnostics and technical evidence|Evidence chain notes/i);
});

test("platform top header keeps review execution status out of primary metadata", () => {
  const source = read("components/layout/PlatformTopHeader.tsx");
  assert.doesNotMatch(source, /normalizeStatus/);
  assert.doesNotMatch(source, /Review partial|Review completed|Review running|Review needs attention/);
  assert.doesNotMatch(source, /reviewStatus/);
});
