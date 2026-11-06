import type { Metadata } from "next";
import { QueryProvider } from "@/providers/query-provider";
import "./globals.css";
export const metadata: Metadata = {
  title: "TalentLens AI — See the potential",
  description: "Private resume analysis and explainable job matching. Built by Mashiel Khan.",
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
