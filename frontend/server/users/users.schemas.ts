import "@/lib/zod-config";

import { z } from "zod";

export const updateUserSchema = z.object({
  name: z.string().min(2, { message: "Name must be at least 2 characters" }),
  email: z.email({ message: "Please enter a valid email address" }),
});

export const updateUserPasswordSchema = z.object({
  currentPassword: z.string().min(8, {
    message: "Current password must be at least 8 characters long",
  }),
  newPassword: z
    .string()
    .min(8, { message: "New password must be at least 8 characters long" }),
  confirmNewPassword: z.string().min(8, {
    message: "Confirm new password must be at least 8 characters long",
  }),
});

/**
 * The word an account without a password types to confirm a deletion.
 *
 * It lives here so the form and the action cannot drift: the form disables the
 * button on a mismatch, the action rejects anything else.
 */
export const DELETE_CONFIRMATION = "DELETE";

/**
 * How the caller proves they own the account before it is deleted.
 *
 * A password account sends `password`; an account created through Google has
 * none and sends `confirmation` instead. Which field counts is decided by the
 * action from the session, never from this payload, so sending the wrong one
 * cannot skip the check.
 */
export const deleteUserSchema = z.object({
  password: z.string().optional(),
  confirmation: z.string().optional(),
});
