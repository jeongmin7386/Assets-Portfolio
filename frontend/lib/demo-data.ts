import type {
  Account,
  AllocationItem,
  DashboardSummary,
  Debt,
  Goal,
  HistoryPoint,
  InvestmentPosition,
  ManualAsset,
  SavingsProduct,
  SyncStatus,
} from "./types";

export const summary: DashboardSummary = {
  as_of: "2026-08-16T19:20:00+09:00",
  net_worth: 57_965_740,
  total_assets: 69_765_740,
  total_debts: 11_800_000,
  cash_value: 9_820_000,
  savings_value: 18_460_000,
  investment_value: 25_035_740,
  gold_value: 2_650_000,
  deposit_value: 12_000_000,
  other_assets_value: 1_800_000,
  net_worth_change: { amount: 2_418_600, rate: 4.35 },
  last_notion_sync: "2026-08-16T19:17:00+09:00",
  last_toss_sync: "2026-08-16T19:19:00+09:00",
  warnings: [],
};

const allocationBase = [
  ["현금", 9_820_000, 15, 10, 20],
  ["예적금", 18_460_000, 25, 20, 30],
  ["ETF", 17_200_000, 30, 27, 34],
  ["개별주식", 7_835_740, 10, 7, 13],
  ["금", 2_650_000, 5, 3, 7],
  ["보증금", 12_000_000, 12, 10, 16],
  ["기타자산", 1_800_000, 3, 0, 5],
] as const;

export const allocation: AllocationItem[] = allocationBase.map(
  ([asset_class, current_value, target_weight, minimum_weight, maximum_weight]) => {
    const current_weight = (current_value / summary.total_assets) * 100;
    const target_amount = summary.total_assets * (target_weight / 100);
    return {
      asset_class,
      current_value,
      current_weight,
      target_weight,
      minimum_weight,
      maximum_weight,
      weight_difference: current_weight - target_weight,
      target_amount,
      amount_difference: current_value - target_amount,
      status:
        current_weight < minimum_weight
          ? "UNDERWEIGHT"
          : current_weight > maximum_weight
            ? "OVERWEIGHT"
            : "NORMAL",
    };
  },
);

export const history: HistoryPoint[] = Array.from({ length: 12 }, (_, index) => {
  const netValues = [
    46.2, 46.8, 47.9, 48.6, 49.4, 50.7, 51.5, 52.9, 54.1, 54.8, 55.55, 57.97,
  ];
  const date = new Date(Date.UTC(2025, 8 + index, 16));
  const net = netValues[index] * 1_000_000;
  const debt = 13_100_000 - index * 118_182;
  return {
    date: date.toISOString(),
    net_worth: net,
    total_assets: net + debt,
    total_debts: debt,
  };
});

export const accounts: Account[] = [
  { id: "acc-1", name: "생활비 통장", institution: "토스뱅크", account_type: "입출금", currency: "KRW", source_type: "NOTION", is_active: true, include_in_net_worth: true },
  { id: "acc-2", name: "자산관리 계좌", institution: "미래은행", account_type: "예적금", currency: "KRW", source_type: "NOTION", is_active: true, include_in_net_worth: true },
  { id: "acc-3", name: "투자 계좌", institution: "토스증권", account_type: "증권", currency: "KRW", source_type: "TOSS", is_active: true, include_in_net_worth: true },
];

export const assets: ManualAsset[] = [
  { id: "asset-1", name: "생활비 잔액", account: "생활비 통장", institution: "토스뱅크", asset_type: "입출금계좌", asset_class: "현금", amount_krw: 7_320_000, currency: "KRW", liquidity: "높음", valued_at: "2026-08-16" },
  { id: "asset-2", name: "비상 현금", account: "현금", institution: "직접 보관", asset_type: "현금", asset_class: "현금", amount_krw: 2_500_000, currency: "KRW", liquidity: "높음", valued_at: "2026-08-16" },
  { id: "asset-3", name: "주거 보증금", account: "주거", institution: "임대인", asset_type: "월세보증금", asset_class: "보증금", amount_krw: 12_000_000, currency: "KRW", liquidity: "낮음", valued_at: "2026-08-01" },
  { id: "asset-4", name: "KRX 금현물", account: "금 계좌", institution: "한국거래소", asset_type: "금현물", asset_class: "금", amount_krw: 2_650_000, currency: "KRW", liquidity: "보통", valued_at: "2026-08-16" },
  { id: "asset-5", name: "퇴직연금 잔액", account: "퇴직연금", institution: "국민은행", asset_type: "기타금융자산", asset_class: "기타자산", amount_krw: 1_800_000, currency: "KRW", liquidity: "낮음", valued_at: "2026-08-01" },
];

export const positions: InvestmentPosition[] = [
  { id: "pos-1", name: "KODEX 미국S&P500TR", symbol: "379800", account: "토스증권 01", market: "KRX", security_type: "ETF", currency: "KRW", quantity: 420, average_price: 15_920, current_price: 18_470, cost_basis: 6_686_400, market_value_krw: 7_757_400, unrealized_pnl_krw: 1_071_000, return_rate: 16.02, portfolio_weight: 30.99 },
  { id: "pos-2", name: "TIGER 미국나스닥100", symbol: "133690", account: "토스증권 01", market: "KRX", security_type: "ETF", currency: "KRW", quantity: 310, average_price: 21_100, current_price: 24_030, cost_basis: 6_541_000, market_value_krw: 7_449_300, unrealized_pnl_krw: 908_300, return_rate: 13.89, portfolio_weight: 29.75 },
  { id: "pos-3", name: "삼성전자", symbol: "005930", account: "토스증권 01", market: "KRX", security_type: "개별주식", currency: "KRW", quantity: 72, average_price: 68_100, current_price: 75_800, cost_basis: 4_903_200, market_value_krw: 5_457_600, unrealized_pnl_krw: 554_400, return_rate: 11.31, portfolio_weight: 21.80 },
  { id: "pos-4", name: "Apple", symbol: "AAPL", account: "토스증권 01", market: "NASDAQ", security_type: "개별주식", currency: "USD", quantity: 14, average_price: 201.24, current_price: 217.38, cost_basis: 3_806_000, market_value_krw: 4_371_440, unrealized_pnl_krw: 565_440, return_rate: 14.86, portfolio_weight: 17.46 },
];

export const savings: SavingsProduct[] = [
  { id: "sav-1", name: "차곡차곡 정기적금", institution: "카카오뱅크", product_type: "정액적립식 적금", current_balance: 8_300_000, monthly_contribution: 500_000, annual_rate: 4.2, opened_at: "2025-11-04", maturity_at: "2026-11-04", days_remaining: 80, estimated_interest_after_tax: 176_420, estimated_maturity_amount: 9_476_420 },
  { id: "sav-2", name: "주택청약종합저축", institution: "우리은행", product_type: "청약", current_balance: 6_160_000, monthly_contribution: 100_000, annual_rate: 3.1, opened_at: "2022-03-18", maturity_at: "2032-03-18", days_remaining: 2039, estimated_interest_after_tax: 620_400, estimated_maturity_amount: 13_980_400 },
  { id: "sav-3", name: "비상금 정기예금", institution: "신한은행", product_type: "예금", current_balance: 4_000_000, monthly_contribution: 0, annual_rate: 3.55, opened_at: "2026-02-10", maturity_at: "2027-02-10", days_remaining: 178, estimated_interest_after_tax: 120_132, estimated_maturity_amount: 4_120_132 },
];

export const debts: Debt[] = [
  { id: "debt-1", name: "학자금 상환", institution: "한국장학재단", debt_type: "학자금대출", original_balance: 15_000_000, current_balance: 9_200_000, annual_rate: 1.7, repayment_progress: 38.67, monthly_payment: 280_000, maturity_at: "2029-12-25" },
  { id: "debt-2", name: "생활 안정 대출", institution: "국민은행", debt_type: "신용대출", original_balance: 4_000_000, current_balance: 2_600_000, annual_rate: 4.9, repayment_progress: 35, monthly_payment: 210_000, maturity_at: "2027-08-30" },
];

export const goals: Goal[] = [
  { id: "goal-1", name: "비상금 800만원", goal_type: "현금", current_value: 9_820_000, target_amount: 8_000_000, progress: 122.75, target_date: "2026-12-31", days_remaining: 137 },
  { id: "goal-2", name: "순자산 8천만원", goal_type: "순자산", current_value: 57_965_740, target_amount: 80_000_000, progress: 72.46, target_date: "2027-12-31", days_remaining: 502 },
  { id: "goal-3", name: "투자자산 4천만원", goal_type: "투자", current_value: 25_035_740, target_amount: 40_000_000, progress: 62.59, target_date: "2028-06-30", days_remaining: 684 },
];

export const syncStatus: SyncStatus = {
  notion: { state: "connected", last_sync: summary.last_notion_sync, message: "6개 Data Source 연결됨" },
  toss: { state: "connected", last_sync: summary.last_toss_sync, message: "읽기 전용 · 1개 계좌" },
  database: { state: "connected", last_sync: summary.as_of, message: "PostgreSQL 정상" },
};
