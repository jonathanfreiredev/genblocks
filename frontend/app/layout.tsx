import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toast";
import { TooltipProvider } from "@/components/ui/tooltip";

// The shadcn preset's typeface: one neutral sans for everything, one mono for
// code and figures. Identity, if it comes, is a later decision.
const geist = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  // The canonical address of the site. Everything relative in the metadata below — the
  // social card above all — is resolved against it, so this is the one line to change
  // if the domain ever does.
  metadataBase: new URL("https://genblocks.jonathanfreire.com"),
  title: {
    default: "GenBlocks",
    template: "%s | GenBlocks",
  },
  description:
    "A public registry of UI blocks and stock images generated from a prompt, each carrying the scores of an independent judge and the attempts that came before it.",
  // Declaring this group replaces the icons Next wires up on its own from the files in
  // this directory, so every size in the set is listed here and the browser picks the
  // one it wants. The manifest is still the file next to this one; Next links it alone.
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon-32x32.png", type: "image/png", sizes: "32x32" },
      { url: "/favicon-16x16.png", type: "image/png", sizes: "16x16" },
      { url: "/icon.png", type: "image/png", sizes: "512x512" },
    ],
    apple: { url: "/apple-icon.png", sizes: "180x180" },
  },
  // The card image is not declared here: `app/opengraph-image.png` next to this file is
  // picked up and wired in by Next, so the picture can change without touching code.
  openGraph: {
    type: "website",
    siteName: "GenBlocks",
  },
  twitter: {
    card: "summary_large_image",
    title: "GenBlocks",
    description: "Every block and image, with the judge's scores.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geist.variable} ${geistMono.variable} h-full antialiased`}
      // The theme script adds `dark` before hydration, so the class differs from
      // the server output on purpose. This suppresses only that one warning.
      suppressHydrationWarning
    >
      <body className="flex min-h-svh flex-col">
        {/* Applies the stored theme before paint, so there is no flash. Keep the
            storage key and the media query in sync with theme-toggle.tsx. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var s=localStorage.getItem("genblocks-theme");var d=s?s==="dark":window.matchMedia("(prefers-color-scheme: dark)").matches;document.documentElement.classList.toggle("dark",d)}catch(e){}})();`,
          }}
        />
        <TooltipProvider>{children}</TooltipProvider>
        <Toaster />
      </body>
    </html>
  );
}
