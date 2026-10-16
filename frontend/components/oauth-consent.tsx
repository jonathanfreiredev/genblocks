import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { describeScopes } from "@/lib/oauth-scopes";

/**
 * Where the decision is submitted. A plain form POST instead of a server action
 * because a consent decision is an OAuth protocol step whose only job is to send
 * the user back to the client, and this way it works without JavaScript.
 */
const DECISION_ENDPOINT = "/api/oauth/decision";

type OAuthConsentProps = {
  authorizationId: string;
  clientName: string;
  clientUri: string;
  redirectUri: string;
  scope: string;
  /** Set when the previous decision could not be recorded. */
  failed?: boolean;
};

export function OAuthConsent({
  authorizationId,
  clientName,
  clientUri,
  redirectUri,
  scope,
  failed = false,
}: OAuthConsentProps) {
  const name = clientName || "An application";
  const scopes = describeScopes(scope);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Authorize {name}</CardTitle>
        <CardDescription>
          <a
            href={clientUri}
            target="_blank"
            rel="noreferrer noopener"
            className="underline underline-offset-4"
          >
            {name}
          </a>{" "}
          wants to connect to your account.
        </CardDescription>
      </CardHeader>

      <CardContent className="flex flex-col gap-5">
        {scopes.length > 0 ? (
          <div className="flex flex-col gap-2">
            <p className="text-sm font-medium">It will be able to:</p>
            <ul className="text-muted-foreground list-disc pl-5 text-sm">
              {scopes.map(({ id, label }) => (
                <li key={id}>{label}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <p className="text-sm">
          Approving gives {name} the same access you have: whatever you can do
          in this application, it can do on your behalf. Only approve it if you
          recognise it.
        </p>

        {failed ? (
          <p role="alert" className="text-destructive text-sm">
            That did not go through. Please try again.
          </p>
        ) : null}

        <form
          action={DECISION_ENDPOINT}
          method="post"
          className="flex flex-col gap-2 sm:flex-row-reverse"
        >
          <input
            type="hidden"
            name="authorization_id"
            value={authorizationId}
          />
          <Button type="submit" name="decision" value="approve">
            Approve
          </Button>
          <Button
            type="submit"
            name="decision"
            value="deny"
            variant="outline"
            className="sm:mr-auto"
          >
            Deny
          </Button>
        </form>
      </CardContent>

      <CardFooter>
        <p className="text-muted-foreground text-xs break-all">
          You will be sent back to {redirectUri} afterwards.
        </p>
      </CardFooter>
    </Card>
  );
}

export function OAuthConsentError({ message }: { message: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Cannot continue</CardTitle>
        <CardDescription>{message}</CardDescription>
      </CardHeader>
    </Card>
  );
}
