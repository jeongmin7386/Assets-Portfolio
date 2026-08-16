import { CalendarDays } from "lucide-react";

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {action ?? (
        <div className="as-of"><CalendarDays size={15} /><span>2026. 08. 16 기준</span></div>
      )}
    </header>
  );
}
