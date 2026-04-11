# PRD Stage 1: Standards Database & Diagnostic Assessment Engine
## MathPath Oregon | Version 1.0 | Target Completion: Month 3

---

## Table of Contents

1. [Overview & Objectives](#11-overview--objectives)
2. [User Personas Addressed](#12-user-personas-addressed)
3. [Functional Requirements](#13-functional-requirements)
   - FR-1: Parent Account Creation & COPPA Compliance
   - FR-2: Oregon Standards Database
   - FR-3: Question Bank (Initial Seed)
   - FR-4: Diagnostic Assessment Engine
   - FR-5: Results & Gap Analysis Display
4. [Non-Functional Requirements](#14-non-functional-requirements)
5. [Data Models](#15-data-models)
6. [API Endpoints](#16-api-endpoints)
7. [UI/UX Requirements](#17-uiux-requirements)
8. [Acceptance Criteria](#18-acceptance-criteria)

---

## 1.1 Overview & Objectives

### Stage Summary

Stage 1 establishes the foundational infrastructure of MathPath Oregon — the Oregon math standards database, the initial question bank, the COPPA-compliant parent/student account system, and the diagnostic assessment engine. Every downstream feature (personalized learning plans, adaptive practice, end-of-grade assessment, remediation) depends on the artifacts produced here: accurate knowledge of what a student currently knows and where their gaps lie.

The diagnostic assessment is the product's first impression. A new student sits down, takes a 35–45 question adaptive assessment that samples all 9 critical Grade 3 prerequisite skills and 4–5 domains of Grade 4 content, and within 60 minutes receives a structured skill-by-skill proficiency profile. That profile is both a parent-facing diagnostic report and the machine-readable BKT (Bayesian Knowledge Tracing) initial state vector that drives every subsequent adaptive decision. Accuracy here is non-negotiable: if a student's P(mastered) is initialized incorrectly, the entire learning plan will be miscalibrated.

### Business Objectives

- **Foundation readiness**: Deliver a working standards database (29 Grade 4 + 9 Grade 3 prerequisite standards), question bank (~132 seed questions), and adaptive diagnostic engine by Month 3, enabling all subsequent stages to build on a stable base.
- **COPPA/FERPA compliance from day one**: Establish verifiable parental consent, encrypted PII storage, and data deletion workflows before any student data is collected, reducing legal risk to zero for the launch cohort.
- **Diagnostic accuracy**: Achieve ≥85% agreement between MathPath diagnostic proficiency classifications and teacher-reported proficiency on a 50-student pilot cohort, validating BKT initialization quality.
- **Parent trust**: Deliver a parent dashboard that makes the diagnostic results legible and actionable within 5 minutes of assessment completion, establishing the product's credibility with the primary paying customer.
- **Platform scalability baseline**: Infrastructure must support 1,000 concurrent assessment sessions from day one, accommodating initial school-district pilots without degradation.

### Success Criteria (Measurable)

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Diagnostic completion rate | ≥80% of started assessments completed | Assessment completion events in DB |
| Diagnostic accuracy vs. teacher report | ≥85% agreement on Below/On/Above Par | Pilot teacher survey (n=50) |
| Parent account creation → consent completion | ≥90% funnel conversion | Funnel analytics |
| Page load time (assessment screen) | <2 seconds (p95) | Synthetic monitoring |
| Question transition latency | <500ms (p95) | Client-side timing |
| COPPA audit pass | 100% | Legal review checklist |
| Seed question bank ready | 132+ validated questions | DB count + validation flag |
| Standards database completeness | All 38 standards seeded (29 G4 + 9 G3) | DB integrity check |
| Uptime during pilot | ≥99.5% | AWS/GCP monitoring |
| Accessibility audit | WCAG 2.1 AA pass | axe-core automated scan + manual audit |

### Out of Scope for Stage 1

- Personalized learning plan generation (Stage 2)
- Adaptive practice sessions beyond the diagnostic (Stage 3)
- AI-powered tutoring/explanations (Stage 4)
- Teacher accounts and classroom dashboards (Stage 5)
- End-of-grade summative assessment (Stage 6)
- Question generation via LLM (Stage 2)
- Real-time multiplayer or social features
- Native iOS/Android apps (web only)
- Payment/subscription management
- Push notifications (email only)

---

## 1.2 User Personas Addressed

### Persona 1: Parent (Account Creator)
**Name**: Maria, 38, Portland OR  
**Context**: Mother of 9-year-old Jayden, who is entering 4th grade. Maria is concerned that Jayden struggled with multiplication facts in 3rd grade and wants to understand where he stands before the school year begins. She is comfortable with smartphones and tablets but not a technical user.  
**Goals**: Create an account quickly; understand what the diagnostic measures; trust that her child's data is safe; receive a clear, plain-language report of results; understand what MathPath will do to help Jayden close gaps.  
**Pain points**: COPPA consent flows that are too long or confusing; results reports that use jargon without explanation; unclear data privacy policies; apps that feel designed for teachers, not parents.  
**Device context**: iPhone 15 or iPad (primary); Mac laptop (secondary).  
**Stage 1 touchpoints**: Registration, consent flow, child profile creation, parent results dashboard, PDF export.

### Persona 2: Student (Diagnostic Taker)
**Name**: Jayden, 9, 4th grade (or entering 4th grade)  
**Context**: Average 4th grader with a mixed math background. Comfortable with tablets. Has a short attention span for anything that feels like a test. Responds well to encouraging language and visual progress cues.  
**Goals**: Get through the assessment without frustration; feel like the app is on his side, not judging him; have questions that make sense without overly complicated language.  
**Pain points**: Small text; confusing fraction input UI; feeling "stuck" without hints; long unbroken sequences of hard questions; feeling like he's failing.  
**Device context**: iPad (classroom and home); Chromebook (school-provided).  
**Stage 1 touchpoints**: Student login (via parent account), diagnostic landing screen, assessment questions, progress indicator, completion screen, student-facing results summary.

### Persona 3: Teacher (Future — Not In Scope Stage 1)
**Name**: Ms. Chen, 4th grade teacher, Beaverton School District  
**Context**: Will be onboarded in Stage 5. In Stage 1, teacher name is an optional field in the child profile (collected for future use) but teachers have no login access and no dashboard.  
**Stage 1 involvement**: Name only, stored as string in student profile. No authentication, no data access.

---

## 1.3 Functional Requirements

---

### FR-1: Parent Account Creation & COPPA Compliance

**FR-1.1 — Parent Email Registration**

- The registration form SHALL collect: legal first name, legal last name, email address, password (with confirmation), and country/state (pre-filled to Oregon).
- The email address SHALL be the primary account identifier. Duplicate emails SHALL be rejected with the message: "An account with this email already exists. [Sign in instead?]"
- Upon form submission, the system SHALL send a verification email to the provided address within 60 seconds containing a single-use verification link (JWT, 24-hour expiry, signed with RS256).
- Verification links SHALL be single-use: clicking a link marks it consumed; subsequent clicks return HTTP 410 Gone with an option to resend.
- Until email is verified, the parent account status is `PENDING_VERIFICATION`. No child profile can be created and no diagnostic can be started from this account.
- If email is not verified within 24 hours, the account status becomes `VERIFICATION_EXPIRED`. The parent can request a new verification email which issues a fresh 24-hour link.
- The registration page SHALL clearly indicate (above the fold, before form submission) that this service is for children under 13 and that parental consent is required by law.

**FR-1.2 — Verifiable Parental Consent (COPPA)**

- Upon email verification, the parent SHALL be directed to a multi-step COPPA consent flow before any child profile can be created.
- The consent flow SHALL comply with COPPA 16 CFR Part 312 "verifiable parental consent" requirements. Initial launch SHALL use the "email plus" method: (1) consent form with privacy policy displayed in full, (2) confirmation email sent to parent email requiring a click to confirm, (3) 24-hour window for revocation after confirmation.
- The consent form SHALL display:
  - What personal data is collected about children (name, grade, school district, assessment responses, skill states, session data)
  - How data is used (personalized learning, progress tracking, service improvement — never sold to third parties)
  - Who has access to the data (parent, student, future: teacher with parent consent, platform operators)
  - Data retention policy (data retained while account is active; deleted within 30 days of deletion request)
  - Contact information for privacy inquiries (privacy@mathpath.org)
  - Full link to Privacy Policy and Terms of Service
- The parent SHALL explicitly check two separate checkboxes: (1) "I have read and agree to the Privacy Policy" and (2) "I provide verifiable parental consent for my child to use MathPath Oregon"
- Checkboxes SHALL NOT be pre-checked.
- Consent SHALL be timestamped with ISO 8601 UTC timestamp, IP address (hashed), user agent string, and stored in the `consent_records` table.
- The system SHALL store consent records indefinitely (not subject to deletion with account deletion) per legal requirements.
- If a parent declines consent, the account SHALL be moved to `CONSENT_DECLINED` status. The parent can revisit the consent flow at any time.

**FR-1.3 — Child Profile Creation**

- After consent completion, the parent SHALL be prompted to create their first child profile.
- Required fields: child's first name (display name only — no last name required), grade level (pre-set to Grade 4 for initial launch, with Grade 3–6 available for future), date of birth (month/year only, used to verify grade-appropriateness, not stored as PII after age calculation).
- Optional fields: school district (dropdown of Oregon school districts), teacher's name (free text, 100 char max).
- One parent account SHALL support up to 5 child profiles (siblings).
- Each child profile SHALL have a unique `student_id` (UUIDv4).
- Child display names SHALL be stripped of any characters that could appear in SQL injection or XSS attacks (sanitized server-side).
- The system SHALL NOT display the child's full name anywhere in the student-facing UI — only a first name or nickname.
- Child profile avatar: parent selects from a set of 12 pre-built animal avatars (no uploaded photos). Avatar selection is cosmetic only.

**FR-1.4 — Privacy Policy Acceptance**

- Privacy Policy and Terms of Service SHALL be versioned (e.g., v1.0, effective date).
- The system SHALL track which version of the Privacy Policy and ToS was accepted by each parent at the time of acceptance.
- If the Privacy Policy is materially updated, existing parents SHALL be prompted to re-accept on next login before accessing the dashboard. Access is gated until re-acceptance.
- A human-readable summary ("plain language privacy notice") SHALL appear on the consent screen before the full policy text.

**FR-1.5 — Parent Account Dashboard**

- After login, the parent lands on a dashboard showing: (a) all child profiles with their diagnostic status, (b) quick action buttons ("Start Diagnostic", "View Results", "Manage Account"), (c) notification badge for any unread results or system messages.
- The dashboard SHALL display for each child: name, grade, avatar, diagnostic status (Not Started / In Progress / Completed), and if completed: overall proficiency level (Below Par / On Par / Above Par) with last-updated date.
- For children with completed diagnostics, a "View Full Report" button SHALL navigate to the parent results screen (FR-5.2).

**FR-1.6 — Data Deletion Request**

- A "Delete My Account" option SHALL be accessible from Account Settings.
- Clicking "Delete My Account" SHALL require the parent to type "DELETE" in a confirmation field and re-enter their password.
- Upon confirmation, the system SHALL:
  - Mark all child profiles as `DELETED`
  - Queue all student data (assessment responses, skill states, session data, learning plan data) for deletion within 30 days per COPPA
  - Retain consent records permanently (legal requirement)
  - Retain anonymized, non-re-identifiable aggregate statistics (total questions answered, etc.)
  - Send a confirmation email to the parent with deletion confirmation and a reference number
- The parent SHALL be able to request deletion of a single child's data without deleting the entire account.
- An in-app data export SHALL be available before deletion: generates a ZIP containing the child's diagnostic results, skill states, and learning history in JSON and PDF formats.

**FR-1.7 — Password Requirements**

- Minimum 8 characters, maximum 128 characters.
- Must contain at least one uppercase letter, one lowercase letter, one digit.
- SHALL be hashed using bcrypt (cost factor 12) before storage. Plaintext passwords SHALL never be logged or stored.
- Password reset: email link (JWT, 15-minute expiry, single-use). Link invalidated immediately after use or expiry.
- The system SHALL check passwords against the HaveIBeenPwned API (k-anonymity model) and warn users if their password appears in known breaches, without blocking account creation.
- Account SHALL be temporarily locked after 5 consecutive failed login attempts; unlocked after 15 minutes or via email.

**FR-1.8 — Session Management**

- JWT access tokens: 15-minute expiry.
- Refresh tokens: 7-day expiry, HTTP-only cookie, SameSite=Strict.
- Refresh token rotation: a new refresh token is issued on each use; the previous one is invalidated.
- Student sessions (child taking the diagnostic) are scoped to a separate session context from the parent session. When a parent "starts" a diagnostic for a child, a child session token is issued that is scoped only to the assessment flow — it cannot access account settings, billing, or other children's data.
- Session inactivity timeout: 30 minutes for parent; 60 minutes for student during active assessment (to prevent loss of progress).
- All active sessions are tracked in Redis with the ability to invalidate all sessions for a user (used by account deletion flow).

---

### FR-2: Oregon Standards Database

**FR-2.1 — Database Schema for Standards**

The `standards` table SHALL store all academic standards with the following fields:

```sql
CREATE TABLE standards (
    standard_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grade           SMALLINT NOT NULL,           -- 3 or 4
    domain          VARCHAR(10) NOT NULL,         -- e.g. '4.OA', '4.NBT'
    cluster         VARCHAR(255) NOT NULL,        -- cluster heading text
    code            VARCHAR(20) UNIQUE NOT NULL,  -- e.g. '4.OA.A.1'
    description     TEXT NOT NULL,               -- full standard text
    dok_level       SMALLINT NOT NULL CHECK (dok_level BETWEEN 1 AND 4),
    strand          VARCHAR(50),                 -- e.g. 'Operations & Algebraic Thinking'
    is_prerequisite BOOLEAN NOT NULL DEFAULT FALSE, -- TRUE for G3 prerequisite standards
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    version_tag     VARCHAR(20) NOT NULL DEFAULT 'OAS-2023',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_standards_grade ON standards(grade);
CREATE INDEX idx_standards_domain ON standards(domain);
CREATE INDEX idx_standards_code ON standards(code);
```

**FR-2.2 — Full Seed Data: Grade 4 Oregon Standards (29 Standards)**

*Domain 4.OA — Operations & Algebraic Thinking (4 standards)*

| code | cluster | description | DOK |
|------|---------|-------------|-----|
| 4.OA.A.1 | Use the four operations with whole numbers to solve problems | Interpret a multiplication equation as a comparison, e.g., interpret 35 = 5 × 7 as a statement that 35 is 5 times as many as 7 and 7 times as many as 5. Represent verbal statements of multiplicative comparisons as multiplication equations. | 2 |
| 4.OA.A.2 | Use the four operations with whole numbers to solve problems | Multiply or divide to solve word problems involving multiplicative comparison, e.g., by using drawings and equations with a symbol for the unknown number to represent the problem, distinguishing multiplicative comparison from additive comparison. | 2 |
| 4.OA.A.3 | Use the four operations with whole numbers to solve problems | Solve multistep word problems posed with whole numbers and having whole-number answers using the four operations, including problems in which remainders must be interpreted. Represent these problems using equations with a letter standing for the unknown quantity. Assess the reasonableness of answers using mental computation and estimation strategies including rounding. | 3 |
| 4.OA.B.4 | Gain familiarity with factors and multiples | Find all factor pairs for a whole number in the range 1–100. Recognize that a whole number is a multiple of each of its factors. Determine whether a given whole number in the range 1–100 is a multiple of a given one-digit number. Determine whether a given whole number in the range 1–100 is prime or composite. | 2 |
| 4.OA.C.5 | Generate and analyze patterns | Generate a number or shape pattern that follows a given rule. Identify apparent features of the pattern that were not explicit in the rule itself. | 3 |

*Domain 4.NBT — Number & Operations in Base Ten (6 standards)*

| code | cluster | description | DOK |
|------|---------|-------------|-----|
| 4.NBT.A.1 | Generalize place value understanding for multi-digit whole numbers | Recognize that in a multi-digit whole number, a digit in one place represents ten times what it represents in the place to its right. | 1 |
| 4.NBT.A.2 | Generalize place value understanding for multi-digit whole numbers | Read and write multi-digit whole numbers using base-ten numerals, number names, and expanded form. Compare two multi-digit numbers based on meanings of the digits in each place, using >, =, and < symbols to record the results of comparisons. | 1 |
| 4.NBT.A.3 | Generalize place value understanding for multi-digit whole numbers | Use place value understanding to round multi-digit whole numbers to any place. | 2 |
| 4.NBT.B.4 | Use place value understanding and properties of operations to perform multi-digit arithmetic | Fluently add and subtract multi-digit whole numbers using the standard algorithm. | 1 |
| 4.NBT.B.5 | Use place value understanding and properties of operations to perform multi-digit arithmetic | Multiply a whole number of up to four digits by a one-digit whole number, and multiply two two-digit numbers, using strategies based on place value and the properties of operations. Illustrate and explain the calculation by using equations, rectangular arrays, and/or area models. | 2 |
| 4.NBT.B.6 | Use place value understanding and properties of operations to perform multi-digit arithmetic | Find whole-number quotients and remainders with up to four-digit dividends and one-digit divisors, using strategies based on place value, the properties of operations, and/or the relationship between multiplication and division. Illustrate and explain the calculation by using equations, rectangular arrays, and/or area models. | 2 |

*Domain 4.NF — Number & Operations — Fractions (7 standards)*

| code | cluster | description | DOK |
|------|---------|-------------|-----|
| 4.NF.A.1 | Extend understanding of fraction equivalence and ordering | Explain why a fraction a/b is equivalent to a fraction (n×a)/(n×b) by using visual fraction models, with attention to how the number and size of the parts differ even though the two fractions themselves are the same size. Use this principle to recognize and generate equivalent fractions. | 2 |
| 4.NF.A.2 | Extend understanding of fraction equivalence and ordering | Compare two fractions with different numerators and different denominators, e.g., by creating common denominators or numerators, or by comparing to a benchmark fraction such as 1/2. Recognize that comparisons are valid only when the two fractions refer to the same whole. Record the results of comparisons with symbols >, =, or <, and justify the conclusions, e.g., by using a visual fraction model. | 2 |
| 4.NF.B.3 | Build fractions from unit fractions | Understand a fraction a/b with a > 1 as a sum of fractions 1/b. (a) Understand addition and subtraction of fractions as joining and separating parts referring to the same whole. (b) Decompose a fraction into a sum of fractions with the same denominator in more than one way. (c) Add and subtract mixed numbers with like denominators, e.g., by replacing each mixed number with an equivalent fraction. (d) Solve word problems involving addition and subtraction of fractions referring to the same whole and having like denominators. | 2 |
| 4.NF.B.4 | Build fractions from unit fractions | Apply and extend previous understandings of multiplication to multiply a fraction by a whole number. (a) Understand a fraction a/b as a multiple of 1/b. (b) Understand a multiple of a/b as a multiple of 1/b. (c) Solve word problems involving multiplication of a fraction by a whole number. | 2 |
| 4.NF.C.5 | Understand decimal notation for fractions, and compare decimal fractions | Express a fraction with denominator 10 as an equivalent fraction with denominator 100, and use this technique to add two fractions with respective denominators 10 and 100. | 2 |
| 4.NF.C.6 | Understand decimal notation for fractions, and compare decimal fractions | Use decimal notation for fractions with denominators 10 or 100. | 1 |
| 4.NF.C.7 | Understand decimal notation for fractions, and compare decimal fractions | Compare two decimals to hundredths by reasoning about their size. Recognize that comparisons are valid only when the two decimals refer to the same whole. Record the results of comparisons with the symbols >, =, or <, and justify the conclusions, e.g., by using a visual model. | 2 |

*Domain 4.GM — Geometry & Measurement (9 standards)*

| code | cluster | description | DOK |
|------|---------|-------------|-----|
| 4.GM.A.1 | Draw and identify lines and angles, and classify shapes by properties of their lines and angles | Draw points, lines, line segments, rays, angles (right, acute, obtuse), and perpendicular and parallel lines. Identify these in two-dimensional figures. | 1 |
| 4.GM.A.2 | Draw and identify lines and angles, and classify shapes by properties of their lines and angles | Classify two-dimensional figures based on the presence or absence of parallel or perpendicular lines, or the presence or absence of angles of a specified size. Recognize right triangles as a category, and identify right triangles. | 2 |
| 4.GM.A.3 | Draw and identify lines and angles, and classify shapes by properties of their lines and angles | Recognize a line of symmetry for a two-dimensional figure as a line across the figure such that the figure can be folded along the line into matching parts. Identify line-symmetric figures and draw lines of symmetry. | 2 |
| 4.GM.B.4 | Measure and convert measurements within a given measurement system | Know relative sizes of measurement units within one system of units including km, m, cm; kg, g; lb, oz.; l, ml; hr, min, sec. Within a single system of measurement, express measurements in a larger unit in terms of a smaller unit. Record measurement equivalents in a two-column table. | 2 |
| 4.GM.B.5 | Measure and convert measurements within a given measurement system | Use the four operations to solve word problems involving distances, intervals of time, liquid volumes, masses of objects, and money, including problems involving simple fractions or decimals, and problems that require expressing measurements given in a larger unit in terms of a smaller unit. Represent measurement quantities using diagrams such as number line diagrams that feature a measurement scale. | 3 |
| 4.GM.C.6 | Geometric measurement: understand concepts of angle and measure angles | Recognize angles as geometric shapes that are formed wherever two rays share a common endpoint, and understand concepts of angle measurement. | 1 |
| 4.GM.C.7 | Geometric measurement: understand concepts of angle and measure angles | Measure angles in whole-number degrees using a protractor. Sketch angles of specified measure. | 1 |
| 4.GM.C.8 | Geometric measurement: understand concepts of angle and measure angles | Recognize angle measure as additive. When an angle is decomposed into non-overlapping parts, the angle measure of the whole is the sum of the angle measures of the parts. Solve addition and subtraction problems to find unknown angles on a diagram in real world and mathematical problems. | 2 |
| 4.GM.D.9 | Solve real-world and mathematical problems involving perimeter and area | Apply the area and perimeter formulas for rectangles in real-world and mathematical problems. | 2 |

*Domain 4.DR — Data Reasoning (3 standards)*

| code | cluster | description | DOK |
|------|---------|-------------|-----|
| 4.DR.A.1 | Represent and interpret data | Make a line plot to display a data set of measurements in fractions of a unit (1/2, 1/4, 1/8). Solve problems involving addition and subtraction of fractions by using information presented in line plots. | 2 |
| 4.DR.B.2 | Represent and interpret data | Collect, organize, display, and interpret data in bar graphs, line plots, and frequency tables. Formulate questions that can be addressed with data and make observations from the data displayed. | 2 |
| 4.DR.C.3 | Represent and interpret data | Understand that data can vary, and use statistical measures (mean, median, mode, range) to describe data sets. | 2 |

**FR-2.3 — Full Seed Data: Grade 3 Prerequisite Standards (9 Standards)**

These 9 standards are the critical prerequisite skills that MathPath Oregon targets for remediation. They represent skills a student should have mastered exiting Grade 3.

| code | domain | description | DOK |
|------|--------|-------------|-----|
| 3.OA.A.4 | 3.OA | Determine the unknown whole number in a multiplication or division equation relating three whole numbers. | 1 |
| 3.OA.C.7 | 3.OA | Fluently multiply and divide within 100, using strategies such as the relationship between multiplication and division or properties of operations. By the end of Grade 3, know from memory all products of two one-digit numbers. | 1 |
| 3.OA.D.8 | 3.OA | Solve two-step word problems using the four operations. Represent these problems using equations with a letter standing for the unknown quantity. Assess the reasonableness of answers using mental computation and estimation strategies including rounding. | 3 |
| 3.NBT.A.2 | 3.NBT | Fluently add and subtract within 1000 using strategies and algorithms based on place value, properties of operations, and/or the relationship between addition and subtraction. | 1 |
| 3.NBT.A.3 | 3.NBT | Multiply one-digit whole numbers by multiples of 10 in the range 10–90 using strategies based on place value and properties of operations. | 1 |
| 3.NF.A.1 | 3.NF | Understand a fraction 1/b as the quantity formed by 1 part when a whole is partitioned into b equal parts; understand a fraction a/b as the quantity formed by a parts of size 1/b. | 2 |
| 3.NF.A.3 | 3.NF | Explain equivalence of fractions in special cases, and compare fractions by reasoning about their size. | 2 |
| 3.GM.C.7 | 3.GM | Relate area to the operations of multiplication and addition. Find the area of a rectangle with whole-number side lengths by tiling it, and show that the area is the same as would be found by multiplying the side lengths. | 2 |
| 3.GM.D.8 | 3.GM | Solve real-world and mathematical problems involving perimeters of polygons, including finding the perimeter given the side lengths, finding an unknown side length, and exhibiting rectangles with the same perimeter and different areas or with the same area and different perimeters. | 2 |

**FR-2.4 — Prerequisite Relationship Graph**

The `prerequisite_relationships` table SHALL store directed edges in the skill dependency graph. Edge direction: `(prerequisite_standard_id) → (dependent_standard_id)` means "you must have mastered the prerequisite before tackling the dependent standard."

Critical edges (complete list):

```
3.OA.C.7  → 4.OA.A.1   (multiplication facts needed for multiplicative comparison)
3.OA.C.7  → 4.OA.A.2   (multiplication facts needed for multiplicative word problems)
3.OA.C.7  → 4.NBT.B.5  (multiplication facts needed for multi-digit multiplication)
3.OA.C.7  → 4.NBT.B.6  (multiplication facts needed for long division)
3.OA.C.7  → 4.NF.B.4   (multiplication needed for fraction × whole number)
3.OA.A.4  → 4.OA.A.2   (unknown in equation concept carries forward)
3.OA.D.8  → 4.OA.A.3   (two-step problems prerequisite for multi-step)
3.NBT.A.2 → 4.NBT.B.4  (add/sub within 1000 prerequisite for standard algorithm)
3.NBT.A.3 → 4.NBT.B.5  (multiples of 10 prerequisite for multi-digit multiplication)
3.NBT.A.2 → 4.NBT.A.2  (understanding of place value carries forward)
4.NBT.A.1 → 4.NBT.A.2  (place value recognition before read/write)
4.NBT.A.2 → 4.NBT.A.3  (read/write before rounding)
4.NBT.B.4 → 4.OA.A.3   (add/sub fluency needed for multi-step problems)
4.NBT.B.5 → 4.OA.A.3   (multiplication fluency needed for multi-step)
3.NF.A.1  → 4.NF.A.1   (basic fraction understanding before equivalence)
3.NF.A.1  → 4.NF.B.3   (unit fractions before adding fractions)
3.NF.A.3  → 4.NF.A.2   (fraction comparison before cross-denominator comparison)
4.NF.A.1  → 4.NF.A.2   (equivalence needed for comparison with unlike denominators)
4.NF.A.1  → 4.NF.B.3   (equivalence needed for add/sub fractions)
4.NF.A.1  → 4.NF.C.5   (equivalence needed for decimal fractions)
4.NF.B.3  → 4.NF.B.4   (add fractions before multiply fraction by whole)
4.NF.C.5  → 4.NF.C.6   (tenths/hundredths equivalence before decimal notation)
4.NF.C.6  → 4.NF.C.7   (decimal notation before decimal comparison)
3.GM.C.7  → 4.GM.D.9   (area concept prerequisite for area formula application)
3.GM.D.8  → 4.GM.D.9   (perimeter prerequisite for combined area/perimeter problems)
4.GM.A.1  → 4.GM.A.2   (identify angles/lines before classify shapes)
4.GM.A.2  → 4.GM.A.3   (classify shapes before symmetry)
4.GM.C.6  → 4.GM.C.7   (angle concept before measuring angles)
4.GM.C.7  → 4.GM.C.8   (measuring angles before additive angle problems)
```

**FR-2.5 — DOK Level Tagging**

Every standard in the database SHALL have a `dok_level` field set according to Webb's Depth of Knowledge framework:
- DOK 1: Recall and Reproduction (e.g., multiplication facts, place value recognition)
- DOK 2: Skills and Concepts (e.g., apply algorithm, compare fractions, interpret equation)
- DOK 3: Strategic Thinking (e.g., multi-step problems, justify reasoning, pattern analysis)
- DOK 4: Extended Thinking (not used in diagnostic; reserved for enrichment)

The DOK assignments in FR-2.2 and FR-2.3 above SHALL be the canonical values at launch.

**FR-2.6 — Admin Interface for Standards Management**

- A password-protected admin panel (`/admin`) SHALL provide CRUD operations on the standards table.
- Admin users are identified by the `role = 'admin'` field in the `users` table; admin role is granted manually by a platform operator (no self-service admin creation).
- The admin standards editor SHALL include: code, description, domain, cluster, grade, DOK level, active/inactive toggle, version tag.
- Changes to standards SHALL require a second admin to approve (two-person rule) before being published to the live database.
- Deactivating a standard does not delete it; it sets `is_active = FALSE` and hides it from student-facing flows while preserving historical data.

**FR-2.7 — Standards Versioning**

- Each standard record SHALL include a `version_tag` field (e.g., `OAS-2023`, `OAS-2025`).
- When Oregon updates its standards, new versions SHALL be inserted as new rows (not overwrites), with the old version's `is_active` set to FALSE.
- Questions in the question bank SHALL reference `standard_code` (the code string), not `standard_id`, to survive version transitions gracefully. On a version update, questions retain their `standard_code` association and are re-linked to the new active version.
- A migration script template SHALL be provided for future standard updates.

**FR-2.8 — API Endpoints for Standards**

See Section 1.6 (API Endpoints) for full specifications. At minimum:
- `GET /api/v1/standards` — list all active standards, filterable by grade, domain
- `GET /api/v1/standards/:code` — get single standard by code
- `GET /api/v1/standards/prerequisites/:code` — get prerequisite standards for a given code
- `GET /api/v1/standards/dependents/:code` — get standards that depend on a given code

**FR-2.9 — Search and Filter**

- Standards SHALL be searchable by: domain, grade, cluster, description text (full-text search using PostgreSQL `tsvector`), DOK level, and `is_prerequisite` flag.
- The admin UI SHALL expose these filters as dropdown/checkbox inputs with live results.
- The API `GET /api/v1/standards` endpoint SHALL accept query parameters: `grade`, `domain`, `dok_level`, `is_prerequisite`, `q` (full-text), `include_inactive`.

**FR-2.10 — Change Audit Log**

- All changes to the `standards` table SHALL be recorded in a `standards_audit_log` table with: `change_id`, `standard_id`, `changed_by` (admin user_id), `change_type` (INSERT/UPDATE/DELETE), `old_values` (JSONB), `new_values` (JSONB), `changed_at` (TIMESTAMPTZ), `change_reason` (text, required).
- The audit log is append-only and not deletable by admin users. Deletion requires direct database access by a platform operator.

---

### FR-3: Question Bank (Initial Seed)

**FR-3.1 — Question Schema**

```sql
CREATE TABLE questions (
    question_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_code       VARCHAR(20) NOT NULL REFERENCES standards(code),
    question_type       VARCHAR(30) NOT NULL CHECK (question_type IN (
                            'multiple_choice', 'short_numeric', 'fill_blank', 'fraction_input'
                        )),
    question_text       TEXT NOT NULL,           -- may contain KaTeX markup
    answer_options      JSONB,                   -- [{id: 'A', text: '...', is_correct: bool}, ...]
    correct_answer      TEXT NOT NULL,           -- for MC: option_id; for numeric: value as string
    correct_answer_alt  TEXT[],                  -- alternate acceptable answers (e.g. '0.5' and '1/2')
    solution_steps      JSONB NOT NULL,          -- [{step: 1, text: '...', hint: bool}, ...]
    difficulty_level    SMALLINT NOT NULL CHECK (difficulty_level BETWEEN 1 AND 5),
    dok_level           SMALLINT NOT NULL CHECK (dok_level BETWEEN 1 AND 4),
    context_type        VARCHAR(30) NOT NULL CHECK (context_type IN (
                            'word_problem', 'computation', 'visual', 'mixed'
                        )),
    is_prerequisite     BOOLEAN NOT NULL DEFAULT FALSE,
    tags                TEXT[] DEFAULT '{}',
    source              VARCHAR(100) NOT NULL,   -- 'seed_v1', 'llm_generated', 'human_authored'
    validated_by        VARCHAR(100),            -- reviewer name or 'automated'
    validation_date     DATE,
    is_validated        BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    has_image           BOOLEAN NOT NULL DEFAULT FALSE,
    image_url           TEXT,                    -- S3 URL if applicable
    numeric_tolerance   DECIMAL(10,6),           -- acceptable error margin for numeric answers
    times_used          INTEGER NOT NULL DEFAULT 0,
    avg_correct_rate    DECIMAL(5,4),            -- updated by cron job from response data
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_questions_standard_code ON questions(standard_code);
CREATE INDEX idx_questions_difficulty ON questions(difficulty_level);
CREATE INDEX idx_questions_type ON questions(question_type);
CREATE INDEX idx_questions_is_validated ON questions(is_validated);
CREATE INDEX idx_questions_is_active ON questions(is_active);
```

**FR-3.2 — Question Types**

*Multiple Choice (question_type = 'multiple_choice')*:
- Exactly 4 answer options (A, B, C, D).
- Options stored in `answer_options` JSONB array: `[{"id": "A", "text": "16", "is_correct": false}, ...]`
- Exactly one option SHALL have `is_correct: true`.
- Options SHALL be displayed in randomized order per student session (randomization seed stored in `assessment_questions` to enable replay/review).
- Option text may contain KaTeX for mathematical expressions.

*Short Numeric Answer (question_type = 'short_numeric')*:
- Student inputs a number via on-screen numeric keypad.
- `correct_answer` stores the canonical numeric string (e.g., "48", "3.75").
- `correct_answer_alt` stores acceptable equivalent forms (e.g., ["3 3/4", "3.750"]).
- `numeric_tolerance` stores acceptable floating-point error (default: 0 for whole numbers; 0.001 for decimals).
- Leading/trailing zeros and equivalent decimal representations SHALL be accepted.

*Fill-in-the-Blank (question_type = 'fill_blank')*:
- Question text contains `____` placeholder which renders as an input field.
- Accepts text input (for non-numeric blanks, e.g., unit names) or numeric input.
- Case-insensitive string matching for text answers.

*Fraction Input (question_type = 'fraction_input')*:
- Separate numerator and denominator input fields rendered as a visual fraction.
- Reduced and non-reduced equivalent fractions SHALL both be accepted (e.g., 2/4 = 1/2).
- Mixed number format also accepted (e.g., "1 1/2" equivalent to "3/2").

**FR-3.3 — Minimum Question Counts**

| Category | Count | Total |
|----------|-------|-------|
| Grade 3 prerequisite skills (9 × 5 min) | 5 per skill | 45 minimum |
| Grade 4 standards (29 × 3 min) | 3 per standard | 87 minimum |
| Buffer / additional coverage | — | 10+ |
| **Seed bank total** | | **142 minimum** |

Distribution within each standard:
- At least 1 question at difficulty levels 2, 3, and 4.
- No more than 2 questions at difficulty level 1 (recall only) per standard.
- At least 1 word problem context per standard with ≥3 questions.
- At least 1 computation context per standard with ≥2 questions.

**FR-3.4 — Difficulty Distribution**

Difficulty levels map as follows:

| Level | Description | BKT Usage |
|-------|-------------|-----------|
| 1 | Pure recall; single-step; no context | Diagnostic initialization only |
| 2 | Skill application; one or two steps; familiar context | Standard CAT lower range |
| 3 | Moderate complexity; multi-step or unfamiliar context | Standard CAT midpoint |
| 4 | Complex application; multi-step word problem; requires strategic thinking | CAT upper range |
| 5 | Extended challenge; multi-standard, DOK 3–4 | Acceleration track only |

**FR-3.5 — Math Rendering (KaTeX)**

- All question text and answer options SHALL support KaTeX syntax for inline and display math.
- KaTeX SHALL be rendered client-side using the `katex` npm package (version ≥0.16.0).
- KaTeX SHALL render synchronously on question display (no flash of unrendered text).
- Supported constructs: fractions (`\frac{a}{b}`), mixed numbers, division (`\div`), multiplication (`\times`), square roots, exponents, inequality symbols (`>`, `<`, `\geq`, `\leq`), number lines (via SVG with embedded KaTeX labels), and place value charts.
- KaTeX SHALL be tested on Chrome, Safari (iOS), and Firefox with no rendering regressions.
- Server-side KaTeX rendering (via `katex` Node module) SHALL be used for PDF generation of results reports.

**FR-3.6 — Image/Visual Support**

- Questions with `has_image = TRUE` reference an `image_url` pointing to a CloudFront-served S3 object.
- All images SHALL be PNG format, minimum 800×600px, maximum 1200×900px, white background.
- Images SHALL have descriptive alt text stored in a separate `image_alt_text` column (added to schema in FR-3.1 above; included in migration).
- Geometry questions (4.GM domain) MAY include visual figures (angles, shapes, protractors, number lines).
- Images are required for: all protractor questions (4.GM.C.7), all symmetry questions (4.GM.A.3), all line/angle identification questions (4.GM.A.1), and any word problem referencing a diagram.
- Images SHALL NOT be required for computation or pure symbolic questions.

**FR-3.7 — Correct Answer Validation**

- Server-side answer validation SHALL be performed for all question types.
- Client-side answer validation provides immediate feedback but is NOT authoritative (prevents simple cheating via DevTools).
- For numeric answers: Python `decimal.Decimal` comparison with tolerance from `numeric_tolerance` field.
- For fraction answers: reduce both student answer and correct answer to lowest terms before comparison.
- For multiple choice: exact match on option `id` string.
- For fill-blank text: lowercase strip + normalize whitespace before comparison.
- Answer correctness is stored as a boolean in `assessment_responses.is_correct`.
- All submissions are stored regardless of correctness (for BKT update).

**FR-3.8 — Distractor Quality for Multiple Choice**

- Each wrong answer (distractor) SHALL correspond to a documented common misconception for that standard.
- Required distractor types for computation questions:
  - "Off by one operation" error (e.g., adding instead of multiplying)
  - "Place value error" (e.g., computing 3×4=12 but writing 120 instead of 12)
  - "Procedural slip" (e.g., forgetting to carry)
  - "Plausible but wrong" (ballpark number that doesn't correspond to any clean error type)
- Distractor documentation SHALL be stored as a JSON comment in the question seed file (not in the production database, to avoid leaking hints).
- Questions with weak distractors (avg_correct_rate > 0.92 from response data) SHALL be flagged for review by the admin question management UI.

**FR-3.9 — Human Review Workflow**

- All seed questions SHALL be reviewed by at least one qualified math educator (Oregon-licensed teacher, grades 3–6) before going live.
- The review workflow:
  1. Question author creates question, sets `is_validated = FALSE`.
  2. Question appears in admin "Pending Review" queue.
  3. Reviewer opens question, checks: grade-appropriateness, mathematical accuracy, standard alignment, distractor quality, language clarity, and absence of bias.
  4. Reviewer marks approved (`is_validated = TRUE`, sets `validated_by` and `validation_date`) or rejected (adds rejection note, question remains in queue for revision).
  5. Only validated questions (`is_validated = TRUE`) are eligible for inclusion in diagnostic assessments.
- The minimum standard for launch is 100% of seed questions validated.

**FR-3.10 — Bulk Import via JSON/CSV**

The question bank SHALL support bulk import via a JSON file with the following structure:

```json
{
  "schema_version": "1.0",
  "questions": [
    {
      "standard_code": "3.OA.C.7",
      "question_type": "multiple_choice",
      "question_text": "What is \\(8 \\times 7\\)?",
      "answer_options": [
        {"id": "A", "text": "54", "is_correct": false},
        {"id": "B", "text": "56", "is_correct": true},
        {"id": "C", "text": "63", "is_correct": false},
        {"id": "D", "text": "48", "is_correct": false}
      ],
      "correct_answer": "B",
      "solution_steps": [
        {"step": 1, "text": "Recall that \\(8 \\times 7 = 56\\).", "hint": false}
      ],
      "difficulty_level": 1,
      "dok_level": 1,
      "context_type": "computation",
      "is_prerequisite": true,
      "tags": ["multiplication_facts", "fluency"],
      "source": "seed_v1"
    }
  ]
}
```

- The bulk import endpoint (`POST /api/v1/admin/questions/import`) SHALL validate all fields against the schema before inserting any records (transactional: all-or-nothing).
- Import validation SHALL report line-by-line errors if any question fails validation, with the specific field and error message.
- CSV import SHALL use the same field names as JSON, with array fields (tags, answer_options) serialized as JSON strings within CSV cells.

**FR-3.11 — Question Tagging System**

Tags are free-text strings stored in the `tags` TEXT[] column. Standard tags defined at launch:

| Tag | Description |
|-----|-------------|
| `multiplication_facts` | Times table fluency questions |
| `word_problem` | Requires reading comprehension |
| `fraction_visual` | Requires fraction model/diagram |
| `place_value` | Involves place value reasoning |
| `estimation` | Involves rounding or estimation |
| `two_step` | Requires two operations |
| `oregon_context` | Uses Oregon-specific geography/culture |
| `real_world` | Applied/contextual problem |
| `computation` | Pure symbolic computation, no context |
| `prerequisite` | Grade 3 prerequisite skill question |

Additional tags may be added by admin users. Tags are indexed via GIN index on the `tags` column for efficient filtering.

**FR-3.12 — Admin Question Management UI**

The admin panel SHALL include a question management interface with:
- Paginated question list view (50/page) with sortable columns: standard_code, difficulty, type, validated status, avg_correct_rate, times_used.
- Filter by: standard, domain, grade, difficulty, type, validated status, tags.
- Question preview with KaTeX rendered (shows exactly what the student sees).
- Edit form for all fields.
- Single-question validation workflow (approve / reject with required comment).
- Bulk actions: activate, deactivate, assign for review.
- Flagged question queue (avg_correct_rate > 0.92 or < 0.25).
- Export filtered question set as JSON or CSV.

---

### FR-4: Diagnostic Assessment Engine

**FR-4.1 — Assessment Structure**

The diagnostic assessment SHALL consist of 35–45 questions with the following composition:

| Section | Skills Covered | Min Questions | Max Questions |
|---------|---------------|--------------|--------------|
| Prerequisite Skills Block | 9 Grade 3 prerequisites | 27 (3/skill) | 36 (4/skill) |
| Grade 4 Sampling Block | 5 Grade 4 domains (4.OA, 4.NBT, 4.NF, 4.GM, 4.DR) | 5 (1/domain) | 9 (1-2/domain) |
| Calibration Block | Mixed; 2-3 questions used for IRT calibration | 3 | 3 |

The adaptive engine SHALL dynamically determine the exact number of questions per skill based on response accuracy (stopping when confidence threshold is met; see FR-4.2).

**FR-4.2 — Adaptive Question Selection (CAT Lite)**

The diagnostic uses a simplified CAT (Computerized Adaptive Testing) approach:

1. **Initial question**: For each skill/standard block, start with a difficulty-2 question (medium-low).
2. **Adjustment rule**:
   - If correct → serve next question at difficulty + 1 (capped at 4).
   - If incorrect → serve next question at difficulty – 1 (floored at 1).
3. **Termination condition per skill**: Stop when 3 questions have been served for the skill AND any of: (a) all 3 answered correctly (likely mastered), (b) all 3 answered incorrectly (likely not mastered), or (c) 4 questions served total.
4. **IRT integration (deferred to Stage 3 full implementation)**: In Stage 1, use simplified 1-parameter logistic (1PL) item difficulty only. Full 3-parameter IRT calibration is a Stage 3 enhancement.
5. **Question selection algorithm** (Python, runs server-side):

```python
def select_next_question(
    student_id: str,
    standard_code: str,
    current_difficulty: int,
    answered_question_ids: list[str]
) -> str:  # returns question_id
    """
    Selects the next question for a given standard in the diagnostic.
    Excludes already-answered questions.
    Targets current_difficulty; falls back to adjacent difficulties if needed.
    Returns question_id of selected question.
    """
    candidates = db.query(
        """
        SELECT question_id, difficulty_level
        FROM questions
        WHERE standard_code = %s
          AND is_validated = TRUE
          AND is_active = TRUE
          AND question_id NOT IN %s
          AND difficulty_level = %s
        ORDER BY RANDOM()
        LIMIT 1
        """,
        (standard_code, tuple(answered_question_ids) or ('',), current_difficulty)
    )
    if candidates:
        return candidates[0]['question_id']
    # Fallback: adjacent difficulty
    for fallback_diff in [current_difficulty + 1, current_difficulty - 1, 3, 2, 4, 1]:
        candidates = db.query(
            "SELECT question_id FROM questions WHERE standard_code = %s "
            "AND is_validated = TRUE AND is_active = TRUE "
            "AND question_id NOT IN %s AND difficulty_level = %s "
            "ORDER BY RANDOM() LIMIT 1",
            (standard_code, tuple(answered_question_ids) or ('',), fallback_diff)
        )
        if candidates:
            return candidates[0]['question_id']
    raise QuestionPoolExhaustedError(f"No valid questions for {standard_code}")
```

**FR-4.3 — Time Limit & Pause/Resume**

- The recommended time for the full diagnostic is 45–60 minutes. There is NO hard time limit that cuts off a student mid-assessment. Time is recorded per-question for analytics but does not affect scoring.
- A soft "session reminder" is displayed if the student has been active for 60 minutes: "You're doing great! You've been going for an hour. Would you like to take a break?" with options: "Keep going" or "Save and continue later."
- Pause/resume: At any point, the student may close the browser or click a "Save my progress" button. Assessment state is persisted to PostgreSQL (current question index, all previous responses, current CAT difficulty per skill). On next login, the student is shown an "Assessment In Progress" card with a "Continue" button that resumes exactly where they left off.
- Assessment state is also checkpointed to Redis on each question submission (key: `diagnostic:{assessment_id}:state`, TTL: 7 days) as a fast-read cache for resume.
- If a student's session expires during an assessment (30-minute inactivity timeout), the state is preserved in PostgreSQL. On re-login, the system restores from the latest checkpoint.

**FR-4.4 — Question Display UI**

- Question cards SHALL use a minimum font size of 18px for question text and 16px for answer options.
- The layout SHALL be single-column, centered, with generous white space (≥ 32px padding on all sides).
- Visual theme: friendly, warm colors (blues, greens, yellows) with NO red or harsh colors in the question UI. Red is reserved for "incorrect" feedback only.
- Each question card SHALL display: (1) a small skill category label ("Multiplication" / "Fractions" / etc.) in muted text, (2) the question text with KaTeX rendered, (3) any associated image, (4) the answer input (type-dependent), (5) a "Check Answer" or "Submit" button.
- Transition between questions: smooth fade animation (200ms), NOT a hard page reload.
- If the student has been on a question for >3 minutes without interaction, a gentle "Take your time!" message appears.

**FR-4.5 — Answer Input UI**

*Multiple Choice*: Large tap-target buttons (minimum 48×48px hit area, per WCAG 2.5.5). Button text includes option label (A/B/C/D) and text. Selected state shows a clear highlight border and check icon. On mobile/tablet, options stack vertically.

*Numeric Keypad*: An on-screen numeric keypad renders for `short_numeric` questions (0–9 buttons, backspace, decimal point, negative sign). Keypad buttons are minimum 56×56px. Physical keyboard input is also accepted on desktop. The input field shows the current value in 24px font.

*Fraction Input*: Two stacked input fields (numerator on top, fraction bar, denominator on bottom) with a whole-number field to the left for mixed numbers. All fields accept numeric keypad input. The fraction renders visually in KaTeX style as the student types.

**FR-4.6 — Progress Indicator**

- A linear progress bar at the top of the screen shows "Question X of approximately Y." (Note: exact total varies due to adaptive selection, so display is approximate: "~40 questions total".)
- A secondary indicator shows per-domain completion: 5 dots or icons representing the 5 Grade 4 domains (4.OA, 4.NBT, 4.NF, 4.GM, 4.DR), each filling in as questions from that domain are answered.
- Progress bar SHALL NOT show correct/incorrect status until the full assessment is complete (no feedback during assessment).

**FR-4.7 — Session Persistence**

Assessment checkpoint stored in `assessments.state_snapshot` (JSONB):

```json
{
  "assessment_id": "uuid",
  "student_id": "uuid",
  "current_question_index": 12,
  "questions_served": ["q_id_1", "q_id_2", ...],
  "responses": [
    {
      "question_id": "uuid",
      "answer_given": "B",
      "is_correct": true,
      "time_taken_seconds": 28,
      "difficulty_at_time": 2
    }
  ],
  "skill_states": {
    "3.OA.C.7": {"questions_served": 3, "correct": 2, "current_difficulty": 3, "done": true},
    "4.NBT.B.5": {"questions_served": 1, "correct": 1, "current_difficulty": 3, "done": false}
  },
  "last_updated": "2024-09-05T14:23:11Z"
}
```

**FR-4.8 — Scoring Engine**

Per-skill accuracy is calculated after assessment completion:

```python
def calculate_skill_accuracy(responses: list[dict], standard_code: str) -> float:
    """Returns accuracy (0.0–1.0) for a given standard code across all responses."""
    skill_responses = [r for r in responses if r['standard_code'] == standard_code]
    if not skill_responses:
        return None  # Not assessed
    return sum(1 for r in skill_responses if r['is_correct']) / len(skill_responses)
```

Per-skill proficiency classification:

| Accuracy | Classification | BKT P(mastered) Initial |
|----------|---------------|------------------------|
| < 0.60 | Below Par | 0.10 |
| 0.60 – 0.79 | On Par | 0.50 |
| ≥ 0.80 | Above Par | 0.80 |

Edge case: If only 1 question was served for a skill (due to pool exhaustion), accuracy is computed on 1 question. This is flagged in the `student_skill_states` record with a `low_confidence` boolean.

**FR-4.9 — BKT Initialization**

Upon diagnostic completion, the system SHALL initialize the student's BKT skill state for each assessed standard. Using pyBKT:

```python
import pyBKT.models as bkt

def initialize_bkt_state_from_diagnostic(
    student_id: str,
    diagnostic_results: dict[str, list[bool]]  # standard_code → [correct, correct, incorrect, ...]
) -> dict[str, dict]:
    """
    Initialize BKT P(mastered) for each skill based on diagnostic responses.
    Returns dict mapping standard_code → BKT state dict.
    """
    bkt_states = {}
    for standard_code, responses in diagnostic_results.items():
        accuracy = sum(responses) / len(responses)
        # Map accuracy to P(L0) — prior probability of already knowing the skill
        if accuracy < 0.60:
            p_l0 = 0.10
        elif accuracy < 0.80:
            p_l0 = 0.40
        else:
            p_l0 = 0.75
        # Use default BKT parameters; will be calibrated in Stage 3
        bkt_states[standard_code] = {
            "p_l0": p_l0,
            "p_t": 0.10,   # P(learn): default, to be calibrated
            "p_s": 0.10,   # P(slip): default
            "p_g": 0.20,   # P(guess): default
            "p_mastered": p_l0,  # Current mastery estimate = prior at initialization
            "initialized_from": "diagnostic",
            "response_count": len(responses)
        }
    return bkt_states
```

The resulting `p_mastered` values are stored per-student per-skill in the `student_skill_states` table.

**FR-4.10 — Scoring Rubric**

| Threshold | Label | Color | Description |
|-----------|-------|-------|-------------|
| < 60% accuracy | Below Par | Orange (#F4A843) | Needs remediation before grade-level content |
| 60–79% accuracy | On Par | Blue (#4A90D9) | Ready for grade-level content |
| ≥ 80% accuracy | Above Par | Green (#4CAF50) | Can be accelerated or enriched |

Overall diagnostic level is computed as the mode of per-skill classifications, with ties broken in favor of the more conservative classification (Below Par > On Par > Above Par).

**FR-4.11 — Results Calculation & Diagnostic Completion Event**

On final answer submission:
1. All responses are finalized in `assessment_responses`.
2. Per-skill accuracy is calculated (FR-4.8).
3. Per-skill proficiency classification assigned (FR-4.10).
4. BKT initial states written to `student_skill_states` (FR-4.9).
5. Overall proficiency level calculated.
6. Assessment record updated: `status = 'completed'`, `completed_at = NOW()`, `overall_level = '...'`.
7. A `diagnostic_completed` event is published to the application event queue (Redis Streams). This event triggers the learning plan generation pipeline in Stage 2.
8. Parent notification email sent: "Your child's MathPath diagnostic is complete. View results →" (with link to parent results dashboard).

**FR-4.12 — Anti-Gaming Measures**

- Question order within each skill block is randomized per session (seeded with `assessment_id + skill_code` for reproducibility in review).
- Answer option order for multiple choice is randomized per session.
- Back-navigation is disabled: once an answer is submitted, the student cannot return to it. The "Previous" button does not exist in the assessment UI.
- The assessment does not display correct/incorrect feedback during the assessment (no immediate right/wrong indicator). Feedback is shown only in the results summary after completion.
- Answer submission is handled server-side; the correct answer is never sent to the client before submission.
- Rapid answer sequences (all questions answered in < 5 seconds each) are flagged in `assessments.flagged_for_review = TRUE` for admin review.
- Session tokens are scoped to a single assessment ID and cannot be reused.

**FR-4.13 — Accessibility Requirements for Assessment**

- Font size toggle: students can increase font size in 3 steps (Default 18px → Large 22px → Extra Large 28px). Setting persists for the assessment session.
- High contrast mode: toggle switches to a WCAG 2.1 AAA-compliant color palette (black background, white text, yellow highlights).
- Keyboard navigation: all answer inputs reachable via Tab; multiple choice selectable via arrow keys and confirmed with Enter.
- Screen reader support: all question text and answer options include appropriate ARIA labels. Fraction inputs use `aria-label="numerator"` and `aria-label="denominator"`.
- KaTeX math expressions include `aria-label` with spoken math (e.g., `aria-label="3 fourths"`).
- Images require alt text (FR-3.6); alt text is read by screen readers.
- No time-based interactions that cannot be extended (WCAG 2.2.1 compliance).

**FR-4.14 — No PII in Question Content**

- All word problems in the question bank SHALL use generic names (Maya, Jordan, Alex, Sam — diverse but non-identifying).
- Questions SHALL NOT reference specific schools, addresses, or any location more specific than "Oregon."
- No photographs of real people SHALL be used in questions.
- Oregon geography context (rivers, mountains, cities by name) is permitted and encouraged for engagement.

**FR-4.15 — Assessment Completion Screen**

Upon completing the last question:
- A full-screen "You Did It!" completion animation plays (confetti, 2 seconds, respects `prefers-reduced-motion`).
- Message: "Amazing work, [first name]! Your results are ready." (child-facing copy, warm tone).
- A single CTA button: "See My Results" → navigates to student results screen (FR-5.1).
- Parent is simultaneously notified via email (FR-4.11 step 8).

---

### FR-5: Results & Gap Analysis Display

**FR-5.1 — Student-Facing Results Screen**

- Layout: Celebratory header ("You're a math explorer!"), overall level displayed as a large icon + label (a mountain peak icon for "Above Par", a path icon for "On Par", a climbing icon for "Below Par").
- Per-skill breakdown shown as a horizontal progress bar for each of the 9 prerequisite skills and 5 Grade 4 domain averages (14 bars total).
- Each bar is color-coded: orange (Below Par), blue (On Par), green (Above Par).
- Skill names use child-friendly language: "Multiplication Facts" (not "3.OA.C.7"), "Adding Fractions" (not "3.NF.A.1 / 4.NF.B.3"), etc. A mapping table between standard codes and child-friendly names SHALL be maintained in the codebase.
- Encouraging, non-judgmental copy: "You've got some cool things to learn!" (Below Par) vs. "You're on the path — keep going!" (On Par) vs. "You're ahead of the pack!" (Above Par).
- A "What's Next?" section teases the learning plan: "MathPath is building your personal math journey. Come back tomorrow to start!" (or "Start now →" if learning plan is ready).
- No numeric percentages shown to the student — only visual bars and level labels.

**FR-5.2 — Parent-Facing Results Screen**

- Section 1: Summary — Child name, overall level, date completed, brief plain-language summary ("Jayden completed the MathPath diagnostic. Here's what we found:").
- Section 2: Prerequisite Skills — Table with columns: Skill Name, Standard Code, Result (Below Par / On Par / Above Par), Questions Answered, Accuracy %. Color-coded rows.
- Section 3: Grade 4 Domain Preview — Donut chart or bar chart showing approximate readiness per domain. Grayed-out domains not yet assessed.
- Section 4: What This Means — 3–5 bullet points written by a math educator explaining the implications of the results in plain language. Example: "Jayden showed strong addition and subtraction but needs support with multiplication facts, which are foundational for all of 4th grade math."
- Section 5: What MathPath Will Do — Brief explanation of the adaptive learning plan that will be generated (Stage 2), with estimated weeks to grade-level proficiency.
- Section 6: Tips for Parents — 2–3 actionable suggestions the parent can do at home.

**FR-5.3 — Skill-by-Skill Proficiency Visualization**

- Both student and parent views use horizontal bar charts rendered in React with SVG (no third-party charting library dependency in the critical path; use a lightweight custom component or recharts).
- Each bar: label (left), filled portion (color-coded), percentage label (right — shown in parent view only).
- Bars are animated on mount (fill from left, 800ms ease-in-out). Respects `prefers-reduced-motion`.
- Bars are grouped by domain with section headers.
- Tapping/clicking a bar in parent view opens a detail panel with: skill description, number of questions answered, which questions were correct/incorrect (shown as colored circles, no question content), and a link to "Practice this skill" (disabled in Stage 1, enabled in Stage 3).

**FR-5.4 — Overall Proficiency Level**

- Three levels: Below Par, On Par, Above Par (as defined in FR-4.10).
- The level is displayed prominently on both student and parent views.
- Visual treatment: below par = orange badge with upward arrow icon; on par = blue badge with checkmark; above par = green badge with star.
- The parent-facing view also displays the percentage of skills at each level (e.g., "3 of 9 prerequisite skills: Below Par").

**FR-5.5 — Gap Summary**

- Parent view includes a "Skills to Focus On" list: all skills classified as Below Par, listed in priority order (most foundational first, using the prerequisite graph from FR-2.4).
- Each skill in the gap list shows: skill name, standard code, accuracy percentage, and a short 1-sentence description of what the skill involves.
- If no skills are Below Par: "Great news! Your child is on track with all foundational skills for 4th grade math."

**FR-5.6 — Comparison Against Grade-Level Baseline (Growth Mindset)**

- Results are expressed relative to grade-level expectations (what a student should know entering Grade 4), NOT relative to other students.
- Language: "Compared to what's expected for entering 4th grade, Jayden is [below / at / above] the typical starting point."
- No percentile ranks, no peer comparisons, no class averages. Strictly criterion-referenced.
- A tooltip/info icon next to "grade-level baseline" explains: "This is based on Oregon math standards for Grade 4. It tells us what skills are expected before starting 4th grade content."

**FR-5.7 — "What Comes Next" Preview**

- A dedicated card at the bottom of the results screen (both student and parent views) previews the personalized learning plan.
- Student view: "MathPath is building your personal adventure map! [Module icon] Multiplication Facts → [Module icon] Fractions → [Module icon] ..."  (shows first 2–3 modules from the generated plan, or a placeholder if the plan isn't generated yet).
- Parent view: "Jayden's learning plan is being prepared. It will include approximately [N] modules, starting with [Skill Name]. Estimated time to grade-level proficiency: [X weeks] with 20 minutes/day." (these estimates come from Stage 2 learning plan generation).
- CTA: "Start Learning Now" (active once learning plan is generated in Stage 2) or "Learning plan coming soon..." (grayed out until Stage 2 is ready for the student).

**FR-5.8 — PDF/Print Export**

- A "Download Report (PDF)" button on the parent results screen generates a printable PDF summary.
- PDF contents: MathPath Oregon branding header, student name (first name only), date, overall level, per-skill breakdown table with accuracy percentages, gap summary, plain-language interpretation, "What comes next" preview.
- PDF generated server-side using WeasyPrint (Python) or Puppeteer (Node) with a dedicated `/api/v1/students/:student_id/diagnostic-report.pdf` endpoint.
- PDF is NOT cached (regenerated on each request to ensure freshness); response time target: < 10 seconds.
- PDF metadata SHALL NOT include the child's full name or date of birth.

---

## 1.4 Non-Functional Requirements

### Performance
- Assessment page initial load (including KaTeX, question content): < 2 seconds at p95, measured from navigation start.
- Question transition (submit answer → display next question): < 500ms at p95. Achieved via pre-fetching the next question in the background immediately after the current question loads.
- Pre-fetch strategy: after question N loads, the client issues a background `GET /api/v1/assessments/:id/next-question-preview` request. The question is cached in component state, enabling near-instant display on submit.
- Diagnostic results calculation (all scoring + BKT initialization): < 2 seconds after final answer submission.
- PDF report generation: < 10 seconds.

### Availability
- Target: 99.5% monthly uptime (approximately 3.6 hours downtime/month).
- Maintenance windows: Tuesdays 10 PM–2 AM Pacific (4-hour window, announced 48 hours in advance via in-app banner).
- Health check endpoint: `GET /health` returns HTTP 200 with `{"status": "ok", "version": "x.y.z"}`.

### Security
- All traffic: TLS 1.3 minimum (TLS 1.2 disabled). HSTS header with 1-year max-age.
- Student data at rest: AES-256 encryption for all PII fields (name, email) via PostgreSQL transparent data encryption or column-level encryption using pgcrypto.
- No PII in application logs. Student names replaced with `[STUDENT]` token; student IDs replaced with truncated UUIDs in logs.
- Dependency scanning: GitHub Dependabot + Snyk on every PR.
- SAST: Semgrep on CI pipeline.
- Secrets management: AWS Secrets Manager (or GCP Secret Manager). No secrets in environment variables or codebase.
- Auth0 for authentication (not home-rolled JWT). Auth0 COPPA compliance settings enabled.
- CORS: strict allowlist of permitted origins.
- Content Security Policy header on all pages.
- Rate limiting: 100 requests/minute per IP on API endpoints; 10 login attempts/minute per IP.

### COPPA Compliance
- Zero data collection before verifiable parental consent (enforced at API middleware level).
- Consent timestamp, IP hash, user agent stored permanently.
- Data subject request (DSR) response within 45 days (30-day deletion, 45-day response SLA per COPPA).
- Annual legal review of consent flow and privacy policy.

### Scalability
- Initial target: 1,000 concurrent diagnostic sessions.
- Load test: Locust or k6 test simulating 1,000 concurrent users, each serving 45 questions, before launch.
- Database connection pooling: PgBouncer, pool size 100.
- Read replicas: 1 PostgreSQL read replica for reporting/results queries.
- Redis: ElastiCache (AWS) or Memorystore (GCP), single-node for Stage 1 (upgrade to cluster in Stage 3).

### Browser & Device Support
- Chrome 90+, Safari 14+, Firefox 88+, Edge 90+.
- iOS Safari 14+ (iPad primary, iPhone secondary).
- Chrome on Android (tablet and phone).
- Minimum screen width: 320px (iPhone SE).
- Primary design target: iPad 10th gen (1080×1668px) in portrait mode.
- No Flash, no ActiveX, no IE11 support.

### Accessibility (WCAG 2.1 AA)
- Color contrast: 4.5:1 for body text, 3:1 for large text and UI components.
- All interactive elements keyboard-navigable.
- No keyboard trap.
- All form fields labeled (no placeholder-only labels).
- Error messages programmatically associated with form fields (aria-describedby).
- Focus visible for all interactive elements.
- No content that flashes more than 3 times per second.
- Assessment UI tested with VoiceOver (iOS), NVDA (Windows), and axe-core automated scans.

---

## 1.5 Data Models

Complete PostgreSQL schema for Stage 1:

```sql
-- ============================================================
-- USERS (Parents / Admins)
-- ============================================================
CREATE TABLE users (
    user_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(320) UNIQUE NOT NULL,
    email_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified_at   TIMESTAMPTZ,
    password_hash       VARCHAR(255) NOT NULL,  -- bcrypt(12)
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    role                VARCHAR(20) NOT NULL DEFAULT 'parent'
                            CHECK (role IN ('parent', 'admin', 'teacher')),
    status              VARCHAR(30) NOT NULL DEFAULT 'PENDING_VERIFICATION'
                            CHECK (status IN (
                                'PENDING_VERIFICATION', 'VERIFICATION_EXPIRED',
                                'ACTIVE', 'CONSENT_DECLINED', 'SUSPENDED', 'DELETED'
                            )),
    privacy_policy_version  VARCHAR(20),
    tos_version             VARCHAR(20),
    privacy_accepted_at     TIMESTAMPTZ,
    failed_login_attempts   SMALLINT NOT NULL DEFAULT 0,
    locked_until            TIMESTAMPTZ,
    last_login_at           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);


-- ============================================================
-- EMAIL VERIFICATION TOKENS
-- ============================================================
CREATE TABLE email_verification_tokens (
    token_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash      VARCHAR(255) NOT NULL,  -- SHA-256 hash of the token
    expires_at      TIMESTAMPTZ NOT NULL,
    consumed        BOOLEAN NOT NULL DEFAULT FALSE,
    consumed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evt_user_id ON email_verification_tokens(user_id);


-- ============================================================
-- CONSENT RECORDS (Never deleted — legal requirement)
-- ============================================================
CREATE TABLE consent_records (
    consent_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,  -- NOT a FK to allow account deletion while retaining consent
    consent_type        VARCHAR(50) NOT NULL CHECK (consent_type IN ('COPPA_INITIAL', 'PRIVACY_UPDATE')),
    privacy_policy_version  VARCHAR(20) NOT NULL,
    tos_version             VARCHAR(20) NOT NULL,
    consented           BOOLEAN NOT NULL,
    consented_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address_hash     VARCHAR(64) NOT NULL,  -- SHA-256 of IP, not raw IP
    user_agent          TEXT,
    confirmation_email_sent_at  TIMESTAMPTZ,
    confirmation_clicked_at     TIMESTAMPTZ,
    revoked             BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at          TIMESTAMPTZ
);

CREATE INDEX idx_consent_user_id ON consent_records(user_id);


-- ============================================================
-- STUDENTS (Child Profiles)
-- ============================================================
CREATE TABLE students (
    student_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_user_id      UUID NOT NULL REFERENCES users(user_id) ON DELETE SET NULL,
    display_name        VARCHAR(100) NOT NULL,  -- first name / nickname only
    grade               SMALLINT NOT NULL CHECK (grade BETWEEN 3 AND 6),
    school_district     VARCHAR(200),
    teacher_name        VARCHAR(200),
    avatar_id           SMALLINT NOT NULL DEFAULT 1 CHECK (avatar_id BETWEEN 1 AND 12),
    status              VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
                            CHECK (status IN ('ACTIVE', 'DELETED')),
    diagnostic_status   VARCHAR(30) NOT NULL DEFAULT 'NOT_STARTED'
                            CHECK (diagnostic_status IN (
                                'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED'
                            )),
    deleted_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_students_parent ON students(parent_user_id);
CREATE INDEX idx_students_status ON students(status);


-- ============================================================
-- STANDARDS (Grade 3 prerequisites + Grade 4 Oregon standards)
-- ============================================================
CREATE TABLE standards (
    standard_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grade           SMALLINT NOT NULL CHECK (grade BETWEEN 3 AND 6),
    domain          VARCHAR(10) NOT NULL,
    cluster         VARCHAR(255) NOT NULL,
    code            VARCHAR(20) UNIQUE NOT NULL,
    description     TEXT NOT NULL,
    dok_level       SMALLINT NOT NULL CHECK (dok_level BETWEEN 1 AND 4),
    strand          VARCHAR(50),
    is_prerequisite BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    version_tag     VARCHAR(20) NOT NULL DEFAULT 'OAS-2023',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_standards_grade ON standards(grade);
CREATE INDEX idx_standards_domain ON standards(domain);
CREATE INDEX idx_standards_code ON standards(code);
CREATE INDEX idx_standards_is_active ON standards(is_active);


-- ============================================================
-- PREREQUISITE RELATIONSHIPS (Directed skill dependency graph)
-- ============================================================
CREATE TABLE prerequisite_relationships (
    relationship_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prerequisite_code   VARCHAR(20) NOT NULL REFERENCES standards(code),
    dependent_code      VARCHAR(20) NOT NULL REFERENCES standards(code),
    strength            VARCHAR(10) NOT NULL DEFAULT 'required'
                            CHECK (strength IN ('required', 'recommended')),
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(prerequisite_code, dependent_code)
);

CREATE INDEX idx_prereq_prereq_code ON prerequisite_relationships(prerequisite_code);
CREATE INDEX idx_prereq_dependent_code ON prerequisite_relationships(dependent_code);


-- ============================================================
-- STANDARDS AUDIT LOG
-- ============================================================
CREATE TABLE standards_audit_log (
    audit_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_id     UUID,  -- may be null for deleted records
    standard_code   VARCHAR(20),
    changed_by      UUID REFERENCES users(user_id),
    change_type     VARCHAR(10) NOT NULL CHECK (change_type IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values      JSONB,
    new_values      JSONB,
    change_reason   TEXT NOT NULL,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- QUESTIONS
-- ============================================================
CREATE TABLE questions (
    question_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_code       VARCHAR(20) NOT NULL REFERENCES standards(code),
    question_type       VARCHAR(30) NOT NULL CHECK (question_type IN (
                            'multiple_choice', 'short_numeric', 'fill_blank', 'fraction_input'
                        )),
    question_text       TEXT NOT NULL,
    answer_options      JSONB,
    correct_answer      TEXT NOT NULL,
    correct_answer_alt  TEXT[] DEFAULT '{}',
    solution_steps      JSONB NOT NULL DEFAULT '[]',
    difficulty_level    SMALLINT NOT NULL CHECK (difficulty_level BETWEEN 1 AND 5),
    dok_level           SMALLINT NOT NULL CHECK (dok_level BETWEEN 1 AND 4),
    context_type        VARCHAR(30) NOT NULL CHECK (context_type IN (
                            'word_problem', 'computation', 'visual', 'mixed'
                        )),
    is_prerequisite     BOOLEAN NOT NULL DEFAULT FALSE,
    tags                TEXT[] DEFAULT '{}',
    source              VARCHAR(100) NOT NULL DEFAULT 'seed_v1',
    validated_by        VARCHAR(100),
    validation_date     DATE,
    is_validated        BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    has_image           BOOLEAN NOT NULL DEFAULT FALSE,
    image_url           TEXT,
    image_alt_text      TEXT,
    numeric_tolerance   DECIMAL(10,6),
    times_used          INTEGER NOT NULL DEFAULT 0,
    avg_correct_rate    DECIMAL(5,4),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_questions_standard_code ON questions(standard_code);
CREATE INDEX idx_questions_difficulty ON questions(difficulty_level);
CREATE INDEX idx_questions_type ON questions(question_type);
CREATE INDEX idx_questions_validated ON questions(is_validated) WHERE is_validated = TRUE;
CREATE INDEX idx_questions_active ON questions(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_questions_tags ON questions USING GIN(tags);
CREATE INDEX idx_questions_ts ON questions USING GIN(to_tsvector('english', question_text));


-- ============================================================
-- ASSESSMENTS
-- ============================================================
CREATE TABLE assessments (
    assessment_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL REFERENCES students(student_id),
    assessment_type     VARCHAR(30) NOT NULL DEFAULT 'diagnostic'
                            CHECK (assessment_type IN ('diagnostic', 'practice', 'summative')),
    status              VARCHAR(20) NOT NULL DEFAULT 'started'
                            CHECK (status IN ('started', 'paused', 'completed', 'abandoned')),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    total_questions     SMALLINT,
    questions_answered  SMALLINT NOT NULL DEFAULT 0,
    overall_level       VARCHAR(20) CHECK (overall_level IN ('Below Par', 'On Par', 'Above Par')),
    state_snapshot      JSONB,  -- current CAT state for resume
    flagged_for_review  BOOLEAN NOT NULL DEFAULT FALSE,
    flag_reason         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_assessments_student ON assessments(student_id);
CREATE INDEX idx_assessments_status ON assessments(status);
CREATE INDEX idx_assessments_type ON assessments(assessment_type);


-- ============================================================
-- ASSESSMENT QUESTIONS (Questions served in an assessment)
-- ============================================================
CREATE TABLE assessment_questions (
    aq_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       UUID NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    question_id         UUID NOT NULL REFERENCES questions(question_id),
    sequence_number     SMALLINT NOT NULL,
    option_order        TEXT[],  -- randomized option ids for MC questions; stored for review
    served_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    difficulty_at_serve SMALLINT,
    UNIQUE(assessment_id, sequence_number)
);

CREATE INDEX idx_aq_assessment ON assessment_questions(assessment_id);


-- ============================================================
-- ASSESSMENT RESPONSES
-- ============================================================
CREATE TABLE assessment_responses (
    response_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       UUID NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
    aq_id               UUID NOT NULL REFERENCES assessment_questions(aq_id),
    question_id         UUID NOT NULL REFERENCES questions(question_id),
    standard_code       VARCHAR(20) NOT NULL,
    answer_given        TEXT,        -- null if skipped
    is_correct          BOOLEAN,
    time_taken_seconds  INTEGER,     -- null if not recorded
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(assessment_id, aq_id)
);

CREATE INDEX idx_ar_assessment ON assessment_responses(assessment_id);
CREATE INDEX idx_ar_standard ON assessment_responses(standard_code);


-- ============================================================
-- STUDENT SKILL STATES (BKT state per student per skill)
-- ============================================================
CREATE TABLE student_skill_states (
    state_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id          UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    standard_code       VARCHAR(20) NOT NULL REFERENCES standards(code),
    p_l0                DECIMAL(6,5) NOT NULL,   -- prior probability of mastery
    p_t                 DECIMAL(6,5) NOT NULL DEFAULT 0.10,  -- P(learn)
    p_s                 DECIMAL(6,5) NOT NULL DEFAULT 0.10,  -- P(slip)
    p_g                 DECIMAL(6,5) NOT NULL DEFAULT 0.20,  -- P(guess)
    p_mastered          DECIMAL(6,5) NOT NULL,   -- current mastery estimate
    proficiency_level   VARCHAR(20) NOT NULL
                            CHECK (proficiency_level IN ('Below Par', 'On Par', 'Above Par')),
    response_count      SMALLINT NOT NULL DEFAULT 0,
    low_confidence      BOOLEAN NOT NULL DEFAULT FALSE,  -- flagged if response_count < 2
    initialized_from    VARCHAR(30) NOT NULL DEFAULT 'diagnostic',
    last_practiced_at   TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, standard_code)
);

CREATE INDEX idx_sss_student ON student_skill_states(student_id);
CREATE INDEX idx_sss_standard ON student_skill_states(standard_code);
CREATE INDEX idx_sss_proficiency ON student_skill_states(proficiency_level);
```

---

## 1.6 API Endpoints

Base URL: `https://api.mathpath.org/api/v1`  
All endpoints return `Content-Type: application/json`.  
All protected endpoints require `Authorization: Bearer <access_token>` header.  
All responses include `request_id` header for tracing.

---

### Authentication Endpoints

#### POST /auth/register
Register a new parent account.

**Auth required**: No

**Request body**:
```json
{
  "email": "parent@example.com",
  "password": "SecurePass1!",
  "first_name": "Maria",
  "last_name": "Rodriguez",
  "state": "OR"
}
```

**Response 201**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "parent@example.com",
  "status": "PENDING_VERIFICATION",
  "message": "Verification email sent. Please check your inbox."
}
```

**Response 409** (duplicate email):
```json
{"error": "EMAIL_EXISTS", "message": "An account with this email already exists."}
```

---

#### POST /auth/verify-email
Verify email using token from verification email.

**Auth required**: No

**Request body**:
```json
{"token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."}
```

**Response 200**:
```json
{"message": "Email verified successfully.", "next_step": "consent"}
```

**Response 410** (expired or already used):
```json
{"error": "TOKEN_EXPIRED", "message": "This link has expired or already been used."}
```

---

#### POST /auth/login
Authenticate a parent account.

**Auth required**: No

**Request body**:
```json
{"email": "parent@example.com", "password": "SecurePass1!"}
```

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "user_id": "550e8400...",
    "email": "parent@example.com",
    "first_name": "Maria",
    "status": "ACTIVE",
    "consent_complete": true
  }
}
```
*(Refresh token set as HTTP-only cookie `mathpath_refresh`)*

**Response 401**:
```json
{"error": "INVALID_CREDENTIALS", "message": "Incorrect email or password."}
```

---

#### POST /auth/refresh
Obtain a new access token using refresh token.

**Auth required**: No (uses refresh token cookie)

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900
}
```

---

#### POST /auth/logout
Invalidate current session.

**Auth required**: Yes

**Response 204**: No content. Clears refresh token cookie.

---

#### POST /auth/forgot-password
Initiate password reset flow.

**Auth required**: No

**Request body**: `{"email": "parent@example.com"}`

**Response 200**: `{"message": "If that email exists, a reset link has been sent."}` (always returns 200 to prevent email enumeration)

---

#### POST /auth/reset-password
Complete password reset.

**Auth required**: No

**Request body**: `{"token": "...", "new_password": "NewSecurePass1!"}`

**Response 200**: `{"message": "Password reset successfully."}`

---

### Consent Endpoints

#### GET /consent/current-version
Get current consent version info.

**Auth required**: Yes

**Response 200**:
```json
{
  "privacy_policy_version": "1.0",
  "tos_version": "1.0",
  "effective_date": "2024-09-01",
  "requires_acceptance": true
}
```

---

#### POST /consent/accept
Record parental consent.

**Auth required**: Yes (must be email-verified)

**Request body**:
```json
{
  "privacy_policy_version": "1.0",
  "tos_version": "1.0",
  "privacy_checkbox": true,
  "coppa_checkbox": true
}
```

**Response 201**:
```json
{
  "consent_id": "uuid",
  "consented_at": "2024-09-05T14:00:00Z",
  "status": "CONSENT_PENDING_EMAIL_CONFIRMATION",
  "message": "A confirmation email has been sent. Please click the link to complete consent."
}
```

---

### Student Profile Endpoints

#### POST /students
Create a child profile.

**Auth required**: Yes (parent, consent_complete = true)

**Request body**:
```json
{
  "display_name": "Jayden",
  "grade": 4,
  "school_district": "Beaverton School District",
  "teacher_name": "Ms. Chen",
  "avatar_id": 5
}
```

**Response 201**:
```json
{
  "student_id": "uuid",
  "display_name": "Jayden",
  "grade": 4,
  "avatar_id": 5,
  "diagnostic_status": "NOT_STARTED"
}
```

---

#### GET /students
List all children for authenticated parent.

**Auth required**: Yes (parent)

**Response 200**:
```json
{
  "students": [
    {
      "student_id": "uuid",
      "display_name": "Jayden",
      "grade": 4,
      "avatar_id": 5,
      "diagnostic_status": "COMPLETED",
      "overall_level": "On Par",
      "last_assessment_at": "2024-09-05T15:30:00Z"
    }
  ]
}
```

---

#### GET /students/:student_id
Get a single student profile.

**Auth required**: Yes (parent of student)

**Response 200**: Full student object including diagnostic status and summary.

---

#### PATCH /students/:student_id
Update child profile fields.

**Auth required**: Yes (parent of student)

**Request body**: Any subset of `{display_name, grade, school_district, teacher_name, avatar_id}`

**Response 200**: Updated student object.

---

#### DELETE /students/:student_id
Request data deletion for a child.

**Auth required**: Yes (parent of student) + password re-confirmation required

**Response 202**:
```json
{
  "message": "Deletion scheduled. Data will be removed within 30 days.",
  "deletion_reference": "DEL-20240905-001",
  "scheduled_for": "2024-10-05T00:00:00Z"
}
```

---

### Standards Endpoints

#### GET /standards
List standards with optional filters.

**Auth required**: Yes (any authenticated user)

**Query params**: `grade`, `domain`, `dok_level`, `is_prerequisite`, `q` (full-text), `include_inactive`

**Response 200**:
```json
{
  "standards": [
    {
      "standard_id": "uuid",
      "code": "4.OA.A.1",
      "grade": 4,
      "domain": "4.OA",
      "cluster": "Use the four operations with whole numbers to solve problems",
      "description": "Interpret a multiplication equation as a comparison...",
      "dok_level": 2,
      "is_prerequisite": false,
      "is_active": true
    }
  ],
  "total": 38
}
```

---

#### GET /standards/:code
Get a single standard by code.

**Auth required**: Yes

**Response 200**: Single standard object.

**Response 404**: `{"error": "NOT_FOUND"}`

---

#### GET /standards/:code/prerequisites
Get all prerequisite standards for a given standard code.

**Auth required**: Yes

**Response 200**:
```json
{
  "standard_code": "4.NBT.B.5",
  "prerequisites": [
    {"code": "3.OA.C.7", "strength": "required", "description": "..."},
    {"code": "3.NBT.A.3", "strength": "required", "description": "..."}
  ]
}
```

---

### Assessment Endpoints

#### POST /assessments/diagnostic
Start a new diagnostic assessment for a student.

**Auth required**: Yes (parent session with child token scope, or child session token)

**Request body**: `{"student_id": "uuid"}`

**Business rules**: 
- Student must not have a completed diagnostic.
- If `IN_PROGRESS` diagnostic exists, return existing assessment instead of creating new.

**Response 201**:
```json
{
  "assessment_id": "uuid",
  "student_id": "uuid",
  "status": "started",
  "first_question": { /* question object — see GET next-question */ },
  "total_estimated": 40,
  "started_at": "2024-09-05T14:00:00Z"
}
```

---

#### GET /assessments/:assessment_id/next-question
Get the next question for an in-progress assessment.

**Auth required**: Yes (scoped to this assessment)

**Response 200**:
```json
{
  "assessment_id": "uuid",
  "sequence_number": 7,
  "progress": {
    "questions_answered": 6,
    "estimated_total": 40,
    "domains_sampled": ["4.OA", "3.OA"]
  },
  "question": {
    "question_id": "uuid",
    "question_text": "What is \\(8 \\times 7\\)?",
    "question_type": "multiple_choice",
    "answer_options": [
      {"id": "A", "text": "54"},
      {"id": "B", "text": "56"},
      {"id": "C", "text": "63"},
      {"id": "D", "text": "48"}
    ],
    "has_image": false,
    "context_type": "computation"
  }
}
```
*Note: `is_correct` and `correct_answer` are NOT included in the response.*

---

#### POST /assessments/:assessment_id/answer
Submit an answer for the current question.

**Auth required**: Yes (scoped to this assessment)

**Request body**:
```json
{
  "question_id": "uuid",
  "sequence_number": 7,
  "answer": "B",
  "time_taken_seconds": 28
}
```

**Response 200**:
```json
{
  "accepted": true,
  "assessment_status": "in_progress",
  "questions_answered": 7,
  "is_complete": false
}
```
*Note: `is_correct` is NOT returned during the assessment to prevent gaming.*

---

#### POST /assessments/:assessment_id/complete
Mark assessment as complete and trigger scoring.

**Auth required**: Yes (scoped to this assessment)

**Business rule**: Only callable after all adaptive branches are satisfied. The server validates completeness before accepting.

**Response 200**:
```json
{
  "assessment_id": "uuid",
  "status": "completed",
  "completed_at": "2024-09-05T15:28:00Z",
  "overall_level": "On Par",
  "results_ready": true
}
```

---

#### GET /assessments/:assessment_id/results
Get full diagnostic results for a completed assessment.

**Auth required**: Yes (parent of the student)

**Response 200**:
```json
{
  "assessment_id": "uuid",
  "student_id": "uuid",
  "completed_at": "2024-09-05T15:28:00Z",
  "overall_level": "On Par",
  "skill_results": [
    {
      "standard_code": "3.OA.C.7",
      "standard_description": "Fluently multiply and divide within 100",
      "child_friendly_name": "Multiplication Facts",
      "questions_answered": 3,
      "correct_count": 1,
      "accuracy": 0.333,
      "proficiency_level": "Below Par",
      "p_mastered": 0.10
    }
  ],
  "domain_summaries": [
    {
      "domain": "4.OA",
      "avg_accuracy": 0.67,
      "proficiency_level": "On Par"
    }
  ],
  "gaps": [
    {"standard_code": "3.OA.C.7", "priority": 1, "reason": "foundational_prerequisite"}
  ]
}
```

---

#### GET /students/:student_id/diagnostic-report.pdf
Generate and download diagnostic results PDF.

**Auth required**: Yes (parent of the student)

**Response**: `Content-Type: application/pdf`, inline or attachment.

---

### Admin Question Endpoints

#### GET /admin/questions
List all questions with filters.

**Auth required**: Yes (admin role)

**Query params**: `standard_code`, `difficulty`, `type`, `is_validated`, `is_active`, `tag`, `page`, `per_page`

**Response 200**: Paginated question list.

---

#### POST /admin/questions
Create a new question.

**Auth required**: Yes (admin role)

**Request body**: Full question object (FR-3.1 schema).

**Response 201**: Created question object.

---

#### GET /admin/questions/:question_id
Get single question by ID.

**Auth required**: Yes (admin role)

**Response 200**: Full question object including solution steps and distractors.

---

#### PATCH /admin/questions/:question_id
Update a question.

**Auth required**: Yes (admin role)

**Response 200**: Updated question object.

---

#### DELETE /admin/questions/:question_id
Deactivate (soft delete) a question.

**Auth required**: Yes (admin role)

**Response 200**: `{"message": "Question deactivated.", "question_id": "uuid"}`

---

#### POST /admin/questions/:question_id/validate
Approve or reject a question.

**Auth required**: Yes (admin role)

**Request body**:
```json
{
  "approved": true,
  "reviewer_name": "Dr. Sarah Kim",
  "notes": "Mathematically accurate, appropriate distractor quality."
}
```

**Response 200**: Updated question object with `is_validated = true`.

---

#### POST /admin/questions/import
Bulk import questions from JSON or CSV.

**Auth required**: Yes (admin role)

**Request**: `Content-Type: multipart/form-data` with `file` field (JSON or CSV).

**Response 200**:
```json
{
  "imported": 45,
  "failed": 2,
  "errors": [
    {"line": 12, "field": "difficulty_level", "message": "Must be between 1 and 5. Got: 6"},
    {"line": 31, "field": "standard_code", "message": "Unknown standard code: '4.OA.Z.9'"}
  ]
}
```

---

## 1.7 UI/UX Requirements

### Screen Inventory

| Screen ID | Screen Name | Path | User | Purpose |
|-----------|-------------|------|------|---------|
| S-01 | Landing / Marketing | `/` | Public | Product introduction, sign-up CTA |
| S-02 | Parent Registration | `/register` | Parent | Create account form |
| S-03 | Email Verification Pending | `/verify-email` | Parent | Instructions to check email |
| S-04 | Email Verified | `/email-confirmed` | Parent | Confirmation, link to consent |
| S-05 | COPPA Consent | `/consent` | Parent | Consent form (multi-step) |
| S-06 | Consent Confirmation Pending | `/consent/pending` | Parent | Awaiting email confirmation click |
| S-07 | Consent Confirmed | `/consent/confirmed` | Parent | Consent complete, create child profile |
| S-08 | Create Child Profile | `/onboarding/child` | Parent | Child name, grade, avatar selection |
| S-09 | Parent Dashboard | `/dashboard` | Parent | Overview of all children and statuses |
| S-10 | Pre-Diagnostic Explainer | `/diagnostic/intro` | Student | What is the diagnostic, what to expect |
| S-11 | Diagnostic Assessment | `/diagnostic/:id` | Student | Active assessment (main interaction screen) |
| S-12 | Assessment Paused | `/diagnostic/:id/paused` | Student | Saved progress confirmation |
| S-13 | Assessment Complete | `/diagnostic/:id/done` | Student | Celebration + "See My Results" |
| S-14 | Student Results | `/results/:student_id` | Student | Child-friendly results summary |
| S-15 | Parent Results | `/dashboard/results/:student_id` | Parent | Detailed results breakdown |
| S-16 | Account Settings | `/settings` | Parent | Profile, password, notifications |
| S-17 | Data Deletion | `/settings/delete` | Parent | Account/child data deletion flow |
| S-18 | PDF Report | (server-rendered) | Parent | Downloadable diagnostic report |
| S-19 | Admin Login | `/admin/login` | Admin | Admin authentication |
| S-20 | Admin Dashboard | `/admin` | Admin | System overview |
| S-21 | Admin Standards | `/admin/standards` | Admin | Standards management |
| S-22 | Admin Questions | `/admin/questions` | Admin | Question management |
| S-23 | Admin Question Edit | `/admin/questions/:id/edit` | Admin | Single question edit/validate |
| S-24 | Error / 404 | `/404` | All | Not found |
| S-25 | Error / 500 | `/500` | All | Server error |

### Navigation Flow

```
Public → S-01 (Landing)
  ↓ [Sign Up]
S-02 (Registration) → S-03 (Check Email)
  ↓ [Click verification link in email]
S-04 (Email Verified) → S-05 (Consent, multi-step)
  ↓ [Accept and submit]
S-06 (Consent Email Sent) → [Click link in email] → S-07 (Consent Confirmed)
  ↓
S-08 (Create Child Profile)
  ↓
S-09 (Parent Dashboard) ──────────────────────────────────────────┐
  ↓ [Start Diagnostic button]                                      │
S-10 (Diagnostic Intro) → S-11 (Assessment: question by question)  │
  │ [Pause] → S-12 (Paused) → [Resume] → S-11                    │
  ↓ [Last answer submitted]                                        │
S-13 (Complete celebration)                                        │
  ↓ [See My Results]                                              │
S-14 (Student Results) ←──── S-15 (Parent Results) ←─────────────┘
                                ↓ [Download PDF]
                              S-18 (PDF Report)
```

### Design Principles for Child-Appropriate UI

**Typography**:
- Question text: minimum 18px, Nunito or similar rounded sans-serif (approachable, readable).
- Answer options: 16px minimum.
- Labels and secondary text: 14px minimum.
- Line height: 1.6 for question text.
- NO all-caps text in student-facing screens.

**Color Palette (Assessment UI)**:
- Background: `#F8F9FF` (soft off-white with slight blue tint — calm, not clinical)
- Question card: `#FFFFFF` with subtle box shadow
- Primary CTA (Submit, Check Answer): `#3B7DD8` (friendly blue), white text
- Correct feedback color: `#4CAF50` (green) — used only post-assessment
- Incorrect feedback color: `#E57373` (soft red, not harsh) — used only post-assessment
- Progress bar fill: `#4A90D9`
- Below Par badge: `#F4A843` (orange — warm, not alarming)
- On Par badge: `#4A90D9` (blue)
- Above Par badge: `#66BB6A` (green)

**Iconography**:
- Use simple, filled icons (Material Symbols or Heroicons) — no decorative illustrations.
- Animals for avatars: friendly animal faces (bear, fox, owl, rabbit, etc.), illustrated in a flat style.
- No scary, violent, or culturally insensitive imagery.

**Tone and Copy**:
- Always address the student by first name in the student-facing UI.
- Use "Let's" instead of "You must": "Let's check your answer!" not "Check your answer."
- Mistakes are learning opportunities: "Oops! Let's look at that one together." (shown on results review, not during assessment).
- Completion messages should be enthusiastic: "You crushed it!" / "Math explorer level UP!"

### Error States

| Flow | Error Condition | Message | Action |
|------|----------------|---------|--------|
| Registration | Duplicate email | "An account with this email already exists." | Link to login |
| Registration | Network failure | "Something went wrong. Please try again." | Retry button |
| Email verification | Expired token | "This link has expired. We'll send a new one." | Auto-send new link |
| Consent | Not verified | "Please verify your email first." | Redirect to S-03 |
| Assessment | Question load failure | "Having trouble loading your question. Hold on..." | Auto-retry 3×, then "Try refreshing." |
| Assessment | Answer submit failure | "Couldn't save your answer. Please try again." | Retry button (keeps answer in field) |
| Assessment | Session expired | "You were away for a while. Your progress is saved!" | "Continue" button |
| Results | Scoring in progress | "We're calculating your results..." | Loading spinner, 5-second poll |
| PDF generation | Timeout | "Your report is taking longer than expected. It will be emailed to you." | Fallback to email delivery |

### Empty States

| Screen | Empty State | Message |
|--------|-------------|---------|
| Parent Dashboard (no children) | Child avatar placeholder | "Add your first child to get started!" + "Add Child" button |
| Parent Dashboard (child, no diagnostic) | Diagnostic illustration | "Ready to find [Child]'s math strengths? Start the free diagnostic!" + "Start Diagnostic" button |
| Admin Questions (no results for filter) | Empty inbox icon | "No questions match your filters. Try adjusting the search." |

---

## 1.8 Acceptance Criteria

### AC-1: Parent Account Creation

- [ ] AC-1.1: A parent can successfully complete registration with valid email, name, and password. A verification email is received within 60 seconds.
- [ ] AC-1.2: Attempting to register with an already-registered email returns an error message directing the user to log in.
- [ ] AC-1.3: The verification link expires after 24 hours. A second click after expiry returns an appropriate error and triggers a resend option.
- [ ] AC-1.4: A parent account with unverified email cannot create a child profile (API returns 403).
- [ ] AC-1.5: Password shorter than 8 characters is rejected with an inline validation error.
- [ ] AC-1.6: Password without a digit or uppercase is rejected.
- [ ] AC-1.7: After 5 failed login attempts, the account is locked for 15 minutes. An appropriate message is shown.

### AC-2: COPPA Consent

- [ ] AC-2.1: The consent flow presents both checkboxes unchecked by default.
- [ ] AC-2.2: The "Complete Consent" button is disabled until both checkboxes are checked.
- [ ] AC-2.3: A consent_record row is created in the database with correct user_id, timestamp, IP hash, and user agent after consent completion.
- [ ] AC-2.4: No child profile can be created before the consent record exists and email confirmation is clicked (API returns 403 with error code COPPA_CONSENT_REQUIRED).
- [ ] AC-2.5: Deleting an account does not delete the consent_record row.

### AC-3: Child Profile

- [ ] AC-3.1: A parent can create up to 5 child profiles; a 6th creation attempt returns an error.
- [ ] AC-3.2: Child display name accepts UTF-8 characters; HTML tags are stripped server-side.
- [ ] AC-3.3: A child profile is created with status = 'ACTIVE' and diagnostic_status = 'NOT_STARTED'.

### AC-4: Oregon Standards Database

- [ ] AC-4.1: The database contains exactly 29 Grade 4 Oregon standards across 5 domains (5 × 4.OA, 6 × 4.NBT, 7 × 4.NF, 9 × 4.GM, 3 × 4.DR).
- [ ] AC-4.2: The database contains exactly 9 Grade 3 prerequisite standards.
- [ ] AC-4.3: All 29 prerequisite relationship edges defined in FR-2.4 are present in the prerequisite_relationships table.
- [ ] AC-4.4: GET /api/v1/standards?grade=4&domain=4.OA returns exactly 5 standards.
- [ ] AC-4.5: GET /api/v1/standards/3.OA.C.7/prerequisites returns an empty array (it has no prerequisites in the G3 scope).
- [ ] AC-4.6: GET /api/v1/standards/4.NBT.B.5/prerequisites returns at least [3.OA.C.7, 3.NBT.A.3].
- [ ] AC-4.7: Admin changes to a standard are logged in standards_audit_log with old_values and new_values.

### AC-5: Question Bank

- [ ] AC-5.1: The seed question bank contains ≥ 142 questions total.
- [ ] AC-5.2: Each of the 9 prerequisite skills has ≥ 5 validated questions.
- [ ] AC-5.3: Each of the 29 Grade 4 standards has ≥ 3 validated questions.
- [ ] AC-5.4: Every question has is_validated = TRUE before it is eligible for diagnostic use.
- [ ] AC-5.5: KaTeX expressions in question_text render correctly on Chrome, Safari, and Firefox without visible errors.
- [ ] AC-5.6: Fraction input questions accept both reduced (1/2) and equivalent (2/4) as correct answers.
- [ ] AC-5.7: Bulk import of a valid JSON file with 10 questions succeeds; a file with one invalid question fails with a field-specific error and imports nothing.
- [ ] AC-5.8: The admin question list view shows avg_correct_rate for questions that have been answered ≥10 times.

### AC-6: Diagnostic Assessment

- [ ] AC-6.1: Starting a diagnostic for a student creates an assessment record with status = 'started' and returns the first question.
- [ ] AC-6.2: Starting a diagnostic for a student who already has a completed diagnostic returns an error (409: DIAGNOSTIC_ALREADY_COMPLETED).
- [ ] AC-6.3: Starting a diagnostic for a student with an in-progress diagnostic returns the existing assessment (200) rather than creating a new one.
- [ ] AC-6.4: Submitting an answer for question N causes the server to select and cache question N+1 via CAT logic.
- [ ] AC-6.5: If a student answers 3 questions on a skill all correctly, no further questions for that skill are served (termination condition met).
- [ ] AC-6.6: If a student answers all 3 questions for a skill incorrectly, the difficulty drops toward 1 across the served questions.
- [ ] AC-6.7: The assessment state_snapshot is updated in PostgreSQL on every answer submission.
- [ ] AC-6.8: After browser close and re-login, the student can resume the diagnostic from the last answered question (not from the beginning).
- [ ] AC-6.9: The correct_answer is never present in any API response before the assessment is completed.
- [ ] AC-6.10: All 5 Grade 4 domains have at least 1 question answered in every completed diagnostic.
- [ ] AC-6.11: Rapid submission (all questions answered in < 5 seconds each) sets flagged_for_review = TRUE on the assessment.
- [ ] AC-6.12: Font size toggle persists across question transitions within an assessment session.
- [ ] AC-6.13: High contrast mode changes the UI palette and persists for the session.
- [ ] AC-6.14: All answer inputs are keyboard-accessible and have appropriate ARIA labels (verified with axe-core).

### AC-7: Scoring & BKT Initialization

- [ ] AC-7.1: A student who answers 0/3 correctly on 3.OA.C.7 receives proficiency_level = 'Below Par' and p_mastered ≤ 0.15.
- [ ] AC-7.2: A student who answers 3/3 correctly on 3.OA.C.7 receives proficiency_level = 'Above Par' and p_mastered ≥ 0.75.
- [ ] AC-7.3: A student_skill_states row is created for each assessed standard upon diagnostic completion.
- [ ] AC-7.4: Overall level is computed as the mode of per-skill levels, with ties broken conservatively.
- [ ] AC-7.5: The diagnostic_completed event is published to Redis Streams after assessment completion.

### AC-8: Results Display

- [ ] AC-8.1: The student results screen (S-14) displays no numeric percentages — only visual bars and level labels.
- [ ] AC-8.2: The parent results screen (S-15) displays per-skill accuracy percentages, standard codes, and proficiency levels for all assessed skills.
- [ ] AC-8.3: The gap summary lists all Below Par skills in prerequisite-priority order (most foundational first).
- [ ] AC-8.4: The PDF download button generates a PDF within 10 seconds for a completed diagnostic.
- [ ] AC-8.5: The PDF does not contain the child's last name or date of birth.
- [ ] AC-8.6: Skill bar charts are animated on mount and respect prefers-reduced-motion.

### AC-9: Non-Functional

- [ ] AC-9.1: Assessment page loads in < 2 seconds at p95 under 100 concurrent users (measured via k6 load test).
- [ ] AC-9.2: Question transition time (answer submit → next question displayed) is < 500ms at p95.
- [ ] AC-9.3: All API responses include TLS 1.3; connections over TLS 1.2 or lower are rejected.
- [ ] AC-9.4: No student PII appears in application logs (verified by log scan).
- [ ] AC-9.5: axe-core automated accessibility scan reports zero critical or serious violations on all student-facing screens.
- [ ] AC-9.6: Load test of 1,000 concurrent assessment sessions completes without errors and with p99 response time < 2 seconds.

---

*End of PRD Stage 1 — Version 1.0*  
*MathPath Oregon | Standards Database & Diagnostic Assessment Engine*  
*Target Completion: Month 3*
