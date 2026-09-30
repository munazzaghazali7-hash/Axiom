import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { NavBar } from "@/components/NavBar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Axiom — Provable Autonomous Data Intelligence",
  description: "Describe what you need in plain English. Axiom plans, collects, and structures source-backed data with cryptographic attestations — no scraper engineering required.",
  keywords: ["Axiom", "data intelligence", "autonomous data collection", "AI agents", "web intelligence", "TEE attestation"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <NavBar />
        <main className="main-content">
          {children}
        </main>
      </body>
    </html>
  );
}
