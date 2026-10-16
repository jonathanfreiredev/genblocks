import { Header } from "@/components/header";
import { VerificationBanner } from "@/components/auth/verification-banner";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { getSession } from "@/server/auth/auth.lib";

export default async function Layout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await getSession();

  return (
    <>
      <Header session={session} />
      {session && !session.user.isVerified ? <VerificationBanner /> : null}
      <main className="relative flex flex-col">
        <Breadcrumbs />
        {children}
      </main>
    </>
  );
}
