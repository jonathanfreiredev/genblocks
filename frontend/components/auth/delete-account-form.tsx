"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { Controller, useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import { toast } from "@/components/ui/toast";
import { cn } from "@/lib/utils";
import { deleteUserAction } from "@/server/users/users.actions";
import {
  DELETE_CONFIRMATION,
  deleteUserSchema,
} from "@/server/users/users.schemas";
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

/**
 * Confirms account deletion. Deletion is irreversible and spans both the local
 * profile and the Supabase identity, so the caller proves ownership again: with
 * the password when the account has one, by typing DELETE when it was created
 * through a provider and has none.
 */
export const DeleteAccountForm = ({
  hasPassword,
  className,
  onSuccess,
  ...props
}: React.ComponentProps<"div"> & {
  hasPassword: boolean;
  onSuccess?: () => void;
}) => {
  const router = useRouter();

  const form = useForm<z.infer<typeof deleteUserSchema>>({
    resolver: zodResolver(deleteUserSchema),
    defaultValues: { password: "", confirmation: "" },
  });

  // The mismatch is visible before submitting: the button stays disabled until
  // the word is typed exactly as the server expects it.
  const confirmation = useWatch({
    control: form.control,
    name: "confirmation",
  });
  const isConfirmationComplete = confirmation === DELETE_CONFIRMATION;

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
              {hasPassword ? (
                <Controller
                  name="password"
                  control={form.control}
                  render={({ field, fieldState }) => (
                    <Field data-invalid={fieldState.invalid}>
                      <FieldLabel htmlFor="delete-password">
                        Password
                      </FieldLabel>
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
              ) : (
                <Controller
                  name="confirmation"
                  control={form.control}
                  render={({ field }) => (
                    <Field>
                      <FieldLabel htmlFor="delete-confirmation">
                        Type {DELETE_CONFIRMATION} to confirm
                      </FieldLabel>
                      <Input
                        {...field}
                        id="delete-confirmation"
                        type="text"
                        placeholder={DELETE_CONFIRMATION}
                        autoComplete="off"
                        spellCheck={false}
                        required
                      />
                      <FieldDescription>
                        This account has no password. The word is checked letter
                        for letter.
                      </FieldDescription>
                    </Field>
                  )}
                />
              )}
            </Field>
          </FieldGroup>
        </FieldSet>

        <Field>
          <Button
            type="submit"
            form="form-delete-account"
            variant="destructive"
            disabled={
              form.formState.isSubmitting ||
              (!hasPassword && !isConfirmationComplete)
            }
          >
            Delete account
          </Button>
        </Field>
      </form>
    </div>
  );
};
