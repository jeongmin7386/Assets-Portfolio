"use client";

import {
  ChartNoAxesCombined,
  CircleDollarSign,
  Coins,
  Goal,
  History,
  LayoutDashboard,
  Landmark,
  Menu,
  PiggyBank,
  Settings,
  ShieldCheck,
  WalletCards,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const navGroups = [
  {
    label: "포트폴리오",
    items: [
      { href: "/overview", label: "개요", icon: LayoutDashboard },
      { href: "/assets", label: "자산", icon: WalletCards },
      { href: "/investments", label: "투자", icon: ChartNoAxesCombined },
      { href: "/savings", label: "예적금", icon: PiggyBank },
      { href: "/debts", label: "부채", icon: Landmark },
    ],
  },
  {
    label: "계획",
    items: [
      { href: "/allocation", label: "자산배분", icon: CircleDollarSign },
      { href: "/goals", label: "재무목표", icon: Goal },
      { href: "/history", label: "자산기록", icon: History },
    ],
  },
];

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <>
      <Link href="/overview" className="brand" onClick={onNavigate} aria-label="Moa 홈">
        <span className="brand-mark"><Coins size={21} strokeWidth={2.4} /></span>
        <span>
          <strong>Moa</strong>
          <small>Asset Portfolio</small>
        </span>
      </Link>
      <nav className="sidebar-nav" aria-label="주요 메뉴">
        {navGroups.map((group) => (
          <div className="nav-group" key={group.label}>
            <p>{group.label}</p>
            {group.items.map(({ href, label, icon: Icon }) => {
              const active = pathname === href;
              return (
                <Link className={active ? "nav-item active" : "nav-item"} href={href} key={href} onClick={onNavigate}>
                  <Icon size={18} strokeWidth={active ? 2.3 : 1.8} />
                  <span>{label}</span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="security-note">
          <ShieldCheck size={17} />
          <div><strong>읽기 전용</strong><span>주문 기능 없음</span></div>
        </div>
        <Link className={pathname === "/settings" ? "nav-item active" : "nav-item"} href="/settings" onClick={onNavigate}>
          <Settings size={18} /><span>연동 설정</span>
        </Link>
      </div>
    </>
  );
}

export function Sidebar() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <aside className="sidebar desktop-sidebar"><SidebarContent /></aside>
      <button className="mobile-menu-button" type="button" onClick={() => setOpen(true)} aria-label="메뉴 열기">
        <Menu size={22} />
      </button>
      {open && (
        <div className="mobile-nav-layer" role="dialog" aria-modal="true" aria-label="모바일 메뉴">
          <button className="mobile-nav-backdrop" type="button" onClick={() => setOpen(false)} aria-label="메뉴 닫기" />
          <aside className="sidebar mobile-sidebar">
            <button className="mobile-close" type="button" onClick={() => setOpen(false)} aria-label="메뉴 닫기"><X size={20} /></button>
            <SidebarContent onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}
    </>
  );
}
