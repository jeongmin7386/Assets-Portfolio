export function formatKRW(value: number | null | undefined, compact = false) {
  if (value == null) return "-";
  if (compact && Math.abs(value) >= 100_000_000) {
    return `${(value / 100_000_000).toFixed(1).replace(".0", "")}억원`;
  }
  if (compact && Math.abs(value) >= 10_000) {
    return `${Math.round(value / 10_000).toLocaleString("ko-KR")}만원`;
  }
  return `${Math.round(value).toLocaleString("ko-KR")}원`;
}

export function formatUSD(value: number | null | undefined) {
  if (value == null) return "-";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(value);
}

export function formatRate(value: number | null | undefined, point = false) {
  if (value == null) return "-";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}${point ? "%p" : "%"}`;
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) return "동기화 기록 없음";
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}
