import "./globals.css";
import { PageFrame } from "@/components/PageFrame";

export const metadata = {
  title: "BTED · Bacterial Transcript 3′ End Database",
  description: "A release-aware catalogue of public experimental bacterial transcript 3′-end records.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><PageFrame>{children}</PageFrame></body></html>;
}
