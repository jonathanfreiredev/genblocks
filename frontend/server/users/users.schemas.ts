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

export const deleteUserSchema = z.object({
  password: z.string().min(1, { message: "Password is required" }),
});
