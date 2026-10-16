import { Playground } from "@/components/demo/playground";
import { ConnectAgent } from "@/components/landing/connect-agent";
import { DiagramSection } from "@/components/landing/diagram-section";
import { Hero } from "@/components/landing/hero";
import { Loop } from "@/components/landing/loop";
import { Section, SectionHeading } from "@/components/landing/section";
import { StackList } from "@/components/landing/stack-list";
import { getSession } from "@/server/auth/auth.lib";

/**
 * The public landing.
 *
 * It lives inside `(root)` on purpose: that layout already brings the nav and
 * the footer, and its breadcrumb hides itself when the trail has a single crumb,
 * which is the case at the root.
 *
 * The order follows the reader: what this is, how the two doors work, what is
 * inside, how to run it, running it here, and finally pointing a client of your
 * own at it. The playground sits before the client instructions because it is the
 * proof that they work.
 */
export default async function HomePage() {
  const session = await getSession();

  return (
    <>
      <Hero isSignedIn={!!session} />
      <DiagramSection />
      <StackList />
      <Loop />

      <Section>
        <SectionHeading
          title="Run it here"
          lead="The same tools an agent gets, run against the server with your account. Two live in the agent's own code, and one of them stops the run to ask you; the third is the server's, so it goes through the door."
        />
        <Playground />
      </Section>

      <ConnectAgent />
    </>
  );
}
