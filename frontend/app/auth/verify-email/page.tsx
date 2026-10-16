import { VerifyEmail } from "@/components/auth/verify-email";

export default async function VerifyEmailPage({
  searchParams,
}: {
  searchParams: Promise<{ email?: string }>;
}) {
  const { email } = await searchParams;

  return <VerifyEmail email={email} />;
}
