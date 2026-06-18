import type { ReactNode } from "react";
import type { StatusTone } from "@/lib/types";

function valueToneClass(tone?: StatusTone) {
  if (tone === "red") return "text-pmri-risk";
  if (tone === "amber") return "text-pmri-amber";
  if (tone === "blue") return "text-pmri-blueSoft";
  return "text-pmri-text2";
}

export type EvidenceItemProps = {
  label: string;
  value: ReactNode;
  tone?: StatusTone;
  detail?: ReactNode;
};

export function EvidenceItem({ label, value, tone, detail }: EvidenceItemProps) {
  return (
    <div className="px-4 py-3.5">
      <p className="text-[0.68rem] font-medium tracking-[0.055em] text-pmri-muted">{label}</p>
      <p className={`data-figure mt-2 text-sm font-semibold leading-5 ${valueToneClass(tone)}`}>{value}</p>
      {detail ? <p className="mt-1 text-xs leading-5 text-pmri-muted">{detail}</p> : null}
    </div>
  );
}
