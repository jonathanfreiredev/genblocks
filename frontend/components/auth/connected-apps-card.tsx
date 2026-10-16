"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { toast } from "@/components/ui/toast";
import { describeScopes } from "@/lib/oauth-scopes";
import { revokeAppAction } from "@/server/oauth/oauth.actions";
import type {
  ConnectedApp,
  ConnectedAppsResult,
} from "@/server/oauth/oauth.lib";
import { Button } from "../ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";

/**
 * The applications the user granted access to.
 *
 * Disconnecting revokes the grant, not the client: the application keeps its
 * registration and has to ask the user again. That is not destructive enough for
 * the danger zone, but deliberate enough to confirm which application it is
 * before cutting it off.
 */
export const ConnectedAppsCard = ({
  result,
}: {
  result: ConnectedAppsResult;
}) => {
  const router = useRouter();
  const [selected, setSelected] = useState<ConnectedApp | null>(null);
  const [isRevoking, setRevoking] = useState(false);

  async function disconnect() {
    if (!selected) {
      return;
    }

    setRevoking(true);
    const res = await revokeAppAction({ clientId: selected.clientId });
    setRevoking(false);

    if (res.serverError) {
      toast.add({
        title: "Could not disconnect the application",
        description: res.serverError.message || "Please try again.",
        type: "error",
      });
      return;
    }

    toast.add({
      title: `${selected.name} disconnected`,
      description: "It will have to ask for access again.",
      type: "success",
    });

    setSelected(null);
    router.refresh();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Connected applications</CardTitle>
        <CardDescription>
          Applications you have given access to your account. Disconnect the
          ones you no longer use.
        </CardDescription>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        {!result.ok ? (
          <p className="text-muted-foreground text-sm">
            Your connected applications could not be loaded. Refresh the page to
            try again.
          </p>
        ) : result.apps.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No application is connected to your account.
          </p>
        ) : (
          <ul className="flex flex-col gap-4">
            {result.apps.map((app) => (
              <li
                key={app.clientId}
                className="flex items-start justify-between gap-4"
              >
                <div className="flex flex-col gap-1">
                  <p className="text-sm font-medium">{app.name}</p>
                  {app.scopes.length > 0 ? (
                    <p className="text-muted-foreground text-xs">
                      {describeScopes(app.scopes.join(" "))
                        .map(({ label }) => label)
                        .join(", ")}
                    </p>
                  ) : null}
                  <p className="text-muted-foreground text-xs">
                    Connected {app.grantedAt}
                  </p>
                </div>

                <Button variant="outline" onClick={() => setSelected(app)}>
                  Disconnect
                </Button>
              </li>
            ))}
          </ul>
        )}

        <Dialog
          open={selected !== null}
          onOpenChange={(open) => {
            if (!open) {
              setSelected(null);
            }
          }}
        >
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Disconnect {selected?.name}?</DialogTitle>
              <DialogDescription>
                It will no longer be able to renew its access and will have to
                ask you again before it can act on your behalf.
              </DialogDescription>
            </DialogHeader>

            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setSelected(null)}
                disabled={isRevoking}
              >
                Cancel
              </Button>
              <Button onClick={disconnect} disabled={isRevoking}>
                Yes, disconnect
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
};
