import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toast";
import { Footer } from "@/components/footer";
import { DemoWakeProvider } from "@/components/demo/wake-provider";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  // The canonical address of the site. Everything relative in the metadata below — the
  // social card above all — is resolved against it, so this is the one line to change
  // if the domain ever does.
  metadataBase: new URL("https://mcpstack.jonathanfreire.com"),
  title: {
    default: "MCPStack",
    template: "%s | MCPStack",
  },
  description:
    "The production-ready foundation for agent-native SaaS: identity, permissions and the MCP server your agents talk to, already wired.",
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
    siteName: "MCPStack",
  },
  twitter: {
    card: "summary_large_image",
    title: "MCPStack",
    description: "The production-ready foundation for agent-native SaaS.",
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
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-svh flex-col">
        {/* Around everything on purpose: the pages that need the demo's services are
            the landing, the playground and the sign-in pages, and they all sit under
            this layout. Mounting it here means one place wakes them, and one place
            knows what they are doing. */}
        <DemoWakeProvider>
          {children}
          <Footer />
          <Toaster />
        </DemoWakeProvider>
      </body>
    </html>
  );
}
