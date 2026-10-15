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

## Update (Oct 2026) — Forgot password, firm dashboard, privacy & consent
- POST /api/auth/forgot-password (generic response, 6-digit code hashed sha256+secret, 15 min TTL collection password_resets, 3/email/hour, 10/IP/hour) and POST /api/auth/reset-password (5 attempts, single use, bumps password_version); screen /forgot-password (link on sign-in)
- Store links: IOS_APP_URL / ANDROID_APP_URL env (landing pages show buttons when set) — waiting on published store URLs
- GET /api/firm/stats (firm admin): totals, per-adviser rows, lead sources; screen /firm-dashboard (button on adviser Home)
- Privacy: backend/privacy.py draft notice (version 2026-10-draft-1), GET /api/privacy, /privacy screen (Profile, sign-up, call-back form); sign-up requires privacy_accepted (stored version + timestamp); leads require consent tick (consent_at + exact consent_text stored)

## Update (Oct 2026) — Forgot password, privacy & consent, firm dashboard
- POST /api/auth/forgot-password (generic response, 6-digit code hashed, 15 min TTL, 5 attempts, rate limited, emailed via Resend) + POST /api/auth/reset-password (single use, bumps password_version); screen /forgot-password from login
- Privacy notice draft (backend/privacy.py, GET /api/privacy, screen /privacy, linked from sign-up, call-back form, Profile); sign-up requires privacy_accepted (version + time stored); call-back requires consent tick box (consent_text + consent_at stored on lead)
- Firm dashboard GET /api/firm/stats (admin) + screen /firm-dashboard (totals, per-adviser, lead sources) from adviser Home
- Store links: set IOS_APP_URL / ANDROID_APP_URL in backend .env (or Deployment → Secrets) once published

## Update (Oct 2026) — Firm self sign-up, branding, marketing tips
- POST /api/firms/register (public, rate-limited): firm name, FRN (6-7 digits), optional principal + FRN, brand_color (#hex), admin name/title/phone/email/password, privacy_accepted → creates firm (plan "trial", trial_ends_at +14 days) + firm-admin adviser (code FIRST-FIRMCODE), returns token
- POST /api/firm/logo (firm admin, multipart PNG/JPG/WebP ≤2MB) → Emergent Object Storage (backend/storage.py, path safe-sorry/firm-logos/{firm_id}/uuid); GET /api/firm-logo/{firm_id} public
- adviser_profile now returns firm_id, brand_color, logo_url, plan, trial_ends_at, trial_days_left (null for SFL "founder")
- PUT /api/firm accepts brand_color; invite/ad landing pages use firm logo + brand colour
- Screens: /firm-signup (link on onboarding), branding section in Adviser settings, trial banner + logo + Marketing tips button on adviser Home, /marketing-tips (static content src/marketing-tips.ts), client Adviser tab shows firm logo/brand line; non-AR firms get correct FCA footer; Book-a-call hidden when no booking link
- Billing: not built (user will supply pricing). Trial expiry shows banner only, nothing is blocked
- Email: mark.turner@sflwealth.co.uk is a real mailbox (SMTP RCPT 250); platform email returns false 422 undeliverable_recipient → user to contact support@emergent.sh

## Update (Oct 2026) — Management presentation
- GET /api/presentation (backend/presentation.py): 11-slide browser deck for SFL management (SFL only, no resale). Arrow keys / swipe / buttons, full-screen, Print → Save as PDF = 1 slide per A4 landscape page

## Update (Oct 2026) — Naming & logo concepts
- "Safe > Sorry" = "better safe than sorry". Email sender name now EMAIL_FROM_NAME="Better Safe Than Sorry" (">" not allowed in sender)
- GET /api/logo-concepts (backend/logo_concepts.py): 5 SVG concepts (A wordmark, B shield, C family roof, D S>S seal, E app icon), navy/gold. Not applied to app yet; user's own draft not received (no asset uploaded)
- Polished logos from user's draft via Gemini Nano Banana (gemini-3-pro-image-preview, script backend/scripts_gen_logo.py): backend/static/logos/logo_v1..v3.png served at /api/static/logos/*, shown at top of /api/logo-concepts. Not applied to app yet
- Logo "Polished 1" applied: app icon / adaptive icon / favicon (emblem crop), splash (full logo on white, bg #FFFFFF), onboarding top-left logo (assets/images/logo-full.png), invite/ad landing hero + presentation cover (/api/static/logos/logo_full_cropped.png)
- CORRECTION: user's chosen logo is the gold-ring version (logo_v2). Dark version generated (logo_v2_dark.png) → keyed to transparent logo_dark_transparent.png / emblem_dark_transparent.png. Applied: onboarding (no box, centred over navy gradient), splash (navy bg), app icon (gold/white emblem on navy), adaptive icon (transparent, bg #223342), favicon, invite/ad landing hero, presentation cover
- GET /api/try (backend/try_page.py, segno): QR code that ANY phone camera can open → web app URL (derived from request host). Fixes "no data found" when iPhone camera scans the Expo Go preview QR (exp:// link needs Expo Go)
- Emails (reset code + new lead) now start with a navy band + gold logo (email_header() in server.py, absolute https URL from x-forwarded-host). Invites are shared via share sheet, not email.
- Lead detail: Needs/Has/Gap table + "What they have now" existing-cover list (from assessment inputs)
- GET /api/adviser/leads/export[?status=] → CSV (UTF-8 BOM, formula-injection safe) contact + consent only, for CRM import (SFL uses Greenlight; import method TBC by SFL ops). Leads tab: "Download for CRM" button (web download / native share sheet via expo-file-system + expo-sharing, src/export-leads.ts); desktop-wide layout (2-3 card columns ≥900/1280px, max width 1240); lead detail max width 760

## Update (Oct 2026) — Rosemount compliance changes
- calc.py → 2026/27: SSP £123.25/wk or 80% AWE if lower (28 wks), New Style ESA £95.55/wk for max 12 months (shown as "may be able to claim… isn't automatic"), BSP for cohabiting partners WITH children (higher rate), Class 4 NI 6% for self-employed; results include tax_year
- Exact Rosemount wording: NOT_ADVICE (assessment step 1 + report top + privacy) and AI_LETTER (under every letter) in frontend/src/compliance-text.ts and backend privacy.py
- AI pseudonymisation: names → PARTNER/CHILD_A tokens before Claude, swapped back after; user's own name never sent
- Erasure: POST /api/auth/delete-account (client, password) and POST /api/adviser/leads/{lid}/erase → deletes user, assessments, leads, resets; logs non-identifying db.erasure_log with DEL-XXXX reference. Screens: /delete-account, lead detail "Delete this person's data"
- Privacy v2026-10-draft-2: SFL sole controller; Rosemount only in AR statement. Firm name now "Secure for Life Wealth Management Ltd" (.env FIRM_NAME + DB)
- Lead detail: "Client-entered, not yet verified. Confirm at fact-find." notice
- Compliance reviewer account in test_credentials.md
- Launch reel: backend/scripts_make_reel.py (PIL frames + imageio-ffmpeg) → /api/static/reels/safe-sorry-launch-reel.mp4 (1080x1920, 27s, 30fps, silent track) + cover jpg. Hook: phone battery % vs "how long would your family's money last?". Uses demo screenshots (Tom). Ends with not-advice + AR disclosure
- Reels served via backend/reels.py: GET /api/reels (mobile download page, playsinline video + Download buttons) and /api/reels/file/{name} with HTTP Range (206) support — fixes iPhone Safari playback (StaticFiles ignored Range). ?download=1 = attachment
- Marketing assets (backend/reel_variants.py + scripts_make_reel.py render(name)): coming-soon reel 27s, award reel 21s (Mark photo + Protection Adviser of the Year 2026, Next Intelligence Awards), two 15s stories ("Link in bio": coming soon / launch), 6-slide carousel 1080x1350 jpg + zip. All listed with download buttons on GET /api/reels
