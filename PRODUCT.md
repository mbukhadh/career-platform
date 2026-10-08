# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Recruiters and hiring managers screening Mohammad (MJ) Bukhadhour for roles in
banking and finance, in Kuwait or the US. They usually arrive from a resume,
LinkedIn, or an application link, and decide in a minute or two whether to
contact him.

## Product Purpose

A personal resume site at `mjbukhadhour.com` for MJ, a senior at Loyola
Marymount University studying Information Systems and Business Analytics,
graduating May 2027. It exists to help him get hired. Success is a recruiter
understanding who he is and what he is looking for, then getting in touch.

Target roles: banking and finance. He is open to data or IT analyst,
operations, and client-facing roles.

## Positioning

Inferred from the repository, not confirmed by MJ: the site is itself one of
his projects. He built it and runs it himself (FastAPI, a database, a cloud VM,
HTTPS on his own domain), so it is evidence of technical skill as well as a
place to list it.

## Operating Context

- One public page showing a profile: name, headline, location, GitHub and
  LinkedIn links, professional summary, experience, education, skills,
  projects, and a contact form.
- Content is stored in a database and rendered by the server. MJ changes
  content in the database, not in the templates.
- Built as coursework for ISBA 4775 at LMU, and reviewed by the instructor as
  well as by recruiters.

## Capabilities and Constraints

Confirmed by MJ:

- **Content stays as it is.** Design work must not add, invent, or reword
  experience, projects, skills, or claims. Only MJ changes content.
- **The site stays database-driven.** FastAPI, Jinja templates, and plain CSS,
  with content coming from the database. No front-end framework or build step.
- **The contact form stays** as the way recruiters reach him, alongside the
  GitHub and LinkedIn links.
- **Content changes are suggestions only.** A critique may recommend content
  changes (for example, mentioning banking and finance in the headline or
  summary), but only as suggestions for MJ to make in the database. Design
  work never edits content.

From the repository:

- Sections with no published entries show a "No … published" line.
- When the database is unavailable, the app serves the latest saved snapshot
  of the profile.
- Email delivery for the contact form was not configured on the server as of
  October 6, 2026.

Undecided:

- Whether the site stays a single page.

## Evidence on Hand

Real content, all in the database (source: `app/seed.py`):

- Name, headline ("Information Systems & Business Analytics student at LMU"),
  location (Los Angeles, California), GitHub and LinkedIn links.
- Summary: one sentence.
- Education: B.S. Information Systems & Business Analytics, Loyola Marymount
  University, expected May 2027.
- Skills: one group, "Programming & Data", with Python and SQL.
- Projects: one, Career Platform (this site).
- Experience: a single placeholder entry, "Experience — coming soon".

Absent, and not to be fabricated: work experience, a photo or logo,
testimonials, metrics, certifications, and any banking or finance coursework,
internships, or projects.

## Product Principles

1. A recruiter should know who MJ is and what he wants within the first screen.
2. Only show what is true today. Thin content is presented honestly, never
   padded.
3. Getting in touch should be the easiest thing to do on the page.
4. The site has to keep working: it is live on his own domain and is itself
   part of what he is showing.
