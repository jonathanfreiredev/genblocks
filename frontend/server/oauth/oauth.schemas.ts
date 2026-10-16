import { z } from "zod";

export const revokeAppSchema = z.object({
  // Grants are identified by the client they were given to, not by an id of their own.
  clientId: z.string().min(1),
});
