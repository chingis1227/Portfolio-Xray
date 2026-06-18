import type { HTMLAttributes, ReactNode } from "react";

export type SurfaceTone = "default" | "glass" | "raised" | "subtle" | "risk" | "warning";

const toneClass: Record<SurfaceTone, string> = {
  default: "pmri-card",
  glass: "pmri-glass-panel",
  raised: "pmri-raised-panel",
  subtle: "pmri-subtle-panel",
  risk: "pmri-risk-panel",
  warning: "pmri-warning-panel"
};

type SurfaceProps = HTMLAttributes<HTMLElement> & {
  as?: "section" | "article" | "aside" | "div";
  tone?: SurfaceTone;
  radius?: "xl" | "2xl" | "3xl";
  padding?: "none" | "sm" | "md" | "lg";
  children: ReactNode;
};

const radiusClass = {
  xl: "rounded-xl",
  "2xl": "rounded-2xl",
  "3xl": "rounded-3xl"
};

const paddingClass = {
  none: "",
  sm: "p-4",
  md: "p-5 md:p-6",
  lg: "p-6 md:p-8"
};

export function Surface({ as: Component = "section", tone = "default", radius = "3xl", padding = "md", className, children, ...props }: SurfaceProps) {
  return (
    <Component className={[toneClass[tone], radiusClass[radius], paddingClass[padding], className].filter(Boolean).join(" ")} {...props}>
      {children}
    </Component>
  );
}

export function Card(props: Omit<SurfaceProps, "tone">) {
  return <Surface tone="default" {...props} />;
}

export function GlassPanel(props: Omit<SurfaceProps, "tone">) {
  return <Surface tone="glass" {...props} />;
}
