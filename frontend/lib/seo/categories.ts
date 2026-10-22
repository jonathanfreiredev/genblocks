import type { Section } from "@/lib/vault/links";

/**
 * One sentence per taxonomy type.
 *
 * The taxonomy carries no prose, but a category page is a landing page: the
 * name alone is thin for a reader and for a search engine. The map is keyed by
 * the public slug, which is unique across both kinds, and the fallback keeps a
 * future category honest until somebody writes its sentence.
 */
const DESCRIPTIONS: Record<string, string> = {
  hero: "Hero sections generated from a brief, with live previews, source code and the independent judge's scores.",
  navbar:
    "Navigation bars generated from a brief, scored for layout, accessibility and finish before publication.",
  footer:
    "Footer sections generated from a brief, with the code and the judge's evidence beside the render.",
  features:
    "Feature sections generated from a brief, with live previews and the source a visitor can copy.",
  cta: "Call-to-action sections generated from a brief, with the render, the code and the judge's scores.",
  pricing:
    "Pricing sections generated from a brief, scored for clarity and composition before they enter the registry.",
  testimonials:
    "Testimonial sections generated from a brief, with live previews and the independent judge's evidence.",
  "social-proof":
    "Social-proof sections generated from a brief, scored for hierarchy, accessibility and finish.",
  stats:
    "Stats sections generated from a brief, with tabular figures, source code and the judge's scores.",
  faq: "FAQ sections generated from a brief, with the code and the judge's evidence beside the render.",
  contact:
    "Contact and enquiry sections generated from a brief, scored before they were published.",
  "forms-auth":
    "Form and authentication screens generated from a brief, scored before they entered the registry.",
  cards:
    "Card layouts generated from a brief, with live previews, source code and the judge's scores.",
  gallery:
    "Gallery sections generated from a brief, scored for composition, accessibility and finish.",
  blog: "Blog and article layouts generated from a brief, with the code and the judge's evidence.",
  team: "Team sections generated from a brief, scored before publication and ready to copy.",
  tables:
    "Table layouts generated from a brief, with the render, the code and the judge's scores.",
  dashboard:
    "Dashboard layouts generated from a brief, scored for hierarchy, density and finish.",
  charts:
    "Chart sections generated from a brief, with source code and the independent judge's evidence.",
  states:
    "Empty, loading and error states generated from a brief, scored before publication.",
  onboarding:
    "Onboarding flows generated from a brief, with live previews and the judge's scores.",
  banners:
    "Banner sections generated from a brief, scored for composition and accessibility.",
  integrations:
    "Integration sections generated from a brief, with the code and the judge's evidence.",
  timeline:
    "Timeline sections generated from a brief, scored before they entered the registry.",
  "newsletter-waitlist":
    "Newsletter and waitlist sections generated from a brief, with the render, code and scores.",
  illustration:
    "Illustrations generated from a prompt, scored by an independent judge before publication.",
  "abstract-background":
    "Abstract backgrounds generated from a prompt, with dimensions and the judge's scores.",
  "texture-pattern":
    "Textures and patterns generated from a prompt, scored before they enter the stock library.",
  "product-mockup":
    "Product and UI mockups generated from a prompt, with the image and the judge's evidence.",
  photography:
    "Photographic stock images generated from a prompt, scored before publication.",
  "spot-icon":
    "Spot illustrations and icons generated from a prompt, with the image and its scores.",
  avatar:
    "Avatar images generated from a prompt, scored for composition and finish.",
  scene:
    "Scene images generated from a prompt, with dimensions and the independent judge's evidence.",
};

export function categoryDescription(
  slug: string,
  name: string,
  section: Section,
): string {
  return (
    DESCRIPTIONS[slug] ??
    `Browse ${name} ${
      section === "blocks" ? "UI blocks" : "stock images"
    } generated from a prompt and scored by an independent judge before publication.`
  );
}

/** The short introduction a catalogue page shows under its heading. */
export function catalogueIntro(section: Section): string {
  return section === "blocks"
    ? "Generated UI blocks with live previews, copyable source and the independent judge's evidence."
    : "AI-generated stock images with the prompt, dimensions and the judge's scores behind each one.";
}
