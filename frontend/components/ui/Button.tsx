import Link from "next/link";
import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const variantClass: Record<ButtonVariant, string> = {
  primary: "pmri-primary-action",
  secondary: "border border-white/[0.10] bg-white/[0.026] text-pmri-text2 hover:border-pmri-blue/40 hover:bg-white/[0.045] hover:text-pmri-text",
  ghost: "border border-transparent bg-transparent text-pmri-muted hover:border-white/[0.08] hover:bg-white/[0.025] hover:text-pmri-text2",
  danger: "border border-pmri-risk/35 bg-pmri-risk/[0.08] text-[#e19a94] hover:border-pmri-risk/55 hover:bg-pmri-risk/[0.12]"
};

const sizeClass: Record<ButtonSize, string> = {
  sm: "px-3.5 py-2 text-xs",
  md: "px-5 py-2.5 text-sm",
  lg: "px-6 py-3 text-sm"
};

function buttonClass({ variant, size, className }: { variant: ButtonVariant; size: ButtonSize; className?: string }) {
  return [
    "pmri-focus inline-flex items-center justify-center gap-2 rounded-full font-semibold leading-none transition disabled:pointer-events-none disabled:opacity-55",
    sizeClass[size],
    variantClass[variant],
    className
  ].filter(Boolean).join(" ");
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
};

export function Button({ variant = "secondary", size = "md", className, type = "button", ...props }: ButtonProps) {
  return <button type={type} className={buttonClass({ variant, size, className })} {...props} />;
}

type ButtonLinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
  href: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
};

export function ButtonLink({ href, variant = "secondary", size = "md", className, children, ...props }: ButtonLinkProps) {
  return (
    <Link href={href} className={buttonClass({ variant, size, className })} {...props}>
      {children}
    </Link>
  );
}
