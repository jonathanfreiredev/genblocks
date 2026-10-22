import type { Metadata } from "next";

import { VerifyEmail } from "@/components/auth/verify-email";

export const metadata: Metadata = {
  title: "Verify your email",
  description: "Confirm the address on your GenBlocks account.",
};

export default async function VerifyEmailPage({
  searchParams,
}: {
  searchParams: Promise<{ email?: string }>;
}) {
  const { email } = await searchParams;

  return <VerifyEmail email={email} />;
}
