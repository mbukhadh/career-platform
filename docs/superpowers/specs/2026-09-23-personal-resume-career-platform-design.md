# Personal Resume Website and Career Platform Foundation

## Status

Draft for user review. This document describes the first product scope and the
foundation it should establish for later career-platform capabilities. No
implementation is authorized by this document alone.

## Product intent

Build a trustworthy, fast personal resume website for recruiters and hiring
managers. The first release should make the owner's professional experience,
skills, education, and contact path easy to understand while presenting
projects and professional credibility clearly enough to support future
portfolio expansion.

The system must be designed so that content is stored as structured records
rather than embedded in page components. The initial owner will update content
through code and database migrations; a private content-management interface is
explicitly out of scope for the first release.

## Goals and success criteria

### Goals

- Present a polished, responsive public resume.
- Make the owner's value proposition, experience, skills, education, and
  contact path scannable.
- Keep content queryable and independently reusable by future pages, APIs, or
  export formats.
- Protect direct contact details while still providing a clear contact action.
- Establish ownership and visibility boundaries that can grow to multiple
  profiles without requiring a data-model rewrite.

### Success criteria

- A recruiter can identify the owner's role, strengths, recent experience, and
  contact action from the landing page without authentication.
- Resume content can be changed by updating structured data and applying a
  migration or seed process; page layout code does not need to be edited for
  ordinary content changes.
- Contact details are not rendered in the initial public HTML or exposed in
  unauthenticated API responses.
- The public profile remains viewable using a versioned last-known-good
  snapshot when the database is unavailable; the fallback must not expose
  drafts or protected contact details.
- The public site is usable on mobile and desktop, keyboard navigable, and
  provides meaningful metadata for search and link previews.
- Adding a second profile, private section, or project collection later has a
  clear extension point in the schema and authorization model.

## Scope

### First release

The public site includes:

- A landing/resume page with a professional summary and primary call to action.
- Work experience entries with employer, role, dates, location, description,
  and ordered accomplishments.
- Education entries with institution, program, dates, and optional details.
- A skills section with grouped skills and explicit display ordering.
- A projects/credibility section limited to the structured project summaries
  needed to showcase work; long-form case studies are future scope.
- A contact action that can use a protected server-side destination without
  publishing the owner's raw email address.
- Basic SEO metadata, a generated sitemap, and a robots policy.

The data layer includes an owner/profile boundary even though the first release
has one active public profile. Content records have stable identifiers,
ordering, publication state, and timestamps.

### Explicitly out of scope

- Public account registration or user-created profiles.
- A private admin dashboard or headless CMS.
- Social networking, messaging, comments, endorsements, or following.
- Job-board or opportunity-management workflows.
- Analytics dashboards beyond the hosting/provider baseline.
- Payments, subscriptions, or monetization.
- Automated resume generation from external profiles.
- Full applicant tracking or recruiter portals.
- Long-form publishing, newsletters, or a content editor.

## Users and access model

### Public visitor

An unauthenticated visitor can view published resume content and use the
contact action. Unpublished, draft, archived, and private records are never
included in public queries or page output.

### Owner

The initial owner is the only content editor. Updates happen through reviewed
code changes, migrations, or seed data. The owner model should be represented
separately from public content so an authenticated administration surface can
be added later without changing every content table.

### Future platform user

The schema should support associating a profile with an account in a later
release, but the first release must not expose account creation or assume that
all platform users share the initial owner's visibility settings.

## Proposed technical baseline

Because the repository is currently an empty project with only a README, the
recommended baseline is:

- TypeScript with Next.js App Router for the public web application and
  server-side request handling.
- PostgreSQL as the durable relational database.
- Prisma as the typed data-access layer and migration tool.
- A managed deployment/runtime compatible with Next.js and managed PostgreSQL.

This baseline keeps the first release straightforward while providing typed
server boundaries, relational integrity, migrations, and a path to authenticated
administration. The public page should query published content on the server;
the browser should not receive database credentials or unrestricted content
queries.

The implementation plan must confirm the exact hosting provider, secrets
management, email/contact delivery mechanism, and whether a local development
database uses Docker or another supported setup. It must also define where the
versioned public snapshot is stored and how it is atomically promoted after a
successful content update.

## Domain model

The initial relational model should contain these logical entities:

- **Owner**: the account/person who controls one or more profiles.
- **Profile**: public identity, slug, headline, summary, location, avatar or
  social preview references, and publication state.
- **Experience**: an ordered role belonging to a profile, including employer,
  title, dates, location, summary, and publication state.
- **Experience accomplishment**: ordered bullet content belonging to an
  experience entry.
- **Education**: an ordered academic entry belonging to a profile.
- **Skill group**: an ordered category such as Languages or Tools.
- **Skill**: an ordered skill belonging to a skill group and profile.
- **Project**: an ordered, optionally published project summary belonging to a
  profile, with links and a short description.
- **Contact configuration**: protected destination and public call-to-action
  settings owned by the profile; raw destination details are server-only.

All child records must be scoped through a profile relationship. Slugs and
public identifiers must be unique within their intended scope. Dates should
support ongoing experience and education without fake end dates. Ordering must
be explicit rather than inferred from creation timestamps.

## Public data flow

1. A visitor requests the public profile route.
2. The server resolves the public profile by its published slug.
3. A repository/data-access module fetches only published profile and child
   records, applying explicit ordering.
4. If the database read fails or times out, the server loads the most recent
   validated, versioned public snapshot. This snapshot contains only
   published, public-safe profile content and is suitable for rendering the
   page and metadata without database access.
5. The server renders the page and metadata from either the database result or
   the snapshot, marking the database result as the source of the newly
   promoted snapshot only after validation succeeds.
6. A contact request, if enabled, is handled by a server route or server
   action that validates input, rate-limits abuse, and forwards to the
   protected destination without returning it to the client.

No client-side query should be able to select arbitrary profiles or retrieve
draft/private records. The data-access boundary should make the published
filter difficult to omit accidentally. Snapshot generation must use the same
published-content boundary, must exclude protected contact configuration, and
must fail without replacing the existing snapshot if validation fails.

## Contact and privacy requirements

- Do not render the owner's raw email address in public HTML, metadata, JSON-LD,
  or unauthenticated API responses.
- Prefer a server-mediated contact form or an explicitly protected mail link.
- Validate and length-limit submitted name, email, message, and optional
  honeypot fields.
- Apply rate limiting and basic abuse controls before attempting delivery.
- Do not log message bodies or protected destination details.
- Return generic success/failure messages that do not reveal whether a
  destination exists.
- Make the contact mechanism configurable so it can later be replaced without
  changing profile content records.

## Presentation and accessibility

The visual direction should be professional, restrained, and content-first:
clear hierarchy, high contrast, readable typography, and prominent but
non-intrusive contact and project actions. The page should be responsive from
small screens upward and avoid interaction patterns that hide core resume
content behind hover-only controls.

The implementation must provide semantic landmarks and headings, keyboard
operation, visible focus states, descriptive link names, alt text where images
carry meaning, and status messaging for contact submission. Automated
accessibility checks should be supplemented by a keyboard-focused smoke test.

## Reliability and error handling

- Missing or unpublished profiles should produce a deliberate not-found
  response rather than an empty success page.
- A database outage must not take down the public profile: serve the latest
  validated public snapshot when one exists.
- Snapshot reads must be independent of the unavailable database and must be
  atomic so visitors never receive a partially written snapshot.
- If neither the database nor a valid snapshot is available, return a
  deliberate service-unavailable response rather than an empty or
  success-shaped page.
- Database and contact-provider failures should be logged server-side with
  actionable context but without secrets or personal message contents.
- Public errors should be concise and should not expose SQL, stack traces,
  schema details, or protected contact data.
- Contact delivery should fail closed: never claim a message was delivered when
  the provider rejected it.
- Migrations must be backward-compatible with the deployed application or
  coordinated with an explicit release step.

## Testing requirements

The implementation should include:

- Data-access tests proving unpublished and private records are excluded.
- Snapshot tests proving database failure serves the last-known-good public
  profile, invalid snapshots are rejected, and snapshot updates are atomic.
- Model/migration tests for profile ownership, ordering, publication state, and
  ongoing date ranges.
- Route or component tests for the public resume sections and not-found state.
- Contact tests for validation, rate limiting, provider failure, and absence of
  the raw destination in responses and rendered markup.
- Accessibility checks for the rendered page and keyboard navigation.
- A production build/type-check and a smoke test against a seeded profile.

## Delivery slices

Implementation should be planned in these independently verifiable slices:

1. Application shell, configuration, database connection, migrations, and
   seed data, including the versioned public snapshot mechanism.
2. Typed domain model and published-content data-access boundary.
3. Responsive public profile/resume page with SEO metadata.
4. Protected contact flow and abuse controls.
5. Snapshot fallback, failure-mode tests, accessibility checks, and deployment
   configuration.

Later features should extend the domain through new profile-scoped entities and
explicit permissions rather than by adding platform behavior directly to the
public resume page.

## Open decisions for spec review

The following are intentionally called out for confirmation before planning:

1. Whether the proposed Next.js, TypeScript, PostgreSQL, and Prisma baseline is
   acceptable.
2. Whether project summaries belong in the first release or should be deferred
   to the later portfolio slice.
3. Which contact mechanism and hosting/provider constraints should govern the
   implementation plan.
