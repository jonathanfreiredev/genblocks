"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { toast } from "@/components/ui/toast";
import { cn } from "@/lib/utils";
import { updateUserAction } from "@/server/users/users.actions";
import { updateUserSchema } from "@/server/users/users.schemas";
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
 * Edits the profile's own fields. Rendered inside a dialog (see
 * `profile-card.tsx`), which is why it takes `onSuccess`: the card is what closes
 * the dialog, once the save has gone through.
 */
export const ProfileEditForm = ({
  user,
  className,
  onSuccess,
  ...props
}: React.ComponentProps<"div"> & {
  user: { name: string; email: string };
  onSuccess?: () => void;
}) => {
  const router = useRouter();

  const form = useForm<z.infer<typeof updateUserSchema>>({
    resolver: zodResolver(updateUserSchema),
    defaultValues: {
      name: user.name,
      email: user.email,
    },
  });

  async function onSubmit(data: z.infer<typeof updateUserSchema>) {
    const res = await updateUserAction(data);

    if (res.serverError) {
      toast.add({
        title: "Profile update failed!",
        description:
          res.serverError.message ||
          "An error occurred while updating profile.",
        type: "error",
      });
      return;
    }

    toast.add({
      title: "Profile updated successfully!",
      description: "Your profile information has been updated.",
      type: "success",
    });

    form.reset(data);
    router.refresh();
    onSuccess?.();
  }

  return (
    <div
      className={cn("flex w-full max-w-125 flex-col gap-6", className)}
      {...props}
    >
      <form id="form-profile-edit" onSubmit={form.handleSubmit(onSubmit)}>
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
          </FieldGroup>
        </FieldSet>

        <Field>
          <Button
            type="submit"
            form="form-profile-edit"
            disabled={form.formState.isSubmitting}
          >
            Update profile
          </Button>
        </Field>
      </form>
    </div>
  );
};
