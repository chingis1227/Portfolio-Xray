import type { ReactNode } from "react";
import type { StatusTone } from "@/lib/types";

type MetricValueProps = {
  label: ReactNode;
  value: ReactNode;
  detail?: ReactNode;
  tone?: StatusTone;
  size?: "sm" | "md";
};

function valueTone(tone?: StatusTone) {
  if (tone === "red") return "text-pmri-risk";
  if (tone === "amber") return "text-pmri-amber";
  if (tone === "blue") return "text-pmri-blueSoft";
  return "text-pmri-text";
}

export function MetricValue({ label, value, detail, tone, size = "md" }: MetricValueProps) {
  return (
    <div className="min-w-0">
      <p className="pmri-type-meta text-pmri-muted">{label}</p>
      <p className={`data-figure mt-2 font-semibold leading-none tracking-[-0.035em] ${size === "sm" ? "text-lg" : "text-2xl"} ${valueTone(tone)}`}>
        {value}
      </p>
      {detail ? <p className="mt-2 text-xs leading-5 text-pmri-muted">{detail}</p> : null}
    </div>
  );
}
