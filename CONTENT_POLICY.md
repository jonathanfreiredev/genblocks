# GenBlocks Content Policy

This is the working text for what GenBlocks will generate, publish and keep. The
binding version is section 8 of the public Terms of Use; this file is the source
we edit first, and the Terms must be updated from it in the same change.

GenBlocks is a registry of **interface blocks** and **generated stock images**. A
block is a React/Tailwind project that somebody copies into their own site. An
image is a generated stock picture, either made for a block or requested on its
own. Both are public. Everything else is out of scope.

## Scope

We accept:

- interface sections and components: heroes, pricing tables, forms, dashboards,
  menus, cards, charts, empty states and similar UI work;
- generated stock-image scenes: photographs, illustrations and abstract scenes.

We do not accept essays, poems, articles, scripts, standalone websites, games,
malware, phishing pages, political campaigns, or any request whose purpose is not
a UI block or a stock image.

## Prohibited content

The following is never accepted, even when it is legal in some jurisdiction:

- **People in generated images**, in any form: a person, a face, a head, a body,
  hands, arms, legs, skin, a silhouette, a crowd, a humanoid character, a
  realistic mannequin or a statue of a person. This is the product's central image
  rule and it has no exceptions.
- **Sexual content and nudity**, including suggestive or fetish content.
- **Minors**: no sexual content involving a minor, and no generated image that
  depicts a minor at all. Because no generated image may contain a person, a
  minor cannot be depicted by design.
- **CSAM**: zero tolerance. Suspected content is blocked, kept out of publication,
  access is restricted, and it is handled through the process below. It is never
  published or redistributed.
- **Violence and gore**, including animal cruelty, torture, mutilation and
  instructions for causing harm.
- **Hate and extremism**, including slurs, supremacist symbols, dehumanisation and
  content that promotes or glorifies violence against a group.
- **Harassment, threats and bullying**, including targeted abuse and doxxing.
- **Self-harm and suicide**, including promotion, instruction or graphic imagery.
- **Illegal activity**, including drug manufacture, weapons, fraud, evasion,
  trafficking and instructions for wrongdoing.
- **Malware, phishing, credential theft and evasion**: code that steals data,
  impersonates a login, evades a detector, or contacts an attacker-controlled
  service.
- **Privacy violations**: personal data, private addresses, private images, or
  content that identifies a person without consent.
- **Real people and deceptive likeness**: recognisable people, celebrities,
  politicians, private individuals, deepfakes or voice/persona impersonation.
- **Brands and third-party rights**: real logos, trademarks, copyrighted
  characters, or a style request that names a living artist.
- **Deceptive interfaces**: a block that pretends to be another company's product,
  collects credentials, hides its purpose, or presents a fake system dialog.
- **Political, religious or ideological persuasion**, gambling, alcohol, tobacco
  and weapons. These are restricted by product choice, not by law.

Ordinary product marketing is allowed. A pricing page, a SaaS hero, a checkout
form or a generic “Acme” dashboard is the product working as intended.

## Technical rules for blocks

A block is presentational. It must not:

- load a script, stylesheet, font, image or media from a host outside the
  registry's asset library;
- contain a `<script>`, `<iframe>`, `<object>`, `<embed>`, `<base>` or a form with
  an `action`;
- navigate the page, open a window, use `window`, `document`, `navigator`, browser
  storage, `eval`, `new Function`, `document.write`, `dangerouslySetInnerHTML` or
  a `javascript:` URL;
- use a dynamic import, `require`, `process`, or a package outside the published
  shelf;
- embed secrets, credentials, tracking pixels or hidden data collection.

These are checked statically, at build time and at render time. The checks are a
safety net, not a security audit: generated code is untrusted and a person who
copies it is responsible for reviewing it.

## Images

Images can be generated for a block or requested on their own. Every image is
public stock once it passes the gates: pictures made for a block and pictures
made independently live in the same library.

A person may describe the picture they want. That direction is checked before the
task is queued. A picture with people is refused; if the person is incidental,
the product may offer a no-person rewrite and only proceeds if the person accepts
it. If the person asks for images with people as the subject, the request is
refused. If a component brief says nothing about images, the builder chooses the
pictures.

An image prompt may describe a scene, a subject, light and composition. It may
not ask for a person, a real person, a brand, a copyrighted character, text that
looks like an interface, or any of the prohibited content above. The bytes that
come back are checked for people before the generic classifier sees them; an image
with a human is not stored. Rendered screenshots pass the same gate.

## Enforcement

- Text is moderated before a task is queued and again after the block is written.
- Standalone image prompts pass a policy preflight, and the prompt is checked
  again before generation. Image bytes and rendered screenshots are checked by
  the no-people detector before they can reach a public asset host, and then by
  the generic safety classifier.
- Production fails closed when moderation or the no-people detector is not
  configured. A missing provider is an outage, not permission to publish.
- A generated image containing a person is refused, not edited silently. The
  operator receives a metadata-only notice with the brief, the user, the reason
  and an image hash; the image itself is not attached or stored.
- Generated artifacts are published after automated moderation and can be removed
  by an operator. The operator receives one notification per generated block and
  per generated image, after publication; the notification is not an approval
  gate.
- Every moderation decision is recorded with the reason and the policy version.
  Content can be permanently deleted, removed from search and taken down; the
  report keeps a snapshot of what it acted on, and operator deletions are
  recorded in a simple audit table.
- Pictures are decoded, bounded by bytes and pixels, re-encoded without EXIF or
  other camera metadata, and only then moderated or stored. Each generated
  artifact carries a provenance record naming the model and the IPTC/C2PA
  digital source type (`trainedAlgorithmicMedia`); the bytes themselves carry no
  hidden metadata.

## Reports, takedowns and appeals

Anyone can report a published block through the report control when it is
available, or through the contact address published on the site's legal page.
Reports are triaged by a human. Internal image assets can be removed by an
operator from the admin inventory.

When content is removed, the author is told what rule was applied and can appeal.
A repeated or serious violation can suspend an account: the person can no longer
sign in and is limited to what an anonymous visitor can see. We preserve only what
is needed for the review, a legal obligation or an active investigation.

## CSAM and illegal content

The product does not generate people. Every generated image is checked for a
human before it is stored; a picture with a person is refused. Suspected CSAM is
never published intentionally. If it appears through a report or another path,
access is restricted and it is handled through the operator process, including
reporting to the relevant authority and/or specialist reporting service as
required by applicable law. The operator receives a metadata-only notice and
decides whether to escalate; the product does not send an automatic report to an
authority.

This section is a product process, not legal advice. The operating entity should
have counsel confirm the reporting, retention and law-enforcement workflow for
its jurisdiction before launch.

## Privacy

Briefs, prompts and generated code may become public. Do not submit personal data,
secrets, API keys or private material. If a brief contains personal data, it may
be redacted or removed. Images are synthetic; they must not be presented as a real
photograph of a real event or person.

## Changes

This policy is versioned with the product. A change that makes previously allowed
content disallowed triggers a re-review of the affected library where practical.
