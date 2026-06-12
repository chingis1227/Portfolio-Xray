import { PageHeader } from "@/components/layout/PageHeader";
import { PortfolioInputTable } from "@/components/portfolio/PortfolioInputTable";
import data from "@/data/demo/portfolio-input.json";
import type { Holding } from "@/lib/types";

const portfolio = data as {
  investorCurrency: string;
  holdings: Holding[];
};

export default function PortfolioInputPage() {
  return (
    <div>
      <PageHeader
        kicker="Step 02 / Portfolio to diagnose"
        title="Define the current portfolio"
        description="Enter the portfolio as it stands today. Portfolio MRI will diagnose this allocation before testing any alternative."
      />

      <PortfolioInputTable
        investorCurrency={portfolio.investorCurrency}
        holdings={portfolio.holdings}
      />
    </div>
  );
}
