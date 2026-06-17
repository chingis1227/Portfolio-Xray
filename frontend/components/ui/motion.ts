"use client";

import type { Variants } from "framer-motion";

export const pmriSpring = {
  type: "spring",
  stiffness: 340,
  damping: 30,
  mass: 0.8
} as const;

export const pmriSoftSpring = {
  type: "spring",
  stiffness: 260,
  damping: 28,
  mass: 0.9
} as const;

export const pageTransition = {
  duration: 0.34,
  ease: [0.22, 1, 0.36, 1]
} as const;

export const pageVariants: Variants = {
  initial: { opacity: 0, y: 14 },
  animate: {
    opacity: 1,
    y: 0,
    transition: pageTransition
  },
  exit: {
    opacity: 0,
    y: 8,
    transition: { duration: 0.18, ease: [0.4, 0, 1, 1] }
  }
};

export const revealVariants: Variants = {
  hidden: { opacity: 0, y: 28 },
  visible: (delayMs: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: {
      ...pmriSoftSpring,
      delay: delayMs / 1000
    }
  })
};

export const listContainerVariants: Variants = {
  hidden: { opacity: 1 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.045,
      delayChildren: 0.035
    }
  }
};

export const listItemVariants: Variants = {
  hidden: { opacity: 0, y: 10, scale: 0.985 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: pmriSoftSpring
  }
};

export const buttonMotion = {
  whileHover: { y: -1, scale: 1.012 },
  whileTap: { scale: 0.985 }
} as const;
