import { PageHeader } from "@/components/layout/PageHeader";
import { PortfolioInputTable } from "@/components/portfolio/PortfolioInputTable";

export function PortfolioInputScreen() {
  return (
    <div>
      <PageHeader
        kicker="Step 01 of 8"
        title="Define the current portfolio"
        description="Enter the portfolio as it stands today. Portfolio MRI will diagnose this allocation before testing any alternative."
      />

      <PortfolioInputTable
        investorCurrency="USD"
        holdings={[]}
      />
    </div>
  );
}
