import { redirect } from "next/navigation";
import { ConnectedAppsCard } from "@/components/auth/connected-apps-card";
import { DeleteAccountCard } from "@/components/auth/delete-account-card";
import { ProfileCard } from "@/components/auth/profile-card";
import { getSession } from "@/server/auth/auth.lib";
import { listConnectedApps } from "@/server/oauth/oauth.lib";

export default async function ProfilePage() {
  const session = await getSession();

  const isLoggedIn = !!session;

  if (!isLoggedIn) {
    redirect("/auth/login");
  }

  const connectedApps = await listConnectedApps();

  return (
    <div className="flex w-full flex-col items-center px-4 py-8">
      <div className="flex w-full max-w-125 flex-col gap-6">
        <ProfileCard
          user={{
            name: session?.user.name || "",
            email: session?.user.email || "",
          }}
        />

        <ConnectedAppsCard result={connectedApps} />

        <DeleteAccountCard />
      </div>
    </div>
  );
}
