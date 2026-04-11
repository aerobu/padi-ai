# PRD Stage 5: MMP — Monetization, Polish & School Onboarding
## PADI.AI | Version 1.0 | Target Completion: Month 20

**Document Status:** Draft  
**Owner:** Product — Growth & Platform  
**Reviewers:** Engineering (Full Stack), Engineering (Payments/Infra), Legal (COPPA/FERPA/PCI), Design, Marketing, QA  
**Dependencies:** Stages 1–4 (all MVP features complete)  
**Epic Reference:** MATH-500 series  
**MMP Milestone:** ✅ Stage 5 Completion = MMP

---

## Table of Contents

1. [Overview & MMP Declaration](#51-overview--mmp-declaration)
2. [Functional Requirements](#52-functional-requirements)
3. [MMP Feature Checklist](#53-mmp-feature-checklist)
4. [Non-Functional Requirements](#54-non-functional-requirements)
5. [Data Models](#55-data-models)
6. [API Endpoints](#56-api-endpoints)
7. [Acceptance Criteria](#57-acceptance-criteria)

---

## 5.1 Overview & MMP Declaration

### What Makes This MMP vs. MVP

The MVP (Stage 4) proved the product works: a student can take a diagnostic, practice with an AI tutor, be assessed against Oregon standards, and improve through a remediation loop. It is a complete, functional learning product.

The MMP (Minimum Marketable Product) makes the product viable as a commercial offering and scalable beyond a small beta cohort. The distinction is not about learning efficacy — that was proven in Stages 1–4. The MMP adds:

| Dimension | MVP (Stage 4) | MMP (Stage 5) |
|---|---|---|
| **Revenue model** | None (free beta) | Subscription billing via Stripe |
| **School/district sales** | Manual, one-off | Scalable bulk onboarding + SSO |
| **Engagement & retention** | Basic sessions | Gamification, mascot, missions, badges |
| **Language access** | English only | English + Spanish |
| **Privacy certification** | COPPA-compliant code | COPPA Safe Harbor certified |
| **Scale** | 200 concurrent users | 10,000 concurrent users |
| **Uptime SLA** | Best effort (99.5%) | 99.9% (school contract eligible) |
| **Analytics** | Basic PostHog events | Full funnel, A/B testing, cohort retention |
| **Content depth** | ~500 questions | 10,000+ questions + video micro-lessons |
| **Accessibility** | WCAG 2.1 AA | WCAG 2.1 AA + dark mode + reduced motion |

### Added Capabilities in Stage 5

**Subscription Billing (FR-21):** Freemium → paid conversion via Stripe. Three-tier model (Individual, Family, Classroom). 14-day free trial. School/district invoicing with PO support.

**School/District Onboarding (FR-22):** Bulk roster CSV import. School admin account type. FERPA Data Processing Agreement flow. SSO via Google Workspace for Education and Clever. School-wide admin dashboard with standards coverage reporting.

**Enhanced UX & Engagement (FR-23):** Named and animated mascot (Pip). 20+ achievement badges. Weekly Math Missions. Parent-child Study Together mode. Handwriting recognition for tablet numeric input. Dark mode and accessibility theme. Full Spanish language support.

**Analytics & A/B Testing (FR-24):** PostHog/Mixpanel integration. Complete event taxonomy. A/B testing framework for product decisions. Funnel analysis and cohort retention. Question quality analytics.

**COPPA Safe Harbor & Privacy (FR-25):** Formal certification (kidSAFE, PRIVO, or TrustArc). Student Privacy Pledge. Data minimization audit. FERPA compliance documentation. Annual privacy review.

**Content Expansion (FR-26):** 10,000+ questions (up from ~500). Video micro-lessons per module. Printable worksheet generator. "Explain to me" Claude-powered concept explanation.

### The MMP is the Commercial Launch Milestone

Stage 5 completion signals that PADI.AI is ready for:
- Public marketing and app store listing
- School and district sales conversations
- Influencer and parenting press outreach
- App Store / Google Play listing
- App Store optimization (ASO)

Everything required to acquire, convert, retain, and monetize customers at scale is in place at MMP.

---

## 5.2 Functional Requirements

### FR-21: Subscription & Billing

#### FR-21.1: Freemium Model

PADI.AI operates on a freemium model. The free tier is deliberately generous enough to demonstrate real value but constrained enough to drive upgrade.

**Free Tier (no payment required, no time limit):**
- Full diagnostic assessment (once per account)
- First learning plan module (first 5 skills) — complete access
- 3 practice sessions per week (capped at 3 sessions, resets every Monday)
- Basic parent dashboard (current week data only)
- No access to EOG Assessment
- No access to progress report PDF
- No teacher sharing

**This design rationale:** The free tier delivers enough value to hook parents whose children need help (the core use case). Parents who see their child making progress on the free tier have strong motivation to convert. The EOG Assessment and full reporting are the natural conversion drivers.

#### FR-21.2: Subscription Tiers

| Tier | Monthly | Annual | Students | Features |
|---|---|---|---|---|
| **Individual** | $14.99/mo | $119/yr (~$9.92/mo, 34% off) | 1 student | Full access: unlimited sessions, all reports, EOG assessment, teacher sharing |
| **Family** | $24.99/mo | $199/yr (~$16.58/mo, 34% off) | Up to 3 students | All Individual features for each student; single family billing |
| **Classroom** | $299/yr | — (annual only) | Up to 30 students | All Individual features; teacher account with class dashboard; school billing (PO support) |

**Pricing rationale:**
- Individual aligns with Duolingo Max ($13.99/mo) and Prodigy Premium ($8.99/mo), priced at a premium due to Oregon-specific curriculum alignment and AI tutoring
- Family tier: 67% of cost of two Individual subscriptions (meaningful discount, drives upgrade)
- Classroom: ~$10/student/year — competitive with IXL ($199/teacher) and Khan Academy's school pricing

#### FR-21.3: Stripe Integration

All payment processing via Stripe. No card data touches PADI.AI servers (Stripe Elements for card input; Stripe.js on client).

**Stripe Products/Prices to configure:**
```
Product: PADI.AI Individual
  Price: price_individual_monthly  → $14.99/month (recurring)
  Price: price_individual_annual   → $119.00/year (recurring)

Product: PADI.AI Family
  Price: price_family_monthly      → $24.99/month (recurring)
  Price: price_family_annual       → $199.00/year (recurring)

Product: PADI.AI Classroom
  Price: price_classroom_annual    → $299.00/year (recurring)
```

**Stripe Customer creation:**
```python
async def create_stripe_customer(user: User) -> str:
    """Creates Stripe customer. Returns Stripe customer ID."""
    customer = await stripe.Customer.create(
        email=user.email,
        name=user.display_name,
        metadata={
            "padi_user_id": str(user.id),
            "account_type": user.account_type
        }
    )
    # Store stripe_customer_id on users table
    await update_user_stripe_id(user.id, customer.id)
    return customer.id
```

**Subscription lifecycle events (Stripe webhooks → FastAPI `/webhooks/stripe`):**

| Stripe Event | Action |
|---|---|
| `customer.subscription.created` | Set `subscriptions.status = 'active'`; unlock premium features |
| `customer.subscription.updated` | Update tier, period_end; recompute feature access |
| `customer.subscription.deleted` | Set `subscriptions.status = 'canceled'`; downgrade to free tier |
| `invoice.payment_succeeded` | Log payment; extend subscription period |
| `invoice.payment_failed` | Trigger dunning sequence (see FR-21.6) |
| `customer.subscription.trial_will_end` | Send trial-ending email (3 days before) |

**Webhook signature verification:**
```python
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    await process_stripe_event(event)
    return {"status": "ok"}
```

#### FR-21.4: Free Trial

- 14-day free trial of full Individual features on first subscription
- Trial starts at payment method entry (Stripe `trial_period_days = 14`)
- Trial reminder emails: 7 days in ("You're halfway through your free trial"), 3 days before end ("Your trial ends in 3 days")
- Trial-to-paid conversion is automatic (Stripe charges automatically at trial end)
- Student retains all progress data if user cancels during/after trial

#### FR-21.5: Subscription Management

In-app subscription management at `/settings/subscription`:

- Current plan display: tier, billing period, next charge date, amount
- **Upgrade:** Individual → Family (prorated; Stripe handles proration)
- **Downgrade:** Family → Individual (effective at period end; no mid-period downgrade refunds)
- **Cancel:** Immediate cancellation or "cancel at period end" (user choice); features remain active until period end
- **Pause:** Available for Individual/Family plans (30-day pause, once per year); Stripe `subscription.pause_collection`
- **Reactivate:** After cancellation, user can reactivate at any time; all progress data retained
- **Change billing period:** Monthly → Annual (prorated credit applied) or Annual → Monthly (effective next cycle)

#### FR-21.6: Payment Failure & Dunning

When `invoice.payment_failed` webhook received:

**Dunning sequence:**
- Day 0 (payment fails): Email "Your payment didn't go through — please update your payment method"
- Day 3 (Stripe retries): Second email if still failed
- Day 7 (Stripe retries): Third email; in-app banner shown at login: "Action needed: Update payment method"
- Day 14: Subscription canceled; downgrade to free tier; email: "Your subscription has ended"
- Student data retained; no data deleted; reactivation available

Stripe handles retry logic (Smart Retries). PADI.AI sends emails at days 0, 3, 7, 14.

#### FR-21.7: Invoicing for Schools

For Classroom tier purchased by schools/districts:

- Invoice payment option: school can request an invoice instead of card payment
- Invoice flow:
  1. School admin selects "Pay by Invoice" at checkout
  2. Enters PO number (optional), billing contact name, billing address
  3. Invoice generated (PDF) and emailed to billing contact
  4. Payment terms: Net 30
  5. Stripe Invoice object used; status tracked
- Annual contract only (no monthly for Classroom)
- PO number stored on `subscriptions.invoice_po_number`
- Renewal invoice sent 45 days before expiry

---

### FR-22: School/District Onboarding

#### FR-22.1: School Admin Account Type

A new account type: `USER_ROLE = 'school_admin'` (distinct from `teacher`, `parent`, `student`).

**School admin capabilities:**
- Create and manage teacher accounts within their school
- Import student rosters (bulk CSV)
- Assign students to classrooms and teachers
- View school-wide analytics dashboard
- Manage school subscription (billing, seat count)
- Sign and submit FERPA Data Processing Agreement (DPA)
- Configure SSO for their school's Google Workspace or Clever instance

**School admin cannot:**
- View session transcripts (teacher-only; parent-approved)
- Modify individual student learning plans
- Access raw BKT parameters (aggregate views only)

#### FR-22.2: Bulk Student Roster Import

**CSV format (schools provide):**
```csv
first_name,last_name,grade,teacher_email,student_id_local
Alex,Martinez,4,jsmith@hillcrest.k12.or.us,12345
Jordan,Thompson,4,jsmith@hillcrest.k12.or.us,12346
Riley,Okafor,4,mbrown@hillcrest.k12.or.us,12347
```

**Import process:**
1. School admin uploads CSV via `/admin/roster/import`
2. System validates: required columns present, grade = 4 (only Grade 4 supported in v1), teacher emails match registered teachers or are new teacher invitations
3. Preview shown: "Importing 28 students. 2 teachers will be invited. Proceed?"
4. On confirm: student accounts created (no email required for students), teacher accounts invited via email
5. Import results: success count, error rows with reason, downloadable error report

**COPPA note:** Bulk import of student data by school admin is covered by FERPA (school official basis), not individual COPPA consent, provided the school has a signed DPA. The school asserts it has appropriate authority under FERPA to share this data with PADI.AI.

**Error handling:**
- Duplicate local student IDs: skip and report
- Invalid teacher emails: flag as error; student still imported but unassigned
- Missing required fields: entire row skipped, reported

#### FR-22.3: Classroom Management

- School admin creates classrooms: `{name: "Room 4A", teacher: jsmith@..., grade: 4}`
- Students assigned to classrooms (many-to-one: one classroom per student)
- Teacher sees only their assigned classroom in Teacher Dashboard
- School admin sees all classrooms
- Mid-year roster changes: add/remove students from classrooms; history retained
- Student moves to new classroom: inherits all progress data; accessible to new teacher if parent consents

#### FR-22.4: FERPA Data Processing Agreement (DPA) Flow

Before any student data is accessible in the school admin account:

1. School admin completes school profile: school name, NCES ID (optional), district, state (Oregon only in v1), billing contact
2. DPA displayed inline (not a click-through; must scroll to bottom)
3. DPA requires: school official name, title, signature (typed), date
4. On signing: `dpa_agreements` record created with signed content hash
5. DPA PDF generated and emailed to school admin for records
6. PADI.AI cosigned DPA sent back within 2 business days (initially manual process; automated in MMP+)
7. Student data access unlocked only after DPA is fully executed

**DPA content must include:**
- Data categories collected (specified)
- Data use limitations (educational purposes only, no advertising, no sale)
- Data deletion schedule (90 days after account termination)
- Security measures
- Subprocessors list (AWS, Auth0, Anthropic, OpenAI, Stripe)
- FERPA compliance acknowledgment
- Contact information for privacy officer

#### FR-22.5: Single Sign-On (SSO)

**Google Workspace for Education:**
- OAuth 2.0 flow via Google Identity
- School admin configures in `/admin/sso/google`: enters their Google Workspace domain (e.g., `hillcrest.k12.or.us`)
- Students and teachers at that domain can log in with "Sign in with Google (School)"
- Auto-provisioning: first login with school Google account creates a student/teacher record and links to roster (if matching by student local ID or email)
- Scope requested: `email`, `profile` only (no Google Drive, no Classroom API in v1)

**Clever Integration:**
- Clever is the dominant EdTech SSO platform for K-12 schools
- PADI.AI registers as a Clever application
- Implementation: Clever OAuth + Clever API for roster sync
- Clever provides: student name, grade, teacher, school — pre-populates roster without CSV import
- Clever sync is one-way: Clever → PADI.AI (not bidirectional)
- Sync runs nightly (2am PT) or on-demand via school admin button
- Clever setup for school: school IT admin installs PADI.AI app from Clever Library

**Technical notes:**
```python
# Clever OAuth callback handler
@router.get("/auth/clever/callback")
async def clever_callback(code: str, state: str):
    # Exchange code for token
    token_data = await clever_exchange_code(code)
    # Get user info from Clever
    clever_user = await clever_get_user(token_data['access_token'])

    # Map Clever role to PADI.AI role
    role_map = {"student": "student", "teacher": "teacher", "district_admin": "school_admin"}
    padi_role = role_map.get(clever_user['type'], 'student')

    # Find or create user
    user = await find_or_create_clever_user(clever_user, padi_role)
    return await create_session(user)
```

#### FR-22.6: School Admin Dashboard

**School-wide proficiency overview:**
- Distribution chart: % of students at each proficiency level (Below Par / Approaching / On Par / Above Par)
- Domain heatmap: average domain score across all students, per domain
- Trend: vs. beginning of year (diagnostic results)
- Active students this week: % of enrolled students who practiced ≥1 session

**Class comparisons:**
- Table: one row per classroom — teacher name, students active %, avg proficiency level, avg skills mastered
- NOT a teacher ranking (framed as "each class's learning journey" not performance rankings)

**Standards coverage:**
- Grid: 29 standards × N classrooms
- Each cell: % of students in that class with P(mastered) ≥ 0.80 for that standard
- Color: red (<50%), yellow (50-79%), green (≥80%)
- Identifies school-wide gaps for curriculum coordinators

#### FR-22.7: Oregon DOE Compliance Reporting

Oregon schools may need to report to the Oregon Department of Education. PADI.AI generates a pre-formatted report:

**Annual Standards Coverage Report (PDF + CSV):**
- School name, academic year
- Per student (anonymized with local student ID): proficiency level per domain, total practice time
- Aggregated: school-wide mastery rate per Oregon standard
- Format matches Oregon School Report Card data submission conventions (v1: approximate match; formal ODE alignment in MMP+)

---

### FR-23: Enhanced UX & Engagement

#### FR-23.1: Student Onboarding Tutorial

**Trigger:** First login after account creation.

**Format:** Interactive in-app walkthrough, < 3 minutes, 6 steps:
1. **Meet Pip** (10 sec): Pip animates, introduces themselves: "Hi! I'm Pip, your math guide. I'll help you practice and learn!"
2. **Your first question** (40 sec): Student answers a sample question (unscored) — demonstrates the question UI, fraction input, and submit button
3. **Getting hints** (30 sec): Pip explains hints: "If you get stuck, you can ask me for a hint! I'll never give you the answer — I'll help you think it through"
4. **Your progress** (20 sec): Shows simplified skill meter: "Every question you answer helps fill up your skill meter — when it's full, you've mastered that skill!"
5. **Parent reports** (10 sec): "Your parent can see your progress any time in their dashboard"
6. **Ready to start!** (10 sec): "Let's see what you already know. Your first practice is ready!"

- Skip option available (but not prominently displayed)
- Tutorial state stored: `onboarding_completed` flag in `students` table
- Tutorial shown once; can be re-triggered from student settings

#### FR-23.2: Pip — Named, Animated Mascot

Pip is PADI.AI's mascot character. Pip design principles:
- Gender-neutral (design uses non-binary visual cues: no stereotypically gendered features)
- Culturally neutral (not based on any human ethnicity; abstract friendly character — think similar to Duolingo Duo)
- Oregon-themed: Pip wears a small rain hat (nod to Oregon weather) and occasionally holds a math symbol
- Color palette: teal and gold (Oregon state colors)

**Pip animation states (CSS keyframe animations):**

| State | Trigger | Animation |
|---|---|---|
| `neutral` | Default, waiting | Subtle breathing motion |
| `happy` | Correct answer | Jump + sparkle burst |
| `thinking` | Question displayed | Chin-tap gesture |
| `encouraging` | Wrong answer / hint | Head tilt + warm wave |
| `celebrating` | Mastery achieved | Full spin + confetti burst |
| `sad_encouraging` | Scaffolded mode trigger | Droopy then recovery — "We'll get through this together!" |

**Technical:** Pip is implemented as Lottie animations (JSON format, lightweight, performant). Designer produces 6 Lottie JSON files. Animations respect `prefers-reduced-motion` (static PNG fallback). Total animation assets < 200KB.

#### FR-23.3: Achievement System (20+ Badges)

**Badge categories and examples:**

| Category | Badge Name | Unlock Condition |
|---|---|---|
| **First Steps** | First Session | Complete first practice session |
| **First Steps** | Hint Hero | Use all 3 hint levels in a session |
| **First Steps** | Fast Learner | Achieve 100% accuracy in a session |
| **Streaks** | 3-Day Streak | Practice 3 days in a row |
| **Streaks** | Week Warrior | Practice 7 days in a row |
| **Streaks** | Month Maven | Practice 20 of 30 days in a month |
| **Mastery** | Fraction Flyer | Master all NF domain skills |
| **Mastery** | Operations Ace | Master all OA domain skills |
| **Mastery** | Measurement Master | Master all MD domain skills |
| **Mastery** | Number Ninja | Master all NBT domain skills |
| **Mastery** | Geometry Genius | Master all G domain skills |
| **Mastery** | Oregon Scholar | Master all 29 skills |
| **Assessment** | Assessment Ready | Complete diagnostic assessment |
| **Assessment** | Challenge Accepted | Complete first EOG assessment |
| **Assessment** | On Par | Reach "On Par" proficiency level |
| **Assessment** | Above Par | Reach "Above Par" proficiency level |
| **Practice** | Century Club | Answer 100 total questions correctly |
| **Practice** | Hint Refuser | Answer 5 consecutive questions without any hints |
| **Practice** | Challenge Seeker | Complete 3 sessions in Challenge Mode |
| **Practice** | Session Superstar | Complete 20 total practice sessions |
| **Special** | Math Mission Complete | Complete first Weekly Math Mission |
| **Special** | Study Partner | Complete a Study Together session with parent |

**Badge storage:** `student_badges` table (badge_id, student_id, unlocked_at, notified)  
**Badge display:** Badge shelf in student profile; 5 most recent shown on session summary  
**Parent notification:** Parent email: "Alex earned a new badge: Week Warrior! 🏆"

#### FR-23.4: Weekly Math Mission

A special weekly challenge set, released every Monday, available for 7 days.

**Format:**
- 15 questions spanning multiple skills and domains (harder than typical practice)
- Theme: Oregon context (e.g., "Mission: Crater Lake Expedition" — all word problems use Crater Lake, elevation, and area data)
- No hints (missions are challenge-oriented; Pip encourages but doesn't hint)
- Completion reward: "Math Mission Complete!" badge + 2x Pip celebration animation

**Content:** Pre-authored by curriculum team (not AI-generated) — 52 missions per year per grade. Stored in `math_missions` and `mission_questions` tables.

**Display:** Homepage widget: "This Week's Math Mission — Oregon Tide Pools Adventure" with countdown timer. Optional — student doesn't have to complete missions to advance their learning plan.

#### FR-23.5: Parent-Child "Study Together" Mode

A mode where a parent and child can work through problems together on the same device.

**Flow:**
1. Parent opens "Study Together" from parent dashboard
2. Parent selects a skill from child's in-progress skills
3. A simplified practice session starts — same question UI, same adaptive selection
4. No hints from Pip (parent is the hint-giver)
5. Parent and child discuss; parent helps child input answer
6. Session tracked separately: labeled `session_mode = 'study_together'` in `practice_sessions`
7. BKT updates normally (knowledge is being demonstrated)
8. After session: parent sees session summary with "Great time together!" summary

**Motivation:** Research shows parent involvement in math practice strongly correlates with student achievement. This feature makes involvement structured and easy.

#### FR-23.6: Handwriting Recognition (Tablet Numeric Input)

For numeric answer questions on touch devices (iPad, Android tablet):

- Canvas draw area replaces numeric keypad
- Student writes their numeric answer in handwriting
- Client-side recognition via **mathpix.js** or **tesseract.js** (numeric-mode OCR)
- Recognized number displayed in a "Did you write X?" confirmation field before submission
- Fallback: if recognition confidence < 0.8, display "I'm not sure what you wrote — can you use the keypad?" with numeric keypad shown
- Toggle: student can switch between handwriting and keypad mode at any time

#### FR-23.7: Dark Mode / Accessibility Theme

**Dark Mode:**
- Triggered by: system `prefers-color-scheme: dark` (automatic) OR manual toggle in student/parent settings
- Color palette: navy/charcoal backgrounds, high-contrast cream text, same accent colors at reduced brightness
- KaTeX equations render correctly in dark mode (custom CSS)
- Math Mission themes and report PDFs remain in light mode (print-friendly)

**Accessibility Theme:**
- High-contrast mode: black/white with no gradient backgrounds (for low-vision users)
- Large text mode: base font size +4px (applies globally)
- Both available in student settings: "Accessibility Options"
- Tested against WCAG 2.1 AA for both modes

**`prefers-reduced-motion`:**
- If set: Pip displays static images instead of Lottie animations
- Correct/wrong feedback uses text + icon only (no bounce animations)
- Progress bar fills instantly (no animation)

#### FR-23.8: Spanish Language Support

Spanish is Oregon's second language. Approximately 20% of Oregon 4th graders are native Spanish speakers or Spanish-dominant bilingual learners. Spanish support is a material accessibility and equity feature, not a nice-to-have.

**Scope of Spanish in Stage 5 (v1):**
- All UI strings (menus, buttons, labels, notifications): translated to Spanish
- Tutor Agent (Pip) responses: delivered in Spanish when `language_preference = 'es'`
- Practice questions: Spanish-translated versions of all cached questions (machine-translated + human review)
- Parent dashboard: fully translated
- Emails: Spanish versions of all email templates
- Progress reports PDF: Spanish versions of student and parent reports

**Out of scope for v1 Spanish:**
- Live-generated questions in Spanish (AI generation in Spanish deferred to MMP+)
- Bilingual mode (English question / Spanish explanation) — deferred
- Diagnostic in Spanish (critical gap; fast-follow after MMP)

**Language selection:**
- During parent account setup: "What language do you prefer?" (English / Spanish) — applies to all communications
- Student language: separate setting, defaults to parent language
- Language toggle available in header: "English / Español"

**Translation management:**
- All UI strings extracted to `i18n/en.json` and `i18n/es.json`
- Translation service: professional translator for UI strings + initial email templates; AI translation with review for question bank
- Process: translator reviews and corrects AI-translated questions before publishing

**Tutor Agent Spanish system prompt addition:**
```
LANGUAGE: The student has selected Spanish as their preferred language.
All responses must be in Spanish. Use simple, friendly Mexican/Oregon-Spanish
vocabulary appropriate for a 9-10 year old. Avoid Latin American slang
that would be unfamiliar. Target 4th-grade reading level in Spanish.
```

---

### FR-24: Analytics & A/B Testing

#### FR-24.1: Analytics Platform Integration

**Primary tool:** PostHog (self-hosted on GCP or cloud) — preferred for privacy compliance (data stays on our infrastructure) and COPPA (no third-party data sharing).

**Alternative:** Mixpanel (cloud) — acceptable if PostHog self-hosting is too resource-intensive for Stage 5.

**Implementation:**
```javascript
// Client-side (Next.js)
import posthog from 'posthog-js'

posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
    api_host: '/ingest',        // proxied through our domain (no direct PostHog calls from browser)
    capture_pageview: false,    // manual pageview tracking
    persistence: 'memory',     // no cookies for students (COPPA)
    disable_surveys: true,
    autocapture: false          // only manual events for COPPA compliance
})
```

**COPPA-compliant analytics approach:**
- No analytics cookies for student accounts (use session storage or in-memory only)
- No cross-device tracking for students
- Student events are pseudonymous: `student_id` UUID only, no PII in event properties
- Parent account events: standard analytics (parents are adults, standard consent applies)
- Analytics data retained for 13 months (rolling window)

#### FR-24.2: Core Event Taxonomy

All events follow naming convention: `{actor}_{object}_{action}` (e.g., `student_session_started`).

**Student Events:**

```typescript
// Session lifecycle
posthog.capture('student_session_started', {
    session_id: string,
    skill_id: string,
    skill_name: string,
    session_mode: 'adaptive' | 'scaffolded' | 'challenge' | 'review',
    bkt_at_start: number,
    session_number: number  // lifetime session count
})

posthog.capture('student_question_answered', {
    session_id: string,
    question_id: string,
    skill_id: string,
    domain: string,
    question_type: string,
    is_correct: boolean,
    attempt_number: number,
    response_time_ms: number,
    difficulty_b: number,
    theta_at_time: number,
    hints_used_before: number
})

posthog.capture('student_hint_requested', {
    session_id: string,
    question_id: string,
    hint_level: 1 | 2 | 3,
    trigger: 'button_press' | 'idk_button' | 'auto_trigger',
    error_type_detected: string | null
})

posthog.capture('student_session_completed', {
    session_id: string,
    duration_minutes: number,
    questions_answered: number,
    accuracy_pct: number,
    skills_mastered: string[],
    bkt_gain: number,  // avg P(mastered) delta
    exit_type: 'natural_end' | 'voluntary_exit' | 'fatigue_detection'
})

posthog.capture('student_skill_mastered', {
    skill_id: string,
    skill_name: string,
    domain: string,
    sessions_to_mastery: number,
    total_attempts: number
})

posthog.capture('student_plan_module_completed', {
    module_id: string,
    module_name: string,
    weeks_to_complete: number
})

posthog.capture('student_assessment_started', {
    assessment_type: 'diagnostic' | 'eog',
    assessment_id: string
})

posthog.capture('student_assessment_completed', {
    assessment_type: 'diagnostic' | 'eog',
    assessment_id: string,
    proficiency_level: string,
    theta: number,
    duration_minutes: number
})
```

**Parent Events:**

```typescript
posthog.capture('parent_signup_completed', {
    signup_source: 'organic' | 'referral' | 'paid_ad' | 'teacher_referral'
})

posthog.capture('parent_subscription_started', {
    plan: 'individual' | 'family' | 'classroom',
    billing_period: 'monthly' | 'annual',
    trial: boolean,
    mrr_usd: number
})

posthog.capture('parent_report_downloaded', {
    report_type: 'student' | 'parent',
    assessment_id: string
})

posthog.capture('parent_share_with_teacher', {
    report_id: string,
    sent_to_email: boolean  // true if email entered; false if just link copied
})
```

#### FR-24.3: A/B Testing Framework

All A/B tests managed through PostHog Feature Flags with multivariate support.

**Test assignment rules:**
- Student experiments: assigned at student account creation; stable assignment (same variant across sessions)
- Variant assignment stored in `student_abtest_assignments` table (not just PostHog) for backend-driven decisions

**Planned A/B tests for Stage 5 launch:**

| Test ID | Hypothesis | Variants | Primary Metric | Sample Size |
|---|---|---|---|---|
| `ABT-001` | Simpler celebration animations → higher completion rate | A: current animations; B: minimal text only | session_completion_rate | n=2,000 |
| `ABT-002` | Hint button color → more hint usage → better outcomes | A: yellow; B: blue; C: pulsing red | hints_per_session / post-hint accuracy | n=3,000 |
| `ABT-003` | Session length default | A: 10 questions; B: 8 questions with review; C: adaptive length | D7 retention | n=5,000 |
| `ABT-004` | Parent onboarding flow | A: video walkthrough; B: text checklist; C: interactive tour | parent_login_D7 | n=1,000 |
| `ABT-005` | Free trial length | A: 7 days; B: 14 days; C: 30 days | trial_conversion_rate | n=2,000 |

**Test infrastructure:**
```python
# Server-side variant assignment
async def get_variant(student_id: str, test_id: str) -> str:
    # Check DB first (stable assignment)
    assignment = await get_abtest_assignment(student_id, test_id)
    if assignment:
        return assignment.variant

    # New assignment: hash-based (deterministic, no storage needed for simple cases)
    import hashlib
    hash_val = int(hashlib.sha256(f"{student_id}-{test_id}".encode()).hexdigest(), 16)
    variants = await get_test_variants(test_id)
    variant = variants[hash_val % len(variants)]

    await store_assignment(student_id, test_id, variant)
    return variant
```

#### FR-24.4: Funnel Analysis

Critical funnel: **Signup → Diagnostic → First Session → Day 7 Active → Subscription**

Track in PostHog as a defined funnel:
1. `parent_signup_completed`
2. `student_assessment_completed` (diagnostic)
3. `student_session_started` (first practice session)
4. `student_session_completed` (within 7 days of signup)
5. `parent_subscription_started`

**Target conversion rates at MMP launch (initial hypotheses to validate):**
- Signup → Diagnostic: ≥ 80% (high intent; user came to us)
- Diagnostic → First Session: ≥ 70%
- First Session → D7 Active: ≥ 45%
- D7 Active → Subscription: ≥ 25%
- Overall Signup → Subscription: ≥ 9%

#### FR-24.5: Question Quality Analytics

Per-question analytics in PostgreSQL (not PostHog — high cardinality):

```sql
-- View: question performance analytics
CREATE MATERIALIZED VIEW question_analytics AS
SELECT
    q.id,
    q.skill_id,
    q.difficulty_b,
    q.question_type,
    COUNT(DISTINCT sr.session_id) AS times_served,
    COUNT(CASE WHEN sr.attempt_number = 1 AND sr.is_correct THEN 1 END)::float
        / NULLIF(COUNT(CASE WHEN sr.attempt_number = 1 THEN 1 END), 0) AS p1_accuracy,
    AVG(sr.response_time_ms) FILTER (WHERE sr.attempt_number = 1) AS avg_response_time_ms,
    COUNT(DISTINCT hi.id)::float / NULLIF(COUNT(DISTINCT sr.session_id), 0) AS hint_rate,
    -- Distractor analysis (for MC)
    COUNT(CASE WHEN sr.student_answer = q.options->>'A' THEN 1 END) AS chose_A,
    COUNT(CASE WHEN sr.student_answer = q.options->>'B' THEN 1 END) AS chose_B,
    COUNT(CASE WHEN sr.student_answer = q.options->>'C' THEN 1 END) AS chose_C,
    COUNT(CASE WHEN sr.student_answer = q.options->>'D' THEN 1 END) AS chose_D
FROM practice_questions q
LEFT JOIN session_questions sq ON sq.question_id = q.id
LEFT JOIN session_responses sr ON sr.session_question_id = sq.id AND sr.attempt_number = 1
LEFT JOIN hint_interactions hi ON hi.session_question_id = sq.id
GROUP BY q.id, q.skill_id, q.difficulty_b, q.question_type;

-- Refresh nightly
CREATE UNIQUE INDEX ON question_analytics(id);
```

Flagging criteria for question review:
- `p1_accuracy < 0.20` (possibly ambiguous or too hard) → flagged as `REVIEW_TOO_HARD`
- `p1_accuracy > 0.95` (too easy, poor discriminability) → flagged as `REVIEW_TOO_EASY`
- `hint_rate > 0.80` (nearly everyone needs a hint) → flagged as `REVIEW_NEEDS_BETTER_HINTS`
- Distractor analysis: if one distractor is chosen < 5% of the time → flag for replacement

---

### FR-25: COPPA Safe Harbor & Privacy Certifications

#### FR-25.1: COPPA Safe Harbor Program

PADI.AI will pursue one of the following COPPA Safe Harbor programs (chosen by legal counsel recommendation):

| Program | Cost | Timeline | Notes |
|---|---|---|---|
| **kidSAFE** | ~$3,000/year | 3-6 months | Most visible for consumer apps; recognized by FTC |
| **PRIVO** | ~$5,000/year | 4-6 months | Strong enterprise/school focus; includes COPPA + FERPA |
| **TrustArc** | ~$8,000/year | 6-12 months | Enterprise-grade; required for some district procurement |

**Recommended path:** Begin with kidSAFE application at Stage 5 kick-off (Month 15) to achieve certification by target MMP launch (Month 20). Pursue PRIVO certification in MMP+ for school/district sales credibility.

**Certification requirements (common across programs):**
- Privacy policy written at accessible reading level (below)
- Data collection inventory documented
- Parental consent mechanism verified by program
- Data security review / penetration test
- Annual audit process agreed to

#### FR-25.2: Student Privacy Pledge

Sign the Student Privacy Pledge (https://studentprivacypledge.org/):

**Key commitments this requires PADI.AI to make:**
- We will not sell student personal information
- We will not behaviorally target advertising to students
- We will not use student data to build a profile to be shared with third parties for marketing purposes
- We will collect only the minimum personal information necessary
- We will not retain student personal information beyond the time needed for educational purposes
- We will support parental access to, correction of, and deletion of student personal information

**Operational changes required:**
- No third-party advertising on student-facing pages (any tier)
- PostHog must be self-hosted or configured to exclude student data from any third-party processing
- Vendor review: every third-party service processing student data must sign a DPA with us

#### FR-25.3: Privacy Policy at 8th Grade Reading Level

The existing privacy policy (legal English) is supplemented by a "Privacy Summary" written at 8th grade reading level (Flesch-Kincaid Grade ≤ 9.0):

**Privacy Summary outline:**
1. **What information do we collect?** (Simple bullet list of data types with plain-English descriptions)
2. **Why do we collect it?** (Linked to feature: "We store your math answers so we know which skills to practice")
3. **Who can see your information?** (Parents always; teachers only if parents allow; we never sell it)
4. **How do we keep it safe?** (HTTPS, password protection, encryption — one sentence each)
5. **How to delete your account** (Step-by-step instructions)
6. **How to ask questions** (Privacy officer contact)

Full legal privacy policy remains available (link at bottom of privacy summary).

#### FR-25.4: Data Minimization Audit

A formal audit document (maintained in Notion or Confluence) cataloging every data point collected, its justification, and its retention period:

| Data Point | Where Stored | Why Collected | Retention |
|---|---|---|---|
| Student first name | `students.display_name` | Display in app | Account active + 90 days |
| Parent email | `users.email` | Authentication, notifications | Account active + 90 days |
| IP address (session) | `practice_sessions.ip_address` | Fraud prevention | 30 days |
| IP address (EOG) | `eog_assessments.ip_address` | Assessment integrity | 1 year |
| Session Q&A history | `session_responses` | BKT updates, parent review | Account active + 90 days |
| BKT states | `skill_mastery_states` | Adaptive learning | Account active + 90 days |
| Tutor conversations | `session_responses.tutor_response` | Parent review, quality improvement | Account active + 90 days |
| Device/browser info | `users.last_known_user_agent` | Technical support | 30 days rolling |
| Payment info | Stripe (not our servers) | Billing | Stripe's retention policy |
| Analytics events | PostHog (self-hosted) | Product improvement | 13 months rolling |

**Minimization decisions documented:**
- We do NOT collect: student last name (not required for app function)
- We do NOT collect: student photos
- We do NOT collect: location data (IP-to-city lookup disabled)
- We do NOT collect: device contacts or calendar
- We do NOT use: third-party advertising trackers

#### FR-25.5: FERPA Compliance Documentation

For school sales, PADI.AI maintains a FERPA compliance document available to school procurement offices:

**FERPA Compliance Summary:**
- **School official basis:** PADI.AI operates under the "school official" FERPA exception when contracted with a school, provided a signed DPA is in place
- **Legitimate educational interest:** Student data is used solely for the educational function the school has contracted PADI.AI to provide
- **No redisclosure:** PADI.AI does not disclose student educational records to any third party other than those listed as subprocessors in the DPA
- **Parental access:** When accessed via direct parent account (Individual/Family plans), parents exercise their own FERPA rights directly; no school intermediary required
- **Annual notification:** Schools who use the Classroom plan are notified annually of their FERPA obligations as the data controller

#### FR-25.6: Annual Privacy Review Process

A formal internal review conducted each October (before the academic year data collection begins in earnest):

**Review checklist:**
1. Subprocessor list updated and re-reviewed
2. Data minimization audit updated
3. Privacy policy reviewed for accuracy
4. Data deletion requests from prior year: all processed within SLA?
5. Access logs: any unauthorized access detected?
6. New features released since last review: each assessed for privacy impact
7. COPPA Safe Harbor program annual audit completed
8. Student Privacy Pledge compliance re-certified

**Output:** Privacy Review Report (internal document), privacy policy version bump if changes made.

---

### FR-26: Content Expansion

#### FR-26.1: 10,000+ Question Bank

Grow the question bank from ~500 (MVP) to 10,000+ (MMP), ensuring:

**Expansion plan:**
- 50+ questions per skill × 29 skills = ~1,450 questions minimum (for full difficulty coverage)
- 150+ questions per skill at target density = ~4,350 questions (preferred)
- Remaining 5,650+: additional variety questions, extended contexts, multi-step problems

**Quality pipeline for bulk question creation:**
1. Curriculum writer creates question specification (skill, type, difficulty, context)
2. o3-mini generates 5 question variants per spec
3. Math teacher reviews and selects/edits best variant
4. System verifies (automated answer verification)
5. IRT parameters estimated from spec; calibrated after first 50 student responses

**Question diversity targets (per skill):**
- Minimum 5 different context themes represented
- Minimum 3 different question types (if applicable to the skill)
- Minimum 3 difficulty levels: easy (b = -1.0), medium (b = 0.0), hard (b = 1.0)
- At least 20% word problems with Oregon-specific contexts

#### FR-26.2: Video Micro-Lessons

2-3 minute concept videos, one per module (29 modules), introduced at the start of each module.

**Format:**
- Screen-capture / animated explainer style (not talking head)
- Voice: professional narrator (warm, encouraging)
- Content: conceptual explanation of the module's central skill, with 2-3 worked examples
- Oregon context: examples use Oregon settings
- Captions: required (WCAG, COPPA, ELL accessibility)
- Spanish subtitles: provided for all videos

**Hosting:** Self-hosted via AWS S3 + CloudFront (preferred, no third-party player tracking) OR embedded YouTube unlisted (faster to launch, less infrastructure). Stage 5 v1: YouTube unlisted with privacy-enhanced embed mode. MMP+: migrate to self-hosted.

**Student access:** Video shown once per module at module start. Can be re-watched from module overview. Skippable after 15 seconds.

**Analytics:** Track `student_video_watched` event (start, complete, skip_at_seconds). Used to assess video quality.

#### FR-26.3: Printable Practice Worksheet Generator

Parents and teachers can generate a printable PDF practice worksheet:

**Generator UI (parent dashboard → "Print Practice"):**
- Select skill(s): pick 1-3 skills from the student's active learning plan
- Select difficulty: easy / medium / hard / mixed
- Select question count: 10, 15, or 20 questions
- Click "Generate Worksheet" → PDF in browser within 10 seconds

**Worksheet format:**
- Student name line, date line, skill name(s) header
- Questions numbered, with answer lines
- Answer key on page 2 (parent-only; not shown if parent prints student copy)
- PADI.AI branding + website URL
- "Keep practicing on PADI.AI!" footer

**Technical:** Questions selected from `practice_questions` bank (not live-generated), rendered to HTML via Jinja2, converted to PDF via Puppeteer.

**Use case:** Teachers who do Friday paper practice, parents who want screen-free reinforcement, tutors working with the student.

#### FR-26.4: "Explain to Me" — Claude-Powered Concept Explanation

Available in any practice session: student (or parent) can ask for an explanation of any math concept in the current module, beyond the current question's hints.

**Access:** Sidebar button "Explain a concept" → opens a scrollable concept library for the current module → student selects concept → Claude generates a personalized explanation.

**Student-facing UI:**
- "What would you like me to explain?"
- Scrollable list: e.g., "What is a denominator?", "Why do fractions need the same bottom number to add?", "What does 'equivalent' mean?", "How is multiplication related to addition?"
- Or: free-text: "I don't understand why 1/2 = 2/4"

**Backend:**
- Concept explanation request → Claude Sonnet 4.6 with structured prompt
- Response: maximum 5 sentences, child-appropriate language (FK Grade 4-5), with one worked Oregon-themed example
- Responses are cached by concept_id (not personalized beyond grade level) to reduce LLM costs
- Cached explanations served for repeated requests (same concept, same grade)

**System prompt:**
```
You are Pip, a friendly math tutor explaining a concept to an Oregon 4th grader.

CONCEPT TO EXPLAIN: {concept}
MODULE CONTEXT: {module_name} — {module_description}

CONSTRAINTS:
- Maximum 5 sentences
- Grade 4-5 reading level (FK ≤ 5.5)
- Include one concrete Oregon-themed example (Oregon nature, food, sports, or landmarks)
- Do NOT solve any specific homework problem
- End with a sentence that connects back to why this concept is useful

Respond with only the explanation text.
```

---

## 5.3 MMP Feature Checklist

The MMP designation requires ALL MVP features (Stage 1–4, listed in FR-4.3) PLUS all Stage 5 features listed below.

### Stage 5: MMP Features
- [ ] **S5-01:** Stripe integration live; all three subscription tiers purchasable
- [ ] **S5-02:** Free tier enforced (3 sessions/week cap; no EOG on free tier)
- [ ] **S5-03:** 14-day free trial works correctly (Stripe trial + auto-charge)
- [ ] **S5-04:** Subscription management UI: upgrade, downgrade, cancel, pause all functional
- [ ] **S5-05:** Payment failure dunning: all 4 emails send on correct schedule
- [ ] **S5-06:** School invoice/PO flow: school admin can checkout with invoice option
- [ ] **S5-07:** School admin account type: registration, school profile, DPA flow all working
- [ ] **S5-08:** Bulk CSV roster import: accepts valid CSV, reports errors, creates student accounts
- [ ] **S5-09:** Classroom management: students assignable to classrooms and teachers
- [ ] **S5-10:** DPA flow: signed DPA record created and PDF emailed to school admin
- [ ] **S5-11:** Google SSO: school domain login works for students and teachers
- [ ] **S5-12:** Clever integration: Clever OAuth login works; nightly roster sync works
- [ ] **S5-13:** School admin dashboard: school-wide proficiency distribution correct
- [ ] **S5-14:** School admin dashboard: standards coverage grid correct
- [ ] **S5-15:** Oregon DOE report: CSV + PDF generated correctly for school admin
- [ ] **S5-16:** Student onboarding tutorial: shown on first login, skippable, completable < 3 min
- [ ] **S5-17:** Pip mascot: all 6 animation states working; reduced-motion fallback works
- [ ] **S5-18:** Achievement system: all 22 badges have correct unlock logic; notifications fire
- [ ] **S5-19:** Weekly Math Mission: auto-published every Monday; completable; badge awarded
- [ ] **S5-20:** Study Together mode: parent can initiate, session tracked correctly
- [ ] **S5-21:** Handwriting recognition: works for numeric input on iPad/Android tablet
- [ ] **S5-22:** Dark mode: all app pages render correctly in dark mode
- [ ] **S5-23:** Accessibility theme: high-contrast and large-text modes working
- [ ] **S5-24:** Spanish UI: all UI strings translated; language toggle works
- [ ] **S5-25:** Spanish Pip responses: Tutor agent responds in Spanish when `language_preference = 'es'`
- [ ] **S5-26:** Spanish questions: all 500+ MVP questions have reviewed Spanish translations
- [ ] **S5-27:** PostHog integration: all events from FR-24.2 firing correctly
- [ ] **S5-28:** A/B testing infrastructure: Feature Flags working; 2+ tests running at launch
- [ ] **S5-29:** Funnel dashboard: signup → subscription funnel visible in PostHog
- [ ] **S5-30:** Question analytics materialized view: refreshing nightly; flagging working
- [ ] **S5-31:** COPPA Safe Harbor application submitted (kidSAFE or equivalent)
- [ ] **S5-32:** Student Privacy Pledge: signed and published
- [ ] **S5-33:** Privacy policy: accessible reading-level summary published
- [ ] **S5-34:** Data minimization audit document: complete and reviewed by legal
- [ ] **S5-35:** FERPA compliance documentation: published for school procurement
- [ ] **S5-36:** Question bank: ≥ 3,000 validated questions (not 10,000 — that's a 6-month post-MMP ramp)
- [ ] **S5-37:** Video micro-lessons: all 29 module videos recorded, captioned, and live
- [ ] **S5-38:** Printable worksheet generator: generates correct PDF within 10 seconds
- [ ] **S5-39:** "Explain to me": concept explanation feature works for all 29 modules
- [ ] **S5-40:** Load testing: 1,000 concurrent users (path to 10,000 validated in architecture review)

**MMP Launch Gate: ALL 39 MVP items (FR-4.3) + ALL 40 MMP items above = MMP ✅**

---

## 5.4 Non-Functional Requirements

| Requirement | Target | Rationale | Priority |
|---|---|---|---|
| **Concurrent users** | 10,000 (architected) / 1,000 (tested at MMP) | School deployments require scale | P0 |
| **Uptime SLA** | 99.9% measured (school contract eligible) | ~8.7 hours/year downtime budget | P0 |
| **Uptime during school hours** | 99.95% (Mon–Fri 7am–6pm PT) | Schools cannot tolerate downtime during instruction | P0 |
| **Payment security** | PCI DSS SAQ A compliance (Stripe handles card data) | Legal requirement | P0 |
| **SSO availability** | Clever and Google OAuth: graceful degradation (email/password fallback if SSO down) | School ops reliability | P1 |
| **Question bank query** | < 100ms for cached question selection query | User experience | P0 |
| **PDF generation (report)** | < 10 seconds | Unchanged from Stage 4 | P0 |
| **PDF generation (worksheet)** | < 10 seconds | Parent/teacher convenience | P1 |
| **Video streaming** | First byte within 2 seconds (CloudFront/CDN cached) | Student engagement | P1 |
| **Analytics event latency** | PostHog events delivered within 30 seconds | A/B test validity | P2 |
| **Spanish translation completeness** | 100% of UI strings; ≥ 95% of cached questions | Accessibility requirement | P0 |
| **Accessibility** | WCAG 2.1 AA (all modes: default, dark, high-contrast) | Legal + equity | P0 |
| **Mobile performance** | Lighthouse Performance ≥ 80 on mobile (4G simulated) | 40%+ of students on mobile | P0 |
| **Data encryption at rest** | AES-256 on all PostgreSQL and S3 data | Security | P0 |
| **Data encryption in transit** | TLS 1.2+ minimum on all endpoints | Security | P0 |
| **Penetration testing** | Annual pentest by qualified third party | COPPA Safe Harbor requirement | P1 |
| **Multi-region** | US-West-2 primary; US-East-1 failover (RDS read replica) | Oregon schools: latency and resilience | P1 |

### Scaling Architecture Notes (Stage 5)

To achieve 10,000 concurrent users (architected):

**Database:**
- PostgreSQL: AWS RDS Multi-AZ (primary + standby failover)
- Read replicas: 2 RDS read replicas for dashboard/report queries
- pgvector: used for semantic search in concept library (FR-26.4)
- Redis: ElastiCache Redis Cluster (3 shards × 2 replicas) for session WM

**Application layer:**
- FastAPI: containerized on AWS ECS (Fargate) — auto-scaling group, min 3, max 50 tasks
- WebSocket connections: AWS API Gateway WebSockets OR ALB sticky sessions
- LangGraph sessions: stateless agents (state stored in Redis); horizontally scalable

**CDN:**
- CloudFront for: Next.js static assets, video micro-lessons, PDF reports (pre-signed URLs)
- Edge caching for: question bank queries (LRU cache), concept explanations (per-concept cache)

**LLM rate limits:**
- Anthropic Claude Sonnet 4.6: 4,000 requests/minute (enterprise tier required at 10k users)
- OpenAI o3-mini: 500 RPM (sufficient; o3-mini usage is burst, not sustained)
- LLM circuit breaker: if provider latency > 10s, fall back to cached responses

---

## 5.5 Data Models

### New Tables for Stage 5

#### subscriptions
```sql
CREATE TABLE subscriptions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_customer_id  VARCHAR(50) UNIQUE NOT NULL,
    stripe_subscription_id VARCHAR(50) UNIQUE,
    plan_tier           VARCHAR(20) NOT NULL,   -- 'individual','family','classroom'
    billing_period      VARCHAR(10) NOT NULL,   -- 'monthly','annual'
    status              VARCHAR(20) NOT NULL,   -- 'trialing','active','past_due','canceled','paused'
    trial_start         TIMESTAMPTZ,
    trial_end           TIMESTAMPTZ,
    current_period_start TIMESTAMPTZ,
    current_period_end  TIMESTAMPTZ,
    canceled_at         TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    mrr_usd             NUMERIC(10,2),          -- monthly recurring revenue
    invoice_po_number   VARCHAR(50),            -- for school/district billing
    seats               INTEGER DEFAULT 1,      -- number of student seats
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT plan_tier_valid CHECK (plan_tier IN ('individual','family','classroom')),
    CONSTRAINT billing_period_valid CHECK (billing_period IN ('monthly','annual')),
    CONSTRAINT status_valid CHECK (status IN (
        'trialing','active','past_due','canceled','paused','incomplete'
    ))
);
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);
```

#### schools
```sql
CREATE TABLE schools (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    nces_id         VARCHAR(20),                -- NCES school ID (optional)
    district_name   VARCHAR(200),
    city            VARCHAR(100),
    state           VARCHAR(2) NOT NULL DEFAULT 'OR',
    zip             VARCHAR(10),
    admin_user_id   UUID REFERENCES users(id),  -- primary school admin
    subscription_id UUID REFERENCES subscriptions(id),
    sso_domain      VARCHAR(200),               -- Google Workspace domain
    clever_id       VARCHAR(50),                -- Clever school ID
    dpa_signed_at   TIMESTAMPTZ,
    dpa_signed_by   VARCHAR(200),               -- name of signer
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_schools_admin ON schools(admin_user_id);
```

#### classrooms
```sql
CREATE TABLE classrooms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id      UUID REFERENCES users(id),
    name            VARCHAR(100) NOT NULL,
    grade           INTEGER NOT NULL DEFAULT 4,
    academic_year   VARCHAR(10) NOT NULL DEFAULT '2025-2026',
    student_count   INTEGER DEFAULT 0,          -- denormalized count
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_classrooms_school ON classrooms(school_id);
CREATE INDEX idx_classrooms_teacher ON classrooms(teacher_id);
```

#### classroom_students
```sql
CREATE TABLE classroom_students (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    classroom_id    UUID NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    enrolled_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    removed_at      TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT unique_classroom_student UNIQUE (classroom_id, student_id)
);
CREATE INDEX idx_cs_classroom ON classroom_students(classroom_id) WHERE is_active;
CREATE INDEX idx_cs_student ON classroom_students(student_id) WHERE is_active;
```

#### dpa_agreements
```sql
CREATE TABLE dpa_agreements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       UUID NOT NULL REFERENCES schools(id),
    signer_name     VARCHAR(200) NOT NULL,
    signer_title    VARCHAR(200),
    signed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    content_hash    VARCHAR(64) NOT NULL,       -- SHA-256 of DPA text at time of signing
    dpa_version     VARCHAR(20) NOT NULL,       -- e.g., "1.2"
    pdf_s3_key      TEXT,                       -- S3 path to executed DPA PDF
    padi_cosigned_at TIMESTAMPTZ,
    is_current      BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_dpa_school ON dpa_agreements(school_id);
```

#### student_badges
```sql
CREATE TABLE student_badges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    badge_id        VARCHAR(50) NOT NULL,       -- e.g., 'week_warrior', 'fraction_flyer'
    unlocked_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notified        BOOLEAN NOT NULL DEFAULT FALSE,   -- parent notified?
    session_id      UUID REFERENCES practice_sessions(id),  -- session where unlocked
    CONSTRAINT unique_student_badge UNIQUE (student_id, badge_id)
);
CREATE INDEX idx_badges_student ON student_badges(student_id);
```

#### math_missions
```sql
CREATE TABLE math_missions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(100) NOT NULL,
    theme           VARCHAR(200),
    description     TEXT,
    week_of         DATE NOT NULL,              -- Monday of the target week
    grade           INTEGER NOT NULL DEFAULT 4,
    question_count  INTEGER NOT NULL DEFAULT 15,
    is_published    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_missions_week ON math_missions(week_of DESC);
```

#### mission_questions
```sql
CREATE TABLE mission_questions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id      UUID NOT NULL REFERENCES math_missions(id) ON DELETE CASCADE,
    question_id     UUID NOT NULL REFERENCES practice_questions(id),
    sequence_num    INTEGER NOT NULL,
    CONSTRAINT unique_mission_question UNIQUE (mission_id, question_id)
);
```

#### student_mission_attempts
```sql
CREATE TABLE student_mission_attempts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    mission_id      UUID NOT NULL REFERENCES math_missions(id),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    questions_correct INTEGER DEFAULT 0,
    questions_total INTEGER NOT NULL,
    accuracy_pct    FLOAT,
    badge_awarded   BOOLEAN DEFAULT FALSE,
    CONSTRAINT unique_student_mission UNIQUE (student_id, mission_id)
);
```

#### student_abtest_assignments
```sql
CREATE TABLE student_abtest_assignments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    test_id         VARCHAR(20) NOT NULL,       -- e.g., 'ABT-001'
    variant         VARCHAR(20) NOT NULL,       -- e.g., 'A', 'B', 'control'
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_student_test UNIQUE (student_id, test_id)
);
CREATE INDEX idx_abtest_student ON student_abtest_assignments(student_id);
CREATE INDEX idx_abtest_test ON student_abtest_assignments(test_id);
```

#### sso_connections
```sql
CREATE TABLE sso_connections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id       UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    provider        VARCHAR(20) NOT NULL,       -- 'google', 'clever'
    provider_config JSONB NOT NULL,             -- provider-specific config (encrypted)
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_sync_at    TIMESTAMPTZ,
    last_sync_status VARCHAR(20),              -- 'success','error'
    last_sync_count INTEGER,                   -- students synced
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT provider_valid CHECK (provider IN ('google','clever'))
);
CREATE INDEX idx_sso_school ON sso_connections(school_id);
```

#### concept_explanations (cache)
```sql
CREATE TABLE concept_explanations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id      VARCHAR(100) NOT NULL,      -- e.g., 'denominator_meaning', '4.NF.B.3'
    language        VARCHAR(5) NOT NULL DEFAULT 'en',
    explanation_text TEXT NOT NULL,
    model_used      VARCHAR(50),
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_served_at  TIMESTAMPTZ,
    serve_count     INTEGER DEFAULT 0,
    CONSTRAINT unique_concept_lang UNIQUE (concept_id, language)
);
```

---

## 5.6 API Endpoints

### Subscriptions & Billing

```
POST   /api/v1/subscriptions/checkout          Create Stripe checkout session
GET    /api/v1/subscriptions/{user_id}         Get current subscription
PATCH  /api/v1/subscriptions/{sub_id}          Update subscription (upgrade/downgrade)
DELETE /api/v1/subscriptions/{sub_id}          Cancel subscription
POST   /api/v1/subscriptions/{sub_id}/pause    Pause subscription
POST   /api/v1/subscriptions/{sub_id}/resume   Resume paused subscription
GET    /api/v1/subscriptions/{sub_id}/invoices  List invoices
POST   /webhooks/stripe                         Stripe webhook receiver
```

**POST /api/v1/subscriptions/checkout — Request:**
```json
{
  "user_id": "usr_abc123",
  "plan_tier": "individual",
  "billing_period": "annual",
  "success_url": "https://app.padi.ai/onboarding?success=true",
  "cancel_url": "https://app.padi.ai/pricing"
}
```

**POST /api/v1/subscriptions/checkout — Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_...",
  "session_id": "cs_..."
}
```

### Schools & Classrooms

```
POST   /api/v1/schools                              Create school
GET    /api/v1/schools/{school_id}                  Get school details
PATCH  /api/v1/schools/{school_id}                  Update school profile

POST   /api/v1/schools/{school_id}/dpa              Submit signed DPA
GET    /api/v1/schools/{school_id}/dpa              Get DPA status

POST   /api/v1/schools/{school_id}/roster/import    Import CSV roster
GET    /api/v1/schools/{school_id}/roster/import/{job_id}  Check import status

POST   /api/v1/schools/{school_id}/classrooms       Create classroom
GET    /api/v1/schools/{school_id}/classrooms        List classrooms
PATCH  /api/v1/schools/{school_id}/classrooms/{id}  Update classroom
POST   /api/v1/schools/{school_id}/classrooms/{id}/students    Add student to classroom
DELETE /api/v1/schools/{school_id}/classrooms/{id}/students/{student_id}  Remove student

GET    /api/v1/schools/{school_id}/dashboard        School admin dashboard data
GET    /api/v1/schools/{school_id}/standards-coverage  Standards coverage grid
GET    /api/v1/schools/{school_id}/doe-report        Oregon DOE report (PDF + CSV)

POST   /api/v1/schools/{school_id}/sso/google       Configure Google SSO
POST   /api/v1/schools/{school_id}/sso/clever       Configure Clever SSO
POST   /api/v1/schools/{school_id}/sso/sync         Trigger manual roster sync
```

**POST /api/v1/schools/{school_id}/roster/import — Request:**
```
Content-Type: multipart/form-data
file: [CSV file]
```

**POST /api/v1/schools/{school_id}/roster/import — Response:**
```json
{
  "import_job_id": "job_abc123",
  "status": "processing",
  "estimated_completion_seconds": 30,
  "preview": {
    "total_rows": 31,
    "valid_rows": 28,
    "error_rows": 3,
    "new_students": 28,
    "teacher_invitations": 2
  }
}
```

### SSO Authentication

```
GET    /auth/google/callback                Google OAuth callback
GET    /auth/clever/callback                Clever OAuth callback
GET    /auth/sso/initiate?domain={domain}   Initiate SSO for school domain (auto-detects provider)
```

### Engagement Features

```
GET    /api/v1/students/{student_id}/badges              Get student badges
GET    /api/v1/badges                                     Full badge catalog

GET    /api/v1/missions/current                          Current week's mission
GET    /api/v1/missions/{mission_id}                     Get mission details
POST   /api/v1/missions/{mission_id}/attempts            Start mission attempt
WS     /ws/missions/{attempt_id}                         Mission attempt WebSocket (same as session WS)
GET    /api/v1/students/{student_id}/mission-attempts    Student mission history

POST   /api/v1/sessions/{session_id}/study-together      Initiate Study Together mode

GET    /api/v1/concepts/{concept_id}/explain             Get concept explanation
POST   /api/v1/concepts/{concept_id}/explain             Generate (if not cached)
```

**GET /api/v1/missions/current — Response:**
```json
{
  "mission_id": "msn_xyz",
  "title": "Crater Lake Depth Adventure",
  "theme": "Oregon's deepest lake",
  "description": "Help the research team measure Crater Lake! Use fractions and measurements to complete the mission.",
  "question_count": 15,
  "week_of": "2026-04-06",
  "expires_at": "2026-04-12T23:59:59Z",
  "student_attempt": null,    // or existing attempt if student started
  "badge_reward": "math_mission_complete"
}
```

### Analytics (Internal)

```
GET    /api/v1/internal/analytics/funnel           Funnel metrics summary
GET    /api/v1/internal/analytics/question-flags   Questions flagged for review
GET    /api/v1/internal/analytics/abtest/{test_id} A/B test results
```

### Content

```
POST   /api/v1/worksheets/generate                  Generate printable worksheet (returns PDF)
GET    /api/v1/modules/{module_id}/video            Get video micro-lesson URL
```

**POST /api/v1/worksheets/generate — Request:**
```json
{
  "student_id": "stu_abc123",
  "skill_ids": ["4.NF.B.3", "4.NF.B.4"],
  "difficulty": "mixed",
  "question_count": 15
}
```

**POST /api/v1/worksheets/generate — Response:**
```json
{
  "worksheet_id": "ws_abc",
  "student_pdf_url": "https://...",    // questions only
  "answer_key_pdf_url": "https://...", // questions + answers
  "question_count": 15,
  "generated_at": "2026-04-02T23:15:00Z"
}
```

---

## 5.7 Acceptance Criteria

### AC-5.1: Freemium Enforcement

**Given** a user on the free tier (no active subscription)  
**When** they attempt their 4th practice session in the same calendar week  
**Then**:
- Session start is blocked
- User sees: "You've completed your 3 free sessions this week. Upgrade to PADI.AI to practice every day."
- "See plans" CTA redirects to `/pricing`
- Existing session data is not affected
- Counter resets on Monday 12:00am PT (Pacific Time)

### AC-5.2: Stripe Checkout Flow

**Given** a parent on free tier clicks "Start Free Trial"  
**When** they complete the Stripe checkout for Individual Monthly plan  
**Then**:
- Stripe `checkout.session.completed` webhook received within 60 seconds
- `subscriptions` record created with `status = 'trialing'`, `trial_end` = 14 days from now
- Student account's premium features unlocked immediately
- Welcome email sent to parent within 5 minutes
- Parent redirected to onboarding success page

### AC-5.3: Trial-to-Paid Conversion

**Given** a parent's 14-day trial ends  
**When** Stripe attempts to charge the payment method on file  
**Then**:
- If payment succeeds: `subscriptions.status` changes from `trialing` to `active`; features remain unlocked
- If payment fails: `subscriptions.status` changes to `past_due`; dunning email sent immediately
- Parent receives email: "Your free trial has ended — here's your receipt" (if successful) OR "Your payment didn't go through" (if failed)

### AC-5.4: Subscription Cancellation

**Given** a parent cancels their subscription at period end  
**When** the subscription period expires  
**Then**:
- `subscriptions.status` = `'canceled'`
- Student can no longer start new sessions beyond the free tier limit
- All student progress data retained (no deletion)
- Parent sees "Reactivate" option in subscription settings
- Reactivation restores all features and shows full historical progress data

### AC-5.5: Bulk Roster Import

**Given** a school admin uploads a valid 30-student CSV  
**When** the import job completes  
**Then**:
- 30 `students` records created within 60 seconds
- Each student linked to correct classroom based on teacher_email in CSV
- Teacher accounts invited (email sent to teacher_email addresses not already registered)
- Import results page shows: "30 students imported successfully. 2 teacher invitations sent."
- Zero PII logged server-side during import (student last names treated as internal identifiers only)

### AC-5.6: Google SSO Login

**Given** a school has configured Google SSO for domain `hillcrest.k12.or.us`  
**When** a student at that school clicks "Sign in with Google (School)"  
**Then**:
- Google OAuth flow completes successfully
- Student is authenticated without entering a PADI.AI password
- If student's Google account email matches a roster-imported student record: they are logged in to that student account
- If no match: new student account created with `display_name` from Google profile, `sso_provider = 'google'`
- Session established; student lands on their practice dashboard

### AC-5.7: Clever SSO + Roster Sync

**Given** a school has configured Clever SSO and the nightly sync runs  
**When** the sync job completes  
**Then**:
- All students in Clever for that school who are Grade 4 are created or updated in PADI.AI
- Students removed from Clever since last sync are marked inactive (not deleted)
- `sso_connections.last_sync_at` updated; `last_sync_status = 'success'`
- School admin sees "Last synced: [timestamp]" on the SSO settings page
- Sync job completes within 5 minutes for up to 500 students

### AC-5.8: Achievement Badge — Week Warrior

**Given** a student has completed a practice session on each of 7 consecutive days  
**When** the session on day 7 is completed  
**Then**:
- `student_badges` record created: `badge_id = 'week_warrior'`, `unlocked_at` = now
- In-app notification shown at session summary: "New Badge: Week Warrior!"
- Parent email queued: "Alex earned a new badge: Week Warrior!"
- Badge appears in student's badge shelf on next login
- Badge cannot be earned a second time (duplicate insert rejected by `UNIQUE` constraint)

### AC-5.9: Weekly Math Mission

**Given** it is Monday and the week's mission is published (`is_published = true`)  
**When** a student opens the app  
**Then**:
- Mission widget visible on student dashboard showing mission title and "Play" button
- Student can start the mission (15-question session via WebSocket, no hints)
- On completion: `student_mission_attempts.completed_at` set; `badge_awarded = true` if not previously awarded
- "Math Mission Complete!" Pip celebration triggered (full spin + confetti)
- Mission widget disappears after the mission's 7-day window expires

### AC-5.10: Spanish Language — Full UI

**Given** a parent sets `language_preference = 'es'` in account settings  
**When** the student logs in  
**Then**:
- All UI strings display in Spanish (menus, buttons, labels, Pip dialogue)
- Pip responses are in Spanish (verified via spot check of 20 response samples)
- Parent dashboard emails received in Spanish
- Math question text displays in Spanish (for questions with reviewed Spanish translations)
- English/Español toggle in header switches language in real time (no page reload)
- Language preference persists across sessions

### AC-5.11: Handwriting Recognition

**Given** a student is on a touch device and answering a numeric question  
**When** they draw a number in the handwriting input canvas  
**Then**:
- Client-side OCR recognizes the number within 1 second
- Recognized number displayed in confirmation field: "Did you write 42?"
- If confidence ≥ 0.8: student can tap "Yes, submit" to submit that answer
- If confidence < 0.8: message shown: "I'm not sure what you wrote — can you use the keypad?" with keypad option
- If student confirms handwritten answer: `session_responses.student_answer` stores the recognized number (not a drawing)

### AC-5.12: "Explain to Me" Feature

**Given** a student is in a practice session on a Fractions module  
**When** they open "Explain a concept" and select "What is a denominator?"  
**Then**:
- If a cached explanation exists (`concept_explanations` table has `concept_id = 'denominator_meaning', language = 'en'`): returned within 500ms
- If no cache: Claude Sonnet 4.6 generates explanation within 3 seconds, stored in cache
- Explanation is ≤ 5 sentences, FK Grade 3.5–5.5, includes an Oregon-themed example
- Explanation does not solve the student's current question
- `concept_explanations.serve_count` incremented

### AC-5.13: Load Test — 1,000 Concurrent Sessions

**Given** a load test simulating 1,000 concurrent practice sessions  
**When** the test runs for 10 minutes  
**Then**:
- P50 tutor response latency < 1.5 seconds
- P95 tutor response latency < 3 seconds
- P99 tutor response latency < 6 seconds
- Zero session state corruption (all sessions resume correctly after test)
- Error rate < 0.1% for question delivery and assessment evaluation
- Zero data mixing between sessions (critical: no student sees another student's data)

### AC-5.14: COPPA Analytics Compliance

**Given** PostHog is integrated and events fire during student practice sessions  
**When** a privacy audit checks the PostHog event properties  
**Then**:
- Zero events contain `student_name`, `parent_name`, `email`, `ip_address`, or any PII field
- All student events use `student_id` UUID as the only identifier
- Analytics cookies are not set for authenticated student accounts (verified via browser dev tools)
- PostHog data resides on self-hosted instance (not shipped to third-party PostHog cloud) OR PostHog's GDPR data processing agreement is in place and no student data flows to PostHog cloud

### AC-5.15: DPA Flow

**Given** a school admin completes the DPA signing form  
**When** they submit the signed DPA  
**Then**:
- `dpa_agreements` record created with `content_hash` of the DPA text version they signed
- DPA PDF generated and emailed to school admin's email within 10 minutes
- `schools.dpa_signed_at` set to current timestamp
- School admin dashboard previously blocked with "Complete DPA to access student data" banner → banner removed
- Roster import and student data access now available

---

*End of PRD Stage 5*
