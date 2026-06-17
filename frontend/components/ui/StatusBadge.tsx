import type { ReactNode } from "react";

const toneClasses = {
  blue: "border-pmri-blue/26 bg-pmri-blue/[0.075] text-pmri-blueSoft shadow-[inset_0_1px_0_rgba(255,255,255,0.045),0_8px_22px_rgba(110,168,215,0.08)]",
  gold: "border-pmri-gold/20 bg-pmri-gold/[0.055] text-pmri-text2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]",
  green: "border-pmri-borderSoft/42 bg-white/[0.036] text-pmri-text2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]",
  amber: "border-pmri-amber/28 bg-pmri-amber/[0.082] text-[#d9bd82] shadow-[inset_0_1px_0_rgba(255,255,255,0.045),0_8px_22px_rgba(195,161,95,0.08)]",
  red: "border-pmri-risk/30 bg-pmri-risk/[0.085] text-[#e19a94] shadow-[inset_0_1px_0_rgba(255,255,255,0.045),0_8px_22px_rgba(182,106,97,0.08)]",
  slate: "border-pmri-border/62 bg-white/[0.038] text-pmri-text2 shadow-[inset_0_1px_0_rgba(255,255,255,0.038)]"
};

const dotClasses = {
  blue: "bg-pmri-blueSoft shadow-[0_0_12px_rgba(157,204,240,0.42)]",
  gold: "bg-pmri-gold shadow-[0_0_10px_rgba(170,183,198,0.25)]",
  green: "bg-pmri-ivory/80 shadow-[0_0_10px_rgba(236,231,220,0.2)]",
  amber: "bg-pmri-amber shadow-[0_0_12px_rgba(195,161,95,0.4)]",
  red: "bg-pmri-risk shadow-[0_0_12px_rgba(182,106,97,0.36)]",
  slate: "bg-pmri-muted/65"
};

type StatusBadgeProps = {
  children: ReactNode;
  tone?: keyof typeof toneClasses;
  dot?: boolean;
};

export function StatusBadge({ children, tone = "slate", dot = tone === "amber" || tone === "red" || tone === "blue" }: StatusBadgeProps) {
  return (
    <span className={`inline-flex max-w-full items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1.5 text-xs font-semibold leading-none tracking-[-0.005em] ${toneClasses[tone]}`}>
      {dot ? <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dotClasses[tone]}`} aria-hidden="true" /> : null}
      {children}
    </span>
  );
}
