"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Controller, useForm } from "react-hook-form";
import { toast } from "@/components/ui/toast";
import { z } from "zod";
import { isProviderEnabled } from "@/lib/auth-providers";
import { safeNextPath } from "@/lib/safe-next-path";
import { cn } from "@/lib/utils";
import { Button } from "../ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldSet,
} from "../ui/field";
import { Input } from "../ui/input";
import { loginFormSchema } from "@/server/auth/auth.schemas";
import { loginAction } from "@/server/auth/auth.actions";
import { GoogleSignInButton } from "./google-sign-in-button";

export const LoginForm = ({
  next,
  className,
  ...props
}: React.ComponentProps<"div"> & {
  /** Path to return to after logging in (the OAuth consent screen uses it). */
  next?: string;
}) => {
  const router = useRouter();
  const emailEnabled = isProviderEnabled("email");
  const googleEnabled = isProviderEnabled("google");

  const form = useForm<z.infer<typeof loginFormSchema>>({
    resolver: zodResolver(loginFormSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  async function onSubmit(data: z.infer<typeof loginFormSchema>) {
    const res = await loginAction(data);

    if (res.serverError) {
      if (res.serverError.reason === "email_not_confirmed") {
        toast.add({
          title: "Email not confirmed",
          description: res.serverError.message,
          type: "warning",
          timeout: 0,
          actionProps: {
            children: "Verify email",
            onClick: () =>
              router.push(
                `/auth/verify-email?email=${encodeURIComponent(data.email)}`,
              ),
          },
        });
        return;
      }

      toast.add({
        title: "Login failed!",
        description:
          res.serverError.message || "An error occurred during login.",
        type: "error",
      });
      return;
    }

    toast.add({
      title: "Logged in successfully!",
      description: "Welcome back!",
      type: "success",
    });

    form.reset();
    router.refresh();
    router.replace(safeNextPath(next));
  }

  return (
    <div
      className={cn("flex w-full max-w-125 flex-col gap-6", className)}
      {...props}
    >
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Log in</CardTitle>
          <CardDescription>
            {emailEnabled
              ? "Enter your email and password to log in to your account."
              : "Continue with one of the options below."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          {emailEnabled ? (
            <form id="form-login" onSubmit={form.handleSubmit(onSubmit)}>
              <FieldSet className="mb-5 w-full">
                <FieldGroup>
                  <Controller
                    name="email"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Field data-invalid={fieldState.invalid}>
                        <FieldLabel htmlFor="email">Email</FieldLabel>
                        <Input
                          {...field}
                          id="email"
                          type="email"
                          placeholder="joe@example.com"
                          required
                        />
                        <FieldDescription>
                          Choose a unique email for your account.
                        </FieldDescription>

                        {fieldState.invalid && (
                          <FieldError errors={[fieldState.error]} />
                        )}
                      </Field>
                    )}
                  />

                  <Controller
                    name="password"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Field data-invalid={fieldState.invalid}>
                        <FieldLabel htmlFor="password">Password</FieldLabel>
                        <Input
                          {...field}
                          id="password"
                          type="password"
                          placeholder="••••••••"
                          autoComplete="off"
                          required
                        />
                        <FieldDescription>
                          Must be at least 8 characters long.
                        </FieldDescription>

                        {fieldState.invalid && (
                          <FieldError errors={[fieldState.error]} />
                        )}
                      </Field>
                    )}
                  />
                </FieldGroup>
                <div className="flex justify-end">
                  <Link
                    href="/auth/forgot-password"
                    className="text-muted-foreground text-sm hover:underline"
                  >
                    Forgot password?
                  </Link>
                </div>
              </FieldSet>

              <Field>
                <Button
                  type="submit"
                  form="form-login"
                  disabled={form.formState.isSubmitting}
                >
                  Log in
                </Button>
              </Field>
            </form>
          ) : null}

          {googleEnabled ? (
            <GoogleSignInButton className="w-full" next={next} />
          ) : null}

          <FieldDescription className="text-center">
            Don&apos;t have an account?{" "}
            <Link href="/auth/signup">
              <Button
                variant="link"
                onClick={() => {
                  form.reset();
                }}
                disabled={form.formState.isSubmitting}
              >
                Sign up
              </Button>
            </Link>
          </FieldDescription>
        </CardContent>
      </Card>
    </div>
  );
};
