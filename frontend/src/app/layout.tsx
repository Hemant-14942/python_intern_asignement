import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FuturesFlow | Binance Testnet Trading Bot",
  description: "Modern UI for a FastAPI-powered Binance Futures Testnet trading bot.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
