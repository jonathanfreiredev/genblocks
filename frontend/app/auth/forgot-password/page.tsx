import type { Metadata } from "next";

import { ForgotPasswordForm } from "@/components/auth/forgot-password-form";

export const metadata: Metadata = {
  title: "Reset your password",
  description: "Ask for a password reset link.",
};

export default function ForgotPasswordPage() {
  return <ForgotPasswordForm />;
}
