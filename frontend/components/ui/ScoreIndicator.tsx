import type { StatusTone } from "@/lib/types";

type ScoreIndicatorProps = {
  score?: number;
  tone?: StatusTone;
  label?: string;
  size?: "xs" | "sm";
};

const toneStyles: Record<string, string> = {
  red: "bg-pmri-risk",
  amber: "bg-pmri-amber",
  green: "bg-pmri-positive",
  blue: "bg-pmri-blue",
  gold: "bg-pmri-amber",
  slate: "bg-pmri-muted"
};

function clampScore(score: number) {
  return Math.max(0, Math.min(100, Math.round(score)));
}

export function ScoreIndicator({ score, tone = "slate", label = "Score", size = "sm" }: ScoreIndicatorProps) {
  const hasScore = typeof score === "number" && Number.isFinite(score);
  const value = hasScore ? clampScore(score) : null;
  const filledBars = value === null ? 0 : Math.max(0, Math.min(5, Math.round(value / 20)));
  const barClass = toneStyles[tone] ?? toneStyles.slate;
  const compact = size === "xs";

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full border border-white/[0.06] bg-black/15 ${compact ? "px-2 py-1" : "px-2.5 py-1.5"}`}
      aria-label={value === null ? `${label}: unavailable` : `${label}: ${value} out of 100`}
      title={value === null ? `${label}: unavailable` : `${label}: ${value}/100`}
    >
      <span className={`data-figure font-semibold text-pmri-text ${compact ? "text-xs" : "text-sm"}`}>
        {value === null ? "N/A" : `${value}%`}
      </span>
      <span className={`flex items-center ${compact ? "gap-0.5" : "gap-1"}`} aria-hidden="true">
        {Array.from({ length: 5 }).map((_, index) => {
          const active = index < filledBars;
          return (
            <span
              key={index}
              className={`${compact ? "h-3 w-1" : "h-4 w-1.5"} rounded-full transition-colors ${active ? `${barClass} opacity-90` : "bg-white/[0.12]"}`}
            />
          );
        })}
      </span>
    </div>
  );
}
