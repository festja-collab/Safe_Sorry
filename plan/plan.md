# Safe > Sorry: Launch Guide and Readiness Plan

A step-by-step guide to taking Safe > Sorry from preview to the App Store and Google Play, with costs and credits explained.
This is information only for now. Nothing gets published until Mark decides to go ahead.

## Who it's for
- **Mark Turner (app owner):** plans the launch, sets up the business and store accounts, and decides when to go live.
- **Later:** SFL, Rosemount compliance, and any future adviser firms that rely on the live app.

## Core features and experience (what launch involves)

### 1. Ownership and business set-up (before any store account)
- **The app belongs to Mark personally.** SFL has given permission to use its name and is the data controller for client data, but owns nothing.
- **Setting up a limited company is recommended** (general guidance, not legal or tax advice; confirm with an accountant). A company:
  - holds the app and its intellectual property separately from Mark personally, and limits personal liability;
  - is needed to get a D-U-N-S number, which both stores require for a company (organisation) account;
  - avoids Google's 12-testers-for-14-days rule, which applies to personal accounts;
  - makes it simpler to sell to other firms later, and to sign contracts and data agreements.
- **Apple's rule for finance apps:** they must be submitted by a legal entity, not an individual. Mark's company would publish the app, and SFL's written permission (and Rosemount's approval) would be attached in Apple's "review notes" to explain the arrangement.
- **Put the arrangement with SFL in writing:**
  - Mark's company owns the app;
  - SFL is the data controller for its clients' data;
  - Mark's company processes that data on SFL's behalf (a data processing agreement);
  - Mark's employment contract doesn't give SFL any claim over the app.
- **ICO registration:** Mark's company will probably need to register with the Information Commissioner's Office (the data-protection regulator) and pay its annual data-protection fee.

### 2. Store accounts
- **Apple Developer Program:** company account in the company's name. Needs the D-U-N-S number and Apple's 2-factor sign-in.
- **Google Play Console:** company account. Goes straight to production with no 12-tester period. The Financial features declaration in the Play Console still needs completing.
- **Apple first:** D-U-N-S plus Apple verification is the longest wait, typically 1–3 weeks.

### 3. What clicking Publish does on Emergent
- **Deploy:**
  - creates the live version: the app's server hosted by Emergent, and the app itself served to phones;
  - from then on, the app runs on phones only, with no public website and no custom web address for the app;
  - the preview carries on separately for testing changes;
  - future changes only go live after a Redeploy.
- **Generate builds (after deploying):**
  - **iPhone:** Emergent builds the app and sends it to TestFlight, Apple's testing app. Mark tests it on his phone, then submits it to Apple for review in App Store Connect.
  - **Android:** Emergent produces the store files (.AAB/.APK). Mark uploads them in the Google Play Console and submits for review.
  - Rebuild after any change that should reach phones.
- **Data:** as agreed, everything from the preview is copied into the live version, including test families and leads. The platform docs don't say whether this happens automatically, so it's done as a deliberate copy step at launch.

### 4. Store listing pack (prepared before submission)
- **Text:** app name, subtitle, short and full descriptions, keywords, category (Finance), and age rating answers. All wording is approved by compliance.
- **Images:**
  - phone screenshots in Apple's and Google's required sizes;
  - Google's feature graphic (the banner image at the top of a Play Store listing);
  - the app icon (already done).
- **Privacy answers:** Apple's privacy "nutrition label" and Google's Data safety form. Both are based on what the app collects: names, email, finances, family details and phone number (for call-backs), plus the AI letter with names hidden.
- **Required web addresses:** a public privacy policy page and a support page, both served by the live app's server.
- **Apple reviewer login:** a test account plus a short explanation of the SFL / Rosemount arrangement. Account deletion is already in the app, which Apple requires.

### 5. After approval
- Add the real App Store and Google Play links. Invite pages, ad landing pages and the "link in bio" then show proper download buttons instead of "Coming soon".
- Switch marketing over: post the launch reel and the launch-day Story, which say "Download".
- Check that invite and ad links point to the live server, not the preview.
- **Laptop use:** advisers use the phone app only for now. Leads and "Download for CRM" work on the phone.

## Costs and credits

| Item | Who charges | Cost | How often |
|---|---|---|---|
| Keeping the app live (deployment) | Emergent | 50 credits | Per month, while deployed |
| Redeploying or rolling back | Emergent | No extra credits (documented) | Each time |
| iPhone and Android builds | Emergent | No per-build charge documented | Each build |
| Building any further changes | Emergent | Credits for the work done | As used |
| AI family letters | Emergent Universal Key balance | Small amount per letter, depending on usage | As used; auto top-up available |
| Apple Developer Program | Apple | US$99 (about £79) | Yearly |
| Google Play Console | Google | US$25 | One-off |
| D-U-N-S number | Dun & Bradstreet | Free | One-off |
| Limited company | Companies House | Registration fee, plus a small yearly confirmation statement fee | One-off, then yearly |
| Accountant for company accounts | Accountant of choice | Varies | Yearly |
| ICO data-protection fee | ICO | Lowest tier, about £52 | Yearly |
| Ads (optional) | Meta / Google | Mark's choice, e.g. £5–£10 a day to test | As chosen |

Credit balances: Profile → Credits (Emergent) and Profile → Universal Key (AI letters, top-ups, auto-recharge).

## User flow (Mark's launch journey)
1. **Business set-up:**
   - form the limited company;
   - get the arrangement with SFL in writing;
   - register with the ICO.
2. **Store accounts:**
   - apply for a D-U-N-S number for the company;
   - open the Apple and Google company developer accounts.
3. **Prepare the listings:** get the store listing pack and the privacy and support pages ready, then have compliance sign off the store wording.
4. **Publish on Emergent:**
   - click Publish → Deploy;
   - copy the preview data across;
   - test on a phone using the deployment QR code.
5. **iPhone:** Generate the iOS build → test it in TestFlight → submit to Apple with the reviewer login and review notes.
6. **Android:** Generate the Android build → upload it in the Google Play Console → complete the Data safety form and Financial features declaration → submit.
7. **After both stores approve:**
   - add the store links;
   - redeploy;
   - start the launch-day posts.

## UI/UX feel
- The app itself doesn't change for launch.
- Store listings keep the same calm navy-and-gold look, warm wording and "not regulated advice" honesty used in the app and the reels.

## Implementation phases
- **Phase 1 (MVP, the part being produced now): this launch guide.**
  - Ownership and company guidance, store account requirements, what Publish does, and the costs and credits table.
  - No changes to the app and no publishing.
- **Phase 2 (when Mark says go): launch preparation and publish.**
  - Store listing pack, plus public privacy and support pages.
  - Deploy, copy the preview data, and generate the iOS and Android builds.
  - Submit to both stores.
- **Phase 3 (after approval): go live.**
  - Add the store links and switch landing pages to download buttons.
  - Redeploy, and switch the marketing to the "Download" versions.
  - Optionally plan a laptop dashboard later.

## Assumptions
- Mark owns the app personally. SFL has given permission only and claims no ownership; this needs confirming in writing.
- The company route is recommended but optional. This is general guidance, not legal or tax advice.
- Apple counts Safe > Sorry as a financial-services app under its rules, so a company account is needed. SFL's written permission explains the link to the regulated firm.
- Costs are as published at the time of writing: Apple US$99/year, Google US$25, Emergent 50 credits/month. Any of these may change.
- Emergent's docs don't document a per-build charge, or whether preview data copies across automatically. A deliberate copy step is planned for the data.
- "Copy everything across" includes test families, leads and accounts, as Mark asked. Mark's adviser account and the compliance reviewer login go live too.
- The live app has no public web address for the app itself. Server-hosted pages (invites, ad landing pages, reels, privacy) are served from the live server's address.
- Advisers use the phone app only at launch.
- The real-inbox check of reset-code and lead emails (still waiting on Emergent support) is resolved before launch.
