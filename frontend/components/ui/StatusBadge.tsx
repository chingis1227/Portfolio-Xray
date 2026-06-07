import type { ReactNode } from "react";

const toneClasses = {
  blue: "border-pmri-blue/30 bg-pmri-blue/10 text-pmri-blueSoft",
  gold: "border-pmri-gold/38 bg-pmri-gold/10 text-pmri-gold",
  green: "border-pmri-positive/30 bg-pmri-positive/10 text-pmri-positive",
  amber: "border-pmri-amber/35 bg-pmri-amber/10 text-pmri-amber",
  red: "border-pmri-risk/35 bg-pmri-risk/10 text-pmri-risk",
  slate: "border-pmri-border/80 bg-white/[0.04] text-pmri-text2"
};

type StatusBadgeProps = {
  children: ReactNode;
  tone?: keyof typeof toneClasses;
  className?: string;
};

export function StatusBadge({ children, tone = "slate", className = "" }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold leading-none tracking-[0.01em] ${toneClasses[tone]} ${className}`}>
      {children}
    </span>
  );
}
