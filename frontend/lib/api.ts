import { z } from "zod";
import {
  accounts,
  allocation,
  assets,
  debts,
  goals,
  history,
  positions,
  savings,
  summary,
  syncStatus,
} from "./demo-data";
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

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001/api";
const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE !== "false";

const numberSchema = z.coerce.number();
const summarySchema = z.object({
  as_of: z.string(),
  net_worth: numberSchema,
  total_assets: numberSchema,
  total_debts: numberSchema,
  cash_value: numberSchema,
  savings_value: numberSchema,
  investment_value: numberSchema,
  gold_value: numberSchema,
  deposit_value: numberSchema,
  other_assets_value: numberSchema,
  net_worth_change: z.object({ amount: numberSchema, rate: numberSchema }),
  last_notion_sync: z.string().nullable(),
  last_toss_sync: z.string().nullable(),
  warnings: z.array(z.string()).default([]),
});

async function request<T>(path: string, fallback: T, init?: RequestInit): Promise<T> {
  if (DEMO_MODE) return Promise.resolve(fallback);
  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
    if (!response.ok) throw new Error(`API ${response.status}`);
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export const portfolioApi = {
  async summary(): Promise<DashboardSummary> {
    const data = await request("/dashboard/summary", summary);
    return summarySchema.parse(data);
  },
  allocation: () => request<AllocationItem[]>("/dashboard/allocation", allocation),
  history: (range = "1y") => request<HistoryPoint[]>(`/history/net-worth?range=${range}`, history),
  accounts: () => request<Account[]>("/accounts", accounts),
  assets: () => request<ManualAsset[]>("/assets", assets),
  positions: () => request<InvestmentPosition[]>("/investments/positions", positions),
  savings: () => request<SavingsProduct[]>("/savings", savings),
  debts: () => request<Debt[]>("/debts", debts),
  goals: () => request<Goal[]>("/goals", goals),
  syncStatus: () => request<SyncStatus>("/sync/status", syncStatus),
  sync: (provider: "notion" | "toss") =>
    request(`/sync/${provider}`, { status: "success", provider }, { method: "POST" }),
};
