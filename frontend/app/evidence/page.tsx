import { Suspense } from "react";
import { EvidenceScreen } from "@/components/evidence/EvidenceScreen";

export default function EvidencePage() {
  return (
    <Suspense fallback={null}>
      <EvidenceScreen />
    </Suspense>
  );
}
