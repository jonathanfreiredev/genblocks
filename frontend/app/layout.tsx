import type { Metadata } from "next";
import { Bricolage_Grotesque, Space_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toast";
import { Footer } from "@/components/footer";

// Voice: headings, body, UI. Variable font — no weight list needed.
const bricolageGrotesque = Bricolage_Grotesque({
  variable: "--font-sans",
  subsets: ["latin"],
});

// Data: uppercase labels, metadata, scores, code. Not a variable font, so the
// two weights the type scale uses are declared explicitly.
const spaceMono = Space_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "700"],
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
      className={`${bricolageGrotesque.variable} ${spaceMono.variable} h-full antialiased`}
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
        {/* Around everything on purpose: the theme has to be applied before the
            first paint, and this is the only script the app ships. */}
        {children}
        <Footer />
        <Toaster />
      </body>
    </html>
  );
}
