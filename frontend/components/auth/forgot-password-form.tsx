"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "@/components/ui/toast";
import { z } from "zod";
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
import { forgotPasswordAction } from "@/server/auth/auth.actions";
import { forgotPasswordSchema } from "@/server/auth/auth.schemas";

export const ForgotPasswordForm = ({
  className,
  ...props
}: React.ComponentProps<"div">) => {
  const [sent, setSent] = useState(false);

  const form = useForm<z.infer<typeof forgotPasswordSchema>>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });

  async function onSubmit(data: z.infer<typeof forgotPasswordSchema>) {
    const res = await forgotPasswordAction(data);

    if (res.serverError) {
      toast.add({
        title: "Request failed!",
        description:
          res.serverError.message || "An error occurred. Please try again.",
        type: "error",
      });
      return;
    }

    setSent(true);
  }

  return (
    <div
      className={cn("flex w-full max-w-125 flex-col gap-6", className)}
      {...props}
    >
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Reset your password</CardTitle>
          <CardDescription>
            Enter your email and we will send you a reset link.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {sent ? (
            <div className="flex flex-col gap-4 text-center">
              <FieldDescription>
                If an account exists for that email, we have sent a reset link.
                Check your inbox.
              </FieldDescription>
              <Link href="/auth/login">
                <Button variant="link" className="w-full">
                  Back to log in
                </Button>
              </Link>
            </div>
          ) : (
            <form id="form-forgot-password" onSubmit={form.handleSubmit(onSubmit)}>
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

                        {fieldState.invalid && (
                          <FieldError errors={[fieldState.error]} />
                        )}
                      </Field>
                    )}
                  />
                </FieldGroup>
              </FieldSet>

              <Field>
                <Button
                  type="submit"
                  form="form-forgot-password"
                  disabled={form.formState.isSubmitting}
                >
                  Send reset link
                </Button>

                <FieldDescription className="text-center">
                  Remembered it?{" "}
                  <Link href="/auth/login">Log in</Link>
                </FieldDescription>
              </Field>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
