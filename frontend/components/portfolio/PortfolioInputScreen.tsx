import { PageHeader } from "@/components/layout/PageHeader";
import { PortfolioInputTable } from "@/components/portfolio/PortfolioInputTable";

export function PortfolioInputScreen() {
  return (
    <div>
      <PageHeader
        kicker="Step 01 / Portfolio to diagnose"
        title="Define the current portfolio case file"
        description="Enter the portfolio as it stands today. The first answer is whether this input is ready for diagnosis, not whether an alternative should be built."
      />

      <PortfolioInputTable
        investorCurrency="USD"
        holdings={[]}
      />
    </div>
  );
}
