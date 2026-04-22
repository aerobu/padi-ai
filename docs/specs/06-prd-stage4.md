# PRD Stage 4: End-of-Grade Assessment & Teacher/Parent Reporting
## PADI.AI | Version 1.0 | Target Completion: Month 14

**Document Status:** Draft  
**Owner:** Product — Assessment & Reporting  
**Reviewers:** Engineering (Backend), Engineering (Frontend), Curriculum, Legal (FERPA/COPPA), QA  
**Dependencies:** Stage 1 (Standards DB + Diagnostic), Stage 2 (Learning Plan), Stage 3 (Adaptive Practice Engine)  
**Epic Reference:** MATH-400 series  
**MVP Milestone:** ✅ Stage 4 Completion = MVP

---

## Table of Contents

1. [Overview & MVP Declaration](#41-overview--mvp-declaration)
2. [Functional Requirements](#42-functional-requirements)
3. [MVP Feature Checklist](#43-mvp-feature-checklist)
4. [Non-Functional Requirements](#44-non-functional-requirements)
5. [Data Models](#45-data-models)
6. [API Endpoints](#46-api-endpoints)
7. [Acceptance Criteria](#47-acceptance-criteria)

---

## 4.1 Overview & MVP Declaration

### Why Stage 4 Completes the MVP

PADI.AI's core value proposition is:

> *An Oregon 4th grader who may be behind in math can take a diagnostic assessment, receive a personalized AI-powered learning plan, practice adaptively with an AI tutor, be assessed against grade-level standards, and continue improving in a closed remediation loop — all without human tutoring intervention.*

Stage 4 closes this loop. Without Stage 4, the product delivers diagnostic insights and adaptive practice — valuable, but incomplete. With Stage 4, the product delivers:

- **A summative outcome signal** (End-of-Grade Assessment): Parents and students know whether the student is On Par, Approaching, or Above Par against Oregon's actual grade-level standards
- **A closed remediation loop** (FR-16): Remaining gaps automatically feed back into an updated learning plan
- **Parent-accessible reporting** (FR-17, FR-18): Parents can see exactly what their child knows, has learned, and needs to learn — in downloadable, shareable formats
- **Teacher visibility** (FR-19): Teachers can observe student progress without manual data entry or parent-intermediated reports
- **Communication infrastructure** (FR-20): Automated notifications close the engagement loop between practice sessions

### What "MVP" Means in This Context

The MVP (Minimum Viable Product) designation at Stage 4 completion means:

**Complete:** The full student learning loop (diagnostic → learning plan → adaptive practice → summative assessment → remediation) is functional for a single student, with parent visibility and basic teacher access.

**Not yet complete (deferred to Stage 5 / MMP):**
- Subscription billing and payment processing (FR-21)
- School/district bulk onboarding (FR-22)
- Enhanced engagement features: mascot, badges, achievements (FR-23)
- Analytics platform integration / A/B testing (FR-24)
- COPPA Safe Harbor certification (FR-25)
- Content expansion to 10,000+ questions; video micro-lessons (FR-26)
- Spanish language support (FR-23)
- SSO / Clever integration (FR-22)
- Performance at school scale (10,000 concurrent users) (NFR-5.x)
- 99.9% uptime SLA (NFR-5.x)

The MVP is intentionally not polished, not scaled for school deployments, and not monetized. It is a complete, working product that delivers genuine educational value and can support initial beta users (target: 50–100 students, invited cohort).

### What's Still Missing for MMP (Stage 5)

MMP (Minimum Marketable Product) adds the commercial and engagement layer that transforms the MVP into a product that can be marketed, sold to schools, and sustained as a business. Stage 5 adds: subscription billing, school onboarding and SSO, gamification/engagement, A/B testing infrastructure, COPPA Safe Harbor certification, content expansion, and Spanish language support.

The transition from MVP to MMP is a business and distribution readiness milestone, not a technical one. The core learning loop does not change in Stage 5.

---

## 4.2 Functional Requirements

### FR-15: End-of-Grade Summative Assessment

The End-of-Grade (EOG) Assessment is a computer-adaptive summative test that evaluates a student's proficiency across all 29 Oregon Grade 4 math standards. It is modeled on the Oregon OSAS (Oregon Statewide Assessment System) format and uses the same IRT-based adaptive item selection as the diagnostic, but with a larger item pool and more rigorous conditions.

#### FR-15.1: Assessment Format & Coverage

**Structure:**
- 40–50 questions total (adaptive; exact count determined by IRT algorithm termination condition)
- Covers all 29 Oregon Grade 4 math standards across 5 domains
- Questions distributed proportionally to Oregon OSAS domain weights:

| Domain | Code | OSAS Weight | Approx. Questions |
|---|---|---|---|
| Operations & Algebraic Thinking | OA | 20% | 8–10 |
| Number & Operations in Base Ten | NBT | 25% | 10–12 |
| Number & Operations — Fractions | NF | 30% | 12–15 |
| Measurement & Data | MD | 15% | 6–8 |
| Geometry | G | 10% | 4–5 |

**Item types (must match OSAS formats):**
- Multiple choice (1 correct of 4): 50% of items
- Numeric entry (whole number or decimal): 25% of items
- Fraction input: 15% of items
- Multi-select (select all that apply): 10% of items

**No drag-and-drop in EOG** (not part of OSAS format; reserved for practice only)

#### FR-15.2: Adaptive Item Selection (CAT — Computer Adaptive Testing)

The EOG uses a full three-parameter IRT (3PL) model for item selection, more rigorous than the practice engine's simplified approach:

```
P(correct | θ) = c + (1 - c) / (1 + exp(-a(θ - b)))

Where:
  θ = student ability estimate
  a = item discrimination (1.0 – 2.0 range)
  b = item difficulty (-3.0 to +3.0)
  c = guessing parameter (0.20 for 4-option MC; 0.0 for numeric entry)
```

**Item selection algorithm (Maximum Fisher Information):**

```python
def select_eog_item(theta: float, administered_items: List[str],
                     domain_counts: dict, target_domain_counts: dict) -> str:
    """
    Select next EOG item using Maximum Fisher Information,
    subject to content balancing constraints.
    """
    available = query_eog_items(
        exclude_ids=administered_items,
        domain_counts_under_target=get_under_target_domains(
            domain_counts, target_domain_counts
        )
    )

    # Fisher Information for each candidate item
    def fisher_info(item: dict) -> float:
        a, b, c = item['a'], item['b'], item['c']
        p = c + (1 - c) / (1 + math.exp(-a * (theta - b)))
        q = 1 - p
        numerator = (a ** 2) * ((p - c) ** 2) * q
        denominator = ((1 - c) ** 2) * p
        return numerator / denominator

    # Content-balanced selection: prefer domains under target allocation
    candidates = [
        item for item in available
        if item['domain'] in get_under_target_domains(domain_counts, target_domain_counts)
    ] or available  # fallback: all available if none are under-represented

    return max(candidates, key=fisher_info)['question_id']
```

**Theta estimation (EAP — Expected A Posteriori):**

```python
def estimate_theta_eap(responses: List[tuple]) -> float:
    """
    responses: List of (a, b, c, is_correct)
    Returns MAP theta estimate using normal prior N(0, 1).
    """
    theta_grid = np.linspace(-3.0, 3.0, 61)  # 0.1 step
    log_posterior = np.zeros(len(theta_grid))

    # Normal prior
    log_posterior += -0.5 * theta_grid ** 2

    # Likelihood for each response
    for a, b, c, u in responses:
        p = c + (1 - c) / (1 + np.exp(-a * (theta_grid - b)))
        p = np.clip(p, 1e-6, 1 - 1e-6)
        log_posterior += u * np.log(p) + (1 - u) * np.log(1 - p)

    posterior = np.exp(log_posterior - log_posterior.max())
    posterior /= posterior.sum()

    return float(np.dot(posterior, theta_grid))
```

**Stopping criteria (first met wins):**
1. Standard Error of Measurement (SEM) < 0.30 (sufficient measurement precision)
2. Minimum 40 items administered
3. Maximum 50 items administered (hard cap regardless of SEM)

#### FR-15.3: Assessment Conditions (Integrity)

The EOG Assessment is administered under stricter conditions than practice:

| Condition | Practice | EOG Assessment |
|---|---|---|
| Hints | ✅ Available | ❌ Not available |
| Tutor/chat | ✅ Available | ❌ Not available |
| Pause | ✅ Allowed (30 min max) | ❌ Not allowed |
| Back navigation | ✅ Allowed within session | ❌ Disabled |
| Time limit | None (soft pacing) | None (untimed by design) |
| Retake interval | After each session | 30 days minimum |
| Context | Practice environment | Distinct "Assessment Mode" UI |

**Integrity measures:**
- Back button disabled (browser history blocked via JavaScript + `popstate` listener)
- Question flag system: student can flag a question for review before final submission
- Final review screen: list all questions answered, flagged items highlighted → confirm submission
- Session token is single-use: if WebSocket drops mid-assessment, student must contact parent to restart (assessment is voided if more than 5 minutes of disconnection; no mid-assessment resume)
- Browser tab visibility API: log if student tabs away; alert displayed on return ("Please stay on this tab during your assessment")
- Assessment attempt logged with `ip_address`, `user_agent`, `start_time`, `end_time`, `tab_switch_count`

#### FR-15.4: Proficiency Levels & Scoring

**Theta → Proficiency Level mapping (Oregon-aligned):**

| Level | Code | Theta Range | Description |
|---|---|---|---|
| Below Par | `BELOW_PAR` | θ < -1.0 | Significantly below grade-level expectations |
| Approaching | `APPROACHING` | -1.0 ≤ θ < 0.0 | Working toward grade-level proficiency |
| On Par | `ON_PAR` | 0.0 ≤ θ < 1.0 | Meeting grade-level expectations |
| Above Par | `ABOVE_PAR` | θ ≥ 1.0 | Exceeding grade-level expectations |

These levels are named "Par" (not "Proficient/Basic") intentionally — golf metaphor keeps framing neutral and non-stigmatizing for children.

**Score report includes:**
- Overall proficiency level (student-facing: simple level indicator)
- Overall theta estimate with SEM (parent/teacher facing)
- Domain-level proficiency breakdown (5 domains)
- Skills still deficient (P(mastered) < 0.60 per BKT, cross-referenced with EOG performance)
- Skills mastered (P(mastered) ≥ 0.95 confirmed by EOG performance)
- Percentile rank vs. Oregon Grade 4 baseline (when population data is available — initially estimated from IRT prior)

#### FR-15.5: Post-Assessment Actions

Immediately following assessment completion:
1. BKT states updated: EOG correct responses treated as 3 BKT observations (high information content); incorrect as 2
2. Skills with θ domain score < -0.5 → auto-added to revised learning plan with priority = HIGH
3. Skills with domain θ ≥ 0.5 → `skill_mastery_states.mastered_at` confirmed
4. Revised learning plan generated (FR-16)
5. Progress report PDF generated asynchronously (FR-17)
6. Parent notification queued (FR-20)

#### FR-15.6: Retake Policy

- Minimum 30-day interval between EOG Assessment attempts
- "Retake available in X days" displayed after first attempt
- Maximum 3 EOG attempts per student per academic year (September–June)
- Each attempt generates a separate `eog_assessments` record; all records retained for trend analysis
- Learning plan automatically adjusted after each attempt; the plan cannot be "gamed" by retaking without practicing

---

### FR-16: Remediation Loop

The Remediation Loop is the mechanism that makes PADI.AI a continuous improvement system rather than a one-time assessment tool. After each EOG Assessment, the system automatically generates a revised learning plan targeted at remaining gaps.

#### FR-16.1: Revised Learning Plan Generation

**Trigger:** EOG Assessment completion (automated; no teacher/parent action required)

**Algorithm:**

```python
def generate_remediation_plan(student_id: str, eog_result: EOGResult,
                               current_bkt_states: dict) -> LearningPlan:
    # 1. Identify deficient skills
    deficient_skills = [
        skill_id for skill_id, bkt in current_bkt_states.items()
        if bkt['p_mastered'] < 0.70  # threshold for "needs more work"
    ]

    # 2. Sort by distance from mastery (ascending p_mastered = highest priority)
    deficient_skills.sort(key=lambda s: current_bkt_states[s]['p_mastered'])

    # 3. Apply prerequisite graph ordering
    ordered_skills = topological_sort_by_prerequisites(deficient_skills)

    # 4. Estimate time to mastery for each skill
    for skill_id in ordered_skills:
        bkt = current_bkt_states[skill_id]
        # Linear extrapolation from current p_mastered to 0.95
        attempts_needed = estimate_attempts_to_mastery(
            p_current=bkt['p_mastered'],
            p_target=0.95,
            p_transit=bkt['p_transit']
        )
        estimated_minutes = attempts_needed * 1.5  # avg 1.5 min per question

    # 5. Build modules (≤ 5 skills per module, ≤ 4 weeks estimated time)
    return build_learning_plan_modules(ordered_skills, current_bkt_states)
```

#### FR-16.2: Student-Facing Motivation Display

After EOG Assessment, the student sees a "What comes next" screen:

```
┌─────────────────────────────────────────────────────┐
│  Your Results                                       │
│                                                     │
│  Overall Level: Approaching ●●○○                    │
│                                                     │
│  Great progress! You're close to On Par.            │
│  Here's what to work on next:                       │
│                                                     │
│  ⭐ Fractions (5 skills remaining)                  │
│  ⭐ Measurement (2 skills remaining)                │
│                                                     │
│  You've already mastered:                           │
│  ✓ Operations & Algebraic Thinking (all 7 skills)  │
│  ✓ Geometry — Lines and Angles                      │
│                                                     │
│  [Continue Learning]    [See Full Report]           │
└─────────────────────────────────────────────────────┘
```

**"How close" indicator:** For each remaining skill, display a progress bar from 0% to mastery, populated from `P(mastered)`:
- P(mastered) < 0.30 → "Just getting started"
- 0.30 ≤ P(mastered) < 0.60 → "Making progress"
- 0.60 ≤ P(mastered) < 0.95 → "Almost there!"

#### FR-16.3: Loop Termination

The remediation loop continues until:
- Student achieves **On Par** or **Above Par** on EOG Assessment (θ ≥ 0.0)
- OR academic year ends (June 15 — plan is archived, not deleted)
- OR parent/teacher manually pauses the plan

#### FR-16.4: Parent Communication for Remediation Loop

Immediately after EOG Assessment completion, parent receives email (FR-20):

```
Subject: [Student Name] completed the PADI.AI End-of-Grade Assessment

Hi [Parent Name],

[Student Name] just completed their End-of-Grade Math Assessment. Here's a summary:

📊 Result: Approaching Grade Level

What this means: [Student Name] is making strong progress and is working toward 
full grade-level proficiency in Oregon 4th grade math.

What happens next: PADI.AI has automatically updated [Student Name]'s 
learning plan to focus on the skills where they can improve most:
• Adding and Subtracting Fractions (4.NF.B.3)
• Measurement Conversions (4.MD.A.1)
• Multiplying Fractions by Whole Numbers (4.NF.B.4)

View the full report: [Link to PDF report]

[Student Name] can continue practicing right away — the updated plan is ready.

The PADI.AI Team
```

---

### FR-17: Student Progress Report

The Student Progress Report is a comprehensive PDF document generated after each EOG Assessment. It serves as the primary artifact parents share with teachers, school counselors, or tutors.

#### FR-17.1: Report Versions

Two versions of the same report, generated from the same data:

| Version | Audience | Complexity | Length |
|---|---|---|---|
| **Student Report** | Student (age 9-10) | Simplified language, visual-heavy | 2 pages |
| **Parent/Teacher Report** | Parent, teacher | Full data, technical detail | 4-6 pages |

Both versions are generated as PDFs (using `WeasyPrint` or `Puppeteer` HTML-to-PDF) and stored in S3.

#### FR-17.2: Student Report Sections

1. **Cover page:** Student name, assessment date, PADI.AI logo, Oregon map graphic
2. **Your Level:** Large visual indicator of proficiency level (Below Par / Approaching / On Par / Above Par), with friendly description ("You're Approaching! That means you've learned a lot and you're getting close to the top!")
3. **What You're Great At:** Visual badges for each mastered skill domain (e.g., "Multiplication Master 🏆")
4. **What You're Working On:** Visual checklist of in-progress skills with encouragement ("You're almost there on Fractions!")
5. **Your Math Journey:** Simple bar chart — skills mastered over time (month by month)
6. **Message from Pip:** Personalized encouragement based on performance trajectory (e.g., "You've improved so much! Keep going!")

#### FR-17.3: Parent/Teacher Report Sections

1. **Cover page:** Student name, parent name, assessment date, report version
2. **Executive Summary:** Overall proficiency level, theta score, SEM, change from previous assessment (if any), one-paragraph narrative summary
3. **Domain-Level Breakdown:** Table showing each of the 5 domains:
   - Domain name
   - Student's domain theta score
   - Proficiency level for this domain
   - Number of standards mastered / total
   - Trend arrow (vs. diagnostic baseline)
4. **Skills Detail — Mastered:** Full list of 29 standards, each marked:
   - ✅ Mastered (with date mastered)
   - 🔄 In Progress (P(mastered) shown as percentage)
   - ⚠️ Needs Work (P(mastered) < 0.40)
5. **Time on Task:** Table by week: sessions completed, total minutes, average accuracy
6. **Learning Trajectory Chart:** Line chart — theta estimate over time (one point per session), with proficiency level bands shown as horizontal bands
7. **Recommended Next Steps:** Auto-generated from remediation plan (top 3 priority skills with description)
8. **Data Sources & Methodology Note:** One paragraph explaining BKT, IRT, and how proficiency levels were determined (for educated parents / teachers)
9. **Share this report:** QR code + URL for shareable read-only link (expires 90 days)

#### FR-17.4: PDF Generation

```python
async def generate_progress_report(
    student_id: str,
    assessment_id: str,
    report_type: Literal["student", "parent"]
) -> str:
    """Returns S3 URL of generated PDF."""

    # 1. Gather all data
    report_data = await compile_report_data(student_id, assessment_id)

    # 2. Render HTML using Jinja2 template
    template = jinja_env.get_template(f"report_{report_type}.html")
    html = template.render(**report_data)

    # 3. Generate PDF (Puppeteer via pyppeteer or WeasyPrint)
    pdf_bytes = await html_to_pdf(html, format="letter", margin="0.75in")

    # 4. Store in S3
    s3_key = f"reports/{student_id}/{assessment_id}/{report_type}_report.pdf"
    await s3_client.put_object(
        Bucket=settings.REPORTS_BUCKET,
        Key=s3_key,
        Body=pdf_bytes,
        ContentType="application/pdf",
        ServerSideEncryption="aws:kms"
    )

    return f"https://{settings.REPORTS_BUCKET}.s3.amazonaws.com/{s3_key}"
```

**Report generation SLA:** < 10 seconds from assessment completion trigger.  
**Fallback:** If PDF generation exceeds 15 seconds, send parent email with link that says "Your report is being prepared — check back in a few minutes" and complete generation asynchronously.

---

### FR-18: Parent Dashboard (Full)

The Parent Dashboard is the primary interface for parents to monitor their child's learning. Stage 3 introduced a lightweight parent view; Stage 4 completes it with full reporting features.

#### FR-18.1: Dashboard Home

**Layout — three-column at desktop, stacked at mobile:**

```
┌──────────────────────────────────────────────────────────┐
│  👋 Hi Sarah! Here's how Alex is doing.                  │
│                                                          │
│  Current Level: Approaching ●●○○   Last practiced: Today │
├─────────────────┬─────────────────┬──────────────────────┤
│  Skills Mastered│  Skills in      │  Time This Week      │
│       12/29     │  Progress: 6    │     47 minutes       │
│  ▓▓▓▓▓▓▓░░░░   │  ████░░░░       │  Goal: 60 min/week   │
├─────────────────┴─────────────────┴──────────────────────┤
│  Recent Sessions                                [See All] │
│  Today · 14 min · 80% correct · Fractions                │
│  Yesterday · 11 min · 73% correct · Operations          │
├──────────────────────────────────────────────────────────┤
│  [Download Latest Report]   [Share with Teacher]         │
└──────────────────────────────────────────────────────────┘
```

#### FR-18.2: Complete Session History

- Paginated list: 20 sessions per page, newest first
- Each row: date, duration, questions answered, accuracy %, skill(s) practiced, session mode
- Click any session: opens Session Detail view
  - All questions answered (text)
  - Student's answers vs. correct answers
  - Hints used per question
  - Tutor conversation transcript (FR-14.8)
  - BKT state at session start and end per skill

#### FR-18.3: Skill-by-Skill Mastery Timeline

- Visual timeline (horizontal bar chart, one bar per skill)
- Skills grouped by domain (5 domain sections, collapsible)
- Each skill bar:
  - Left side: skill name + Oregon standard code
  - Bar fill: current P(mastered) (0–100%)
  - Green indicator: if mastered, shows mastery date
  - Click skill: opens skill detail with full practice history for that skill
- Filter: "Show all" / "Mastered" / "In Progress" / "Not started"
- Sorting: by domain, by mastery %, by last practiced date

#### FR-18.4: Weekly/Monthly Time-on-Task Charts

- Toggle: Week / Month / All time view
- Bar chart: total practice minutes per day (week view) or per week (month view)
- Overlaid line: accuracy trend
- Summary stats: total sessions, total minutes, average session length, best day/time
- "Weekly goal" progress ring: configurable by parent (default: 60 minutes/week)

#### FR-18.5: Comparison to Grade-Level Expectations

**Critical design constraint:** Comparison is ONLY to grade-level expectations (Oregon OSAS proficiency standards), never to other students. No percentile rankings vs. peers in the dashboard. This is both pedagogically appropriate (growth mindset) and FERPA-compliant.

Display:
- Grade 4 standard targets (where each skill should be by end of year) vs. student's current state
- "On track" / "Ahead" / "Needs more time" status per domain

#### FR-18.6: Achievement Milestones Timeline

- Chronological feed of milestone events:
  - "Mastered [Skill Name]" (with date)
  - "Completed Module: Fractions Part 1"
  - "Completed End-of-Grade Assessment"
  - "Reached On Par level!"
  - "10-session streak!"
- Each milestone has a visual icon and can be shared (generates shareable image card — opt-in)

#### FR-18.7: Upcoming Plan Modules

- Display: next 2 modules in the learning plan
- Per module: module name, skills included, estimated time, current progress
- CTA: "Start Session" button (launches app to correct skill for student)
- "Adjust plan" option (opens a request-to-support flow; plans auto-managed but parent can flag concerns)

#### FR-18.8: Share with Teacher

- Button: "Share progress with teacher"
- Action: Generate a 90-day read-only link to the Parent/Teacher Report PDF
- Optional: enter teacher's email to send directly (via SendGrid)
- Link displays: assessment date, proficiency level, skills summary — no raw BKT parameters (too technical)
- Parent can revoke the link at any time from settings
- All share events logged (`report_shares` table) for FERPA compliance audit

---

### FR-19: Teacher Dashboard (Basic)

The Teacher Dashboard provides read-only visibility into the progress of students who have chosen to share their data with the teacher. This is a basic implementation in Stage 4; full school-managed classroom features are Stage 5.

#### FR-19.1: Teacher Account Type

- Teachers register with email + school name (no SSO in Stage 4 — OAuth only in Stage 5)
- Teacher account type = `USER_ROLE = 'teacher'` (distinct from `student` and `parent`)
- Teachers cannot create student accounts or modify student plans
- Teacher access to student data is governed by parent consent (FR-18.8: "Share with teacher")
- FERPA basis: Parent-authorized disclosure (not school official basis — school official basis in Stage 5)

#### FR-19.2: Student Roster View

For each student who has shared data with the teacher:

| Student Name | Grade Level | Current Level | Skills Mastered | Skills in Progress | Last Active | Time This Month |
|---|---|---|---|---|---|---|
| Alex M. | 4 | Approaching | 12/29 | 6 | Today | 47 min |
| Jordan T. | 4 | On Par | 21/29 | 5 | Yesterday | 83 min |
| Riley S. | 4 | Below Par | 4/29 | 3 | 5 days ago | 12 min |

- Sortable by any column
- Clicking a student row expands to show their domain-level breakdown (collapsed by default)
- "Inactive" flag: students not active in 7+ days are highlighted

#### FR-19.3: Class-Level Aggregate View

For the teacher's shared roster, display aggregate insights:

**Common Weak Areas (skills with average P(mastered) < 0.50 across roster):**
- Displayed as ranked list: "3 of your 5 students are struggling with Adding Fractions with Unlike Denominators (4.NF.B.3)"
- Grouped by domain
- Useful for: identifying which skills need whole-class instruction

**Domain Heatmap:**
- 5×N grid (5 domains × N students)
- Each cell colored: red (P < 0.40), yellow (0.40–0.79), green (≥ 0.80)
- Quick visual identification of class-wide gaps

**Note displayed to teacher:** "These insights are based only on students who have chosen to share their data with you. Data reflects individual learning journeys; results should not be used to compare students to one another."

#### FR-19.4: Export Roster Data to CSV

- "Export" button: generates a CSV file with one row per student
- CSV columns: `student_first_name`, `overall_level`, `theta_score`, `skills_mastered_count`, `skills_in_progress_count`, `total_minutes_this_month`, `last_active_date`, per-domain proficiency level (5 columns)
- PII: only first name included (no last name, no student ID) — minimized for teacher use case
- CSV is generated on-demand (not pre-stored)
- Export event logged for FERPA audit

#### FR-19.5: Read-Only Constraint

- Teacher cannot modify any student data, plans, or settings
- Teacher cannot message students
- Teacher cannot create or delete student accounts
- Teacher cannot see session transcripts (only parent can — FR-14.8)
- If a teacher needs to intervene, they communicate with the parent directly (outside the app)

---

### FR-20: Notifications System

#### FR-20.1: Parent Email Notifications

All emails to parents are sent via **SendGrid** (or AWS SES as fallback). Email templates use responsive HTML with plain-text fallback. From address: `hello@padi.ai`.

**Notification types and triggers:**

| Notification | Trigger | Frequency Cap |
|---|---|---|
| Assessment Complete | EOG Assessment submitted | Once per assessment |
| Milestone Achieved | Skill mastered, module completed, level change | Once per milestone |
| Weekly Summary | Every Sunday at 7pm (parent's local time) | Once per week |
| Inactivity Alert | No student sessions in 7 consecutive days | Once per inactivity period |
| Streak Reminder | Student has 3+ day streak at risk (hasn't practiced today by 5pm) | Once per day |
| Welcome | Account created | Once |
| Report Ready | Progress report PDF generated | Once per assessment |

**Assessment Complete Email (FR-16.4):** Specified in FR-16 above.

**Weekly Summary Email (template):**

```
Subject: Alex's PADI.AI Update — Week of [Date]

This week Alex:
• Completed 4 practice sessions (47 minutes total)
• Answered 38 questions (76% correct)
• Made progress on: Fractions, Measurement

Mastered this week:
⭐ Adding Fractions with Like Denominators

Overall Progress: Approaching grade level (12 of 29 skills mastered)

[View Full Dashboard]    [Download Report]
```

**Inactivity Alert (template):**

```
Subject: Alex hasn't practiced in 7 days — here's a quick way to help

Hi Sarah,

We noticed Alex hasn't practiced on PADI.AI in 7 days. 

Research shows consistent short sessions (even 10 minutes) are the most 
effective for building math skills.

💡 Tip: Try adding PADI.AI to Alex's after-school routine — 
even 2 sessions a week makes a big difference.

[Open Alex's Practice Session]
```

#### FR-20.2: In-App Notifications for Students

Displayed in the app UI (notification bell icon in header, max 3 unread shown):

| Notification | Trigger | Display |
|---|---|---|
| Streak reminder | Hasn't practiced today (shown at app open after 2pm) | "Keep your streak going! Practice today." |
| New skill unlocked | Previous skill mastered | "New skill unlocked: [Skill Name]! Ready to try it?" |
| Module complete | All skills in module mastered | "You finished Module [X]! Amazing work!" |
| Assessment ready | 30 days since last EOG, or all current plan skills mastered | "Your End-of-Grade Assessment is ready!" |
| Level up | Proficiency level changes upward | "You reached On Par! Keep it up!" |

In-app notifications are stored in `student_notifications` table (read/unread state). Cleared after 30 days.

#### FR-20.3: Email Preferences Management

In parent settings (`/settings/notifications`):

- Toggle per notification type (all on by default)
- Cannot disable: Account security notifications (email change, password reset)
- Time-of-day preference: When to receive streak reminders (default: 4pm local time)
- Unsubscribe: Global unsubscribe link in every email (per CAN-SPAM); unsubscribes from marketing emails but not transactional (assessment complete, report ready)

#### FR-20.4: COPPA Compliance — No Direct Child Communication

**Hard rule:** The system will never send an email, SMS, or push notification directly to a student's email address or device.

All communications route through the parent account:
- Student in-app notifications: shown within the app session only (no email/push to student)
- Account creation requires parent email only (student does not have an email on record)
- If a student attempts to add their own email in profile settings: error "Notifications are managed by your parent"

---

## 4.3 MVP Feature Checklist

The following features, spanning Stages 1 through 4, must ALL be complete and passing acceptance criteria for the product to qualify as MVP. This checklist is the definitive go/no-go list for MVP launch.

### Stage 1: Standards DB & Diagnostic Assessment ✅ (Previously completed)
- [ ] **S1-01:** Oregon Grade 4 standards database: all 29 standards across 5 domains seeded, with descriptions, prerequisites, and domain mappings
- [ ] **S1-02:** Diagnostic Assessment: 35-45 adaptive IRT questions, covers all 29 standards proportionally
- [ ] **S1-03:** Diagnostic completion: student can start and complete a full diagnostic assessment
- [ ] **S1-04:** Diagnostic results: generates initial BKT P(mastered) estimates for all 29 skills
- [ ] **S1-05:** Auth0 COPPA flow: parent consent captured before student account creation; parental email verified
- [ ] **S1-06:** Student account under 13: no email required for student; parent email is primary contact
- [ ] **S1-07:** Diagnostic UI: mobile-responsive, accessible (WCAG 2.1 AA), KaTeX rendering
- [ ] **S1-08:** Diagnostic state persistence: diagnostic survives browser refresh

### Stage 2: Learning Plan Generator ✅ (Previously completed)
- [ ] **S2-01:** Learning plan generated from diagnostic results within 30 seconds of diagnostic completion
- [ ] **S2-02:** Learning plan: modules organized by prerequisite graph, correct sequencing
- [ ] **S2-03:** Learning plan: estimated time per module displayed
- [ ] **S2-04:** Learning plan: parent and student can view the plan in the dashboard
- [ ] **S2-05:** Learning plan: updates in real time as skills are mastered

### Stage 3: Adaptive Practice Engine & AI Tutoring
- [ ] **S3-01:** Practice sessions: student can start a session and receive questions for their current skill
- [ ] **S3-02:** Question generator: cached questions served for all 29 standards at ≥ 3 difficulty levels each
- [ ] **S3-03:** Question generator: live generation fallback works for all 29 standards
- [ ] **S3-04:** Assessment agent: correctly evaluates MC, numeric, and fraction input answers
- [ ] **S3-05:** Assessment agent: error classification returns correct error code for ≥ 14 of 15 error taxonomy types (in test suite)
- [ ] **S3-06:** Tutor agent: delivers 3-level hint ladder for every question type
- [ ] **S3-07:** Tutor agent: child-safe language (FK ≤ 5.5, no negative phrases) on ≥ 95% of responses
- [ ] **S3-08:** BKT: correct update equations applied after every response (unit-tested)
- [ ] **S3-09:** BKT: mastery declared correctly at P ≥ 0.95 + 5-correct streak
- [ ] **S3-10:** Dual memory: LTM persists across sessions; WM isolated per session
- [ ] **S3-11:** Frustration detection: `session_mode` switches to scaffolded when score > 7.0
- [ ] **S3-12:** Session persistence: state survives browser refresh, resumes correctly
- [ ] **S3-13:** Session summary: displayed at session end with accurate statistics
- [ ] **S3-14:** P95 tutor latency: < 3 seconds (load tested at 100 concurrent sessions)
- [ ] **S3-15:** LLM cost: < $0.15/session for a 10-question session (measured empirically)
- [ ] **S3-16:** COPPA: zero PII in any LLM prompt (automated log audit passing)

### Stage 4: End-of-Grade Assessment & Reporting
- [ ] **S4-01:** EOG Assessment: student can start and complete a full 40-50 question adaptive assessment
- [ ] **S4-02:** EOG Assessment: covers all 29 standards proportionally per domain weights
- [ ] **S4-03:** EOG Assessment: no hints, no tutor, no back navigation during assessment
- [ ] **S4-04:** EOG Assessment: proficiency level correctly computed from theta estimate
- [ ] **S4-05:** EOG Assessment: 30-day retake restriction enforced
- [ ] **S4-06:** Remediation loop: revised learning plan auto-generated after EOG completion
- [ ] **S4-07:** Remediation loop: deficient skills correctly prioritized by P(mastered) ascending
- [ ] **S4-08:** Progress report: Student PDF generates within 10 seconds of assessment completion
- [ ] **S4-09:** Progress report: Parent PDF generates within 10 seconds of assessment completion
- [ ] **S4-10:** Progress report: PDF includes all required sections (FR-17.2, FR-17.3)
- [ ] **S4-11:** Parent dashboard: complete session history viewable
- [ ] **S4-12:** Parent dashboard: skill mastery timeline correct (reflects actual BKT states)
- [ ] **S4-13:** Parent dashboard: time-on-task charts accurate
- [ ] **S4-14:** Parent dashboard: Share with Teacher flow generates valid read-only link
- [ ] **S4-15:** Teacher dashboard: teacher can register and view shared students
- [ ] **S4-16:** Teacher dashboard: class-level weak areas correctly computed
- [ ] **S4-17:** Teacher dashboard: CSV export works with correct data
- [ ] **S4-18:** Notifications: assessment complete email sent to parent within 5 minutes of assessment end
- [ ] **S4-19:** Notifications: weekly summary email sends correctly on schedule
- [ ] **S4-20:** Notifications: inactivity alert fires correctly after 7 days
- [ ] **S4-21:** COPPA: no direct email/notification sent to student email address
- [ ] **S4-22:** FERPA: teacher access restricted to parent-consented data only

**MVP Launch Gate: ALL 39 items above must be checked ✅**

---

## 4.4 Non-Functional Requirements

| Requirement | Target | Measurement | Priority |
|---|---|---|---|
| Report PDF generation | < 10 seconds | Timed in staging/production | P0 |
| Parent dashboard load (initial) | < 3 seconds | Lighthouse Performance ≥ 75 | P0 |
| Teacher dashboard load | < 3 seconds | APM | P1 |
| EOG Assessment: no back-navigation | 100% enforced | QA: browser back button test | P0 |
| EOG Assessment: tab switch detection | Detected within 500ms | QA: manual test | P0 |
| EOG Assessment: network drop handling | Clearly communicated to student; attempt voided if > 5 min offline | QA | P0 |
| Email deliverability | > 95% inbox placement rate | SendGrid Analytics | P0 |
| PDF storage | S3 with KMS encryption | Infrastructure review | P0 |
| Report link expiry | Shareable report links expire after 90 days | Automated test | P1 |
| Concurrent users at MVP | 200 concurrent (beta cohort) | Load test | P1 |
| Data retention | Student data retained per COPPA (active + 90 days post-deletion) | Policy + code audit | P0 |
| HTTPS everywhere | All endpoints HTTPS only; no HTTP | Security scan | P0 |
| Auth0 session expiry | Student session: 8 hours; parent session: 7 days | Auth0 config | P1 |

---

## 4.5 Data Models

### New Tables for Stage 4

#### eog_assessments
```sql
CREATE TABLE eog_assessments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    attempt_number      INTEGER NOT NULL DEFAULT 1,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at            TIMESTAMPTZ,
    duration_seconds    INTEGER,

    -- Scoring
    theta_estimate      FLOAT,
    theta_sem           FLOAT,              -- Standard Error of Measurement
    proficiency_level   VARCHAR(20),        -- 'BELOW_PAR','APPROACHING','ON_PAR','ABOVE_PAR'

    -- Domain-level scores
    domain_scores       JSONB,              -- {"OA": 0.5, "NBT": -0.2, "NF": -0.8, "MD": 0.1, "G": 0.7}

    -- Item metadata
    items_administered  INTEGER,
    final_sem           FLOAT,

    -- Integrity
    ip_address          INET,
    user_agent          TEXT,
    tab_switch_count    INTEGER DEFAULT 0,
    integrity_flags     TEXT[],             -- e.g., ['TAB_SWITCH_3X']

    -- Status
    status              VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    voided              BOOLEAN NOT NULL DEFAULT FALSE,
    void_reason         TEXT,

    CONSTRAINT proficiency_valid CHECK (proficiency_level IN (
        'BELOW_PAR','APPROACHING','ON_PAR','ABOVE_PAR'
    )),
    CONSTRAINT status_valid CHECK (status IN ('in_progress','completed','voided'))
);
CREATE INDEX idx_eog_student ON eog_assessments(student_id, started_at DESC);
```

#### eog_responses
```sql
CREATE TABLE eog_responses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       UUID NOT NULL REFERENCES eog_assessments(id) ON DELETE CASCADE,
    question_id         UUID NOT NULL REFERENCES practice_questions(id),
    sequence_num        INTEGER NOT NULL,
    skill_id            VARCHAR(20) NOT NULL REFERENCES standards(standard_id),
    domain              VARCHAR(10) NOT NULL,
    student_answer      TEXT,
    is_correct          BOOLEAN,
    response_time_ms    INTEGER,
    theta_before        FLOAT,              -- theta estimate when question was selected
    theta_after         FLOAT,             -- theta estimate after this response
    fisher_info         FLOAT,             -- information contributed by this item
    flagged_for_review  BOOLEAN DEFAULT FALSE,
    answered_at         TIMESTAMPTZ,
    CONSTRAINT sequence_positive CHECK (sequence_num > 0)
);
CREATE INDEX idx_eog_responses_assessment ON eog_responses(assessment_id);
CREATE INDEX idx_eog_responses_skill ON eog_responses(skill_id);
```

#### progress_reports
```sql
CREATE TABLE progress_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    assessment_id   UUID REFERENCES eog_assessments(id),  -- null for interim reports
    report_type     VARCHAR(20) NOT NULL,        -- 'student','parent'
    report_version  INTEGER NOT NULL DEFAULT 1,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    s3_key          TEXT NOT NULL,
    s3_url          TEXT NOT NULL,
    expires_at      TIMESTAMPTZ,                -- for shareable links
    file_size_bytes INTEGER,
    generation_ms   INTEGER,                    -- how long PDF generation took
    CONSTRAINT report_type_valid CHECK (report_type IN ('student','parent'))
);
CREATE INDEX idx_reports_student ON progress_reports(student_id);
```

#### report_shares
```sql
CREATE TABLE report_shares (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES progress_reports(id),
    shared_by       UUID NOT NULL REFERENCES users(id),         -- parent who shared
    shared_with     VARCHAR(254),           -- teacher email (nullable if link only)
    share_token     VARCHAR(64) UNIQUE NOT NULL,  -- random token for URL
    expires_at      TIMESTAMPTZ NOT NULL,          -- 90 days from creation
    revoked_at      TIMESTAMPTZ,
    revoked         BOOLEAN NOT NULL DEFAULT FALSE,
    access_count    INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_report_shares_token ON report_shares(share_token);
CREATE INDEX idx_report_shares_report ON report_shares(report_id);
```

#### teacher_student_access
```sql
CREATE TABLE teacher_student_access (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    granted_by      UUID NOT NULL REFERENCES users(id),     -- parent who granted
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT unique_teacher_student UNIQUE (teacher_id, student_id)
);
CREATE INDEX idx_tsa_teacher ON teacher_student_access(teacher_id) WHERE is_active;
CREATE INDEX idx_tsa_student ON teacher_student_access(student_id) WHERE is_active;
```

#### notification_log
```sql
CREATE TABLE notification_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id        UUID NOT NULL REFERENCES users(id),
    notification_type   VARCHAR(50) NOT NULL,
    channel             VARCHAR(20) NOT NULL,   -- 'email','in_app'
    subject             TEXT,
    body_preview        TEXT,                   -- first 200 chars for audit
    sendgrid_message_id TEXT,
    status              VARCHAR(20) NOT NULL,   -- 'queued','sent','delivered','failed','bounced'
    sent_at             TIMESTAMPTZ,
    opened_at           TIMESTAMPTZ,
    clicked_at          TIMESTAMPTZ,
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT channel_valid CHECK (channel IN ('email','in_app','push'))
);
CREATE INDEX idx_notification_recipient ON notification_log(recipient_id, created_at DESC);
```

#### student_notifications (in-app)
```sql
CREATE TABLE student_notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title           VARCHAR(100) NOT NULL,
    body            TEXT NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '30 days'),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_student_notif ON student_notifications(student_id, is_read, created_at DESC);
```

#### remediation_plans
```sql
-- Extends learning_plans from Stage 2; this table tracks post-EOG remediation plans
CREATE TABLE remediation_plans (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL REFERENCES students(id),
    source_assessment_id UUID NOT NULL REFERENCES eog_assessments(id),
    learning_plan_id    UUID NOT NULL REFERENCES learning_plans(id),
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    priority_skills     TEXT[] NOT NULL,    -- skill_ids in priority order
    estimated_weeks     INTEGER,
    status              VARCHAR(20) NOT NULL DEFAULT 'active',
    CONSTRAINT status_valid CHECK (status IN ('active','completed','superseded'))
);
```

#### eog_item_bank
```sql
-- EOG assessment items are separate from practice_questions (higher quality, validated)
CREATE TABLE eog_item_bank (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id        VARCHAR(20) NOT NULL REFERENCES standards(standard_id),
    domain          VARCHAR(10) NOT NULL,
    question_text   TEXT NOT NULL,
    question_type   VARCHAR(20) NOT NULL,
    options         JSONB,
    correct_answer  TEXT NOT NULL,
    solution_steps  JSONB,
    difficulty_b    FLOAT NOT NULL,
    discrimination_a FLOAT NOT NULL DEFAULT 1.0,
    guessing_c      FLOAT NOT NULL DEFAULT 0.25,
    item_format     VARCHAR(20) NOT NULL,    -- 'MC','numeric','fraction','multi_select'
    validated       BOOLEAN NOT NULL DEFAULT FALSE,
    times_administered INTEGER NOT NULL DEFAULT 0,
    empirical_b     FLOAT,                  -- b parameter after real-world calibration
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT domain_valid CHECK (domain IN ('OA','NBT','NF','MD','G'))
);
CREATE INDEX idx_eog_item_skill ON eog_item_bank(skill_id, difficulty_b);
CREATE INDEX idx_eog_item_domain ON eog_item_bank(domain, difficulty_b);
```

---

## 4.6 API Endpoints

### EOG Assessment

```
POST   /api/v1/eog-assessments                            Start new EOG assessment
GET    /api/v1/eog-assessments/{assessment_id}            Get assessment details/status
POST   /api/v1/eog-assessments/{assessment_id}/submit     Final submission
GET    /api/v1/students/{student_id}/eog-assessments      List all attempts
GET    /api/v1/students/{student_id}/eog-assessments/eligibility  Check if retake allowed
```

**POST /api/v1/eog-assessments — Request:**
```json
{
  "student_id": "stu_abc123"
}
```

**POST /api/v1/eog-assessments — Response:**
```json
{
  "assessment_id": "eog_xyz789",
  "status": "in_progress",
  "items_to_administer_estimate": "40-50",
  "websocket_url": "wss://api.padi.ai/ws/eog/eog_xyz789",
  "assessment_token": "at_...",
  "instructions": {
    "title": "End-of-Grade Math Assessment",
    "body": "Answer each question as best you can. You cannot go back once you submit an answer. There are no hints available during this assessment.",
    "estimated_time_minutes": "60-75"
  }
}
```

**POST /api/v1/eog-assessments/{assessment_id}/submit — Request:**
```json
{
  "confirm_submission": true
}
```

**POST /api/v1/eog-assessments/{assessment_id}/submit — Response:**
```json
{
  "assessment_id": "eog_xyz789",
  "status": "completed",
  "proficiency_level": "APPROACHING",
  "theta_estimate": -0.32,
  "theta_sem": 0.24,
  "items_administered": 45,
  "domain_scores": {
    "OA": 0.45,
    "NBT": 0.21,
    "NF": -0.71,
    "MD": -0.12,
    "G": 0.53
  },
  "report_urls": {
    "student_report": "https://...",
    "parent_report": "https://..."
  },
  "remediation_plan_id": "rp_abc123"
}
```

**WS /ws/eog/{assessment_id} — EOG Session:**

Messages follow same pattern as practice session WebSocket (FR-11/3.7), with these differences:
- No `hint_request` message type (hints disabled)
- No `tutor_message` message type
- Server never sends `hint` or `tutor_response` message types
- Additional server message: `{"type": "tab_switch_warning", "switch_count": 2, "max_before_flag": 5}`
- Additional server message: `{"type": "final_review_ready", "unanswered_count": 0, "flagged_count": 3}`

### Reports

```
GET    /api/v1/reports/{report_id}                       Get report metadata
GET    /api/v1/reports/{report_id}/download              Download PDF (presigned S3 URL)
POST   /api/v1/reports/{report_id}/share                 Create shareable link
DELETE /api/v1/reports/{report_id}/share/{share_token}   Revoke share link
GET    /api/v1/reports/shared/{share_token}              Access shared report (public, no auth required)

GET    /api/v1/students/{student_id}/reports             List all reports
POST   /api/v1/students/{student_id}/reports/generate    Manually trigger report generation
```

**POST /api/v1/reports/{report_id}/share — Response:**
```json
{
  "share_token": "sh_abc123xyz",
  "share_url": "https://app.padi.ai/shared/sh_abc123xyz",
  "expires_at": "2026-07-02T23:15:00Z",
  "report_type": "parent"
}
```

### Parent Dashboard

```
GET    /api/v1/parents/{parent_id}/dashboard             Dashboard summary data
GET    /api/v1/parents/{parent_id}/students/{student_id}/sessions   Full session history (paginated)
GET    /api/v1/parents/{parent_id}/students/{student_id}/skills     Skill mastery timeline
GET    /api/v1/parents/{parent_id}/students/{student_id}/time-on-task  Weekly/monthly time data
GET    /api/v1/parents/{parent_id}/students/{student_id}/milestones  Achievement milestones
GET    /api/v1/parents/{parent_id}/students/{student_id}/plan-preview  Upcoming plan modules
```

**GET /api/v1/parents/{parent_id}/dashboard — Response:**
```json
{
  "students": [
    {
      "student_id": "stu_abc123",
      "display_name": "Alex",
      "current_level": "APPROACHING",
      "skills_mastered": 12,
      "skills_total": 29,
      "skills_in_progress": 6,
      "time_this_week_minutes": 47,
      "last_session_at": "2026-04-02T21:30:00Z",
      "streak_days": 3,
      "latest_report_url": "https://...",
      "recent_sessions": [...]
    }
  ]
}
```

### Teacher Dashboard

```
GET    /api/v1/teachers/{teacher_id}/dashboard           Teacher dashboard summary
GET    /api/v1/teachers/{teacher_id}/students            Roster of shared students
GET    /api/v1/teachers/{teacher_id}/students/{student_id}/summary  Per-student summary
GET    /api/v1/teachers/{teacher_id}/class-insights      Aggregate class insights
GET    /api/v1/teachers/{teacher_id}/students/export     CSV export (generates file)
```

### Notifications

```
GET    /api/v1/notifications/preferences/{user_id}       Get notification preferences
PATCH  /api/v1/notifications/preferences/{user_id}       Update preferences
GET    /api/v1/students/{student_id}/notifications       List in-app notifications
PATCH  /api/v1/students/{student_id}/notifications/{notif_id}/read   Mark as read
POST   /api/v1/notifications/unsubscribe                 Global email unsubscribe (from email link)
```

---

## 4.7 Acceptance Criteria

### AC-4.1: EOG Assessment Start & Conditions

**Given** a student who has completed the diagnostic and has no active EOG assessment within the last 30 days  
**When** they initiate `POST /api/v1/eog-assessments`  
**Then**:
- Assessment record created with `status = 'in_progress'`
- WebSocket URL returned with valid single-use assessment token
- First question served within 2 seconds of WebSocket connection
- First question's domain is OA or NBT (highest-weight domains served first in v1 ordering)

### AC-4.2: EOG Back Navigation Blocked

**Given** a student is on Question 5 of the EOG Assessment  
**When** they press the browser back button  
**Then**:
- Current page does not change (browser history navigation blocked)
- A modal appears: "You cannot go back during the assessment. Please continue with the current question."
- No question is re-served

### AC-4.3: EOG Tab Switch Detection

**Given** a student switches away from the assessment browser tab  
**When** `document.visibilityState` changes to 'hidden'  
**Then**:
- `tab_switch_count` incremented in `eog_assessments`
- On return: modal shown: "Please stay on this tab during your assessment. (Switch #2 of 5)"
- After 5 tab switches: assessment flagged with `integrity_flags = ['EXCESSIVE_TAB_SWITCHES']` in report
- Assessment is not voided for tab switches alone (no punishment, only logging)

### AC-4.4: EOG Network Disconnection

**Given** a student loses network connectivity for > 5 minutes during the EOG Assessment  
**When** they reconnect  
**Then**:
- Assessment WebSocket reconnects
- A modal is shown: "It looks like you were disconnected for more than 5 minutes. This attempt has been ended to maintain assessment integrity. Your progress so far has been saved."
- Assessment `status` set to 'voided', `void_reason = 'network_disconnection_exceeded_5min'`
- Student can start a new EOG attempt after the 30-day interval (voided attempt does not count against attempt limit)

### AC-4.5: EOG CAT Stopping Criteria

**Given** a student is taking the EOG Assessment  
**When** they have answered 40 questions  
**Then**:
- If `theta_sem < 0.30`: assessment terminates, `status = 'completed'`, results computed
- If `theta_sem ≥ 0.30`: additional questions served until SEM < 0.30 or 50 questions reached

**When** 50 questions have been administered (regardless of SEM):
- Assessment terminates with `status = 'completed'`
- Result computed using current theta estimate and SEM

### AC-4.6: EOG Proficiency Level Computation

**Given** a student completes the EOG Assessment with `theta_estimate = -0.15`  
**When** proficiency level is computed  
**Then**:
- `proficiency_level = 'APPROACHING'` (theta in range [-1.0, 0.0))
- Domain scores computed separately for each of the 5 domains
- `domain_scores` JSON stored in `eog_assessments`
- Results available in GET /api/v1/eog-assessments/{assessment_id} within 500ms of submission

### AC-4.7: EOG Retake Restriction

**Given** a student completed an EOG Assessment on April 2, 2026  
**When** they attempt to start a new EOG Assessment on April 25, 2026  
**Then**:
- `POST /api/v1/eog-assessments` returns HTTP 429
- Response body: `{"error": "retake_not_eligible", "eligible_at": "2026-05-02", "days_remaining": 7}`
- No new assessment record is created

### AC-4.8: Remediation Plan Auto-Generation

**Given** a student completes an EOG Assessment with proficiency_level = 'APPROACHING'  
**When** results are computed  
**Then**:
- Deficient skills (P(mastered) < 0.70) are identified from `skill_mastery_states`
- Skills are sorted ascending by P(mastered)
- Prerequisite ordering is applied (topological sort)
- A new `learning_plans` record and associated `remediation_plans` record are created within 10 seconds of assessment completion
- Student's dashboard shows "Your learning plan has been updated" notification

### AC-4.9: Progress Report PDF Generation

**Given** an EOG Assessment is completed  
**When** the report generation job is triggered  
**Then**:
- Both student and parent PDF versions are generated within 10 seconds
- Both PDFs are stored in S3 with server-side KMS encryption
- Parent receives an email with download link within 5 minutes of assessment completion
- PDF contains all required sections per FR-17.2 (student) and FR-17.3 (parent)
- PDF file size < 5MB

### AC-4.10: Parent Dashboard — Session History Accuracy

**Given** a parent views their child's session history  
**When** the history loads  
**Then**:
- All completed sessions for the student are listed (no session missing)
- Each session shows correct: date, duration, questions answered, accuracy %, skills practiced
- Sessions are sorted newest-first
- Clicking a session opens the Session Detail view within 2 seconds
- Session detail contains full question list, student answers, and tutor conversation transcript

### AC-4.11: Teacher Dashboard — Data Restrictions

**Given** a teacher accesses the Teacher Dashboard  
**When** they view student roster data  
**Then**:
- Only students who have explicitly shared data via FR-18.8 are visible
- Student last name is not displayed (first name only)
- Student session transcripts are NOT accessible (parent-only data)
- BKT P(mastered) raw values are NOT displayed (translated to percentage bars)
- Teacher cannot access any data for non-shared students

### AC-4.12: Teacher Dashboard — CSV Export

**Given** a teacher with 5 shared students clicks "Export"  
**When** the CSV is generated  
**Then**:
- CSV is generated within 5 seconds
- CSV contains exactly 5 data rows (one per student) plus header row
- Columns match spec: first_name, overall_level, theta_score, skills_mastered_count, skills_in_progress_count, total_minutes_this_month, last_active_date, domain proficiency levels (5 columns)
- No student last name, no student ID, no email in CSV
- Export event logged in audit table

### AC-4.13: Email — Assessment Complete

**Given** a student completes the EOG Assessment  
**When** the notification job processes (within 5 minutes)  
**Then**:
- Parent receives email to their registered email address
- Email subject: "[Student Name] completed the PADI.AI End-of-Grade Assessment"
- Email body includes: proficiency level, top 3 deficient skills, link to PDF report
- Email is sent via SendGrid and `notification_log` record shows `status = 'sent'`
- No email is sent to any student email address

### AC-4.14: Email — Inactivity Alert

**Given** a student has not completed any practice sessions for 7 consecutive days  
**When** the nightly notification job runs  
**Then**:
- Parent receives inactivity alert email
- Email is sent only once per inactivity period (not repeated daily)
- Alert resets when student completes a new session
- `notification_log` record created with `notification_type = 'inactivity_alert'`

### AC-4.15: COPPA — No Student Communications

**Given** any notification trigger (assessment complete, streak, milestone, etc.)  
**When** the notification system processes the event  
**Then**:
- Zero emails are sent to addresses stored in `students` table
- Zero push notifications sent to any device if the device is linked only to a student account (no parent account on same device)
- In-app notifications stored in `student_notifications` table for display only within authenticated session
- Automated test: `student.email` field is null for all student records; email is stored only on `users` table for parent accounts

---

*End of PRD Stage 4*
