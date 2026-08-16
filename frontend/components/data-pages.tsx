"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowDownRight,
  ArrowUpRight,
  CalendarClock,
  Check,
  Clock3,
  Database,
  Landmark,
  PiggyBank,
  RefreshCw,
  Server,
  Sparkles,
  Target,
  TrendingUp,
  WalletCards,
} from "lucide-react";
import { useState } from "react";
import { portfolioApi } from "@/lib/api";
import { formatDateTime, formatKRW, formatRate, formatUSD } from "@/lib/format";
import type { AssetClass } from "@/lib/types";
import { AllocationDonut, InvestmentComposition, NetWorthChart } from "./charts";
import { PageHeader } from "./page-header";
import { StatCard } from "./stat-card";
import { StatusPill } from "./status-pill";

function EmptyLoading() {
  return <div className="content-loading"><RefreshCw className="spin" size={18} /> 데이터를 불러오는 중...</div>;
}

export function AssetsView() {
  const { data } = useQuery({ queryKey: ["assets"], queryFn: portfolioApi.assets });
  const [filter, setFilter] = useState<"전체" | AssetClass>("전체");
  if (!data) return <EmptyLoading />;
  const filtered = filter === "전체" ? data : data.filter((item) => item.asset_class === filter);
  const total = data.reduce((sum, item) => sum + item.amount_krw, 0);
  return (
    <>
      <PageHeader eyebrow="MANUAL ASSETS" title="수동 자산" description="Notion에서 직접 관리하는 현금·보증금·금·기타자산입니다." />
      <section className="stat-grid three">
        <StatCard label="수동 자산 합계" value={formatKRW(total)} detail={`${data.length}개 자산`} icon={WalletCards} />
        <StatCard label="즉시 사용 가능" value={formatKRW(data.filter((item) => item.liquidity === "높음").reduce((sum, item) => sum + item.amount_krw, 0))} detail="유동성 높음" icon={Sparkles} tone="positive" />
        <StatCard label="장기성 자산" value={formatKRW(data.filter((item) => item.liquidity === "낮음").reduce((sum, item) => sum + item.amount_krw, 0))} detail="보증금·연금" icon={Landmark} tone="accent" />
      </section>
      <section className="panel table-panel">
        <div className="panel-header responsive"><div><p className="eyebrow">ASSET LIST</p><h3>자산 목록</h3></div><div className="filter-row">{(["전체", "현금", "보증금", "금", "기타자산"] as const).map((item) => <button className={filter === item ? "filter-chip active" : "filter-chip"} key={item} onClick={() => setFilter(item)}>{item}</button>)}</div></div>
        <div className="table-scroll">
          <table><thead><tr><th>자산명</th><th>계좌 / 기관</th><th>분류</th><th>현재가치</th><th>통화</th><th>유동성</th><th>기준일</th></tr></thead>
            <tbody>{filtered.map((asset) => <tr key={asset.id}><td><strong>{asset.name}</strong><small>{asset.asset_type}</small></td><td>{asset.account}<small>{asset.institution}</small></td><td><span className="asset-dot" data-class={asset.asset_class} />{asset.asset_class}</td><td className="number">{formatKRW(asset.amount_krw)}</td><td>{asset.currency}</td><td><span className={`liquidity ${asset.liquidity}`}>{asset.liquidity}</span></td><td>{asset.valued_at.replaceAll("-", ".")}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    </>
  );
}

export function InvestmentsView() {
  const { data } = useQuery({ queryKey: ["positions"], queryFn: portfolioApi.positions });
  if (!data) return <EmptyLoading />;
  const marketValue = data.reduce((sum, item) => sum + item.market_value_krw, 0);
  const cost = data.reduce((sum, item) => sum + item.cost_basis, 0);
  const pnl = marketValue - cost;
  const returnRate = cost ? (pnl / cost) * 100 : 0;
  return (
    <>
      <PageHeader eyebrow="TOSS SECURITIES" title="투자 자산" description="토스증권 보유 종목을 읽기 전용으로 동기화한 평가 현황입니다." />
      <section className="stat-grid four">
        <StatCard label="평가금액" value={formatKRW(marketValue)} detail={`${data.length}개 보유종목`} icon={TrendingUp} />
        <StatCard label="투자원금" value={formatKRW(cost)} detail="평균 매입단가 기준" icon={WalletCards} />
        <StatCard label="평가손익" value={formatKRW(pnl)} detail="미실현 손익" icon={ArrowUpRight} tone={pnl >= 0 ? "positive" : "negative"} />
        <StatCard label="전체 수익률" value={formatRate(returnRate)} detail="수수료·세금 제외" icon={Sparkles} tone="positive" />
      </section>
      <section className="split-grid narrow-right">
        <article className="panel table-panel">
          <div className="panel-header"><div><p className="eyebrow">POSITIONS</p><h3>보유 종목</h3></div><span className="read-only">READ ONLY</span></div>
          <div className="table-scroll"><table><thead><tr><th>종목</th><th>구분</th><th>보유수량</th><th>현재가</th><th>평가금액</th><th>평가손익</th><th>비중</th></tr></thead>
            <tbody>{data.map((item) => <tr key={item.id}><td><strong>{item.name}</strong><small>{item.symbol} · {item.market}</small></td><td>{item.security_type}</td><td className="number">{item.quantity.toLocaleString("ko-KR")}</td><td className="number">{item.currency === "USD" ? formatUSD(item.current_price) : formatKRW(item.current_price)}</td><td className="number">{formatKRW(item.market_value_krw)}</td><td className={item.unrealized_pnl_krw >= 0 ? "number positive-text" : "number negative-text"}>{formatKRW(item.unrealized_pnl_krw)}<small>{formatRate(item.return_rate)}</small></td><td><div className="weight-cell"><span style={{ width: `${item.portfolio_weight}%` }} /><strong>{item.portfolio_weight.toFixed(1)}%</strong></div></td></tr>)}</tbody>
          </table></div>
        </article>
        <article className="panel">
          <div className="panel-header"><div><p className="eyebrow">COMPOSITION</p><h3>상품 구성</h3></div></div>
          <InvestmentComposition positions={data} />
          <div className="mini-insight"><span>ETF 비중</span><strong>{((data.filter((item) => item.security_type === "ETF").reduce((sum, item) => sum + item.market_value_krw, 0) / marketValue) * 100).toFixed(1)}%</strong></div>
          <div className="mini-insight"><span>해외자산 비중</span><strong>{((data.filter((item) => item.currency !== "KRW").reduce((sum, item) => sum + item.market_value_krw, 0) / marketValue) * 100).toFixed(1)}%</strong></div>
        </article>
      </section>
    </>
  );
}

export function SavingsView() {
  const { data } = useQuery({ queryKey: ["savings"], queryFn: portfolioApi.savings });
  if (!data) return <EmptyLoading />;
  const total = data.reduce((sum, item) => sum + item.current_balance, 0);
  const totalPlanned = data.reduce((sum, item) => sum + item.monthly_contribution, 0);
  const avgRate = data.reduce((sum, item) => sum + item.annual_rate * item.current_balance, 0) / total;
  const closest = [...data].sort((a, b) => a.days_remaining - b.days_remaining)[0];
  return (
    <>
      <PageHeader eyebrow="SAVINGS" title="예적금" description="만기와 예상 이자를 함께 보며 안정 자산의 흐름을 관리합니다." />
      <section className="stat-grid four">
        <StatCard label="총 예적금" value={formatKRW(total)} detail={`${data.length}개 상품`} icon={PiggyBank} />
        <StatCard label="월 납입 예정" value={formatKRW(totalPlanned)} detail="자동이체 기준" icon={CalendarClock} tone="accent" />
        <StatCard label="가중평균 금리" value={`${avgRate.toFixed(2)}%`} detail="현재잔액 가중" icon={TrendingUp} tone="positive" />
        <StatCard label="가장 가까운 만기" value={`${closest.days_remaining}일`} detail={closest.name} icon={Clock3} />
      </section>
      <section className="product-grid">{data.map((item) => <article className="panel product-card" key={item.id}><div className="product-head"><span className="product-icon"><PiggyBank size={20} /></span><div><small>{item.institution}</small><h3>{item.name}</h3></div><span className="product-type">{item.product_type}</span></div><div className="product-balance"><span>현재잔액</span><strong>{formatKRW(item.current_balance)}</strong></div><div className="product-stats"><div><span>월 납입</span><strong>{item.monthly_contribution ? formatKRW(item.monthly_contribution) : "일시납"}</strong></div><div><span>금리</span><strong>{item.annual_rate.toFixed(2)}%</strong></div><div><span>만기까지</span><strong>{item.days_remaining}일</strong></div></div><div className="maturity-row"><span>예상 세후이자</span><strong>{formatKRW(item.estimated_interest_after_tax)}</strong></div><div className="maturity-row total"><span>예상 만기금액</span><strong>{formatKRW(item.estimated_maturity_amount)}</strong></div><div className="date-range"><span>{item.opened_at}</span><i /><span>{item.maturity_at}</span></div></article>)}</section>
      <p className="estimate-note">예상 금액은 단순 추정치이며 실제 이자·세금·납입 일정에 따라 달라질 수 있습니다.</p>
    </>
  );
}

export function DebtsView() {
  const { data } = useQuery({ queryKey: ["debts"], queryFn: portfolioApi.debts });
  if (!data) return <EmptyLoading />;
  const total = data.reduce((sum, item) => sum + item.current_balance, 0);
  const original = data.reduce((sum, item) => sum + item.original_balance, 0);
  return (
    <>
      <PageHeader eyebrow="LIABILITIES" title="부채" description="현재 잔액과 상환 속도를 자산과 분리해 추적합니다." />
      <section className="debt-hero"><div><span>총부채</span><strong>{formatKRW(total)}</strong><small>초기 원금 {formatKRW(original)} 중 {formatKRW(original - total)} 상환</small></div><div className="debt-ring" style={{ "--progress": `${((original - total) / original) * 360}deg` } as React.CSSProperties}><span>{(((original - total) / original) * 100).toFixed(1)}%</span><small>상환</small></div></section>
      <section className="product-grid two">{data.map((item) => <article className="panel debt-card" key={item.id}><div className="product-head"><span className="product-icon debt"><Landmark size={20} /></span><div><small>{item.institution} · {item.debt_type}</small><h3>{item.name}</h3></div></div><div className="debt-amounts"><div><span>현재잔액</span><strong>{formatKRW(item.current_balance)}</strong></div><div><span>초기원금</span><strong>{formatKRW(item.original_balance)}</strong></div></div><div className="progress-track"><i style={{ width: `${item.repayment_progress}%` }} /></div><div className="progress-label"><span>상환 진행률</span><strong>{item.repayment_progress.toFixed(1)}%</strong></div><div className="product-stats"><div><span>금리</span><strong>{item.annual_rate.toFixed(2)}%</strong></div><div><span>월 상환</span><strong>{formatKRW(item.monthly_payment)}</strong></div><div><span>만기</span><strong>{item.maturity_at.slice(0, 7)}</strong></div></div></article>)}</section>
    </>
  );
}

export function AllocationView() {
  const { data } = useQuery({ queryKey: ["allocation"], queryFn: portfolioApi.allocation });
  if (!data) return <EmptyLoading />;
  const targetSum = data.reduce((sum, item) => sum + item.target_weight, 0);
  return (
    <>
      <PageHeader eyebrow="ALLOCATION" title="자산배분" description="현재 비중과 목표 범위를 비교해 다음 의사결정에 필요한 차이만 보여줍니다." />
      {Math.abs(targetSum - 100) > 0.01 && <div className="warning-banner">활성 목표비중의 합계가 {targetSum.toFixed(1)}%입니다. 100%로 조정해 주세요.</div>}
      <section className="split-grid allocation-page-grid"><article className="panel"><div className="panel-header"><div><p className="eyebrow">CURRENT</p><h3>현재 자산 구성</h3></div></div><AllocationDonut data={data} compact /></article><article className="panel rebalance-card"><div className="panel-header"><div><p className="eyebrow">REBALANCE</p><h3>리밸런싱 인사이트</h3></div></div>{data.filter((item) => item.status !== "NORMAL").map((item) => <div className="rebalance-item" key={item.asset_class}>{item.amount_difference < 0 ? <ArrowDownRight /> : <ArrowUpRight />}<div><strong>{item.asset_class}</strong><span>목표보다 {Math.abs(item.weight_difference).toFixed(1)}%p {item.weight_difference < 0 ? "낮음" : "높음"}</span></div><b>{item.amount_difference < 0 ? `${formatKRW(Math.abs(item.amount_difference), true)} 부족` : `${formatKRW(item.amount_difference, true)} 초과`}</b></div>)}<p className="card-note">허용범위 안의 차이는 경고로 표시하지 않습니다. 자동매매는 실행하지 않습니다.</p></article></section>
      <section className="panel table-panel"><div className="panel-header"><div><p className="eyebrow">TARGET COMPARISON</p><h3>현재 vs 목표</h3></div><span className="target-sum"><Check size={14} /> 목표합계 {targetSum}%</span></div><div className="table-scroll"><table><thead><tr><th>자산군</th><th>현재금액</th><th>현재비중</th><th>목표비중</th><th>차이</th><th>허용범위</th><th>상태</th></tr></thead><tbody>{data.map((item) => <tr key={item.asset_class}><td><strong><span className="asset-dot" data-class={item.asset_class} />{item.asset_class}</strong></td><td className="number">{formatKRW(item.current_value)}</td><td className="number">{item.current_weight.toFixed(1)}%</td><td className="number">{item.target_weight.toFixed(1)}%</td><td className={item.weight_difference >= 0 ? "number positive-text" : "number negative-text"}>{formatRate(item.weight_difference, true)}</td><td>{item.minimum_weight ?? 0} ~ {item.maximum_weight ?? "-"}%</td><td><StatusPill value={item.status} /></td></tr>)}</tbody></table></div></section>
    </>
  );
}

export function GoalsView() {
  const { data } = useQuery({ queryKey: ["goals"], queryFn: portfolioApi.goals });
  if (!data) return <EmptyLoading />;
  return (
    <>
      <PageHeader eyebrow="FINANCIAL GOALS" title="재무 목표" description="수동 진행률 대신 실제 자산 값으로 목표 달성도를 계산합니다." />
      <section className="goal-summary"><Target size={22} /><div><strong>{data.length}개의 목표를 추적 중</strong><span>현재 평균 달성률 {Math.min(data.reduce((sum, item) => sum + item.progress, 0) / data.length, 100).toFixed(1)}%</span></div></section>
      <section className="product-grid goal-grid">{data.map((item) => { const done = item.progress >= 100; return <article className={done ? "panel goal-card completed" : "panel goal-card"} key={item.id}><div className="goal-head"><span>{item.goal_type}</span>{done && <StatusPill value="달성" />}</div><h3>{item.name}</h3><div className="goal-values"><div><span>현재</span><strong>{formatKRW(item.current_value)}</strong></div><div><span>목표</span><strong>{formatKRW(item.target_amount)}</strong></div></div><div className="goal-progress-label"><strong>{item.progress.toFixed(1)}%</strong><span>{done ? "목표를 달성했어요" : `${formatKRW(item.target_amount - item.current_value)} 남음`}</span></div><div className="progress-track goal"><i style={{ width: `${Math.min(item.progress, 100)}%` }} /></div><div className="goal-date"><CalendarClock size={15} /><span>{item.target_date.replaceAll("-", ".")} · {item.days_remaining}일 남음</span></div></article>; })}</section>
    </>
  );
}

export function HistoryView() {
  const [range, setRange] = useState("1y");
  const { data } = useQuery({ queryKey: ["history", range], queryFn: () => portfolioApi.history(range) });
  if (!data) return <EmptyLoading />;
  const first = data[0]; const last = data[data.length - 1]; const change = last.net_worth - first.net_worth;
  return (
    <>
      <PageHeader eyebrow="HISTORY" title="자산 기록" description="매일 저장된 스냅샷으로 자산 성장과 부채 감소를 확인합니다." action={<div className="range-tabs">{["1m", "3m", "6m", "1y", "all"].map((item) => <button className={range === item ? "active" : ""} key={item} onClick={() => setRange(item)}>{item.toUpperCase()}</button>)}</div>} />
      <section className="stat-grid three"><StatCard label="기간 순자산 증가" value={formatKRW(change)} detail={formatRate((change / first.net_worth) * 100)} icon={ArrowUpRight} tone="positive" /><StatCard label="현재 총자산" value={formatKRW(last.total_assets)} detail="스냅샷 기준" icon={WalletCards} /><StatCard label="현재 총부채" value={formatKRW(last.total_debts)} detail="꾸준히 감소 중" icon={ArrowDownRight} tone="accent" /></section>
      <section className="panel large-chart-panel"><div className="panel-header"><div><p className="eyebrow">NET WORTH</p><h3>순자산 성장 추이</h3></div><div className="chart-keys"><span className="net">순자산</span><span className="asset">총자산</span><span className="debt">총부채</span></div></div><NetWorthChart data={data} /></section>
      <section className="panel snapshot-list"><div className="panel-header"><div><p className="eyebrow">SNAPSHOTS</p><h3>최근 스냅샷</h3></div></div>{[...data].reverse().slice(0, 5).map((item, index) => <div className="snapshot-row" key={item.date}><span>{item.date.slice(0, 10).replaceAll("-", ".")}</span><strong>{formatKRW(item.net_worth)}</strong><small>{index === data.length - 1 ? "-" : "+0.8%"}</small></div>)}</section>
    </>
  );
}

export function SettingsView() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["sync-status"], queryFn: portfolioApi.syncStatus });
  const syncMutation = useMutation({ mutationFn: portfolioApi.sync, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sync-status"] }) });
  if (!data) return <EmptyLoading />;
  const cards = [
    { key: "notion" as const, name: "Notion", description: "Accounts · Assets · Savings · Debts · Goals · Allocation Targets", icon: Database },
    { key: "toss" as const, name: "Toss Securities", description: "계좌 · 보유종목 · 현재가 · 환율 (읽기 전용)", icon: TrendingUp },
    { key: "database" as const, name: "PostgreSQL", description: "통합 데이터 · 스냅샷 · 동기화 이력", icon: Server },
  ];
  return (
    <>
      <PageHeader eyebrow="SETTINGS" title="연동 설정" description="외부 데이터 연결과 마지막 동기화 상태를 확인합니다." />
      <section className="settings-list">{cards.map(({ key, name, description, icon: Icon }) => { const status = data[key]; const syncing = syncMutation.isPending && syncMutation.variables === key; return <article className="panel connection-card" key={key}><span className="connection-icon"><Icon size={21} /></span><div className="connection-main"><div><h3>{name}</h3><StatusPill value={status.state === "connected" ? "연결됨" : status.state === "stale" ? "주의" : "연결 안 됨"} /></div><p>{description}</p><small>{status.message} · {formatDateTime(status.last_sync)}</small></div>{key !== "database" && <button className="sync-button" onClick={() => syncMutation.mutate(key)} disabled={syncing}><RefreshCw className={syncing ? "spin" : ""} size={16} />{syncing ? "동기화 중" : "지금 동기화"}</button>}</article>; })}</section>
      <section className="security-panel"><div><span className="connection-icon secure"><Check size={20} /></span><div><h3>민감정보는 서버에서만 처리됩니다</h3><p>Notion API 키, 토스증권 Client Secret, Access Token, 데이터베이스 비밀번호는 브라우저나 LocalStorage에 저장하지 않습니다.</p></div></div><span className="read-only">READ ONLY</span></section>
    </>
  );
}
