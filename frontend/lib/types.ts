export type AssetClass =
  | "현금"
  | "예적금"
  | "ETF"
  | "개별주식"
  | "금"
  | "보증금"
  | "기타자산";

export type SyncState = "connected" | "disconnected" | "stale" | "syncing";

export interface DashboardSummary {
  as_of: string;
  net_worth: number;
  total_assets: number;
  total_debts: number;
  cash_value: number;
  savings_value: number;
  investment_value: number;
  gold_value: number;
  deposit_value: number;
  other_assets_value: number;
  net_worth_change: { amount: number; rate: number };
  last_notion_sync: string | null;
  last_toss_sync: string | null;
  warnings: string[];
}

export interface AllocationItem {
  asset_class: AssetClass;
  current_value: number;
  current_weight: number;
  target_weight: number;
  minimum_weight: number | null;
  maximum_weight: number | null;
  weight_difference: number;
  target_amount: number;
  amount_difference: number;
  status: "UNDERWEIGHT" | "NORMAL" | "OVERWEIGHT";
}

export interface HistoryPoint {
  date: string;
  net_worth: number;
  total_assets: number;
  total_debts: number;
}

export interface ManualAsset {
  id: string;
  name: string;
  account: string;
  institution: string;
  asset_type: string;
  asset_class: AssetClass;
  amount_krw: number;
  currency: string;
  liquidity: "높음" | "보통" | "낮음";
  valued_at: string;
}

export interface InvestmentPosition {
  id: string;
  name: string;
  symbol: string;
  account: string;
  market: string;
  security_type: "ETF" | "개별주식" | "OTHER";
  currency: string;
  quantity: number;
  average_price: number;
  current_price: number;
  cost_basis: number;
  market_value_krw: number;
  unrealized_pnl_krw: number;
  return_rate: number;
  portfolio_weight: number;
}

export interface SavingsProduct {
  id: string;
  name: string;
  institution: string;
  product_type: string;
  current_balance: number;
  monthly_contribution: number;
  annual_rate: number;
  opened_at: string;
  maturity_at: string;
  days_remaining: number;
  estimated_interest_after_tax: number;
  estimated_maturity_amount: number;
}

export interface Debt {
  id: string;
  name: string;
  institution: string;
  debt_type: string;
  original_balance: number;
  current_balance: number;
  annual_rate: number;
  repayment_progress: number;
  monthly_payment: number;
  maturity_at: string;
}

export interface Goal {
  id: string;
  name: string;
  goal_type: string;
  current_value: number;
  target_amount: number;
  progress: number;
  target_date: string;
  days_remaining: number;
}

export interface Account {
  id: string;
  name: string;
  institution: string;
  account_type: string;
  currency: string;
  source_type: "NOTION" | "TOSS";
  is_active: boolean;
  include_in_net_worth: boolean;
}

export interface SyncStatus {
  notion: { state: SyncState; last_sync: string | null; message: string };
  toss: { state: SyncState; last_sync: string | null; message: string };
  database: { state: SyncState; last_sync: string | null; message: string };
}
