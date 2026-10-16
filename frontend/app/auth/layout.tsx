import { getSession } from "@/server/auth/auth.lib";
import { redirect } from "next/navigation";

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
    </div>
  );
}
