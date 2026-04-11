# Product Plan: PADI.AI

*Version 1.0 — April 2026 | Confidential — Internal Planning Document*

---

## 1. Product Overview

### Summary

PADI.AI is an AI-powered adaptive math learning platform purpose-built for Oregon 4th graders. It combines a precision diagnostic assessment (BKT + IRT psychometrics), a state-specific standards database (29 Oregon Grade 4 standards, 2021 edition), and an AI question generation pipeline (Claude Sonnet, GPT-4o, o3-mini via LangGraph multi-agent architecture) to deliver truly personalized math instruction — one that diagnoses each student's exact skill gaps, identifies the prerequisite Grade 3 concepts blocking Grade 4 progress, and generates infinitely varied practice until mastery is real and measured.

Oregon's 4th graders pass the state math proficiency bar at only 31% (NAEP 2024), eight points below the national average. PADI.AI's thesis is that this is a solvable problem — but only with a platform that starts from the root cause (unaddressed prerequisite gaps) rather than drilling more grade-level content at a student who lacks the foundation to understand it.

The platform serves three user types:
- **Students (primary):** Oregon 4th graders (ages 9–10) who interact with the adaptive practice interface daily
- **Parents:** Guardians who manage their child's account, monitor progress, and receive weekly reports
- **Teachers:** 4th grade classroom teachers who use PADI.AI as a differentiation tool and track class-level performance

---

### Key User Journeys

**Student Journey:**
1. Parent creates account (COPPA-compliant consent flow) → child account provisioned
2. Student completes 20–25 item diagnostic assessment (adaptive, ~20 minutes)
3. System generates personalized skill map (mastered, in-progress, not-started for all 29 standards)
4. Student begins first adaptive practice session based on highest-priority gap identified
5. Daily 15–20 minute sessions → BKT model updates mastery probability after each question
6. When BKT P(mastery) ≥ 0.90 for a standard, it is marked mastered; next standard in sequence begins
7. If Grade 3 prerequisite gap detected, system inserts prerequisite mini-lesson before Grade 4 standard
8. Every 8–10 weeks: summative reassessment validates BKT estimates, updates skill map
9. Parent receives weekly digest email with progress summary and encouragement script

**Parent Journey:**
1. Sees SBAC results / teacher feedback showing child is below proficiency → searches for help
2. Finds PADI.AI via Facebook group / Google ad / school newsletter
3. Starts free diagnostic (no payment required)
4. Receives diagnostic results: skill map showing which of 29 standards are mastered vs. gap
5. "Aha moment": sees specific gaps (e.g., "Your child hasn't mastered multiplying fractions — here's why it matters for middle school")
6. Upgrades to Pro ($14.99/month) to unlock full learning plan and ongoing adaptive practice
7. Receives weekly email: "Kai practiced 4 times this week and mastered 2 new skills. Next up: multi-step word problems."
8. Views parent dashboard: skill map progress, session history, projected SBAC readiness

**Teacher Journey:**
1. Discovers PADI.AI via colleague recommendation, OETC conference, or founder outreach
2. Signs up for classroom trial (free for 30 days with ≥15 students)
3. Sends home parent invitation links to students
4. Views class dashboard: distribution of mastery across 29 standards for all students
5. Identifies class-wide gaps (e.g., "22 of 25 students have a gap in 4.NF.B") → plans targeted small-group instruction
6. Uses PADI.AI as daily "math warm-up" (15 min individual practice) while circulating for small-group work
7. Receives monthly outcome report: class-level proficiency gains vs. diagnostic baseline
8. Shares outcome report with principal as evidence of SBAC readiness progress

---

### User Personas

**Persona 1: Maria, the Concerned Parent**
- **Background:** 38-year-old parent of two in Beaverton, OR. Works as a dental hygienist, partner works in tech. Family income ~$120K. Her 4th grader, Noah, received an SBAC score report in October showing "Level 1 — Below Standard" in math for the second consecutive year.
- **Goals:** Understand why Noah is struggling, find a solution that works without requiring a private tutor ($80–$120/hour is too expensive), help Noah build confidence before middle school
- **Frustrations:** IXL is "just more homework" — Noah hates it; Khan Academy videos are too long; she can't tell if any of these tools are actually working; she doesn't know enough math to help herself
- **How PADI.AI helps:** Free diagnostic gives Maria a concrete, plain-language answer to "where exactly is Noah?" The skill map converts abstract SBAC scores into specific, actionable gaps ("Noah hasn't mastered understanding fractions on a number line — this is blocking his ability to do fraction addition"). Weekly email digest keeps Maria informed without requiring her to log in. The parent dashboard lets her see progress in real time. She feels like PADI.AI is a partner, not just another app.

**Persona 2: Jaylen, the Struggling Student**
- **Background:** 9-year-old 4th grader at a Title I school in Portland. Lives with his grandmother, who is his primary caregiver. His classroom has 27 students; his teacher has limited time for individual differentiation. He's been told he "struggles with math" but doesn't know why.
- **Goals:** Stop feeling "dumb at math"; get through math class without anxiety; eventually feel like he "gets it"
- **Frustrations:** Math class moves too fast; he feels embarrassed when he doesn't know an answer; he doesn't know what he's supposed to review because he doesn't know what he doesn't know
- **How PADI.AI helps:** The diagnostic tells Jaylen (in child-friendly language) exactly what to work on — removing the anxiety of not knowing where to start. The adaptive engine never shows him problems that are too hard (it backs up to where he actually is). The multi-agent tutor gives hints without judgment — he can ask "I don't understand" as many times as he needs. Progress celebrations (mastery markers, streak counts) give Jaylen daily micro-wins that rebuild his math identity.

**Persona 3: Ms. Nguyen, the Overwhelmed Teacher**
- **Background:** 4th grade teacher at an elementary school in Salem-Keizer SD. 12 years of teaching experience. Has 26 students, 9 of whom are below grade level in math. Uses IXL for practice but finds that students are "just clicking through" without real learning. Her SBAC scores have stagnated for 3 years.
- **Goals:** Find a differentiation tool that actually diagnoses and remediates gaps without requiring her to individually assess each student; prove to her principal that she has a plan for her below-grade-level students; reduce the administrative burden of tracking 26 individual student progress trajectories
- **Frustrations:** IXL gives her a lot of data but not actionable insights; DreamBox requires too much setup and the district won't pay for it; she doesn't have time to manually differentiate instruction for 9 students with different gaps; parent communication about math progress takes hours every month
- **How PADI.AI helps:** Diagnostic run in first week of school gives Ms. Nguyen a class-level heat map across all 29 standards — immediately actionable for grouping students. Class dashboard shows her which standards are blocking the most students, so she can plan whole-class re-teaching sessions targeted at the most common gaps. Monthly outcome report is pre-formatted for sharing with her principal. Parent dashboard means parents self-serve progress info, reducing her email load.

---

## 2. Product Phases & Stage Definitions

### Proof of Concept (PoC) — Internal Only, Not User-Facing

**Definition:** The PoC is an internal prototype built and operated entirely by the founding team. It is not released to external users. Its purpose is to validate core technical assumptions before investing in production infrastructure.

**What it proves:**
1. That the AI question generation pipeline (LangGraph + Claude Sonnet + GPT-4o) can produce mathematically correct, grade-appropriate questions for Oregon Grade 4 standards at acceptable quality (≥75% first-pass validation)
2. That the BKT model (pyBKT) can be initialized with reasonable priors for Oregon Grade 4 standards and produce sensible mastery probability updates given simulated student response data
3. That the Oregon 2021 Math Standards can be modeled as a structured dependency graph and queried efficiently (e.g., "given student profile X, what is the next standard to practice?")
4. That the diagnostic assessment can be built as an adaptive test (computerized adaptive testing / CAT) that estimates student ability across standards in 20–25 items with acceptable measurement error

**PoC is complete when:** All four above assumptions are validated by internal testing with synthetic or manually-collected data. The founding team has confidence that the core technical stack will work at MVP scale.

**What PoC does NOT include:** Any user-facing UI, real student data, authentication, payment, or production deployment. It is a local development environment demo.

---

### MVP (Minimum Viable Product) — First Release to Real Users

**Definition:** The first version of PADI.AI released to actual students and parents. Designed to deliver the core value proposition (diagnostic + personalized learning plan + adaptive practice) with the minimum feature set required to make that delivery trustworthy, useful, and safe. The MVP is a consumer product (parent-paid) targeting individual families.

**Core value delivered by MVP:** A parent can sign up, their 4th grader completes a diagnostic, they receive a clear skill map, and their child can practice math adaptively for 3+ months with measurable learning gains — all on a COPPA-compliant, reliable platform.

**MVP Feature List:**
| # | Feature | Description |
|---|---------|-------------|
| 1 | COPPA-compliant parent registration & child account creation | Parent signs up, provides verifiable consent, creates child's account |
| 2 | Oregon Grade 4 standards database (29 standards, 5 domains) | Complete standards DB with prerequisite relationships |
| 3 | Adaptive diagnostic assessment (20–25 items, CAT) | IRT-based entry diagnostic covering all 29 standards |
| 4 | Student skill map (post-diagnostic) | Visual display of mastered / in-progress / not-started standards |
| 5 | Personalized learning plan generation | Sequenced plan addressing gaps in prerequisite order |
| 6 | AI-generated adaptive practice questions | LangGraph pipeline generating Oregon-standard-aligned questions |
| 7 | Question validation pipeline | Automated + human review ensuring ≥75% accuracy |
| 8 | BKT mastery tracking | Real-time mastery probability updates per standard after each question |
| 9 | Multi-agent tutoring hints | Step-by-step hint system (3 levels of scaffolding) |
| 10 | Grade 3 prerequisite content | Standards and questions for identified Grade 3 gaps |
| 11 | Session structure (15–20 min daily sessions) | Daily session with clear start/end, progress indicator |
| 12 | Basic parent dashboard | Session history, current skill map, standards mastered count |
| 13 | Freemium gating (free diagnostic + 2 weeks, paid Pro) | Stripe-integrated payment flow |
| 14 | Weekly parent email digest | Automated email summary of student activity and progress |
| 15 | Student progress celebrations | Mastery milestone markers, streak counters |
| 16 | In-app "flag a problem" button | Student/parent can flag incorrect or confusing questions |
| 17 | Password reset / account management | Basic account self-service |
| 18 | Mobile-responsive web UI (React/Next.js) | Works on tablet and phone browser; no native app required |

**What MVP explicitly does NOT include:** Teacher/classroom dashboard, district reporting, summative assessments, multi-child family accounts, social features, in-app chat support, offline mode, native iOS/Android apps.

> **Mobile/Tablet Strategy (Updated April 2026):** The primary student persona uses an iPad as their primary device. The revised approach is: **Stage 1–2:** Tablet-first responsive web (768px iPad portrait as primary breakpoint, not 1440px desktop). Explicit iPad Safari and Chromebook Chrome QA is required at every stage gate. **Stage 2–3:** Add PWA (Progressive Web App) with Service Worker for offline caching and home screen install — this covers ~80% of native app use cases at ~15% of the effort. **Post-MMP:** React Native with Expo for native iOS/Android if school/district contracts require App Store distribution. Touch targets must be ≥44×44px everywhere (WCAG 2.1 AA). Math input (fractions, multi-step expressions) must be validated on iPad Safari before every milestone.

---

### MMP (Minimum Marketable Product) — First Version Worth Selling Broadly

**Definition:** The first version of PADI.AI worth marketing to schools and districts as well as consumers. Adds the polish, institutional features, monetization infrastructure, and outcome reporting needed for B2B sales. The MMP is when PADI.AI becomes a credible commercial product — not just a beta app.

**MMP builds on MVP and adds:**
| # | Feature | Description |
|---|---------|-------------|
| 19 | Teacher/classroom dashboard | Class-level skill map, per-student progress, standard distribution heatmap |
| 20 | Class roster management | Teacher can add students, send parent invitations, manage classroom |
| 21 | Classroom license billing | School/classroom purchase flow; purchase order support |
| 22 | Multi-child family accounts | Parents can manage 2+ children from one account |
| 23 | Summative assessment (end-of-unit) | 8-week reassessment validating BKT estimates; SBAC-format questions |
| 24 | Monthly outcome report (parent) | PDF report showing learning gains vs. diagnostic baseline |
| 25 | Monthly outcome report (teacher) | Class-level proficiency report; SBAC readiness projection |
| 26 | FERPA-compliant data processing | Full DPA template; data isolation; no cross-district data sharing |
| 27 | Student streak and engagement mechanics | Daily streaks, mastery badges, weekly challenges |
| 28 | Question quality analytics dashboard (internal) | Admin view of validation rates, flagged questions, accuracy metrics |
| 29 | A/B testing infrastructure | Ability to test question types, UI variations, session structures |
| 30 | Customer support chat (Intercom or similar) | In-app support for parents and teachers |
| 31 | Annual subscription billing | Annual Pro plan ($99/year); school annual invoicing |
| 32 | SOC 2 Type I controls documentation | Formal security controls for school/district procurement requirements |

---

### Full Product v1.0 — Complete First-Generation Product

**Definition:** The production-ready, fully-featured first generation of PADI.AI. All core learning features complete. Ready for district-level sales, independent outcome evaluation, and Series A fundraising. Includes multi-grade content (Grades 3–5), full assessment suite, and advanced analytics.

**Full Product v1.0 adds to MMP:**
| # | Feature | Description |
|---|---------|-------------|
| 33 | Grade 3 standalone curriculum | Full 4th-grade-style product for 3rd graders (28 Grade 3 standards) |
| 34 | Grade 5 standalone curriculum | Extension upward; bridges to middle school readiness |
| 35 | District admin dashboard | District-level analytics, school comparison, grant reporting |
| 36 | SBAC readiness prediction | ML model predicting student's likely SBAC score category based on BKT data |
| 37 | Intervention alert system | Automatic alert to teacher if student hasn't practiced in 5+ days or shows sudden regression |
| 38 | Student goal-setting interface | Student can set weekly practice goals; parent co-signs |
| 39 | Differentiated report cards | Printable parent-teacher conference summary aligned to standards |
| 40 | API for district SIS integration | Integration with Synergy, PowerSchool for roster sync |
| 41 | SSO (Google Classroom, Clever) | Single sign-on for school deployments |
| 42 | Offline practice mode | Downloaded session cache for low-connectivity environments |
| 43 | Multilingual UI (Spanish) | UI localized for Oregon's large Spanish-speaking student population (~22% of Oregon students) |
| 44 | Advanced question bank analytics | Difficulty parameter refinement, item discrimination analysis |
| 45 | Independent outcome study integration | Data export for university research partner; IRB-compliant anonymization |

---

## 3. Milestone Table

| # | Milestone | Stage | Target Date | Success Criteria | Dependencies |
|---|-----------|-------|-------------|-----------------|--------------|
| M01 | Technical infrastructure setup | PoC | Month 1, Week 2 | AWS/GCP environment provisioned; GitHub repo initialized; CI/CD pipeline (GitHub Actions) running; PostgreSQL + Redis + pgvector deployed in dev | None |
| M02 | Oregon Grade 4 standards database built | PoC | Month 1, Week 4 | All 29 Oregon 2021 Grade 4 Math Standards entered as structured records; prerequisite relationships documented for all standards; Grade 3 prerequisite standards added (partial, for identified dependencies) | Oregon 2021 Math Standards document (CC-licensed, publicly available) |
| M03 | BKT model initialized and validated | PoC | Month 2, Week 2 | pyBKT model initialized with reasonable priors for Oregon Grade 4 standards; validated against simulated student response data (synthetic); BKT update function produces sensible mastery probability updates | Standards DB (M02); pyBKT library |
| M04 | AI question generation pipeline (v0.1) | PoC | Month 2, Week 4 | LangGraph pipeline can generate a question for any Oregon Grade 4 standard on demand; Generator + Validator + Standard Tagger agents functional; ≥60% first-pass validation rate on 50-question internal test | LangGraph; Anthropic API; OpenAI API |
| M05 | Adaptive diagnostic assessment (CAT) prototype | PoC | Month 3, Week 2 | CAT engine can select items adaptively based on current ability estimate; 20-item diagnostic produces ability estimate with SE ≤ 0.5 logits on simulated data; all 29 standards covered in diagnostic item bank | BKT model (M03); question generation pipeline (M04) |
| M06 | Prerequisites dependency graph complete | PoC | Month 3, Week 4 | Every Grade 4 standard has ≥1 documented Grade 3 prerequisite; dependency graph queryable ("given gap in 4.NF.B.3, what Grade 3 prerequisites are required?"); graph validated against ODE progressions document | Standards DB (M02) |
| M07 | COPPA-compliant auth system | MVP | Month 4, Week 2 | Auth0 integration complete; parent registration flow with verifiable parental consent (email verification + age gate); child accounts provisioned under parent; no PII collected from child before parental consent | Auth0; legal review of COPPA flow |
| M08 | Student-facing UI (diagnostic + practice) v0.1 | MVP | Month 4, Week 4 | Next.js frontend deployed to staging; student can complete diagnostic assessment; student can answer adaptive practice questions; mobile-responsive; WCAG 2.1 AA accessibility baseline | Auth system (M07); question generation pipeline (M04) |
| M09 | Question validation pipeline ≥75% accuracy | MVP | Month 5, Week 2 | Automated validation (SymPy + LLM validator) achieving ≥75% first-pass accuracy on 200-question test set; human review workflow for rejected questions; in-app "flag" button functional | Question generation pipeline (M04) |
| M10 | Personalized learning plan engine | MVP | Month 5, Week 4 | System generates sequenced learning plan from diagnostic output; plan respects prerequisite order; Grade 3 prerequisites inserted correctly for identified gaps; plan visible on student and parent UI | BKT model (M03); standards DB (M02); prereq graph (M06) |
| M11 | Parent dashboard v1.0 | MVP | Month 6, Week 2 | Parent can view: child's current skill map, sessions this week, standards mastered count, learning plan summary; weekly digest email auto-generated | Auth system (M07); learning plan engine (M10) |
| M12 | Beta launch (10–50 students) | Validation | Month 6, Week 4 | 10+ students onboarded from personal network; all completing diagnostic; all receiving learning plan; no critical bugs in first 2 weeks; founder monitoring daily | All MVP features above (partial) |
| M13 | Multi-agent tutoring hints (3-level scaffolding) | MVP | Month 7, Week 2 | Students can request hints during practice; 3-level progressive hints generated by LangGraph hint agent; hints are mathematically correct and grade-appropriate | Question generation pipeline (M04) |
| M14 | Freemium payment flow (Stripe) | MVP | Month 7, Week 4 | Stripe integration complete; free tier (diagnostic + 2 weeks) gated; Pro upgrade flow functional; subscription management (cancel, upgrade, downgrade) working; test with 5 real payment transactions | Auth system (M07) |
| M15 | Beta outcome data review | Validation | Month 8, Week 2 | Analysis of 8-week beta data: diagnostic accuracy agreement ≥80%, parent NPS ≥40, question flag rate ≤10%, ≥3 students showing measurable learning gain; go/no-go decision for MVP launch | Beta launch (M12) |
| M16 | MVP public launch | MVP | Month 10, Week 1 | PADI.AI Pro publicly available; Stripe accepting payments; App stable (99% uptime over launch week); first 10 paying customers within 2 weeks of launch | All MVP features complete; Stripe (M14); COPPA review |
| M17 | First paying customer (consumer) | MVP | Month 10, Week 2 | First Pro subscriber signs up and pays ($14.99); confirmation email sent; subscription active | MVP launch (M16) |
| M18 | 100 active students milestone | MVP | Month 11 | 100 students have completed the diagnostic and started the learning plan (paid + free); engagement rate ≥3 sessions/week for ≥50% of active students | MVP launch (M16) |
| M19 | Teacher/classroom dashboard v1.0 | MMP | Month 13, Week 2 | Teacher can view class roster, per-student skill maps, class-level standard distribution heatmap; teacher can send parent invitation links; classroom-level session activity summary | MVP complete; DPA template drafted |
| M20 | First school partnership (pilot, non-paying) | MMP | Month 14 | ≥1 Oregon elementary school with ≥15 students using PADI.AI in classroom; signed pilot agreement; teacher NPS collected at end of 4-week pilot | Teacher dashboard (M19); FERPA DPA template |
| M21 | COPPA/FERPA compliance formal review | MMP | Month 14, Week 4 | Third-party attorney review of data collection flows, DPA template, privacy policy, student data retention policies; all issues resolved; DPA template ready for school signatures | Auth system (M07); legal counsel engaged |
| M22 | Summative assessment feature | MMP | Month 15, Week 2 | 8-week summative assessment functional; SBAC-format questions; results compared to diagnostic baseline; parent and teacher outcome reports generated | Question generation pipeline; BKT model |
| M23 | Monthly outcome reports (parent + teacher) | MMP | Month 15, Week 4 | Automated PDF generation of monthly outcome reports for parents (student-level) and teachers (class-level); SBAC alignment language; first reports sent to all active users | Summative assessment (M22) |
| M24 | MMP launch & classroom license pricing | MMP | Month 16, Week 1 | MMP feature set complete; classroom license purchase flow functional ($8/student/year); school billing (PO + invoice support); 3+ schools in paid or pilot relationship | Teacher dashboard (M19); compliance review (M21); Stripe school billing |
| M25 | 500 active monthly students milestone | MMP | Month 17 | 500 students actively practicing (≥1 session in trailing 30 days); consumer + school combined | MMP launch (M24) |
| M26 | First paying school partnership | MMP | Month 18 | First school signs annual classroom license; purchase order received; DPA signed; school billing active | Compliance review (M21); teacher dashboard (M19) |
| M27 | Outcome data for investor/press narrative | MMP | Month 20 | Internal study of ≥100 students with ≥30 hours PADI.AI use showing ≥20% proficiency gain vs. diagnostic baseline; report formatted for sharing with investors and press | 100+ students with sufficient data (from Month 10+) |
| M28 | Grade 5 curriculum launch | Full v1.0 | Month 22 | All Oregon Grade 5 Math Standards (24 standards) in database; Grade 5 adaptive practice functional; Grade 5 diagnostic available; first Grade 5 students onboarded | Grade 4 platform stable; standards DB extension |
| M29 | SSO (Google Classroom / Clever) | Full v1.0 | Month 22, Week 4 | Teachers can provision student accounts via Google Classroom or Clever; roster sync automated; SSO login for student and teacher | MMP complete; Google Workspace API; Clever API |
| M30 | Series A readiness metrics achieved | Full v1.0 | Month 24 | ARR ≥ $200K; 1,500+ active monthly students; 5+ paying school partnerships; independent outcome data published or in progress; 12+ months runway | All above milestones |

---

## 4. Feature Roadmap by Stage

### Stage 1 (Months 1–3): Foundation & Diagnostic

**Goal:** Build the technical foundation and core diagnostic capability. End state: internal team can run a simulated student through a diagnostic and receive a skill map.

---

**F01: Oregon Grade 4 Standards Database**
- User story: *As a product manager, I want every Oregon Grade 4 standard stored as a structured record (ID, domain, description, prerequisite IDs, grade level) so that every question, learning plan, and mastery report can reference specific standards.*
- Priority: P0
- Effort: M
- Dependencies: 2021 Oregon Math Standards document (publicly available)

**F02: Grade 3 Prerequisite Standards Database**
- User story: *As an adaptive engine, I want to look up the Grade 3 prerequisites for any Grade 4 standard so that I can insert remediation content when a student has a prerequisite gap.*
- Priority: P0
- Effort: M
- Dependencies: F01; ODE Grade 3–4 progression document

**F03: Standards Dependency Graph (Directed Acyclic Graph)**
- User story: *As a learning plan engine, I want to query a directed graph of standard prerequisite relationships so that I can sequence learning content in prerequisite order.*
- Priority: P0
- Effort: M
- Dependencies: F01, F02

**F04: IRT Item Bank (Seed Items for Diagnostic)**
- User story: *As the diagnostic engine, I want a seed bank of 60+ pre-calibrated IRT items (at least 2 per standard) so that the CAT can function before AI-generated questions are validated.*
- Priority: P0
- Effort: L
- Dependencies: F01; human item writing (founder + math educator consultant)

**F05: Computerized Adaptive Testing (CAT) Engine**
- User story: *As a student, I want the diagnostic to feel the right difficulty — not too easy, not too hard — so that I stay engaged and the results are accurate.*
- Priority: P0
- Effort: XL
- Dependencies: F04; pyBKT / IRT library

**F06: BKT Model Initialization (pyBKT)**
- User story: *As the adaptive engine, I want a BKT model initialized with reasonable priors for each Grade 4 standard so that I can estimate student mastery probability and update it after every question.*
- Priority: P0
- Effort: L
- Dependencies: F01; pyBKT library

**F07: AI Question Generation Pipeline — Generator Agent**
- User story: *As a student, I want every practice problem to be a fresh, unique question so that I'm genuinely learning the concept rather than memorizing answers.*
- Priority: P0
- Effort: XL
- Dependencies: F01; LangGraph; Anthropic API; OpenAI API

**F08: AI Question Generation Pipeline — Validator Agent**
- User story: *As a parent, I want to trust that every question my child sees has been checked for mathematical accuracy so that I don't have to worry about my child learning incorrect math.*
- Priority: P0
- Effort: L
- Dependencies: F07; SymPy library; OpenAI API (second-pass validation)

**F09: AI Question Generation Pipeline — Standard Tagger Agent**
- User story: *As the BKT engine, I want every generated question tagged to a specific Oregon standard so that mastery updates are applied to the correct standard.*
- Priority: P0
- Effort: S
- Dependencies: F07, F08

**F10: Question Difficulty Calibrator Agent**
- User story: *As the adaptive engine, I want generated questions difficulty-calibrated to a target IRT theta parameter so that practice sessions maintain appropriate challenge level.*
- Priority: P1
- Effort: M
- Dependencies: F07, F08, F09

**F11: Development Infrastructure (AWS/GCP, PostgreSQL, Redis, pgvector)**
- User story: *As the engineering team, I want a reproducible cloud development environment so that all development is consistent and deployable.*
- Priority: P0
- Effort: M
- Dependencies: AWS or GCP account; Terraform or CDK scripts

**F12: FastAPI Backend Skeleton**
- User story: *As the engineering team, I want a FastAPI-based backend with defined API endpoints so that frontend and backend development can proceed in parallel.*
- Priority: P0
- Effort: S
- Dependencies: F11

**F13: CI/CD Pipeline (GitHub Actions)**
- User story: *As the engineering team, I want automated testing and deployment on every pull request so that we catch regressions before they reach users.*
- Priority: P1
- Effort: S
- Dependencies: F11, F12

---

### Stage 2 (Months 4–6): Learning Plan Engine

**Goal:** Build the student-facing application shell, COPPA-compliant auth, personalized learning plan engine, and parent dashboard. End state: first beta students can sign up, complete the diagnostic, and receive a personalized learning plan.

---

**F14: Auth0 COPPA-Compliant Authentication**
- User story: *As a parent, I want to create an account for my child with my explicit consent so that I control what data is collected and my child's privacy is protected.*
- Priority: P0
- Effort: M
- Dependencies: Auth0 account; COPPA legal review; F11

**F15: Parent Registration & Child Account Provisioning Flow**
- User story: *As a parent, I want to sign up in under 5 minutes and immediately invite my child to start the diagnostic so that we can get started without friction.*
- Priority: P0
- Effort: M
- Dependencies: F14

**F16: Student Diagnostic UI (Next.js)**
- User story: *As a student, I want a clean, simple question interface that shows me one question at a time, lets me select an answer, and gives me feedback, so that taking the diagnostic doesn't feel stressful.*
- Priority: P0
- Effort: L
- Dependencies: F05; F12; F15

**F17: Student Skill Map (Post-Diagnostic Visualization)**
- User story: *As a parent, I want to see a visual map of which math standards my child has mastered, is working on, and hasn't started, so that I understand exactly where they stand.*
- Priority: P0
- Effort: M
- Dependencies: F05, F06, F16

**F18: Personalized Learning Plan Engine**
- User story: *As a student, I want to know exactly what to practice next — based on my diagnostic results — so that I'm always working on the most important gap, not random topics.*
- Priority: P0
- Effort: XL
- Dependencies: F03, F06, F17

**F19: Learning Plan Display UI**
- User story: *As a parent, I want to see my child's personalized learning plan — what they're working on, what's coming next, and how it connects to their goals — so that I understand the plan and trust it.*
- Priority: P1
- Effort: M
- Dependencies: F18, F16

**F20: Adaptive Practice Session Engine**
- User story: *As a student, I want my practice session to serve me questions at the right difficulty level — updating in real-time based on how I'm doing — so that I'm always challenged but never overwhelmed.*
- Priority: P0
- Effort: XL
- Dependencies: F06, F07, F08, F09, F10, F18

**F21: Practice Session UI**
- User story: *As a student, I want a distraction-free, encouraging interface for my 15-minute math practice session so that I can focus and feel good about making progress.*
- Priority: P0
- Effort: L
- Dependencies: F20

**F22: Multi-Agent Tutoring Hint System (3-Level Scaffolding)**
- User story: *As a student, I want to ask for a hint when I'm stuck — and get a hint that helps me think through the problem rather than just giving me the answer — so that I actually learn.*
- Priority: P1
- Effort: L
- Dependencies: F07; LangGraph

**F23: Grade 3 Prerequisite Remediation Insertion**
- User story: *As the learning plan engine, I want to automatically insert Grade 3 prerequisite practice when a student's diagnostic shows a Grade 3 gap is blocking a Grade 4 standard, so that the student builds the foundation they need rather than struggling with content they can't yet access.*
- Priority: P0
- Effort: M
- Dependencies: F02, F03, F18, F20

**F24: BKT Mastery Update Loop (Per-Question)**
- User story: *As the adaptive engine, I want to update the BKT mastery probability for the current standard after every question so that the system always has an accurate, up-to-date estimate of what the student knows.*
- Priority: P0
- Effort: M
- Dependencies: F06, F20

**F25: Mastery Milestone Marker & Standard Completion**
- User story: *As a student, I want to see a clear celebration when I master a standard (BKT P ≥ 0.90) so that I feel the tangible reward of hard work and stay motivated to continue.*
- Priority: P1
- Effort: S
- Dependencies: F24, F21

**F26: Basic Parent Dashboard v1.0**
- User story: *As a parent, I want a dashboard showing my child's session history, current skill map, and number of standards mastered so that I can track progress without needing to understand the technical details.*
- Priority: P1
- Effort: M
- Dependencies: F17, F24, F25

**F27: Weekly Parent Email Digest (Automated)**
- User story: *As a parent, I want to receive a weekly email summarizing my child's practice activity and progress so that I stay informed even if I don't log into the app every day.*
- Priority: P1
- Effort: M
- Dependencies: F26; SendGrid or AWS SES

**F28: In-App "Flag a Problem" Button**
- User story: *As a parent or student, I want to flag a question that seems wrong or confusing so that the PADI.AI team can review it and fix it quickly.*
- Priority: P1
- Effort: S
- Dependencies: F21; F12

**F29: Beta Onboarding Flow (Founder-Assisted)**
- User story: *As a beta tester, I want a simple, guided onboarding experience that walks me through creating an account, starting the diagnostic, and understanding my child's results so that I don't need to figure it out on my own.*
- Priority: P0
- Effort: S
- Dependencies: F15, F16, F17, F26

---

### Stage 3 (Months 7–10): Adaptive Practice & Tutoring → MVP

**Goal:** Complete all MVP features, launch Stripe payment flow, polish the student and parent experience, and launch the MVP publicly. End state: PADI.AI Pro is available to any Oregon parent.

---

**F30: Stripe Freemium Payment Integration**
- User story: *As a parent, I want to upgrade from the free diagnostic to a paid Pro subscription smoothly, with clear pricing and easy cancellation, so that I feel confident in the purchase.*
- Priority: P0
- Effort: M
- Dependencies: F15; Stripe account; Auth0

**F31: Freemium Content Gating**
- User story: *As the product, I want to limit free tier users to the diagnostic + 3 practice sessions (2 weeks) and then prompt upgrade so that we convert engaged free users to paid.*
- Priority: P0
- Effort: S
- Dependencies: F30, F20

**F32: Streak Mechanics (Daily Practice Streak)**
- User story: *As a student, I want to see my daily practice streak so that I'm motivated to practice every day and build a math habit.*
- Priority: P1
- Effort: S
- Dependencies: F21

**F33: Session Progress Indicator**
- User story: *As a student, I want to see how far I am through today's session so that I know how much time is left and can plan accordingly.*
- Priority: P1
- Effort: S
- Dependencies: F21

**F34: Mobile-Responsive UI Audit & Fixes**
- User story: *As a parent whose child uses a tablet, I want the PADI.AI interface to work perfectly on a tablet browser so that my child can practice comfortably without needing a laptop.*
- Priority: P0
- Effort: M
- Dependencies: F16, F21, F26

**F35: WCAG 2.1 AA Accessibility Audit**
- User story: *As a student with a visual or cognitive accessibility need, I want PADI.AI to meet accessibility standards so that I can use it without barriers.*
- Priority: P1
- Effort: M
- Dependencies: F16, F21; accessibility audit tool (Axe, Lighthouse)

**F36: Performance Optimization (< 2s page load)**
- User story: *As a student on a home internet connection, I want PADI.AI to load quickly so that slow loading doesn't interrupt my practice session.*
- Priority: P1
- Effort: M
- Dependencies: F11; Redis caching layer; CDN configuration

**F37: Error Handling & Recovery**
- User story: *As a student mid-session, I want the app to gracefully handle network errors and resume my session where I left off so that I don't lose progress.*
- Priority: P1
- Effort: M
- Dependencies: F20; F21; Redis session state

**F38: Privacy Policy & Terms of Service (COPPA-compliant)**
- User story: *As a parent, I want to read a clear, plain-language privacy policy that explains exactly what data is collected about my child and how it is used so that I can make an informed decision.*
- Priority: P0
- Effort: S (legal drafting); S (engineering integration)
- Dependencies: Legal counsel; F15

**F39: MVP Analytics Instrumentation (Mixpanel or Amplitude)**
- User story: *As the product team, I want to track key user events (diagnostic start, diagnostic complete, session start, session complete, upgrade, cancellation) so that we can measure engagement and conversion.*
- Priority: P0
- Effort: M
- Dependencies: F16, F21, F30; student-safe analytics (no PII to third-party analytics)

**F40: MVP Launch Marketing Landing Page**
- User story: *As a potential customer, I want to visit a clear landing page that explains what PADI.AI does, shows the diagnostic results example, and makes it easy to start for free, so that I understand the value immediately.*
- Priority: P0
- Effort: M
- Dependencies: Design system; Next.js

---

### Stage 4 (Months 11–14): Assessment & Reporting → MVP Milestone

**Goal:** Add summative assessment, formal outcome reporting, and teacher-facing features to close the loop on learning outcomes and enable school-channel sales conversations.

---

**F41: Summative Assessment (8-Week Reassessment)**
- User story: *As a parent, I want my child to take a full reassessment every 8 weeks so that I can see concrete evidence of learning gains compared to where they started.*
- Priority: P0
- Effort: L
- Dependencies: F04, F05, F06; question bank with sufficient items

**F42: Outcome Report Generator (Parent)**
- User story: *As a parent, I want a formatted PDF report every month showing my child's learning gains, standards mastered, and projected SBAC readiness so that I can share it with their teacher.*
- Priority: P0
- Effort: M
- Dependencies: F41; F24; PDF generation library

**F43: Outcome Report Generator (Teacher)**
- User story: *As a teacher, I want a monthly class-level outcome report showing average proficiency gains, distribution of mastery, and SBAC readiness projection so that I can report to my principal with data.*
- Priority: P0
- Effort: M
- Dependencies: F42; teacher account model

**F44: Teacher / Classroom Dashboard v1.0**
- User story: *As a teacher, I want to see a class-level heatmap of standard mastery across all my students so that I can immediately identify class-wide gaps to address in whole-group instruction.*
- Priority: P0
- Effort: L
- Dependencies: F17; F24; teacher registration flow

**F45: Teacher Registration & Classroom Creation**
- User story: *As a teacher, I want to create a classroom, add students from my roster, and send home parent invitation links, all in under 15 minutes, so that setup doesn't consume my planning time.*
- Priority: P0
- Effort: M
- Dependencies: F14; F44

**F46: FERPA-Compliant Data Processing (DPA Template)**
- User story: *As a school administrator, I want to sign a Data Processing Agreement with PADI.AI that clearly defines how student data is handled, so that my district can approve PADI.AI for classroom use.*
- Priority: P0
- Effort: S (engineering: data isolation); L (legal: DPA drafting)
- Dependencies: Legal counsel; F11 data architecture

**F47: Class Roster Management (Bulk Import)**
- User story: *As a teacher, I want to import my class roster from a CSV or from Google Classroom so that I don't have to manually enter 25 students.*
- Priority: P1
- Effort: M
- Dependencies: F45; CSV parser; Google Classroom API (optional)

**F48: Per-Student Progress View (Teacher)**
- User story: *As a teacher, I want to click on any student in my class and see their full skill map and recent session activity so that I can have an informed conversation with their parent at conferences.*
- Priority: P1
- Effort: M
- Dependencies: F44; F17

**F49: Classroom License Billing (Stripe)**
- User story: *As a school administrator, I want to purchase a classroom license for my grade level by credit card or purchase order so that PADI.AI can be funded through our school budget.*
- Priority: P0
- Effort: M
- Dependencies: F30; Stripe invoicing

**F50: First School Pilot Onboarding**
- User story: *As a school pilot participant, I want a dedicated onboarding session (video call with founder) that walks my teacher through setup and gives my principal a one-page outcome tracking overview, so that the pilot starts successfully.*
- Priority: P0 (operational, not engineering)
- Effort: S (engineering); M (founder time)
- Dependencies: F44, F45, F46, F49

---

### Stage 5 (Months 15–20): MMP Polish & Monetization

**Goal:** Launch MMP with full polish, engagement mechanics, multi-child accounts, school infrastructure, and start building toward Series A metrics. First paying school partnership.

---

**F51: Multi-Child Family Accounts**
- User story: *As a parent with two Oregon elementary students, I want to manage both children from one account at a family price, so that PADI.AI is affordable for my whole family.*
- Priority: P1
- Effort: M
- Dependencies: F14, F15, F30

**F52: Family Plan Pricing ($22.99/month for up to 3 children)**
- User story: *As a parent of multiple children, I want a family pricing option that is cheaper per child than individual subscriptions so that I have an incentive to enroll all my kids.*
- Priority: P1
- Effort: S
- Dependencies: F51, F30

**F53: Annual Subscription Flow ($99/year)**
- User story: *As a parent who is committed to PADI.AI long-term, I want to pay annually at a discount so that I save money and PADI.AI has predictable revenue.*
- Priority: P1
- Effort: S
- Dependencies: F30

**F54: Mastery Badges & Achievement System**
- User story: *As a student, I want to earn badges for milestones like "10 standards mastered" and "30-day streak" so that I have visible, shareable proof of my math progress.*
- Priority: P2
- Effort: M
- Dependencies: F25, F32

**F55: Weekly Challenge Mode**
- User story: *As a student, I want a special weekly challenge that's a bit harder than normal so that I can stretch beyond my comfort zone and feel proud of accomplishing something difficult.*
- Priority: P2
- Effort: M
- Dependencies: F20, F21

**F56: Parent-Controlled Practice Schedule**
- User story: *As a parent, I want to set a recommended daily practice time (e.g., 4:30–5:00 PM on school days) so that PADI.AI fits into our family routine.*
- Priority: P2
- Effort: S
- Dependencies: F14, F27

**F57: A/B Testing Infrastructure**
- User story: *As the product team, I want to run A/B tests on question formats, session structures, and onboarding flows so that we can systematically improve conversion and engagement.*
- Priority: P1
- Effort: M
- Dependencies: F39; feature flag system (LaunchDarkly or Unleash)

**F58: Customer Support Chat (Intercom)**
- User story: *As a parent with a billing question or a teacher with a setup issue, I want in-app chat support so that I can get help without sending email into a void.*
- Priority: P1
- Effort: S
- Dependencies: Intercom account; F15

**F59: Question Quality Analytics Dashboard (Internal)**
- User story: *As the CTO, I want a dashboard showing daily question validation pass rates, flagged question counts, and resolution times so that I can monitor and maintain question quality.*
- Priority: P1
- Effort: M
- Dependencies: F08, F28, F39

**F60: SOC 2 Type I Controls Documentation**
- User story: *As a school district procurement officer, I want to see PADI.AI's SOC 2 Type I report so that I can satisfy our district's IT security review requirements.*
- Priority: P1
- Effort: L (6–8 weeks with Vanta/Drata)
- Dependencies: F11 infrastructure; Vanta or Drata account (~$500/month)

**F61: MMP Launch & PR**
- User story: *As a potential school customer who reads EdSurge, I want to see a press article about PADI.AI's outcome data so that I can discover and evaluate PADI.AI without the PADI.AI team having to cold-outreach me.*
- Priority: P1 (operational)
- Effort: M (founder time)
- Dependencies: Outcome data (M27); press kit

---

### Stage 6 (Months 21–24): Full Product & Expansion

**Goal:** Launch Grade 5 curriculum, SSO integrations, district-level features, and achieve Series A readiness metrics. End state: Full Product v1.0.

---

**F62: Grade 5 Oregon Standards Database**
- User story: *As a 5th grade student, I want PADI.AI to have a personalized learning path for my grade level so that I can continue my math mastery journey.*
- Priority: P0 (for expansion)
- Effort: M
- Dependencies: F01 methodology; 2021 Oregon Grade 5 Standards document

**F63: Grade 5 Diagnostic & Adaptive Practice**
- User story: *As a parent of a 5th grader, I want PADI.AI to offer the same diagnostic-first adaptive practice for Grade 5 that it offers for Grade 4 so that my child can benefit too.*
- Priority: P0 (for expansion)
- Effort: L
- Dependencies: F62; F05, F20

**F64: SSO — Google Classroom Integration**
- User story: *As a teacher using Google Classroom, I want to provision student accounts and sync my class roster through Google Classroom so that I don't have to manage accounts separately.*
- Priority: P1
- Effort: L
- Dependencies: F45; Google Classroom API

**F65: SSO — Clever Integration**
- User story: *As a district IT administrator, I want PADI.AI to integrate with Clever so that student authentication and roster provisioning are handled through our existing district identity system.*
- Priority: P1
- Effort: L
- Dependencies: F45; Clever API

**F66: District Admin Dashboard**
- User story: *As a district curriculum coordinator, I want a dashboard showing aggregate mastery data across all schools and grade levels in my district so that I can identify systemic gaps and report to the school board.*
- Priority: P0 (for district sales)
- Effort: L
- Dependencies: F44; multi-school data model

**F67: SBAC Readiness Prediction Model**
- User story: *As a teacher, I want PADI.AI to predict which of my students are at risk of scoring below proficient on the spring SBAC so that I can prioritize intervention before the test.*
- Priority: P1
- Effort: L
- Dependencies: F41; F24; ML model trained on BKT data + SBAC outcomes

**F68: Multilingual UI — Spanish (ES)**
- User story: *As a Spanish-speaking parent, I want the PADI.AI parent dashboard and email reports in Spanish so that I can understand my child's progress without needing an interpreter.*
- Priority: P1
- Effort: M
- Dependencies: F26, F27; professional translation; i18n library

**F69: Student Goal-Setting Interface**
- User story: *As a student, I want to set my own weekly practice goal (e.g., "I will practice 4 times this week") and see whether I achieved it so that I feel ownership over my learning.*
- Priority: P2
- Effort: S
- Dependencies: F21, F32

**F70: District License Billing & Contract Flow**
- User story: *As a district business administrator, I want to receive a formal proposal, sign a multi-year district license agreement, and be invoiced annually, so that PADI.AI can be funded through our district EdTech budget.*
- Priority: P0 (for district revenue)
- Effort: M
- Dependencies: F49; contract template; legal review

**F71: University Research Partnership Data Export**
- User story: *As a university researcher partnered with PADI.AI, I want to access anonymized student outcome data via a secure, IRB-compliant data export so that I can conduct independent outcome evaluation.*
- Priority: P1
- Effort: M
- Dependencies: F41; F24; IRB-compliant anonymization pipeline; university research partner identified

---

## 5. Resource Plan

### Team Composition by Stage

**Stage 1–2 (Months 1–6): Founding Team Only**

| Role | FTE | Hire/Contract | Notes |
|------|-----|---------------|-------|
| Technical Founder / CTO | 1.0 | Founder | Full-stack + ML; leads all engineering |
| Product / CEO Founder | 1.0 | Founder | Product strategy, GTM, customer development |
| Math Education Consultant | 0.25 | Contract | Part-time; builds standards DB, validates questions; ~$3,000 |
| COPPA/FERPA Legal Counsel | 0.05 | Contract | 10 hours at ~$350/hr = ~$3,500 for initial review |

**Stage 3 (Months 7–10): First Engineering Hire**

| Role | FTE | Annual Salary | Monthly Cost |
|------|-----|---------------|-------------|
| Technical Founder / CTO | 1.0 | $0 (founder equity) | — |
| Product / CEO Founder | 1.0 | $0 (founder equity) | — |
| Senior Full-Stack Engineer | 1.0 | $140,000 | $11,667 |
| Math Education Consultant | 0.25 | $48,000/yr FTE equivalent | $1,000/mo contract |
| Designer (UI/UX) | 0.5 | $100,000 FTE equiv. | $4,167/mo contract |

*Monthly burn at Stage 3: ~$17,000–$20,000 (including infrastructure, benefits, contractor fees)*

**Stage 4 (Months 11–14): Growth Team**

| Role | FTE | Annual Salary | Monthly Cost |
|------|-----|---------------|-------------|
| Technical Founder / CTO | 1.0 | $120,000 (market salary at seed) | $10,000 |
| Product / CEO Founder | 1.0 | $100,000 | $8,333 |
| Senior Full-Stack Engineer | 1.0 | $140,000 | $11,667 |
| ML Engineer | 0.5 | $160,000 FTE equiv. | $6,667/mo contract |
| Designer (UI/UX) | 0.5 | $100,000 FTE equiv. | $4,167/mo contract |
| Math Education Consultant | 0.25 | — | $1,000/mo contract |

*Monthly burn at Stage 4: ~$45,000–$50,000*

**Stage 5–6 (Months 15–24): Scaling Team (post-seed round)**

| Role | FTE | Annual Salary | Monthly Cost |
|------|-----|---------------|-------------|
| CEO (Founder) | 1.0 | $120,000 | $10,000 |
| CTO (Founder) | 1.0 | $120,000 | $10,000 |
| Senior Full-Stack Engineer | 2.0 | $140,000 each | $23,333 |
| ML Engineer | 1.0 | $160,000 | $13,333 |
| Product Manager | 1.0 | $120,000 | $10,000 |
| Designer (UI/UX) | 1.0 | $100,000 | $8,333 |
| Head of Growth / Marketing | 1.0 | $110,000 | $9,167 |
| Customer Success (Schools) | 1.0 | $80,000 | $6,667 |
| Math Education Lead | 0.5 | $90,000 FTE equiv. | $3,750/mo contract |

*Monthly burn at Stage 5–6: ~$95,000–$105,000 (excluding infrastructure and benefits)*
*With 25% benefits load: ~$120,000–$130,000/month all-in*

---

### Curriculum Specialist Contractor

A key non-engineering resource needed from Stage 2 onward. This is a part-time contractor role, not a full-time hire.

| Attribute | Details |
|---|---|
| **Role** | Oregon-credentialed elementary math educator (Grade 3–5) |
| **Engagement type** | Freelance contractor via Upwork or direct referral |
| **Start** | Stage 2 kickoff (Month ~5) |
| **Hours/month** | 10–15 hrs/month |
| **Rate** | $75–$100/hr |
| **Monthly cost** | $750–$1,500/month |
| **Duration** | Ongoing through MMP and beyond |

**Responsibilities:**
1. Review 30–50 AI-generated questions per month for mathematical accuracy, Oregon OSAS format alignment, and age-appropriateness
2. Spot-check BKT mastery thresholds for pedagogical reasonableness
3. Advise on hint language and explanation quality for the Tutor Agent
4. Review Spanish translations of math vocabulary (Stage 5) — requires bilingual educator for this phase

**How to find:**
- Upwork: Search "Oregon elementary math teacher" or "Common Core math 4th grade curriculum"
- LinkedIn: Search "Oregon Department of Education" + "curriculum specialist"
- Oregon Education Association (OEA): Professional network referrals
- Local substitute teacher networks in Portland/Beaverton/Salem areas

---

### Development Cost Per Stage

| Stage | Months | Engineering Headcount | Avg Monthly Burn | Total Dev Cost |
|-------|--------|----------------------|------------------|----------------|
| Stage 1–2 (Foundation + Diagnostic) | 1–6 | 2 founders + 0.25 consultant | ~$8,000 | ~$48,000 |
| Stage 3 (MVP Build + Launch) | 7–10 | 2 founders + 1 senior eng + 0.5 designer | ~$22,000 | ~$88,000 |
| Stage 4 (Assessment + School Features) | 11–14 | 2 founders + 1 senior eng + 0.5 ML + 0.5 designer | ~$42,000 | ~$168,000 |
| Stage 5 (MMP + Monetization) | 15–20 | Full team (9 FTE equivalent) | ~$120,000 | ~$720,000 |
| Stage 6 (Full Product + Expansion) | 21–24 | Full team (9 FTE equivalent) | ~$125,000 | ~$500,000 |
| **Total (24 months)** | | | | **~$1,524,000** |

---

### Solo Development Mode — Revised Timeline & Assumptions

> **Updated April 2026:** PADI.AI is being built by a single developer using Claude Code AI agents as the primary development force multiplier. This section supersedes the team-based estimates above for planning purposes.

#### Development Model

| Factor | Team-Based (Original) | Solo + AI Agents (Revised) |
|---|---|---|
| Team size | 3–7 people | 1 developer + Claude Code agents |
| Primary dev method | Human engineers + PR reviews | AI agent task execution + human review/testing |
| Communication overhead | Daily standups, PRs, code reviews | Eliminated — single decision-maker |
| Boilerplate/CRUD speed | Standard human velocity | ~2× faster (AI generation) |
| Complex architecture speed | Fast (team specialization) | ~50% slower (single reviewer) |
| COPPA/security decisions | Team discussion | Always use Claude Sonnet 4.6; never delegate to local models |

#### Agent-Executable Task Sizing

Tasks are broken into **agent-executable chunks** — discrete, independently testable units of work a Claude Code agent can complete in a single session (2–4 hours):

| Task Type | Good Agent Task? | Example |
|---|---|---|
| Single API endpoint (CRUD) | ✅ Yes | `POST /api/v1/students/{id}/diagnostic/start` |
| Single React component | ✅ Yes | `DiagnosticProgressBar` component with tests |
| Single algorithm function | ✅ Yes | `bkt_update(prior, correct, params)` |
| Database migration | ✅ Yes | Alembic migration for `assessment_sessions` table |
| Full stage end-to-end | ❌ Too big | Split into individual endpoints + components |
| Architecture decisions | ❌ Wrong tool | Use Plan mode / Opus 4.6 first |

#### Revised Timeline (Solo + AI Agents)

| Stage | Original (Team) | Solo Optimistic | Solo Realistic | Key Constraint |
|---|---|---|---|---|
| Stage 0 (Infrastructure + LLM Layer) | Not in original plan | 3 weeks | 4 weeks | One-time setup |
| Stage 1 (Foundation + Diagnostic) | 3 months | 4 months | 5 months | COPPA flow complexity; 500+ question generation |
| Stage 2 (Learning Plan + Question Gen) | 3 months | 5 months | 6 months | LLM validation pipeline throughput |
| Stage 3 (Adaptive AI Tutoring) | 4 months | 6 months | 8 months | LangGraph + BKT integration complexity |
| Stage 4 (MVP) | 4 months | 5 months | 7 months | IRT + assessment + dashboards |
| Stage 5 (MMP) | 6 months | 8 months | 10 months | Stripe + school onboarding + i18n |
| **Total to MMP** | **20 months** | **30 months** | **36 months** | |

**Recommendation:** Budget for 30 months (optimistic) and plan for 36 months (realistic). If timeline needs to compress, reduce scope within each stage rather than cutting quality on COPPA compliance or BKT accuracy.

#### Stage 0: Pre-Development Infrastructure (Weeks 1–4)

Before writing any product code, complete this setup stage:

| Task | Estimated Time | Model |
|---|---|---|
| Turborepo monorepo setup + pnpm workspaces | 4–6 hrs | Qwen local |
| LiteLLM abstraction layer + LLM_ROUTING config | 3–4 hrs | Sonnet 4.6 |
| Ollama setup + Qwen2.5:72b + health check API | 2–3 hrs | Sonnet 4.6 |
| Auth0 tenant (COPPA plan) + PKCE flow configuration | 4–6 hrs | Sonnet 4.6 |
| PostgreSQL DDL (core tables) + Alembic setup | 4–6 hrs | Sonnet 4.6 |
| GitHub Actions CI/CD (lint → type → test → build) | 3–4 hrs | Sonnet 4.6 |
| CLAUDE.md files (root + apps/api + apps/web) | 2–3 hrs | Haiku 4.5 |
| **Total Stage 0** | **22–32 hrs (~3–4 weeks part-time)** | |

#### Per-Stage Time Estimates (Solo)

| Stage | Estimated Agent Hours | Estimated Calendar Time | Notes |
|---|---|---|---|
| Stage 0 (Setup) | 22–32 hrs | 3–4 weeks | Run once; parallel with legal research |
| Stage 1 (Diagnostic) | 150–200 hrs | 4–5 months | Includes 500+ question generation batch |
| Stage 2 (Learning Plan) | 120–160 hrs | 5–6 months | Curriculum specialist starts here |
| Stage 3 (Tutoring) | 180–240 hrs | 6–8 months | Highest complexity stage |
| Stage 4 (MVP) | 150–200 hrs | 5–7 months | IRT implementation is research-heavy |
| Stage 5 (MMP) | 200–280 hrs | 8–10 months | Stripe + i18n are high-surface-area |
| **Total to MMP** | **820–1,110 hrs** | **30–36 months** | ~25–35 hrs/month sustained pace |

---

### Infrastructure Cost Estimates Per Stage

**Stage 1–2 (Months 1–6): Development only**
| Item | Monthly Cost |
|------|-------------|
| AWS/GCP (dev environment) | $200 |
| Anthropic API (Claude Sonnet, dev usage) | $300 |
| OpenAI API (GPT-4o + o3-mini, dev usage) | $200 |
| Auth0 (free developer tier) | $0 |
| PostgreSQL (RDS dev instance) | $50 |
| Redis (dev) | $30 |
| GitHub + CI/CD | $50 |
| Monitoring (Datadog or Sentry, basic) | $50 |
| **Stage 1–2 Total (×6 months)** | **~$5,280** |

**Stage 3 (Months 7–10): Beta + MVP launch**
| Item | Monthly Cost |
|------|-------------|
| AWS/GCP (staging + prod, t3.medium) | $500 |
| Anthropic API (Claude Sonnet, ~5K questions/month) | $750 |
| OpenAI API (~3K questions/month) | $400 |
| Auth0 (B2C Essential, ≤7K MAU) | $240 |
| PostgreSQL RDS (prod) | $200 |
| Redis (ElastiCache) | $100 |
| pgvector (included in RDS) | $0 |
| CDN (CloudFront) | $50 |
| SendGrid (email) | $30 |
| Stripe (2.9% + $0.30 per transaction) | $variable (~$30 at 100 customers) |
| Monitoring (Datadog) | $150 |
| Sentry (error tracking) | $30 |
| **Stage 3 Total (×4 months)** | **~$9,920** |

**Stage 4–5 (Months 11–20): MMP scale**
| Item | Monthly Cost |
|------|-------------|
| AWS/GCP (prod, auto-scaling, t3.large) | $1,200 |
| Anthropic API (~30K questions/month) | $4,500 |
| OpenAI API (~15K questions/month) | $2,000 |
| Auth0 (B2C Professional) | $800 |
| PostgreSQL RDS (multi-AZ) | $600 |
| Redis (ElastiCache, Multi-AZ) | $300 |
| CDN | $100 |
| Email (SendGrid Pro) | $90 |
| Intercom (customer support) | $250 |
| Vanta (SOC 2 compliance) | $500 |
| LaunchDarkly (feature flags) | $200 |
| Mixpanel/Amplitude (analytics) | $200 |
| Datadog (monitoring) | $400 |
| Sentry | $50 |
| Legal (DPA reviews, school contracts) | $500 avg |
| **Stage 4–5 Monthly Total** | **~$11,690** |
| **Stage 4–5 Total (×10 months)** | **~$116,900** |

**Stage 6 (Months 21–24): Full Product**
| Item | Monthly Cost |
|------|-------------|
| AWS/GCP (scaled, includes grade 5 traffic) | $2,000 |
| Anthropic + OpenAI APIs (~80K questions/month) | $11,000 |
| Auth0 + Clever + Google SSO | $1,200 |
| All other infrastructure (as above) | $3,000 |
| **Stage 6 Monthly Total** | **~$17,200** |
| **Stage 6 Total (×4 months)** | **~$68,800** |

---

### Total Investment Summary

| Category | Stage 1–2 | Stage 3 | Stage 4 | Stage 5 | Stage 6 | **Total** |
|----------|-----------|---------|---------|---------|---------|----------|
| Personnel (dev, design, ML) | $48,000 | $88,000 | $168,000 | $432,000 | $200,000 | **$936,000** |
| Infrastructure (AWS/GCP, APIs, SaaS) | $5,280 | $9,920 | $46,760 | $70,140 | $68,800 | **$200,900** |
| Legal & Compliance | $7,000 | $3,500 | $15,000 | $20,000 | $10,000 | **$55,500** |
| Sales & Marketing | $0 | $5,000 | $15,000 | $60,000 | $50,000 | **$130,000** |
| Miscellaneous (tools, travel, OETC) | $1,000 | $2,000 | $5,000 | $10,000 | $8,000 | **$26,000** |
| **Total by Stage** | **$61,280** | **$108,420** | **$249,760** | **$592,140** | **$336,800** | **$1,348,400** |

**Funding Strategy:**
- **Months 1–6 (~$61K):** Founder bootstrapping / personal capital
- **Months 7–12 (~$108K):** Founder + Friends & Family pre-seed ($100K–$150K target, raised at Month 5–6 on strength of PoC validation)
- **Months 13–24 (~$842K):** Seed round ($800K–$1.2M target, raised at Month 12 on strength of MVP metrics and initial school partnerships)
- **Month 30–36:** Series A ($3M–$5M target, raised on strength of ARR ≥ $500K, outcome data, and expansion traction)

---

## 6. Dependencies & Critical Path

### External Dependencies

| Dependency | Type | Owner | Risk Level | Mitigation |
|------------|------|--------|------------|------------|
| 2021 Oregon Math Standards document | Content (CC-licensed, free) | Oregon DOE | Low | Document is publicly available; already downloaded |
| Anthropic Claude Sonnet API | LLM API | Anthropic | Medium | Multi-provider architecture; GPT-4o fallback |
| OpenAI GPT-4o / o3-mini API | LLM API | OpenAI | Medium | Anthropic fallback; open-source model fallback for simple questions |
| pyBKT library (open source) | ML Library | GitHub | Low | Fork if needed; well-documented; stable library |
| Auth0 (COPPA-compliant auth) | Authentication SaaS | Auth0/Okta | Low | AWS Cognito as backup option; migration possible in 6 weeks |
| Stripe (payments) | Payment SaaS | Stripe | Low | Well-established; Braintree as fallback |
| LangGraph (agent orchestration) | Open-source framework | LangChain | Medium | Framework evolving rapidly; pin to stable version; maintain abstraction layer |
| AWS/GCP cloud infrastructure | Cloud | AWS or GCP | Low | Both supported by Terraform; migration between providers possible |
| COPPA/FERPA legal counsel | Legal | External attorney | Medium | Engage in Month 1; budget $3,500–$7,000 for initial review |
| Vanta/Drata (SOC 2 compliance) | Compliance SaaS | Vanta | Low | Drata as alternative; ~$500/month |
| Google Classroom API (Stage 6) | Integration API | Google | Medium | Optional; Clever as alternative; CSV import as fallback |
| Clever API (Stage 6) | Integration API | Clever | Medium | Optional; Google Classroom as alternative |
| University research partner | Research partner | TBD (OSU/UO) | Medium | Begin outreach at Month 12; not on critical path until Month 20 |
| Oregon DOE standards updates | Regulatory | Oregon DOE | Low | Monitor annually; modular DB makes updates manageable |

---

### Critical Path Analysis

The critical path — the sequence of tasks where any delay directly delays the end milestone — for each major milestone is:

**Critical Path to Beta Launch (Month 6):**
```
Oregon Standards DB (M02)
→ Standards Dependency Graph (M06)
→ BKT Model Initialization (M03)
→ Seed IRT Item Bank (F04)
→ CAT Diagnostic Engine (F05)
→ AI Question Generation Pipeline (M04 → M09)
→ Learning Plan Engine (F18)
→ Student Diagnostic UI (F16)
→ COPPA Auth System (M07)
→ Parent Dashboard v1.0 (F26)
→ Beta Onboarding Flow (F29)
→ BETA LAUNCH (M12)
```
*Longest chain: ~14 weeks. Must start Standards DB in Week 1 of Month 1.*

**Critical Path to MVP Launch (Month 10):**
```
Beta Launch (M12)
→ Beta Outcome Review + Fixes (M15)
→ Stripe Payment Integration (F30)
→ Mobile Responsive Audit (F34)
→ COPPA Privacy Policy + ToS (F38)
→ MVP Launch Marketing Page (F40)
→ MVP LAUNCH (M16)
```
*Parallel: Multi-agent tutoring (F22), Streak mechanics (F32), Analytics (F39) — all parallel to critical path above.*

**Critical Path to First School Partnership (Month 14):**
```
MVP Launch (M16)
→ Beta Outcome Data (M15 → 8 weeks post-launch)
→ Teacher Dashboard v1.0 (M19)
→ FERPA DPA Template (M21)
→ School Pilot Onboarding (F50)
→ FIRST SCHOOL PARTNERSHIP (M20)
```
*Parallel: Classroom License Billing (F49), Teacher Registration (F45) — must not block this path.*

**Critical Path to MMP Launch (Month 16):**
```
First School Partnership (M20)
→ COPPA/FERPA Formal Review (M21)
→ Summative Assessment (F41)
→ Outcome Reports (F42, F43)
→ Classroom License Billing (F49)
→ MMP LAUNCH (M24)
```

**Critical Path to Series A Readiness (Month 24):**
```
MMP Launch (M24)
→ 500 Active Students (M25)
→ First Paying School (M26)
→ Outcome Data Publication (M27)
→ ARR Growth to $200K+
→ SERIES A READINESS (M30)
```

---

### Risk Buffer Recommendations

| Phase | Recommended Buffer | Rationale |
|-------|-------------------|-----------|
| Stage 1–2 (Months 1–6) | +3 weeks | Standards DB more complex than estimated; BKT initialization may require calibration iterations |
| Stage 3 (Months 7–10): MVP | +4 weeks | Stripe + COPPA compliance integration historically slower than estimated; always add buffer before first public launch |
| Stage 4 (Months 11–14): School Features | +3 weeks | Legal review cycles (DPA, FERPA) have external dependencies outside team control |
| Stage 5 (Months 15–20): MMP | +3 weeks | SOC 2 Type I can take 8–12 weeks; start earlier than planned |
| Stage 6 (Months 21–24): Full Product | +4 weeks | SSO integrations (Google, Clever) have approval processes with 4–8 week review queues |
| **Total recommended buffer** | **+17 weeks** | Apply as 2-week buffers at end of each stage rather than lumped at end |

**Buffering approach:** Do not compress buffers to hit dates. PADI.AI's credibility with schools depends entirely on reliability and quality. A 2-week delay in MVP launch is recoverable. Shipping a bad diagnostic to schools is not. Quality gate > timeline.

**Go/No-Go Criteria at Each Stage:**

| Gate | Criteria to Proceed | If Criteria Not Met |
|------|---------------------|---------------------|
| Beta Launch Gate (Month 6) | Question validation ≥60%; CAT diagnostic functional on 10 simulated students; COPPA auth passing legal review | Extend Stage 2 by 2 weeks; do not launch beta with failing validation |
| MVP Launch Gate (Month 10) | Beta parent NPS ≥40; question flag rate ≤10%; Stripe tested with 5 real transactions; no P0 bugs open | Delay MVP launch 2–4 weeks; fix P0 bugs first |
| School Partnership Gate (Month 14) | FERPA DPA reviewed by attorney; teacher dashboard tested with at least 2 teachers; data isolation verified | Do not sign school DPA without attorney review; delay school partnership |
| MMP Launch Gate (Month 16) | SOC 2 Type I controls documented; summative assessment validated; first school pilot NPS ≥50 | Delay MMP launch; do not market to schools without compliance documentation |
| Series A Readiness Gate (Month 24) | ARR ≥$200K; 1,500 active students; 5+ school partnerships; outcome data ≥20% gain | Extend runway; delay raise by 3–6 months rather than raising at insufficient metrics |

---

*Document prepared by PADI.AI founding team — April 2026. All estimates are projections based on comparable EdTech product development experience. Timelines assume two full-time founders with full-stack engineering capability and one part-time math education consultant.*
