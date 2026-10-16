"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { toast } from "@/components/ui/toast";
import { z } from "zod";
import { cn } from "@/lib/utils";
import { Button } from "../ui/button";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldSet,
} from "../ui/field";
import { Input } from "../ui/input";
import { updateUserPasswordSchema } from "@/server/users/users.schemas";
import { updateUserPasswordAction } from "@/server/users/users.actions";
import { useRouter } from "next/navigation";

export const ChangePasswordForm = ({
  className,
  onSuccess,
  ...props
}: React.ComponentProps<"div"> & { onSuccess?: () => void }) => {
  const router = useRouter();

  const form = useForm<z.infer<typeof updateUserPasswordSchema>>({
    resolver: zodResolver(updateUserPasswordSchema),
    defaultValues: {
      currentPassword: "",
      newPassword: "",
      confirmNewPassword: "",
    },
  });

  async function onSubmit(data: z.infer<typeof updateUserPasswordSchema>) {
    const { confirmNewPassword, ...resetData } = data;

    if (data.newPassword !== data.confirmNewPassword) {
      toast.add({
        title: "Passwords do not match!",
        description: "Please make sure your passwords match.",
        type: "error",
      });
      return;
    }

    const res = await updateUserPasswordAction(resetData);

    if (res.serverError) {
      toast.add({
        title: "Password change failed!",
        description:
          res.serverError.message ||
          "An error occurred while changing password.",
        type: "error",
      });
      return;
    }

    toast.add({
      title: "Password changed successfully!",
      description: "Your password has been updated.",
      type: "success",
    });

    form.reset();
    router.refresh();
    onSuccess?.();
  }

  return (
    <div
      className={cn("flex w-full max-w-125 flex-col gap-6", className)}
      {...props}
    >
      <form id="form-change-password" onSubmit={form.handleSubmit(onSubmit)}>
        <FieldSet className="mb-5 w-full">
          <FieldGroup>
            <Field>
              <Controller
                name="currentPassword"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="currentPassword">
                      Current Password
                    </FieldLabel>
                    <Input
                      {...field}
                      id="currentPassword"
                      type="password"
                      placeholder="••••••••"
                      autoComplete="current-password"
                      required
                    />

                    {fieldState.invalid && (
                      <FieldError errors={[fieldState.error]} />
                    )}
                  </Field>
                )}
              />
            </Field>
            <Field>
              <Field className="grid grid-cols-2 gap-4">
                <Controller
                  name="newPassword"
                  control={form.control}
                  render={({ field, fieldState }) => (
                    <Field data-invalid={fieldState.invalid}>
                      <FieldLabel htmlFor="newPassword">
                        New Password
                      </FieldLabel>
                      <Input
                        {...field}
                        id="newPassword"
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
                  name="confirmNewPassword"
                  control={form.control}
                  render={({ field, fieldState }) => (
                    <Field data-invalid={fieldState.invalid}>
                      <FieldLabel htmlFor="confirmNewPassword">
                        Confirm Password
                      </FieldLabel>
                      <Input
                        {...field}
                        id="confirmNewPassword"
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
          </FieldGroup>
        </FieldSet>

        <Field>
          <Button
            type="submit"
            form="form-change-password"
            disabled={form.formState.isSubmitting}
          >
            Change Password
          </Button>
        </Field>
      </form>
    </div>
  );
};
