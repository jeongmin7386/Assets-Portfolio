import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string;
  detail?: string;
  tone?: "default" | "positive" | "negative" | "accent";
  icon?: LucideIcon;
}

export function StatCard({ label, value, detail, tone = "default", icon: Icon }: StatCardProps) {
  return (
    <article className={`stat-card tone-${tone}`}>
      <div className="stat-card-head">
        <span>{label}</span>
        {Icon && <span className="stat-icon"><Icon size={17} /></span>}
      </div>
      <strong>{value}</strong>
      {detail && <p>{detail}</p>}
    </article>
  );
}
