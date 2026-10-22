import { permanentRedirect } from "next/navigation";

/**
 * There is no home page: the gallery is the product, and Blocks is its default.
 *
 * A permanent redirect tells a crawler that `/blocks` is the canonical address
 * of the front page, rather than a temporary detour.
 */
export default function Home() {
  permanentRedirect("/blocks");
}
