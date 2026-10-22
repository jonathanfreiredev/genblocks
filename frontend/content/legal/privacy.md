# Privacy Notice

Last updated: 22 October 2026

GenBlocks is a public registry of generated interface blocks and stock images. This notice explains how we process personal data when you visit the site, create an account, use the assistant, publish an artifact, or report content. It is written for the General Data Protection Regulation (GDPR), the German Data Protection Act (BDSG), and section 25 of the German Telecommunications and Digital Services Data Protection Act (TDDDG).

## 1. Who is responsible

The controller for the processing described in this notice is:

Jonathan Eduardo Freire Espinoza\
trading as Jonathan Freire\
Mommsenstr. 31\
10629 Berlin\
Germany\
Email: [jonathan.freireespinoza@gmail.com](mailto:jonathan.freireespinoza@gmail.com)

We have not appointed a data protection officer. Questions about this notice or about your data can be sent to the email address above. The full provider information required by German law is in the [Impressum](/impressum).

## 2. What we collect

### 2.1 Account and sign-in data

When you create an account, Supabase Auth processes your email address, password, display name, email verification status, and the identifiers needed to keep you signed in. Passwords are handled by Supabase and are not stored by GenBlocks in plain text. Providing an email address and a display name is required to create an account. Without them, we cannot create or operate the account.

If you sign in with Google, Google authenticates you and shares your name, email address, and Google account identifier with Supabase. We do not receive your Google password or access to your other Google services.

We do not process payment data today. If paid features are introduced, we will update this notice and name the payment provider before any charge is made.

Our own database keeps a profile linked to your Supabase user ID. It contains your email address, display name, account status, and any operator ban or restriction. Your display name can appear publicly beside a published block or image. Your email address is not shown in the public catalogue.

If you connect an AI agent through the MCP server, Supabase stores the OAuth grant and the scopes you approved. You can review and revoke connected apps from your profile.

### 2.2 Briefs, prompts, and generated artifacts

When you ask for a block or an image, we store the brief or prompt you submit, the size and category of an image request, the task status, the steps shown in the interface, the generated files and images, the judge's scores and notes, the harness checks, the model name, and a trace identifier where tracing is enabled.

Published blocks and images are public. Their briefs, prompts, code, scores, display name, and creation date can be read by anyone and may be indexed by search engines. Do not submit personal data, secrets, API keys, passwords, private addresses, or confidential business information.

### 2.3 Assistant conversations and connected agents

The assistant processes the messages you send, the tool calls it makes, the blocks and images it finds, and the proposals it prepares. The conversation is held in the server process for the current session so that the next turn can continue it. We do not keep a durable chat transcript in our database, and a server restart can end the conversation.

If you connect an AI agent through the MCP server, the agent acts with the access you grant it. Requests it makes are processed in the same way as requests you make yourself. Public registry data is available to the agent, and a task it creates belongs to your account.

### 2.4 Reports, moderation, and operator records

When you report an artifact, we store the target, the reason, the details you write, your account ID, the status of the report, and the operator's decision. Reports are visible to the operators who review them, not to the public.

Text, image prompts, generated images, and rendered screenshots pass through moderation and safety checks. We record the result, the reason, the policy version, and the model used. If a prompt or image hits an image-policy rule, the operator receives a notification with metadata such as the brief, your account email or ID, the reason, the task ID, and a hash of the image. The image itself is not attached to that notification.

We keep a simple deletion audit when an operator removes a public item. It records the item that was removed, the operator, the result, and the paths that were deleted.

### 2.5 Cookies and local storage

We use only storage that is necessary to provide the service:

- Supabase session cookies, whose names begin with `sb-`, keep you signed in and protect your account. They are set by our authentication provider.
- The `sidebar_state` cookie remembers whether the navigation column is open. It lasts seven days.
- The local storage key `genblocks-theme` remembers whether you chose the light or dark theme.
- The local storage key `genblocks-chat-thread` remembers the current assistant conversation ID, so the next page load can continue the same conversation.

These items are necessary for the service you requested. We do not use advertising cookies, tracking pixels, or third-party analytics. If we introduce a non-essential cookie or similar technology, we will ask for your consent before it is set, as required by section 25(1) TDDDG.

You can delete local storage and cookies through your browser settings. Deleting the authentication cookies signs you out. Deleting the theme or conversation key only resets that preference.

### 2.6 Technical logs

Our hosting and application infrastructure records request data such as IP address, user agent, requested path, timestamp, response status, request ID, and error details. We use these records to operate the service, investigate failures, prevent abuse, and maintain security. Vercel, Google Cloud, and Supabase may keep their own logs under their terms.

## 3. Why we process data and on what legal basis

We process account data, submissions, and generated artifacts to provide the service you request, including publishing what you choose to make public. The legal basis is Article 6(1)(b) GDPR.

We process technical logs, moderation records, reports, and security data to operate the service safely, prevent abuse, and protect our legitimate interests and those of our users. The legal basis is Article 6(1)(f) GDPR. Our legitimate interests are security, reliability, fraud prevention, and compliance with content-safety rules.

We process data when this is necessary to comply with legal obligations, for example when we must respond to a lawful request, preserve evidence, or report illegal content. The legal basis is Article 6(1)(c) GDPR.

We use strictly necessary cookies and local storage under section 25(2) TDDDG. We do not rely on consent for the processing described in this notice.

We do not ask for special categories of personal data and do not intend to process them. Please do not include health, religious, political, sexual, or other sensitive information in a brief or message. If you do, we process it as part of the service you requested, and the content may become public if the task is published. We will erase or redact personal data on request as described in section 8.

## 4. Who receives data

We use service providers to run GenBlocks. Where a provider processes personal data on our behalf, it acts as a processor under Article 28 GDPR and is bound by a data processing agreement. Some providers act as independent controllers for their own services, most notably Google when you choose Google sign-in.

The current production setup uses these providers:

- Supabase Inc. (USA) provides authentication and, in the production setup, the PostgreSQL database. The project is hosted in Frankfurt, Germany (`eu-central-1`). Supabase may access the project from the United States for support and operations.
- Vercel Inc. (USA) hosts the frontend. Its Functions are configured in Frankfurt, Germany (`fra1`), while its CDN and routing middleware can process request metadata and cookies at edge locations outside Germany.
- Google Cloud EMEA Limited (Ireland) and Google LLC (USA) host the backend API and the MCP server on Cloud Run in Frankfurt, Germany (`europe-west3`). Cloud Run stores customer data in the selected region. Google may process service logs and support data in the European Union and the United States.
- Cloudinary Ltd. (Israel) stores generated images and screenshots and delivers them through a content delivery network. Cloudinary uses AWS infrastructure in the European Union, the United States, the United Kingdom, Singapore, and Israel. Its EEA-only storage option is an enterprise feature and is not used by this deployment. The European Commission has recognised Israel as providing an adequate level of data protection.
- Modal Labs, Inc. (USA) runs the isolated sandbox that builds and renders generated blocks. It receives the generated project files and image assets, not your account credentials. Modal's default routing and its application logs are in the United States. The sandbox containers are not pinned to the European Union.
- OpenAI, L.L.C. (USA) processes assistant messages, briefs, generated code, and images for generation, judging, and moderation. OpenAI's API terms state that content submitted through its API is not used to train its models by default. We do not use your content to train our own models.
- Black Forest Labs GmbH (Germany) generates images from the prompts we send to its FLUX API.
- Groq, Inc. (USA) is a fallback provider for text moderation and image-direction checks when OpenAI is not configured. It receives the relevant text.
- Voyage AI, Inc. (USA) creates embeddings from images, screenshots, and text used for retrieval.
- Chroma, Inc. (USA) stores embeddings and public metadata used to search the registry.
- Langfuse GmbH (Germany) receives traces with briefs, prompts, judge notes, and timings when tracing is enabled. Tracing is optional.
- Resend, Inc. (USA) sends notification emails to the operators. Those messages can include an account email, a brief, a task ID, and a report summary. Resend stores message content and logs in the United States; choosing an EU sending region would only change where the message is sent from.
- Google Ireland Limited (Ireland) and Google LLC (USA) process your sign-in when you choose Google authentication, as independent controllers for your Google account.

We may also disclose data when the law requires it, when a competent authority makes a lawful request, or when this is necessary to establish, exercise, or defend legal claims. We do not sell personal data.

## 5. International transfers

Some providers are outside the European Economic Area. Where a transfer is not covered by an adequacy decision, we rely on appropriate safeguards, in particular the European Commission's Standard Contractual Clauses and, where applicable, the EU-US Data Privacy Framework. You can ask us for more information about the safeguards using the contact address above.

## 6. How long we keep data

Account and profile data is kept until you delete your account. Authentication records at Supabase are deleted or anonymised when the account is deleted, subject to backup rotation and legal retention duties.

Tasks, briefs, generated artifacts, scores, and public catalogue entries are kept while they remain part of the registry. Published artifacts can remain public after you delete your account. In that case, we remove the link to your profile and your display name from the item, but the brief, code, image, and scores remain public until the item is removed or we delete the personal data in it.

The assistant's conversation memory is held only in the server process and is lost when that process restarts. It is not a durable archive.

Reports, moderation records, deletion audits, and security records are kept for as long as needed to review the case, document the decision, prevent abuse, and meet legal obligations.

Application logs are kept for up to 30 days, unless a security incident, a legal claim, or a legal obligation requires a longer period. Hosting providers may keep their own logs under their terms. Langfuse traces are kept according to the retention settings of the tracing project. Backups are kept for a rolling period and then overwritten.

Where this notice states a purpose rather than a fixed period, we keep the data only while that purpose still applies and review the retention at least once a year.

## 7. Your rights

You have the right to:

- access the personal data we hold about you;
- correct inaccurate data;
- delete your data, subject to legal exceptions;
- restrict processing;
- receive data you provided in a structured, commonly used, machine-readable format;
- object to processing based on our legitimate interests;
- withdraw consent at any time, where processing is based on consent;
- lodge a complaint with a data protection supervisory authority.

You can exercise these rights by writing to [jonathan.freireespinoza@gmail.com](mailto:jonathan.freireespinoza@gmail.com). We may ask for information to confirm your identity before acting on a request. We normally answer within one month. If a request is complex, we may extend that period as the GDPR allows and will tell you why.

You have the right to object at any time, on grounds relating to your situation, to processing based on Article 6(1)(f) GDPR. If you object, we will stop that processing unless we can show compelling legitimate grounds or the processing is necessary to establish, exercise, or defend legal claims. You can object using the email address above.

You can complain to the data protection authority of your habitual residence, your place of work, or the place of the alleged infringement. The authority for the controller's location in Germany is also competent.

## 8. Deleting your account and your content

You can delete your account from your profile. Deletion requires a fresh password confirmation. If you signed in only with Google and cannot use the password confirmation, contact us and we will delete the account after verifying that you control it.

Account deletion removes your profile and your Supabase identity. It does not automatically remove published blocks or images, because those are public registry entries and may already have been copied or cited. The author link is removed. Where a brief or artifact still contains personal data, we will erase or redact that data on request, even if a de-identified artifact remains public. We do not treat a public artifact as a reason to refuse an erasure request that the law requires us to grant.

We may keep the minimum records needed to comply with the law, resolve disputes, or prevent abuse. This can include a deletion audit, a ban record, or a report.

## 9. Children

GenBlocks is not intended for anyone under 16. You must be at least 16 years old to create an account or use the generation features. If we learn that an account belongs to someone under 16, we will close it and delete the related profile data. If you believe a child has created an account, contact us.

## 10. Automated decisions and AI

Moderation, duplicate detection, retrieval, and monthly quotas work automatically. They can refuse a request, hide an artifact, or stop a task. They do not produce a decision with legal or similarly significant effects about you. Reports and account bans are reviewed by a person.

Generated text and images are produced by third-party AI models. They can be wrong, incomplete, or similar to material produced for someone else. We do not use your content to train our own models. We record provenance for generated artifacts where the registry provides it, and we apply the no-people rule described in the [Terms of Use](/terms). The no-people detector returns a yes or no answer about the presence of a person. It does not create a biometric template or identify anyone.

## 11. Security

We use TLS for traffic, access controls for our systems, least-privilege credentials, and contractual protections with our providers. No service is completely secure. If a data breach is likely to result in a high risk to your rights, we will notify you and the competent authority as required by law.

## 12. Changes to this notice

We may update this notice when the service or the law changes. The date at the top shows the current version. If a change is material, we will notify account holders by email or in the interface before it takes effect, where the law requires notice.

## 13. Contact and complaints

For any question about this notice, a data subject request, or a complaint, write to [jonathan.freireespinoza@gmail.com](mailto:jonathan.freireespinoza@gmail.com).

If you are not satisfied with our answer, you can complain to a data protection supervisory authority. You can find the authority for your German state through the [Datenschutzkonferenz](https://www.datenschutzkonferenz-online.de/).
