import { getSession } from "@/server/auth/auth.lib";
import { redirect } from "next/navigation";
import { WakeNotice } from "@/components/demo/wake-notice";

export default async function Layout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const resIsLoggedIn = await getSession();

  if (!!resIsLoggedIn) {
    redirect("/");
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center">
      {children}
      {/* The sign-in itself goes to Supabase, which never sleeps; the profile that
          follows it goes to the API, which does. So the wait is mentioned here too,
          under whatever the visitor came to fill in. */}
      <WakeNotice className="mt-6" />
    </div>
  );
}
