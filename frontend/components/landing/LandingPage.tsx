import Link from "next/link";
import { BrandMark } from "@/components/onboarding/BrandMark";
import { Reveal } from "@/components/onboarding/Reveal";

const problemBullets = [
  "No clear allocation logic",
  "No view of hidden concentration",
  "No stress evidence before changing",
  "No framework to defend a decision"
];

const workflow = [
  {
    number: "01",
    title: "Input",
    text: "Enter the portfolio as it stands today: tickers, weights, currency, and cash."
  },
  {
    number: "02",
    title: "Diagnosis",
    text: "Diagnose exposures, concentration, risk contributors, and structural weak points in the current portfolio."
  },
  {
    number: "03",
    title: "Stress Lab",
    text: "Replay stress scenarios and identify what hurts, what helps, and where protection is missing."
  },
  {
    number: "04",
    title: "Client Fit",
    text: "Compare the evidence against the stated profile in plain language."
  },
  {
    number: "05",
    title: "Verdict",
    text: "Test one diagnostic path and get a grounded, non-binding decision-support verdict."
  }
];

const architecture = [
  ["Portfolio Diagnosis", "Composition, factor sensitivity, hidden exposure, risk budget, and weakness map."],
  ["Stress Test Lab", "Synthetic and historical pressure tests with helped/hurt evidence and hedge-gap context."],
  ["Problem Classification", "Turns evidence into a diagnosis before any diagnostic test is prepared."],
  ["Diagnostic Test Launchpad", "Suggests one diagnostic test path from the actual problem, not from generic optimization."],
  ["Current vs Test Candidate", "Shows what improves, what worsens, what is neutral, and what remains unclear."],
  ["Grounded Report", "Client-ready commentary tied to active review evidence and explicit limitations."]
];

const precisionStats = [
  ["Current first", "Diagnosis begins with the existing portfolio."],
  ["1 path", "One hypothesis is tested at a time."],
  ["Same review", "Evidence is tied to the active review chain."],
  ["Non-binding", "Verdict frames support, not orders."]
];

const platformEntryHref = "/onboarding/sign-in";

export function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-pmri-bg text-pmri-text">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_6%,rgba(96,165,250,0.13),transparent_24%),radial-gradient(circle_at_12%_14%,rgba(170,183,198,0.075),transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.035),transparent_42%)]" />

      <header className="relative z-20 mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-6 md:px-8">
        <Link href="/" className="pmri-focus flex items-center gap-3 rounded-full">
          <BrandMark size="md" />
          <div>
            <p className="text-sm font-semibold tracking-[-0.025em] text-pmri-text">Portfolio MRI</p>
            <p className="text-xs text-pmri-muted">Investment Decision Room</p>
          </div>
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-pmri-muted md:flex" aria-label="Landing navigation">
          <a href="#problem" className="transition hover:text-pmri-text">Problem</a>
          <a href="#workflow" className="transition hover:text-pmri-text">How it works</a>
          <a href="#architecture" className="transition hover:text-pmri-text">Architecture</a>
          <a href="#precision" className="transition hover:text-pmri-text">Precision</a>
          <Link href={platformEntryHref} className="pmri-focus rounded-full border border-pmri-blue/35 px-5 py-2.5 font-semibold text-pmri-text transition hover:border-pmri-blue/60 hover:bg-pmri-blue/[0.08]">
            Enter Platform
          </Link>
        </nav>
      </header>

      <section className="relative z-10 mx-auto flex min-h-[calc(100vh-88px)] w-full max-w-7xl flex-col items-center justify-center px-5 pb-24 pt-10 text-center md:px-8">
        <div className="pointer-events-none absolute inset-x-[-16vw] bottom-[-230px] h-[620px] border-y border-pmri-blue/10 opacity-80 pmri-moving-grid" />
        <Reveal layout="hero">
          <p className="data-figure text-4xl font-semibold tracking-[0.45em] text-pmri-blueSoft drop-shadow-[0_0_18px_rgba(96,165,250,0.25)] md:text-6xl">
            PORTFOLIO MRI
          </p>
          <p className="mt-5 text-xs font-medium uppercase tracking-[0.55em] text-pmri-muted">
            Portfolio diagnostics & investment decision-support system
          </p>
          <h1 className="mx-auto mt-8 max-w-6xl text-5xl font-semibold leading-[0.98] tracking-[-0.055em] text-pmri-text md:text-7xl lg:text-8xl">
            Diagnose portfolio risk before you rebalance.
          </h1>
          <p className="mx-auto mt-7 max-w-3xl text-lg leading-8 text-pmri-text2 md:text-xl">
            Portfolio MRI turns current holdings into stress-tested decision evidence before any alternative is considered.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href={platformEntryHref} className="pmri-focus pmri-primary-action inline-flex items-center justify-center rounded-full px-8 py-3.5 text-sm font-semibold transition">
              Enter Platform
            </Link>
            <a href="#workflow" className="pmri-focus inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-semibold text-pmri-blueSoft transition hover:text-pmri-text">
              See how it works ↓
            </a>
          </div>
          <div className="mx-auto mt-10 flex max-w-3xl flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-pmri-muted">
            <span>Current portfolio first</span>
            <span className="text-pmri-blueSoft">•</span>
            <span>Stress-tested evidence</span>
            <span className="text-pmri-blueSoft">•</span>
            <span>Diagnostic tests, not orders</span>
          </div>
        </Reveal>
      </section>

      <section id="problem" className="relative z-10 border-y border-pmri-border/40 bg-pmri-secondary/45 px-5 py-24 md:px-8">
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[0.95fr_1.05fr]">
          <Reveal>
            <h2 className="text-4xl font-semibold uppercase leading-[1.05] tracking-[-0.045em] text-pmri-text md:text-6xl">
              Too many tickers. Too little diagnosis.
            </h2>
            <div className="mt-8 h-1 w-24 rounded-full bg-pmri-blueSoft" />
            <p className="mt-8 max-w-2xl text-lg leading-8 text-pmri-text2">
              Many investors hold a collection of ETFs, funds, stocks, and cash and call it a portfolio. But a list of products does not explain concentration, interaction, stress behavior, or what would make a change worth testing.
            </p>
          </Reveal>
          <Reveal delay={120} layout="stack">
            <div className="grid gap-4">
              {problemBullets.map((item) => (
                <div key={item} className="flex items-center gap-4 rounded-2xl border border-pmri-border/45 bg-white/[0.02] px-5 py-4">
                  <span className="h-2 w-2 rotate-45 bg-pmri-blueSoft shadow-[0_0_18px_rgba(96,165,250,0.55)]" aria-hidden="true" />
                  <span className="font-medium text-pmri-text2">{item}</span>
                </div>
              ))}
            </div>
            <p className="rounded-3xl border border-pmri-blue/20 bg-pmri-blue/[0.055] p-6 text-lg leading-8 text-pmri-text2">
              The result: portfolios built on narrative, not evidence. Portfolio MRI gives the current portfolio a structured diagnostic chain before any alternative is considered.
            </p>
          </Reveal>
        </div>
      </section>

      <section id="workflow" className="relative z-10 px-5 py-24 md:px-8">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_10%,rgba(96,165,250,0.08),transparent_28%)]" />
        <div className="relative mx-auto max-w-7xl">
          <Reveal layout="centered">
            <p className="pmri-label text-pmri-blueSoft">How it works</p>
            <h2 className="mx-auto mt-4 max-w-6xl text-4xl font-semibold uppercase leading-[1.02] tracking-[-0.045em] text-pmri-text md:text-6xl">
              From raw holdings to a defensible decision path.
            </h2>
            <p className="mx-auto mt-6 max-w-3xl text-lg leading-8 text-pmri-text2">
              The platform is not a dashboard wall. It is a guided sequence from input to diagnosis, evidence, one testable hypothesis, comparison, verdict, and report.
            </p>
          </Reveal>
          <div className="mt-14 grid gap-5 md:grid-cols-2 xl:grid-cols-5">
            {workflow.map((item, index) => (
              <Reveal key={item.number} delay={index * 85}>
                <article className="pmri-card pmri-interactive-card flex min-h-[310px] flex-col rounded-3xl p-6 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-pmri-blue/35 bg-pmri-blue/[0.075] data-figure text-sm text-pmri-blueSoft">
                    {item.number}
                  </div>
                  <h3 className="mt-7 text-xl font-semibold uppercase tracking-[0.08em] text-pmri-text">{item.title}</h3>
                  <p className="mt-5 text-sm leading-7 text-pmri-text2">{item.text}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="architecture" className="relative z-10 overflow-hidden border-y border-pmri-border/40 bg-pmri-secondary/55 px-5 py-24 md:px-8">
        <div className="pointer-events-none absolute right-[-14%] top-[-12%] h-[560px] w-[560px] rounded-full border border-pmri-blue/10 bg-[radial-gradient(circle,rgba(96,165,250,0.13),transparent_60%)]" />
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[0.82fr_1.18fr]">
          <Reveal>
            <p className="pmri-label text-pmri-blueSoft">One system. One evidence chain.</p>
            <h2 className="mt-4 text-4xl font-semibold uppercase leading-[1.04] tracking-[-0.045em] text-pmri-text md:text-6xl">
              Diagnosis architecture, not an optimizer cockpit.
            </h2>
            <p className="mt-7 text-lg leading-8 text-pmri-text2">
              Portfolio MRI connects diagnosis evidence, stress behavior, Client Fit context, diagnostic testing, comparison, verdict, and grounded commentary into one portfolio-first workflow.
            </p>
          </Reveal>
          <div className="grid gap-4 md:grid-cols-2">
            {architecture.map(([title, text], index) => (
              <Reveal key={title} delay={index * 70}>
                <article className="rounded-3xl border border-pmri-border/55 bg-white/[0.025] p-6 transition hover:border-pmri-blue/30 hover:bg-white/[0.04]">
                  <h3 className="text-lg font-semibold tracking-[-0.025em] text-pmri-text">{title}</h3>
                  <p className="mt-3 text-sm leading-7 text-pmri-muted">{text}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="precision" className="relative z-10 px-5 py-24 md:px-8">
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[1fr_0.9fr]">
          <Reveal>
            <h2 className="text-4xl font-semibold uppercase tracking-[-0.045em] text-pmri-text md:text-6xl">
              Built for precision.
            </h2>
            <div className="mt-10 grid overflow-hidden rounded-3xl border border-pmri-border/50 bg-white/[0.018] md:grid-cols-2">
              {precisionStats.map(([value, label]) => (
                <div key={value} className="border-b border-r border-pmri-border/40 p-8 text-center last:border-r-0 md:[&:nth-child(2n)]:border-r-0 md:[&:nth-child(n+3)]:border-b-0">
                  <p className="data-figure text-4xl font-semibold tracking-[-0.04em] text-pmri-blueSoft drop-shadow-[0_0_18px_rgba(96,165,250,0.28)]">{value}</p>
                  <p className="mt-2 text-sm leading-6 text-pmri-muted">{label}</p>
                </div>
              ))}
            </div>
          </Reveal>
          <Reveal delay={120} layout="centeredColumn">
            <p className="text-xl leading-9 text-pmri-text2">
              Every screen is designed to answer a decision question: what did we receive, what is the diagnosis, what evidence supports it, what hypothesis is being tested, what changed, and whether the evidence is strong enough for a non-binding verdict.
            </p>
            <p className="mt-6 text-sm leading-7 text-pmri-muted">
              The product keeps generated evidence files, stale runs, legacy optimizer outputs, and technical diagnostics separated from the current user-facing decision path.
            </p>
          </Reveal>
        </div>
      </section>

      <section className="relative z-10 px-5 pb-24 md:px-8">
        <Reveal>
          <div className="mx-auto max-w-5xl rounded-[2rem] border border-pmri-blue/20 bg-[linear-gradient(135deg,rgba(59,130,246,0.16),rgba(255,255,255,0.025)_38%,rgba(16,17,20,0.9))] p-8 text-center shadow-decision md:p-12">
            <p className="pmri-label text-pmri-blueSoft">Ready to inspect your portfolio...</p>
            <h2 className="mt-3 text-4xl font-semibold uppercase tracking-[-0.045em] text-pmri-text md:text-6xl">Open the decision room.</h2>
            <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-pmri-text2">
              Sign in, answer the short setup questions, then enter your tickers and weights. The system starts with diagnosis, not a trade instruction.
            </p>
            <Link href={platformEntryHref} className="pmri-focus pmri-primary-action mt-8 inline-flex items-center justify-center rounded-full px-8 py-3.5 text-sm font-semibold transition">
              Enter Platform
            </Link>
          </div>
        </Reveal>
      </section>
    </main>
  );
}
