import Link from "next/link";
import { BrandMark } from "@/components/onboarding/BrandMark";
import { Reveal } from "@/components/onboarding/Reveal";

const workflow = [
  ["01", "Input Portfolio", "Enter current holdings, weights, currency, and cash as the evidence source."],
  ["02", "Diagnosis", "Read concentration, exposure, risk contribution, and weakness signals first."],
  ["03", "Stress Lab", "Replay pressure scenarios and see which exposures drive losses."],
  ["04", "Client Fit", "Layer investor context beside the portfolio evidence."],
  ["05", "Verdict", "Compare the current portfolio with one bounded test path."],
];

const evidenceProblems = [
  ["Optimize first", "Many tools jump to allocation changes before the portfolio problem is visible."],
  ["Stress later", "Risk often appears as a score, not as a pressure path with contributors."],
  ["Lose lineage", "The reasoning chain between holdings, evidence, test path, and verdict gets fragmented."],
];

const architecture = [
  ["Portfolio Diagnosis", "Current holdings become the primary evidence source."],
  ["Stress Test Lab", "Loss paths, helped/hurt contributors, and hedge gaps."],
  ["Problem Classification", "A diagnosis that names the portfolio problem clearly."],
  ["Candidate Launchpad", "One bounded test path, tied to the same review."],
  ["Current vs Candidate", "What improves, worsens, stays neutral, or remains unclear."],
  ["Decision Verdict", "A grounded trade-off readout with evidence and limits."],
];

const precisionStats = [
  ["Current first", "The existing portfolio stays the subject."],
  ["Evidence first", "The portfolio problem is visible before a path is tested."],
  ["One path", "The launchpad keeps the comparison readable."],
  ["Same run", "Screens follow the same review lineage."],
];

const platformEntryHref = "/onboarding/sign-in";

export function LandingPage() {
  return (
    <main id="main-content" className="relative min-h-screen overflow-hidden bg-pmri-bg text-pmri-text">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_72%_10%,rgba(160,195,236,0.09),transparent_24%),radial-gradient(ellipse_at_80%_18%,rgba(196,181,253,0.07),transparent_30%)]" />

      <header className="relative z-20 mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 md:px-8">
        <Link href="/" className="pmri-focus flex items-center gap-3 rounded-full">
          <BrandMark size="md" />
          <div>
            <p className="text-sm font-normal tracking-[-0.01em] text-pmri-text">Portfolio MRI</p>
            <p className="font-mono text-[0.65rem] uppercase tracking-[0.16em] text-pmri-muted">Investment Decision Room</p>
          </div>
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-pmri-text2 md:flex" aria-label="Landing navigation">
          <a href="#workflow" className="transition hover:text-pmri-text">Workflow</a>
          <a href="#evidence" className="transition hover:text-pmri-text">Evidence</a>
          <a href="#architecture" className="transition hover:text-pmri-text">System</a>
          <a href="#precision" className="transition hover:text-pmri-text">Boundaries</a>
          <Link href={platformEntryHref} className="pmri-focus rounded-full border border-white/25 px-5 py-2.5 text-pmri-text transition hover:border-white/50 hover:bg-white/[0.04]">
            Enter Platform
          </Link>
        </nav>
      </header>

      <section className="relative z-10 mx-auto flex min-h-[calc(100vh-80px)] w-full max-w-7xl flex-col justify-center px-5 pb-24 pt-10 md:px-8">
        <Reveal layout="hero">
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-pmri-muted">Diagnosis-first portfolio intelligence</p>
          <h1 className="mt-7 max-w-6xl text-[clamp(4rem,11vw,8.7rem)] font-normal leading-[0.9] tracking-[-0.055em] text-pmri-text">
            Understand the portfolio before changing it
          </h1>
          <p className="mt-8 max-w-3xl text-lg leading-8 text-pmri-text2 md:text-xl">
            Portfolio MRI turns current holdings into stress-tested evidence, then tests one bounded candidate path only after the problem is named.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link href={platformEntryHref} className="pmri-focus pmri-primary-action inline-flex items-center justify-center rounded-full px-7 py-3 text-sm transition">
              Enter Platform
            </Link>
            <a href="#workflow" className="pmri-focus inline-flex items-center justify-center rounded-full border border-white/25 px-7 py-3 text-sm text-pmri-text transition hover:border-white/50 hover:bg-white/[0.04]">
              Read workflow
            </a>
          </div>
          <div className="mt-12 grid max-w-4xl gap-3 border-y border-pmri-border py-5 font-mono text-[0.68rem] uppercase tracking-[0.16em] text-pmri-muted md:grid-cols-3">
            <span>Current portfolio first</span>
            <span>Stress evidence before candidates</span>
            <span>One review lineage</span>
          </div>
        </Reveal>
      </section>

      <section id="evidence" className="relative z-10 border-y border-pmri-border px-5 py-16 md:px-8">
        <div className="mx-auto max-w-7xl">
          <Reveal>
            <p className="pmri-label">Evidence first</p>
            <h2 className="mt-4 max-w-5xl text-4xl font-normal leading-[1.02] tracking-[-0.04em] text-pmri-text md:text-6xl">
              Most portfolio tools jump straight to the fix
            </h2>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-pmri-text2">
              Portfolio MRI slows the moment down: current holdings become evidence, stress behavior becomes visible, and the candidate path only appears after the problem is named.
            </p>
          </Reveal>
          <div className="mt-10 grid gap-px overflow-hidden rounded-lg border border-pmri-border bg-pmri-border md:grid-cols-3">
            {evidenceProblems.map(([title, text], index) => (
              <Reveal key={title} delay={index * 60}>
                <article className="h-full bg-pmri-surface p-6">
                  <h3 className="text-2xl font-normal tracking-[-0.03em] text-pmri-text">{title}</h3>
                  <p className="mt-4 text-sm leading-7 text-pmri-text2">{text}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="workflow" className="relative z-10 border-b border-pmri-border px-5 py-20 md:px-8">
        <div className="mx-auto max-w-7xl">
          <Reveal>
            <p className="pmri-label">Canonical flow</p>
            <h2 className="mt-4 max-w-5xl text-4xl font-normal leading-[1.02] tracking-[-0.04em] text-pmri-text md:text-6xl">
              A strict chain from raw holdings to a grounded verdict
            </h2>
          </Reveal>
          <div className="mt-12 grid gap-px overflow-hidden rounded-lg border border-pmri-border bg-pmri-border md:grid-cols-5">
            {workflow.map(([number, title, text], index) => (
              <Reveal key={number} delay={index * 70}>
                <article className="h-full min-h-[280px] bg-pmri-surface p-6">
                  <p className="font-mono text-xs uppercase tracking-[0.18em] text-pmri-muted">{number}</p>
                  <h3 className="mt-8 text-2xl font-normal tracking-[-0.03em] text-pmri-text">{title}</h3>
                  <p className="mt-5 text-sm leading-7 text-pmri-text2">{text}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="architecture" className="relative z-10 px-5 py-20 md:px-8">
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[0.8fr_1.2fr]">
          <Reveal>
            <p className="pmri-label">System map</p>
            <h2 className="mt-4 text-4xl font-normal leading-[1.02] tracking-[-0.04em] text-pmri-text md:text-6xl">
              A decision room for portfolio evidence
            </h2>
            <p className="mt-7 text-lg leading-8 text-pmri-text2">
              Portfolio MRI keeps the same review context moving forward: current portfolio, stress behavior, client fit context, candidate test, comparison, and verdict.
            </p>
          </Reveal>
          <div className="grid gap-px overflow-hidden rounded-lg border border-pmri-border bg-pmri-border md:grid-cols-2">
            {architecture.map(([title, text], index) => (
              <Reveal key={title} delay={index * 55}>
                <article className="h-full bg-pmri-surface p-6 transition hover:bg-pmri-surface2">
                  <h3 className="text-xl font-normal tracking-[-0.025em] text-pmri-text">{title}</h3>
                  <p className="mt-3 text-sm leading-7 text-pmri-text2">{text}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="precision" className="relative z-10 border-t border-pmri-border px-5 py-20 md:px-8">
        <div className="mx-auto max-w-7xl">
          <Reveal>
            <p className="pmri-label">Product boundaries</p>
            <h2 className="mt-4 max-w-5xl text-4xl font-normal tracking-[-0.04em] text-pmri-text md:text-6xl">
              Built to preserve diagnostic discipline
            </h2>
          </Reveal>
          <div className="mt-12 grid gap-px overflow-hidden rounded-lg border border-pmri-border bg-pmri-border md:grid-cols-4">
            {precisionStats.map(([value, label]) => (
              <div key={value} className="bg-pmri-surface p-7">
                <p className="text-3xl font-normal tracking-[-0.04em] text-pmri-text">{value}</p>
                <p className="mt-3 text-sm leading-6 text-pmri-muted">{label}</p>
              </div>
            ))}
          </div>
          <div className="mt-12 max-w-4xl rounded-lg border border-white/25 bg-pmri-bg p-7">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-pmri-muted">Ready</p>
            <h2 className="mt-3 text-4xl font-normal tracking-[-0.04em] text-pmri-text md:text-6xl">Open the investment decision room</h2>
            <p className="mt-5 max-w-2xl text-base leading-7 text-pmri-text2">
              Sign in, answer the short setup questions, and enter the current portfolio. The first output is diagnosis: exposure, stress behavior, and the problem worth testing.
            </p>
            <Link href={platformEntryHref} className="pmri-focus pmri-primary-action mt-7 inline-flex items-center justify-center rounded-full px-7 py-3 text-sm transition">
              Enter Platform
            </Link>
            <p className="mt-8 max-w-3xl border-t border-pmri-border pt-5 text-xs leading-6 text-pmri-muted">
              Portfolio MRI provides non-binding diagnostic decision support. It does not provide investment advice, suitability approval, or trade instructions.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
