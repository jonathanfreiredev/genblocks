"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { Controller, useForm } from "react-hook-form";
import { toast } from "@/components/ui/toast";
import { z } from "zod";
import { isProviderEnabled } from "@/lib/auth-providers";
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
import Link from "next/link";
import { signupFormSchema } from "@/server/auth/auth.schemas";
import { signupAction } from "@/server/auth/auth.actions";
import { GoogleSignInButton } from "./google-sign-in-button";

export function SignupForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const router = useRouter();
  const emailEnabled = isProviderEnabled("email");
  const googleEnabled = isProviderEnabled("google");

  const form = useForm({
    resolver: zodResolver(signupFormSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  async function onSubmit(data: z.infer<typeof signupFormSchema>) {
    const { confirmPassword, ...signupData } = data;

    if (data.password !== data.confirmPassword) {
      toast.add({
        title: "Passwords do not match!",
        description: "Please make sure your passwords match.",
        type: "error",
      });
      return;
    }

    const res = await signupAction(signupData);

    if (res.serverError) {
      toast.add({
        title: "Signup failed!",
        description:
          res.serverError.message || "An error occurred during signup.",
        type: "error",
      });
      return;
    }

    form.reset();

    // Email confirmation required: go to a persistent page so the user knows
    // to check their inbox (a toast can be dismissed too easily).
    if (res.data?.requiresVerification) {
      router.replace(
        `/auth/verify-email?email=${encodeURIComponent(data.email)}`,
      );
      return;
    }

    // Confirmation disabled: Supabase already signed the user in.
    toast.add({
      title: "Account created successfully!",
      description: "Welcome! You are signed in.",
      type: "success",
    });
    router.replace("/");
  }

  return (
    <div
      className={cn("flex w-full max-w-125 flex-col gap-6", className)}
      {...props}
    >
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Create your account</CardTitle>
          <CardDescription>
            {emailEnabled
              ? "Enter your email below to create your account"
              : "Continue with one of the options below."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          {emailEnabled ? (
            <form id="form-signup" onSubmit={form.handleSubmit(onSubmit)}>
              <FieldSet className="mb-5 w-full">
                <FieldGroup>
                  <Controller
                    name="name"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <Field data-invalid={fieldState.invalid}>
                        <FieldLabel htmlFor="name">Name</FieldLabel>
                        <Input
                          {...field}
                          id="name"
                          type="text"
                          autoComplete="off"
                          placeholder="John Doe"
                          required
                        />

                        {fieldState.invalid && (
                          <FieldError errors={[fieldState.error]} />
                        )}
                      </Field>
                    )}
                  />
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
                          autoComplete="off"
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
                  <Field>
                    <Field className="grid grid-cols-2 gap-4">
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

                            {fieldState.invalid && (
                              <FieldError errors={[fieldState.error]} />
                            )}
                          </Field>
                        )}
                      />
                      <Controller
                        name="confirmPassword"
                        control={form.control}
                        render={({ field, fieldState }) => (
                          <Field data-invalid={fieldState.invalid}>
                            <FieldLabel htmlFor="confirmPassword">
                              Confirm Password
                            </FieldLabel>
                            <Input
                              {...field}
                              id="confirmPassword"
                              type="password"
                              placeholder="••••••••"
                              autoComplete="off"
                              required
                            />

                            {fieldState.invalid && (
                              <FieldError errors={[fieldState.error]} />
                            )}
                          </Field>
                        )}
                      />
                    </Field>
                    <FieldDescription>
                      Must be at least 8 characters long.
                    </FieldDescription>
                  </Field>
                  <Field>
                    <Button
                      type="submit"
                      form="form-signup"
                      disabled={form.formState.isSubmitting}
                    >
                      Create Account
                    </Button>
                  </Field>
                </FieldGroup>
              </FieldSet>
            </form>
          ) : null}

          {googleEnabled ? (
            <GoogleSignInButton className="w-full" />
          ) : null}

          <FieldDescription className="text-center">
            Already have an account?{" "}
            <Link href="/auth/login">
              <Button
                variant="link"
                onClick={() => {
                  form.reset();
                }}
                disabled={form.formState.isSubmitting}
              >
                Log in
              </Button>
            </Link>
          </FieldDescription>
        </CardContent>
      </Card>
    </div>
  );
}
export { signupFormSchema };
