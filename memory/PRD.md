# Safe > Sorry — PRD

## Original problem statement
UK protection gap assessment mobile app. Gap assessment questionnaire, personalised report, educational content, adviser lead capture. User: "I want the app to play on the users emotions... make the user see what the gap, unattended to, would mean for their family in real terms if the worst were to happen. It shouldn't just be a calculator."

## User choices
- Email/password auth with saved profiles
- Rule-based UK calc + AI explanation (Claude Sonnet 5.5, Emergent LLM key)
- Leads: form → DB + adviser email (Emergent Resend) + "Book a call" Calendly link (placeholder)
- Warm & friendly design (journal/paper personality: Fraunces + Quicksand, cream/sage/clay)
- App name "Safe > Sorry" (email sender name "Safe Over Sorry" because ">" is not allowed)

## Architecture
- Backend FastAPI: server.py (auth JWT+bcrypt, assessments, story, articles, leads, config), calc.py (UK tax/NI, BSP, SSP/ESA, runway simulation, impacts, milestones), emailer.py (Resend proxy + guardrails), articles.py
- Frontend Expo Router: onboarding, auth, assessment (12 one-question steps), report/[id] (hero headline, savings runway, milestone timeline, real-terms impacts, AI letter, gap cards, adviser CTA), (tabs) Home/Learn/Adviser/Profile, article/[slug]

## Implemented (Oct 2026)
- All of the above; testing iteration 1: 17/17 backend + full frontend flows passed

## Known / config
- Adviser email: ADVISER_EMAIL=delivered@resend.dev (placeholder) in backend/.env
- CALENDLY_URL placeholder in backend/.env
- Email sending currently blocked by insufficient Emergent credits (402) — leads still saved

## Backlog
- P1: Password reset, admin lead view, real adviser email/Calendly
- P1: Share story card image / PDF export of report
- P2: Quote estimates per gap (monthly premium ranges), reminders to review after life events, dark mode

## Update (Oct 2026) — Adviser details configurable
- Adviser name, bio, photo URL, phone, firm name, FCA number, adviser email and Calendly link all come from backend/.env (ADVISER_NAME, ADVISER_BIO, ADVISER_PHOTO_URL, ADVISER_PHONE, FIRM_NAME, FCA_NUMBER, ADVISER_EMAIL, CALENDLY_URL) via GET /api/config
- Adviser tab: tap-to-call button, FCA disclosure footer
- Real values still pending from user (placeholders in place)

## Update (Oct 2026) — Real adviser details
- Adviser: Mark Turner, Senior Protection Specialist, SFL Wealth Management Ltd (FRN 912517), AR of Rosemount Financial Solutions (IFA) Limited (FRN 535515)
- Leads → mark.turner@sflwealth.co.uk; Calendly https://calendly.com/mark-turner-sflw; phone 07882 719456; photo from sflwealth.co.uk team page
- AR disclosure footer on Adviser tab
- Pending: firm compliance sign-off before publishing
- Theme switched to SFL-inspired white/navy (#223342)/gold (#BF9B30)

## Update (Oct 2026) — Security hardening
- Mongo-backed rate limiter (backend/limiter.py, TTL collection rate_limits)
- Limits: failed logins 5/email & 10/IP per 15 min; registrations 5/IP/hour; assessments 5/user/day; AI stories 5/user/day; leads 3/user/day
- Password min 10 chars for new accounts; JWT lifetime 7 days; constant-time login (dummy hash)

## Update (Oct 2026) — Compliance review pack
- GET /api/compliance-pack: printable HTML pack (backend/compliance_pack.py) generated from live settings: summary, review access, journey, all customer wording, calc assumptions + worked example, AI prompt + fixed sample letter, data/processors/security, Consumer Duty, open items, sign-off table

## Update (Oct 2026) — Multi-firm foundation + lead inbox
- Collections: firms; users gain role (client/adviser), adviser_id, firm_id, is_firm_admin, adviser profile fields, adviser_code (unique)
- Seed (startup, $setOnInsert): SFL firm + Mark adviser (firm admin, code MARK-SFL); migrates existing clients/leads to Mark
- Client: optional adviser code at sign-up; Profile → Your adviser (link by code); Adviser tab reads /api/my-adviser
- Adviser: dashboard Home (stats, share code, new leads), Leads tab (filter chips), lead detail (call/email, status new/contacted/closed, family summary, open full report), Adviser & firm settings
- Endpoints: /api/my-adviser, /api/me/adviser, /api/adviser/leads[/{id}] (GET/PATCH), /api/adviser/stats, /api/adviser/profile (GET/PUT), /api/firm (PUT, admin)
- Next: firm admin adding advisers, Stripe subscriptions, per-firm branding

## Update (Oct 2026) — Invite a client
- Adviser Home → "Invite a client" (/invite): name, 3 message templates, optional note, live preview, native share sheet
- Public landing page GET /api/invite/{code}?name= (backend/invite.py): adviser photo, code, store buttons (IOS_APP_URL / ANDROID_APP_URL env; "Coming soon" when empty), FCA line

## Update (Oct 2026) — Password change, ad landing, lead tracking, add advisers
- POST /api/auth/change-password (pwdv claim revokes old tokens; returns fresh token); forced change when must_change_password (403 on normal routes, tabs redirect to /change-password)
- Ad landing page GET /api/start[/{code}]?src=FB shows code MARK-SFL-FB; invite page shows MARK-SFL-INV
- Codes with suffix resolve to adviser + source; users store signup_code/signup_source/heard_from ("How did you hear about us?" chips); leads snapshot source; lead card/detail show source; stats by_source/by_heard on adviser dashboard; ad link generator with campaign chips
- Firm admin: GET/POST /api/firm/advisers (auto code FIRST-FIRMCODE, one-time temporary password, forced change on first login); screen /firm-advisers from Adviser settings
