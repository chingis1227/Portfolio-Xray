import type { ReactNode } from "react";

const toneClasses = {
  blue: "border-pmri-blue/24 bg-pmri-blue/[0.045] text-pmri-blueSoft",
  gold: "border-pmri-borderSoft/45 bg-white/[0.026] text-pmri-text2",
  green: "border-pmri-positive/24 bg-pmri-positive/[0.052] text-[#8fd1b2]",
  amber: "border-pmri-amber/26 bg-pmri-amber/[0.06] text-[#d5bb88]",
  red: "border-pmri-risk/26 bg-pmri-risk/[0.06] text-[#e09595]",
  slate: "border-pmri-border/58 bg-white/[0.028] text-pmri-text2"
};

type StatusBadgeProps = {
  children: ReactNode;
  tone?: keyof typeof toneClasses;
  className?: string;
};

export function StatusBadge({ children, tone = "slate", className = "" }: StatusBadgeProps) {
  return (
    <span className={`inline-flex max-w-full items-center whitespace-nowrap rounded-full border px-2.5 py-1.5 text-xs font-medium leading-none tracking-[-0.005em] ${toneClasses[tone]} ${className}`}>
      {children}
    </span>
  );
}
