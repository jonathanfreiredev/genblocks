import type { Metadata } from "next";

import { SignupForm } from "@/components/auth/signup-form";

export const metadata: Metadata = {
  title: "Sign up",
  description: "Create the account that owns your tasks.",
};

export default async function SignupPage() {
  return <SignupForm />;
}
