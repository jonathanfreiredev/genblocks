import { z } from "zod";

export const signupFormSchema = z.object({
  name: z.string().min(2, { message: "Name must be at least 2 characters" }),
  email: z.email({ message: "Please enter a valid email address" }),
  password: z
    .string()
    .min(8, { message: "Password must be at least 8 characters long" }),
  confirmPassword: z.string().min(8, {
    message: "Confirm Password must be at least 8 characters long",
  }),
});

export const loginFormSchema = z.object({
  email: z.email({ message: "Please enter a valid email address" }),
  password: z
    .string()
    .min(8, { message: "Password must be at least 8 characters long" }),
});

export const forgotPasswordSchema = z.object({
  email: z.email({ message: "Please enter a valid email address" }),
});

export const resendVerificationSchema = z.object({
  email: z.email({ message: "Please enter a valid email address" }),
});

export const resetPasswordSchema = z.object({
  password: z
    .string()
    .min(8, { message: "Password must be at least 8 characters long" }),
  confirmPassword: z.string().min(8, {
    message: "Confirm Password must be at least 8 characters long",
  }),
});

/**
 * Google sign-in asks the user for nothing, but the page it started from is
 * worth carrying through so the browser can return there. The consent screen
 * depends on it.
 */
export const googleSignInSchema = z.object({
  next: z.string().optional(),
});
