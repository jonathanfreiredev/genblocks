import { redirect } from "next/navigation";

/**
 * There is no home page: the gallery is the product, and Blocks is its default.
 */
export default function Home() {
  redirect("/blocks");
}
