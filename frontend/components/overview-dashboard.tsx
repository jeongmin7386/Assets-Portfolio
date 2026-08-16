"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowDownRight, ArrowUpRight, Landmark, PiggyBank, TrendingUp, WalletCards } from "lucide-react";
import { portfolioApi } from "@/lib/api";
import { formatDateTime, formatKRW, formatRate } from "@/lib/format";
import { AllocationDonut, NetWorthChart } from "./charts";
import { PageHeader } from "./page-header";
import { StatCard } from "./stat-card";

export function OverviewDashboard() {
  const summaryQuery = useQuery({ queryKey: ["summary"], queryFn: portfolioApi.summary });
  const allocationQuery = useQuery({ queryKey: ["allocation"], queryFn: portfolioApi.allocation });
  const historyQuery = useQuery({ queryKey: ["history", "1y"], queryFn: () => portfolioApi.history("1y") });

  if (!summaryQuery.data || !allocationQuery.data || !historyQuery.data) return <OverviewSkeleton />;
  const summary = summaryQuery.data;
  const positive = summary.net_worth_change.amount >= 0;

  return (
    <>
      <PageHeader eyebrow="MY PORTFOLIO" title="오늘의 자산" description="흩어진 자산을 모아, 지금의 재무 위치를 선명하게 봅니다." />
      {summary.warnings.length > 0 && <div className="warning-banner">{summary.warnings.join(" · ")}</div>}
      <section className="net-worth-hero">
        <div>
          <span className="hero-label">순자산</span>
          <h2>{formatKRW(summary.net_worth)}</h2>
          <p className={positive ? "change positive" : "change negative"}>
            {positive ? <ArrowUpRight size={17} /> : <ArrowDownRight size={17} />}
            지난달보다 {formatKRW(summary.net_worth_change.amount)} ({formatRate(summary.net_worth_change.rate)})
          </p>
        </div>
        <div className="hero-meta">
          <span>마지막 업데이트</span>
          <strong>{formatDateTime(summary.as_of)}</strong>
          <small>Notion · Toss 최신 데이터 반영</small>
        </div>
      </section>

      <section className="stat-grid four">
        <StatCard label="총자산" value={formatKRW(summary.total_assets)} detail="부채 차감 전 자산" icon={WalletCards} />
        <StatCard label="총부채" value={formatKRW(summary.total_debts)} detail={`자산의 ${((summary.total_debts / summary.total_assets) * 100).toFixed(1)}%`} icon={Landmark} tone="negative" />
        <StatCard label="투자자산" value={formatKRW(summary.investment_value)} detail="평가금액 기준" icon={TrendingUp} tone="positive" />
        <StatCard label="예적금" value={formatKRW(summary.savings_value)} detail="3개 상품 운용 중" icon={PiggyBank} tone="accent" />
      </section>

      <section className="overview-grid">
        <article className="panel allocation-panel">
          <div className="panel-header"><div><p className="eyebrow">ALLOCATION</p><h3>자산 구성</h3></div><a href="/allocation">자세히 보기</a></div>
          <AllocationDonut data={allocationQuery.data} />
        </article>
        <article className="panel history-panel">
          <div className="panel-header"><div><p className="eyebrow">GROWTH</p><h3>순자산 변화</h3></div><span className="period-chip">최근 1년</span></div>
          <div className="chart-kpi"><strong>{formatKRW(summary.net_worth, true)}</strong><span>12개월 +25.5%</span></div>
          <NetWorthChart data={historyQuery.data} />
        </article>
      </section>
      <section className="insight-strip">
        <div><span>현금성 자산</span><strong>{formatKRW(summary.cash_value + summary.savings_value)}</strong><small>총자산의 {(((summary.cash_value + summary.savings_value) / summary.total_assets) * 100).toFixed(1)}%</small></div>
        <div><span>투자 평가액</span><strong>{formatKRW(summary.investment_value)}</strong><small className="positive-text">이번 달 +3.8%</small></div>
        <div><span>부채 상환율</span><strong>37.9%</strong><small>초기 원금 대비</small></div>
        <div><span>데이터 기준</span><strong>실시간 + 수동</strong><small>Toss · Notion 통합</small></div>
      </section>
    </>
  );
}

function OverviewSkeleton() {
  return (
    <div className="skeleton-page" aria-label="자산 데이터를 불러오는 중">
      <div className="skeleton header-skeleton" />
      <div className="skeleton hero-skeleton" />
      <div className="skeleton-grid">{[1, 2, 3, 4].map((item) => <div className="skeleton card-skeleton" key={item} />)}</div>
      <p>자산 데이터를 안전하게 불러오는 중...</p>
    </div>
  );
}
