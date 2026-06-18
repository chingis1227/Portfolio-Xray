import type { ReactNode } from "react";

type AdvancedDisclosureProps = {
  title: ReactNode;
  summary?: ReactNode;
  children: ReactNode;
  id?: string;
  defaultOpen?: boolean;
};

export function AdvancedDisclosure({ id, title, summary, children, defaultOpen = false }: AdvancedDisclosureProps) {
  return (
    <details id={id} open={defaultOpen} className="pmri-technical-disclosure rounded-3xl p-5 md:p-6">
      <summary className="pmri-focus cursor-pointer list-none rounded-2xl border border-white/[0.075] bg-white/[0.022] px-4 py-3 transition hover:border-pmri-blue/35 hover:bg-white/[0.04]">
        <span className="flex flex-col gap-1">
          <span className="text-sm font-semibold text-pmri-text">{title}</span>
          {summary ? <span className="text-xs leading-5 text-pmri-muted">{summary}</span> : null}
        </span>
      </summary>
      <div className="mt-5 space-y-5">{children}</div>
    </details>
  );
}
