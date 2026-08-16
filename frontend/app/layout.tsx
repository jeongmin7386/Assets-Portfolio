import type { Metadata } from "next";
import { headers } from "next/headers";
import { Providers } from "./providers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "localhost:3001";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? (host.startsWith("localhost") ? "http" : "https");
  const origin = `${protocol}://${host}`;
  const description = "흩어진 자산을 한눈에 이해하는 개인 자산 포트폴리오 대시보드";
  return {
    metadataBase: new URL(origin),
    title: { default: "Moa — 자산 포트폴리오", template: "%s · Moa" },
    description,
    openGraph: {
      title: "Moa — 나의 자산을 한눈에",
      description,
      type: "website",
      url: origin,
      images: [{ url: `${origin}/og.png`, width: 1731, height: 909, alt: "Moa 자산 포트폴리오 대시보드" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "Moa — 나의 자산을 한눈에",
      description,
      images: [`${origin}/og.png`],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
