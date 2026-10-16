"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
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
import { resetPasswordAction } from "@/server/auth/auth.actions";
import { resetPasswordSchema } from "@/server/auth/auth.schemas";

export const ResetPasswordForm = ({
  className,
  ...props
}: React.ComponentProps<"div">) => {
  const router = useRouter();

  const form = useForm<z.infer<typeof resetPasswordSchema>>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { password: "", confirmPassword: "" },
  });

  async function onSubmit(data: z.infer<typeof resetPasswordSchema>) {
    if (data.password !== data.confirmPassword) {
      toast.add({
        title: "Passwords do not match!",
        description: "Please make sure your passwords match.",
        type: "error",
      });
      return;
    }

    const res = await resetPasswordAction(data);

    if (res.serverError) {
      toast.add({
        title: "Reset failed!",
        description:
          res.serverError.message ||
          "An error occurred while resetting your password.",
        type: "error",
      });
      return;
    }

    toast.add({
      title: "Password reset successfully!",
      description: "You can now log in with your new password.",
      type: "success",
    });

    router.replace("/auth/login");
  }

  return (
    <div
      className={cn("flex w-full max-w-125 flex-col gap-6", className)}
      {...props}
    >
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">Choose a new password</CardTitle>
          <CardDescription>Enter your new password below.</CardDescription>
        </CardHeader>
        <CardContent>
          <form id="form-reset-password" onSubmit={form.handleSubmit(onSubmit)}>
            <FieldSet className="mb-5 w-full">
              <FieldGroup>
                <Controller
                  name="password"
                  control={form.control}
                  render={({ field, fieldState }) => (
                    <Field data-invalid={fieldState.invalid}>
                      <FieldLabel htmlFor="password">New Password</FieldLabel>
                      <Input
                        {...field}
                        id="password"
                        type="password"
                        placeholder="••••••••"
                        autoComplete="new-password"
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
                        autoComplete="new-password"
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
                form="form-reset-password"
                disabled={form.formState.isSubmitting}
              >
                Reset password
              </Button>

              <FieldDescription className="text-center">
                Must be at least 8 characters long.
              </FieldDescription>
            </Field>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
