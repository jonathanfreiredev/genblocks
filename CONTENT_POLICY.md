# GenBlocks Content Policy

This is the product policy for what GenBlocks will generate, publish and keep. It
is written to be reused by the public terms page later; it is not itself the
contract with a user.

GenBlocks is a registry of **interface blocks** and **stock images**. A block is a
React/Tailwind project that somebody copies into their own site. An image is a
generated photograph or illustration used inside one of those blocks. Everything
else is out of scope.

## Scope

We accept:

- interface sections and components: heroes, pricing tables, forms, dashboards,
  menus, cards, charts, empty states and similar UI work;
- stock-image scenes that illustrate those blocks.

We do not accept essays, poems, articles, scripts, standalone websites, games,
malware, phishing pages, political campaigns, or any request whose purpose is not
a UI block or a stock image.

## Prohibited content

The following is never accepted, even when it is legal in some jurisdiction:

- **Sexual content and nudity**, including suggestive or fetish content.
- **Minors**: no sexual content involving a minor, and no generated image that
  depicts a minor at all. Age-ambiguous people are treated as minors for images.
- **CSAM**: zero tolerance. A suspected match is blocked, quarantined and handled
  through the process below; it is never published or redistributed.
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

An image prompt may describe a scene, a subject, light and composition. It may
not ask for a minor, a real person, a brand, a copyrighted character, text that
looks like an interface, or any of the prohibited content above. An image is
checked before it is stored and again by the rubric before it enters the library.
A picture that fails is not written; a picture that was already published can be
removed.

## Enforcement

- Text is moderated before a task is queued and again after the block is written.
- Image prompts are moderated before generation; image bytes and rendered
  screenshots are moderated before they can reach a public asset host.
- Production fails closed when moderation or CSAM scanning is not configured. A
  missing provider is an outage, not permission to publish.
- A dedicated CSAM hash-matching and child-safety service is required for image
  work. It runs before any general-purpose moderation API, so known or suspected
  CSAM is never sent to a provider that is not designed to handle it. Generic
  classifiers are an additional layer, never a substitute.
- High-risk or ambiguous work is held for human review. At the current volume,
  reviewing every published artifact is the default.
- Every moderation decision is recorded with the reason and the policy version.
  Content can be soft-deleted, removed from search and taken down without losing
  the audit record.

## Reports, takedowns and appeals

Anyone can report a block or an image through the report control when it is
available, or through the contact address published on the site's legal page.
Reports are triaged by a human.

When content is removed, the author is told what rule was applied and can appeal.
A repeated or serious violation can suspend generation for an account. We preserve
only what is needed for the review, a legal obligation or an active investigation.

## CSAM and illegal content

Suspected CSAM is not published, not stored in a public CDN, not sent to a
general-purpose moderation API, and not shown to other users. It is isolated,
access is restricted, and it is reported to the relevant authority and/or
specialist reporting service as required by applicable law. We cooperate with lawful requests and do not require a user to identify
themselves before a report is reviewed.

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
