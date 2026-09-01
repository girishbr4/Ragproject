import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  variable: "--font-plus-jakarta",
  display: "swap",
});

export const metadata: Metadata = {
  title: "HDFC Mutual Fund FAQ Assistant",
  description:
    "Get instant, source-verified factual answers about HDFC mutual fund schemes. No investment advice — facts only.",
  keywords: ["HDFC", "mutual fund", "FAQ", "expense ratio", "SIP", "ELSS", "exit load"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        className={`${plusJakartaSans.variable} font-sans bg-[#0b1326] text-[#dae2fd] antialiased overflow-x-hidden`}
      >
        {children}
      </body>
    </html>
  );
}
