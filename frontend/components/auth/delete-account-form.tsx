"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { toast } from "@/components/ui/toast";
import { cn } from "@/lib/utils";
import { deleteUserAction } from "@/server/users/users.actions";
import { deleteUserSchema } from "@/server/users/users.schemas";
import { Button } from "../ui/button";
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldSet,
} from "../ui/field";
import { Input } from "../ui/input";

/**
 * Confirms account deletion. Deletion is irreversible and spans both the local
 * profile and the Supabase identity, so it asks for the password again.
 */
export const DeleteAccountForm = ({
  className,
  onSuccess,
  ...props
}: React.ComponentProps<"div"> & { onSuccess?: () => void }) => {
  const router = useRouter();

  const form = useForm<z.infer<typeof deleteUserSchema>>({
    resolver: zodResolver(deleteUserSchema),
    defaultValues: { password: "" },
  });

  async function onSubmit(data: z.infer<typeof deleteUserSchema>) {
    const res = await deleteUserAction(data);

    if (res.serverError) {
      toast.add({
        title: "Could not delete your account!",
        description:
          res.serverError.message ||
          "An error occurred while deleting your account.",
        type: "error",
      });
      return;
    }

    toast.add({
      title: "Account deleted",
      description: "Your account and profile have been removed.",
      type: "success",
    });

    onSuccess?.();

    // The session is gone, so leave the protected area.
    router.replace("/");
    router.refresh();
  }

  return (
    <div className={cn("flex w-full flex-col gap-6", className)} {...props}>
      <form id="form-delete-account" onSubmit={form.handleSubmit(onSubmit)}>
        <FieldSet className="mb-5 w-full">
          <FieldGroup>
            <Field>
              <Controller
                name="password"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="delete-password">Password</FieldLabel>
                    <Input
                      {...field}
                      id="delete-password"
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
          </FieldGroup>
        </FieldSet>

        <Field>
          <Button
            type="submit"
            form="form-delete-account"
            variant="destructive"
            disabled={form.formState.isSubmitting}
          >
            Delete account
          </Button>
        </Field>
      </form>
    </div>
  );
};
