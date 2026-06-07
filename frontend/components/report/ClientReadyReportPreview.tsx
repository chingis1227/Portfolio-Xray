type ReportSection = {
  title: string;
  body: string;
};

export function ClientReadyReportPreview({ title, subtitle, sections, monitoring, boundaryNote }: { title: string; subtitle: string; sections: ReportSection[]; monitoring: string; boundaryNote: string }) {
  const [executiveSummary, ...supportingSections] = sections;

  return (
    <section className="pmri-card rounded-2xl p-6 md:p-8">
      <div className="border-b border-pmri-border pb-7">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pmri-gold">Report preview</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-[-0.02em] text-pmri-text md:text-4xl">{title}</h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-pmri-text2">{subtitle}</p>
      </div>

      {executiveSummary ? (
        <article className="mt-7 rounded-2xl border border-pmri-gold/35 bg-pmri-gold/10 p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-pmri-gold">Executive summary</p>
          <h3 className="mt-2 text-2xl font-semibold tracking-[-0.02em] text-pmri-text">{executiveSummary.title}</h3>
          <p className="mt-3 max-w-4xl text-base leading-7 text-pmri-text2">{executiveSummary.body}</p>
        </article>
      ) : null}

      <div className="mt-7 grid gap-4 md:grid-cols-2">
        {supportingSections.map((section) => (
          <article key={section.title} className="rounded-2xl border border-pmri-border bg-white/[0.03] p-5">
            <h3 className="text-lg font-semibold text-pmri-text">{section.title}</h3>
            <p className="mt-3 text-sm leading-7 text-pmri-text2">{section.body}</p>
          </article>
        ))}
      </div>
      <div className="mt-7 grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <article className="rounded-2xl border border-pmri-blue/35 bg-pmri-blue/10 p-5">
          <h3 className="font-semibold text-pmri-blueSoft">Monitoring</h3>
          <p className="mt-2 text-sm leading-7 text-pmri-text2">{monitoring}</p>
        </article>
        <article className="rounded-2xl border border-pmri-gold/35 bg-pmri-gold/10 p-5">
          <h3 className="font-semibold text-pmri-gold">Decision boundary</h3>
          <p className="mt-2 text-sm leading-7 text-pmri-gold">{boundaryNote}</p>
        </article>
      </div>
    </section>
  );
}
