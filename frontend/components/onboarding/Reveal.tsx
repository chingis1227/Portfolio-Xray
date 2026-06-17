"use client";

import { motion, useInView, useReducedMotion } from "framer-motion";
import { useRef, type ReactNode } from "react";
import { revealVariants } from "@/components/ui/motion";

const revealLayoutClasses = {
  default: "",
  hero: "relative z-10 w-full",
  stack: "space-y-6",
  centered: "text-center",
  centeredColumn: "flex flex-col justify-center"
};

type RevealLayout = keyof typeof revealLayoutClasses;

export function Reveal({
  children,
  layout = "default",
  delay = 0
}: {
  children: ReactNode;
  layout?: RevealLayout;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -12% 0px", amount: 0.12 });
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      ref={ref}
      className={revealLayoutClasses[layout]}
      custom={reduceMotion ? 0 : delay}
      initial={reduceMotion ? { opacity: 1, y: 0 } : "hidden"}
      animate={isInView || reduceMotion ? "visible" : "hidden"}
      variants={revealVariants}
    >
      {children}
    </motion.div>
  );
}
