"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

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
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.12 }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`${revealLayoutClasses[layout]} pmri-scroll-reveal ${visible ? "pmri-scroll-reveal-visible" : ""}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}
