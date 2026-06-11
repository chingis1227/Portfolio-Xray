type ReportSection = {
  title: string;
  body: string;
};

export function ClientReadyReportPreview({ title, subtitle, sections, nextObservation, boundaryNote }: { title: string; subtitle: string; sections: ReportSection[]; nextObservation: string; boundaryNote: string }) {
  const [executiveSummary, ...supportingSections] = sections;

  return (
    <section className="pmri-card rounded-2xl p-6 md:p-8">
      <div className="border-b border-pmri-border/40 pb-6">
        <p className="pmri-label">Report preview</p>
        <h2 className="pmri-heading-display mt-3 max-w-4xl text-pmri-text">{title}</h2>
        <p className="mt-3 max-w-3xl text-base leading-7 text-pmri-text2">{subtitle}</p>
      </div>

      {executiveSummary ? (
        <article className="mt-6 rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-6">
          <p className="pmri-label">Executive summary</p>
          <h3 className="pmri-heading-section mt-2 text-2xl text-pmri-text">{executiveSummary.title}</h3>
          <p className="mt-3 max-w-4xl text-base leading-7 text-pmri-text2">{executiveSummary.body}</p>
        </article>
      ) : null}

      <div className="mt-7 grid gap-4 md:grid-cols-2">
        {supportingSections.map((section) => (
          <article key={section.title} className="rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-5">
            <h3 className="pmri-heading-section text-lg text-pmri-text">{section.title}</h3>
            <p className="mt-3 text-sm leading-7 text-pmri-text2">{section.body}</p>
          </article>
        ))}
      </div>
      <div className="mt-7 grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <article className="rounded-2xl border border-pmri-blue/22 bg-pmri-blue/[0.055] p-5">
          <h3 className="font-medium text-pmri-blueSoft">What to watch next</h3>
          <p className="mt-2 text-sm leading-7 text-pmri-text2">{nextObservation}</p>
        </article>
        <article className="rounded-2xl border border-pmri-border/45 bg-white/[0.026] p-5">
          <h3 className="font-medium text-pmri-text2">Decision boundary</h3>
          <p className="mt-2 text-sm leading-7 text-pmri-text2">{boundaryNote}</p>
        </article>
      </div>
    </section>
  );
}
