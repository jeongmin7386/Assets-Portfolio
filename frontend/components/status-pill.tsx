export function StatusPill({ value }: { value: string }) {
  const tone = value === "NORMAL" || value === "연결됨" || value === "달성" ? "good" : value === "UNDERWEIGHT" || value === "주의" ? "warn" : value === "OVERWEIGHT" || value === "오류" ? "bad" : "neutral";
  const label: Record<string, string> = { UNDERWEIGHT: "비중 부족", NORMAL: "적정", OVERWEIGHT: "비중 초과" };
  return <span className={`status-pill ${tone}`}><i />{label[value] ?? value}</span>;
}
