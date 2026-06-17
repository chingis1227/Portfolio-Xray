import Link from "next/link";
import { BrandMark } from "@/components/onboarding/BrandMark";
import { Reveal } from "@/components/onboarding/Reveal";

const platformEntryHref = "/onboarding/sign-in";

const navItems = [
  ["Diagnosis", "#diagnosis"],
  ["Stress Lab", "#stress"],
  ["Decision", "#decision"],
  ["Report", "#report"]
];

const metrics = [
  ["Concentration", "High", "36% in two drivers"],
  ["Stress loss", "-18.4%", "Rate shock scenario"],
  ["Client Fit", "Watch", "Drawdown tolerance gap"]
];

const feed = [
  ["Portfolio Diagnosis", "Risk is concentrated before the candidate stage begins."],
  ["Stress Test Lab", "Inflation shock and liquidity stress both expose the same weakness."],
  ["Candidate Launchpad", "One diagnostic test is ready: reduce concentration while preserving intent."]
];

const featureGrid = [
  ["Current portfolio first", "The system starts with actual holdings, weights, currency, and cash before any alternative is shown."],
  ["Diagnosis before action", "Concentration, risk contribution, hidden exposure, and stress behavior are explained in one evidence chain."],
  ["One candidate hypothesis", "Portfolio MRI tests a candidate as a diagnostic path, not as an automatic recommendation."],
  ["Grounded commentary", "Verdicts and reports stay tied to run-local evidence, limits, and non-binding decision support."],
  ["Client Fit context", "Profile constraints are visible context, not suitability approval or a reason to hide material issues."],
  ["Monitoring posture", "The product keeps the user focused on what changed and why it matters after the review."]
];

const steps = [
  ["01", "Input Portfolio", "Enter the portfolio as it stands today."],
  ["02", "Portfolio Diagnosis", "Find the structure and weak points."],
  ["03", "Stress Test Lab", "Replay pressure before proposing a fix."],
  ["04", "Client Fit Check", "Add profile context without turning it into approval."],
  ["05", "Candidate Launchpad", "Choose one testable path from the diagnosis."],
  ["06", "Decision Verdict", "Compare evidence and produce a bounded verdict."]
];

function MiniChart() {
  return (
    <div className="relative h-52 overflow-hidden rounded-[1.6rem] border border-white/[0.07] bg-black/40 p-5">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_24%,rgba(110,168,215,0.16),transparent_42%)]" />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="data-figure text-3xl font-semibold tracking-[-0.06em] text-pmri-text">$130,067</p>
          <p className="mt-1 text-xs text-pmri-muted">Current portfolio value</p>
        </div>
        <span className="rounded-full border border-pmri-amber/24 bg-pmri-amber/10 px-3 py-1 text-xs font-semibold text-pmri-amber">Watch</span>
      </div>
      <svg className="relative mt-8 h-20 w-full" viewBox="0 0 520 120" aria-hidden="true">
        <path d="M4 84 C 54 72, 74 62, 118 70 S 177 102, 215 74 S 272 37, 314 48 S 383 80, 430 38 S 490 20, 516 28" fill="none" stroke="rgba(110,168,215,0.9)" strokeLinecap="round" strokeWidth="3" />
        <path d="M4 98 C 62 86, 102 78, 156 86 S 238 108, 306 84 S 388 70, 516 66" fill="none" stroke="rgba(236,231,220,0.42)" strokeLinecap="round" strokeWidth="2" />
        <path d="M4 108 L516 108" stroke="rgba(255,255,255,0.08)" strokeDasharray="6 8" />
      </svg>
      <div className="relative mt-3 flex gap-4 text-xs text-pmri-muted">
        <span>Current</span>
        <span className="text-pmri-blueSoft">Stress adjusted</span>
        <span>Reference</span>
      </div>
    </div>
  );
}

function ProductPreview() {
  return (
    <div className="pmri-device-frame relative mx-auto w-full max-w-5xl rounded-[2.1rem] border border-white/[0.09] bg-black/70 p-3 shadow-[0_40px_120px_rgba(0,0,0,0.62)]">
      <div className="overflow-hidden rounded-[1.65rem] border border-white/[0.08] bg-[linear-gradient(135deg,rgba(18,20,24,0.96),rgba(5,6,8,0.96))]">
        <div className="flex items-center gap-2 border-b border-white/[0.06] px-5 py-3">
          <span className="h-2.5 w-2.5 rounded-full bg-pmri-risk" />
          <span className="h-2.5 w-2.5 rounded-full bg-pmri-amber" />
          <span className="h-2.5 w-2.5 rounded-full bg-pmri-blue" />
          <span className="ml-4 text-xs font-medium text-pmri-muted">Portfolio MRI Decision Room</span>
        </div>
        <div className="grid gap-4 p-4 lg:grid-cols-[1.08fr_0.92fr]">
          <div className="space-y-4">
            <MiniChart />
            <div className="grid gap-3 sm:grid-cols-3">
              {metrics.map(([label, value, caption]) => (
                <div key={label} className="rounded-[1.25rem] border border-white/[0.07] bg-white/[0.035] p-4">
                  <p className="text-xs text-pmri-muted">{label}</p>
                  <p className="data-figure mt-2 text-2xl font-semibold text-pmri-text">{value}</p>
                  <p className="mt-2 text-xs leading-5 text-pmri-muted">{caption}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="space-y-3">
            <div className="rounded-[1.45rem] border border-white/[0.1] bg-[linear-gradient(145deg,rgba(255,255,255,0.09),rgba(255,255,255,0.025))] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
              <div className="flex items-center justify-between gap-3">
                <span className="rounded-full bg-white/[0.08] px-3 py-1 text-xs font-semibold text-pmri-text2">Morning diagnosis</span>
                <span className="text-xs text-pmri-muted">Run-local evidence</span>
              </div>
              <p className="mt-5 text-base font-semibold leading-7 text-pmri-text">
                The portfolio is not failing because expected return is unknown. It is exposed because the same holdings drive concentration, stress loss, and Client Fit tension.
              </p>
            </div>
            {feed.map(([title, text]) => (
              <div key={title} className="rounded-[1.35rem] border border-white/[0.065] bg-black/35 p-5">
                <p className="text-sm font-semibold text-pmri-text2">{title}</p>
                <p className="mt-2 text-sm leading-6 text-pmri-muted">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function FloatingDockPreview() {
  return (
    <div className="mx-auto mt-8 flex max-w-3xl items-center justify-center rounded-[2.2rem] border border-white/[0.1] bg-[linear-gradient(180deg,rgba(65,67,72,0.74),rgba(28,29,33,0.72))] p-3 shadow-[0_24px_80px_rgba(0,0,0,0.55),inset_0_1px_0_rgba(255,255,255,0.12)] backdrop-blur-2xl">
      {steps.slice(0, 6).map(([number, title], index) => (
        <div key={title} className={`flex h-12 w-12 items-center justify-center rounded-[1.15rem] border text-xs font-semibold transition md:h-14 md:w-14 ${index === 1 ? "border-white/28 bg-white/[0.16] text-pmri-text" : "border-transparent text-pmri-muted"}`} title={title}>
          {number}
        </div>
      ))}
    </div>
  );
}

export function LandingPage() {
  return (
    <main className="relative min-h-[100dvh] overflow-hidden bg-pmri-bg text-pmri-text">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_-10%,rgba(236,239,243,0.13),transparent_26%),radial-gradient(circle_at_78%_12%,rgba(110,168,215,0.13),transparent_28%),radial-gradient(circle_at_12%_34%,rgba(195,161,95,0.07),transparent_30%),linear-gradient(180deg,rgba(255,255,255,0.035),transparent_38%)]" />
      <div className="pmri-asteroid pointer-events-none absolute left-1/2 top-[-160px] h-[420px] w-[420px] -translate-x-1/2 rounded-full opacity-50 blur-[0.2px]" />

      <header className="relative z-20 mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 md:px-8">
        <Link href="/" className="pmri-focus flex items-center gap-3 rounded-full">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/[0.09] bg-white/[0.04] shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
            <BrandMark size="sm" />
          </span>
          <div>
            <p className="text-sm font-semibold tracking-[-0.025em] text-pmri-text">Portfolio MRI</p>
            <p className="text-xs text-pmri-muted">Diagnosis-first decision room</p>
          </div>
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-pmri-muted md:flex" aria-label="Landing navigation">
          {navItems.map(([label, href]) => (
            <a key={href} href={href} className="transition hover:text-pmri-text">{label}</a>
          ))}
          <Link href={platformEntryHref} className="pmri-focus rounded-full bg-white px-5 py-2.5 font-semibold text-black transition hover:bg-pmri-text2">
            Enter Platform
          </Link>
        </nav>
      </header>

      <section className="relative z-10 mx-auto grid min-h-[calc(100dvh-86px)] w-full max-w-7xl items-center gap-12 px-5 pb-20 pt-8 md:px-8 lg:grid-cols-[0.9fr_1.1fr]">
        <Reveal>
          <p className="inline-flex rounded-full border border-white/[0.08] bg-white/[0.045] px-4 py-2 text-xs font-semibold text-pmri-text2 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
            Current portfolio first. Candidate second.
          </p>
          <h1 className="mt-7 max-w-4xl text-5xl font-semibold leading-[0.96] tracking-[-0.065em] text-pmri-text md:text-7xl lg:text-8xl">
            Diagnose the portfolio before you change it.
          </h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-pmri-text2 md:text-xl">
            Portfolio MRI turns holdings into stress-tested decision evidence, then tests one candidate path only when the diagnosis supports it.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href={platformEntryHref} className="pmri-focus inline-flex items-center justify-center rounded-full bg-white px-8 py-3.5 text-sm font-semibold text-black transition hover:bg-pmri-text2">
              Enter Platform
            </Link>
            <a href="#diagnosis" className="pmri-focus inline-flex items-center justify-center rounded-full border border-white/[0.12] bg-white/[0.035] px-6 py-3.5 text-sm font-semibold text-pmri-text2 transition hover:border-white/25 hover:bg-white/[0.06] hover:text-pmri-text">
              See the evidence chain
            </a>
          </div>
          <div className="mt-10 grid max-w-2xl grid-cols-3 gap-3 text-left">
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
              <p className="data-figure text-2xl font-semibold text-pmri-text">01</p>
              <p className="mt-1 text-xs text-pmri-muted">Diagnosis starts the run</p>
            </div>
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
              <p className="data-figure text-2xl font-semibold text-pmri-text">1</p>
              <p className="mt-1 text-xs text-pmri-muted">Candidate test path</p>
            </div>
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.03] p-4">
              <p className="data-figure text-2xl font-semibold text-pmri-text">0</p>
              <p className="mt-1 text-xs text-pmri-muted">Trade instructions</p>
            </div>
          </div>
        </Reveal>
        <Reveal delay={120}>
          <ProductPreview />
        </Reveal>
      </section>

      <FloatingDockPreview />

      <section id="diagnosis" className="relative z-10 mx-auto max-w-7xl px-5 py-24 md:px-8">
        <Reveal layout="centered">
          <p className="pmri-label text-pmri-blueSoft">Diagnosis architecture</p>
          <h2 className="mx-auto mt-4 max-w-4xl text-4xl font-semibold leading-[1.02] tracking-[-0.05em] text-pmri-text md:text-6xl">
            A calm evidence chain, not a dashboard wall.
          </h2>
          <p className="mx-auto mt-6 max-w-3xl text-lg leading-8 text-pmri-text2">
            Each screen answers one decision question and keeps legacy optimizer artifacts away from the primary user journey.
          </p>
        </Reveal>
        <div className="mt-14 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {featureGrid.map(([title, text], index) => (
            <Reveal key={title} delay={index * 55}>
              <article className="pmri-card pmri-interactive-card min-h-48 rounded-[1.7rem] p-6">
                <h3 className="text-xl font-semibold tracking-[-0.035em] text-pmri-text">{title}</h3>
                <p className="mt-4 text-sm leading-7 text-pmri-muted">{text}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </section>

      <section id="stress" className="relative z-10 border-y border-white/[0.06] bg-white/[0.025] px-5 py-24 md:px-8">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.8fr_1.2fr]">
          <Reveal>
            <p className="pmri-label text-pmri-blueSoft">Canonical flow</p>
            <h2 className="mt-4 text-4xl font-semibold leading-[1.03] tracking-[-0.05em] text-pmri-text md:text-6xl">
              From input to verdict with no hidden leap.
            </h2>
            <p className="mt-6 text-lg leading-8 text-pmri-text2">
              The user moves through diagnosis, stress evidence, Client Fit context, one candidate hypothesis, comparison, and bounded commentary.
            </p>
          </Reveal>
          <div className="grid gap-3">
            {steps.map(([number, title, text], index) => (
              <Reveal key={title} delay={index * 55}>
                <div className="flex items-center gap-5 rounded-[1.5rem] border border-white/[0.07] bg-black/30 p-5">
                  <span className="data-figure flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/[0.09] bg-white/[0.045] text-sm font-semibold text-pmri-text2">{number}</span>
                  <div>
                    <h3 className="text-lg font-semibold tracking-[-0.03em] text-pmri-text">{title}</h3>
                    <p className="mt-1 text-sm leading-6 text-pmri-muted">{text}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="decision" className="relative z-10 mx-auto max-w-7xl px-5 py-24 md:px-8">
        <Reveal>
          <div className="rounded-[2rem] border border-white/[0.09] bg-[linear-gradient(135deg,rgba(255,255,255,0.08),rgba(255,255,255,0.025)_44%,rgba(0,0,0,0.32))] p-8 shadow-[0_32px_90px_rgba(0,0,0,0.45)] md:p-12">
            <div className="grid gap-10 lg:grid-cols-[1fr_0.8fr] lg:items-end">
              <div>
                <p className="pmri-label text-pmri-blueSoft">Non-binding by design</p>
                <h2 className="mt-4 max-w-3xl text-4xl font-semibold leading-[1.02] tracking-[-0.05em] text-pmri-text md:text-6xl">
                  The verdict explains support, trade-offs, and limits.
                </h2>
                <p className="mt-6 max-w-2xl text-lg leading-8 text-pmri-text2">
                  Portfolio MRI does not present Client Fit as approval and does not hide material problems because a profile field is missing or favorable.
                </p>
              </div>
              <div className="rounded-[1.6rem] border border-white/[0.08] bg-black/35 p-5">
                <p className="text-sm font-semibold text-pmri-text">Decision verdict</p>
                <p className="mt-4 text-3xl font-semibold tracking-[-0.05em] text-pmri-text">Testable, not executable.</p>
                <p className="mt-4 text-sm leading-7 text-pmri-muted">
                  The candidate is framed as evidence to review with known limitations, not as a trade order.
                </p>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      <section id="report" className="relative z-10 px-5 pb-28 md:px-8">
        <Reveal layout="centered">
          <div className="mx-auto max-w-4xl text-center">
            <p className="pmri-label text-pmri-blueSoft">Ready to inspect your portfolio</p>
            <h2 className="mt-4 text-4xl font-semibold leading-[1.02] tracking-[-0.05em] text-pmri-text md:text-6xl">Open the decision room.</h2>
            <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-pmri-text2">
              Sign in, enter tickers and weights, then let the product diagnose the current portfolio before it tests any alternative.
            </p>
            <Link href={platformEntryHref} className="pmri-focus mt-8 inline-flex items-center justify-center rounded-full bg-white px-8 py-3.5 text-sm font-semibold text-black transition hover:bg-pmri-text2">
              Enter Platform
            </Link>
          </div>
        </Reveal>
      </section>
    </main>
  );
}
