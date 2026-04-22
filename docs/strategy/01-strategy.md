# Product Strategy: PADI.AI

*Version 1.0 — April 2026 | Confidential — Internal Strategy Document*

---

## 1. Vision & Mission

### Long-Term Vision (10-Year)

**"Every Oregon child arrives at middle school mathematically confident — regardless of zip code, income, or prior performance."**

By 2036, PADI.AI becomes the default adaptive math infrastructure for Oregon elementary education: a platform trusted by districts, beloved by families, and validated by measurable learning-outcome data showing sustained proficiency gains above the national average. We expand from Oregon into the Pacific Northwest and ultimately serve any state willing to build a rigorous, standards-aligned, AI-driven math learning layer for its students. In doing so, we disprove the education technology industry's "5% problem" — the historical ceiling of ~5% outcome improvement — and replace it with a new standard: 20%+ proficiency lift, documented and reproducible.

### Mission Statement

**"PADI.AI closes the math proficiency gap for Oregon 4th graders by delivering AI-generated, standards-exact adaptive instruction — diagnosing exactly where each student is, building personalized learning paths from the ground up, and continuously adapting until mastery is real."**

The mission is specific: Oregon, 4th grade, math. We are not trying to be everything to every learner. We are building the deepest, most accurate math learning experience for one cohort in one state — and doing it better than anything that exists today.

### Core Belief About How Children Learn Math

Math is not a linear subject — it is a dependency graph. Every concept depends on prior concepts, and a gap at any node in the graph propagates forward silently, compounding until it becomes a crisis (the 4th grade wall, the 7th grade algebra wall). The dominant failure mode of existing platforms is that they assign practice at the current grade level without diagnosing the actual prerequisite gaps that block comprehension. A 4th grader who cannot fluently multiply two-digit numbers cannot meaningfully engage with area models — not because of effort or intelligence, but because of a missing 3rd-grade foundation.

Our core belief: **children learn math when instruction meets them precisely where they are, fills gaps in prerequisite knowledge before advancing, and provides infinitely patient, judgment-free practice at exactly the right difficulty level.** This is not achievable by human teachers alone in classrooms of 25+ students. It requires AI — but AI that is grounded in the specific standards of the child's state, not generic content optimized for national averages.

---

## 2. Strategic Positioning

### Product Category Definition

PADI.AI is an **AI-powered adaptive standards mastery platform** — a category distinct from:

- **Drill-and-practice apps** (IXL, Prodigy): These generate repetitive exercises mapped to standards but do not diagnose prerequisite gaps, adapt at the sub-concept level in real-time, or use frontier LLMs to generate infinite novel question variations.
- **Video-lecture platforms** (Khan Academy, Zearn): These deliver content but rely on passive consumption; mastery is inferred rather than measured via psychometric models.
- **Game-based learning apps** (DreamBox, Prodigy): These use engagement mechanics (game loops, badges) to drive retention but sacrifice instructional fidelity for fun; their adaptive algorithms are proprietary black boxes with limited validation.

PADI.AI occupies a distinct position: **diagnostic-first, prerequisite-aware, standards-exact, AI-generated adaptive instruction** — closer in ambition to a private math tutor than to a gamified practice app.

### Target Customer Segments

**Primary: Parents of Oregon 4th graders**
- Households with children currently in 4th grade in Oregon public schools (approx. 47,000 students statewide)
- Motivated by: SBAC/state assessment results showing their child is below proficiency; teacher feedback; concern about math anxiety; desire to supplement classroom instruction
- Willingness to pay: $12–$20/month for a product that demonstrably works
- Decision cycle: Short (parent sees a need, researches options, starts free trial within 1–2 weeks)
- Key influencers: Other parents, teacher recommendations, school newsletter endorsements

**Secondary: Classroom Teachers / Elementary Schools**
- Oregon 4th grade teachers (approx. 2,000 classrooms statewide)
- Motivated by: Students arriving below grade level with no diagnostic data; classroom time insufficient for differentiated instruction; accountability pressure from SBAC proficiency targets
- Purchase channel: School/district budget, principal approval, Title I funds for equity-focused tools
- Decision cycle: Longer (6–18 months; requires admin buy-in, procurement, FERPA review)
- Key influencers: Instructional coaches, curriculum coordinators, Oregon DOE endorsement

**Tertiary: School Districts / Oregon DOE**
- Oregon's 197 school districts, particularly those with Title I designations (40%+ of Oregon schools)
- Motivated by: Accountability metrics (ESSA requirements), federal math improvement grants, equity mandates
- Purchase channel: District-level RFP, EdTech pilot programs, federal Title I/II/IV-A funds
- Decision cycle: 12–24 months; relationship-driven; requires outcome data
- Key influencers: Superintendents, curriculum directors, state DOE endorsement

### Positioning Statement

> **"For Oregon families and teachers with 4th graders who are struggling in math, PADI.AI is the AI-powered adaptive standards mastery platform that delivers measurable proficiency gains by diagnosing and remediating the exact prerequisite gaps blocking each student — unlike IXL, DreamBox, and Khan Academy, which practice at grade level without addressing the 3rd-grade foundational gaps that cause most 4th-grade math failure — because PADI.AI is the only platform built on the Oregon-specific 2021 Math Standards, powered by frontier AI that generates unlimited novel practice problems, and guided by a diagnostic-first BKT+IRT adaptive engine that never advances a student until mastery is real."**

### Brand Pillars

1. **Precision** — We know exactly which of Oregon's 29 Grade 4 math standards each student has mastered. Not approximately. Not estimated from a placement quiz. Precisely, updated after every question, via Bayesian Knowledge Tracing validated against IRT. Parents and teachers see a real-time skill map, not a vague "grade level" score.

2. **Depth** — We go deeper than any competitor on standards fidelity. We built our standards database from the CC-licensed 2021 Oregon Math Standards — 29 standards across 5 domains — not a generic Common Core mapping. Every question we generate is tagged to a specific standard, sub-skill, and prerequisite chain. Depth is not a feature; it is our foundation.

3. **Equity** — Oregon's math crisis is not evenly distributed. Rural schools, low-income families, and students of color bear a disproportionate share of the 69% non-proficiency rate. PADI.AI is designed to serve these students first: a free diagnostic tier ensures access, Title I pricing makes school adoption affordable, and our platform works on any device with a browser.

4. **Trustworthiness** — We serve children under 13. COPPA and FERPA compliance is non-negotiable. We never sell student data. Our AI question generation pipeline has a human validation layer that maintains ≥75% accuracy before any question reaches a student. Parents have full visibility and control over their child's data.

---

## 3. Core Differentiators (Deeply Explained)

### Differentiator 1: Oregon-Specific Standards Fidelity

**What it is:** PADI.AI is built on the 2021 Oregon Mathematics Standards (CC-licensed), specifically mapping all 29 Grade 4 standards across 5 domains: Operations & Algebraic Thinking (OA), Number & Operations in Base Ten (NBT), Number & Operations — Fractions (NF), Measurement & Data (MD), and Geometry (G). Every question, every learning plan, every diagnostic item, and every mastery assessment is tagged directly to one of these 29 standards — not to a generic "Common Core" label that may not perfectly match Oregon's current adopted version.

**Why this matters vs. generic CC platforms:** The 2021 Oregon Math Standards differ from generic CC in several important ways: Oregon added specific computational fluency expectations, adjusted sequencing of fraction concepts, and embedded mathematical practices into domain-specific standards in ways that reflect Oregon's instructional philosophy. Platforms like IXL and Khan Academy use the Common Core State Standards as their reference, which creates alignment gaps for Oregon teachers trying to prepare students for Oregon's SBAC assessment. When a teacher uses PADI.AI and sees "Standard 4.NBT.B.5 — Multiply multi-digit numbers using strategies based on place value and properties of operations," they know that label maps exactly to what Oregon's SBAC will assess. This is not a minor convenience — it is the difference between a platform being usable in a classroom for standards-based instruction versus being a supplemental drill tool with a generic label.

**The competitive moat:** Building this Oregon-specific standards database required manually cross-referencing the 2021 Oregon standards document, the Oregon SBAC blueprint, and the ODE's grade-by-grade progressions — work that no national competitor has done for a state with 600,000 K-12 students. As we expand to Washington and California, we will build the same state-specific depth, creating a compounding moat: no national competitor can afford to go this deep for every state.

### Differentiator 2: AI-Generated Adaptive Content with Frontier LLMs

**What it is:** PADI.AI does not rely on a static question bank. Every practice problem is generated on-demand by a multi-agent pipeline using Claude Sonnet (Anthropic), GPT-4o (OpenAI), and o3-mini (OpenAI) — with a validation layer that checks mathematical correctness, grade-level language appropriateness, and standard alignment before any question reaches a student. The generation pipeline is built on LangGraph, enabling a structured agent workflow: a Generator agent creates the question, a Validator agent checks mathematical accuracy and language complexity, a Standard Tagger agent confirms alignment, and a Difficulty Calibrator agent adjusts parameters based on the student's current BKT probability.

**The infinite variety advantage:** Static question banks (IXL, Zearn) are finite. A motivated student practicing a concept 20 times starts seeing repeated or near-identical questions, reducing the cognitive load that drives learning. More insidiously, students can memorize specific question-answer pairs rather than developing underlying procedural fluency. PADI.AI generates genuinely novel questions for every practice session — changing surface structure (numbers, context, word problem scenario) while holding the underlying mathematical concept constant. This means a student practicing 4.NF.B.3 (adding fractions with like denominators) encounters a different real-world scenario, different denominator, and different number combination every time, forcing genuine concept application rather than pattern memorization.

**The 75%+ validated accuracy standard:** AI-generated math content has a known failure mode: LLMs occasionally generate mathematically incorrect questions or answers, particularly for multi-step problems or complex fraction operations. Our validation pipeline addresses this: the Validator agent checks every generated question's answer programmatically (using Python's SymPy library for algebraic verification where possible) and semantically (using a second LLM pass). Questions that fail validation are rejected and regenerated. Human reviewers spot-check a 10% sample weekly. Our internal target is ≥75% first-pass validation rate; rejected questions are logged and used to fine-tune generation prompts. This is not a minor engineering detail — it is the trust layer that makes teacher and parent adoption possible.

### Differentiator 3: Structured Diagnostic-to-Mastery Pipeline

**What it is:** PADI.AI's core instructional architecture is not "practice until you get 80% correct three times in a row" (the implicit model of most competitors). It is a structured six-stage pipeline:

1. **Diagnostic Entry Assessment** — Adaptive 20-30 item assessment on entry, using IRT item calibration to efficiently estimate the student's ability level across all 29 Grade 4 standards in approximately 20-25 minutes.
2. **Gap Analysis vs. Grade Baseline** — The diagnostic output is compared to the Oregon Grade 4 standard-by-standard expected mastery sequence to identify which standards the student has mastered, which are in progress, and which are blocked by prerequisite gaps.
3. **Personalized Learning Plan** — A sequenced plan that addresses prerequisite gaps first (pulling in Grade 3 content where necessary), then builds Grade 4 standards in dependency order. The plan is visible to parents and teachers as a skill roadmap.
4. **Adaptive Practice** — Daily practice sessions (15-20 minutes) that continuously update BKT probability estimates for each standard. Difficulty adjusts within each session based on real-time performance. The session ends when the student has either reached mastery threshold on the target standard or hit a fatigue indicator.
5. **End-of-Grade Summative Assessment** — Periodic full-coverage assessment (every 8-10 weeks) that mirrors SBAC format and validates BKT estimates against held-out items. Results are reported in the same language Oregon teachers use.
6. **Continued Remediation Loop** — Standards not yet mastered cycle back into the learning plan. The system never marks a student "done" until they have demonstrated mastery across all 29 Grade 4 standards at the specified BKT threshold (P(mastery) ≥ 0.90).

**Why this beats "practice until mastery":** The simplest adaptive model — "practice this concept until you get enough correct answers" — fails because correct answers alone are a noisy signal. A student can answer 3 of 4 fraction questions correctly by applying a procedural trick learned by rote, while the BKT model correctly detects that their slip rate and guess rate indicate fragile, not genuine, mastery. More importantly, the structured pipeline sequences remediation intelligently: rather than practicing Grade 4 content the student cannot yet access, PADI.AI backs up to Grade 3 prerequisite gaps, fills them, and then returns to Grade 4 content — a strategy no competitor implements systematically.

### Differentiator 4: Prerequisite Remediation (3rd-Grade Gap Identification)

**What it is:** When PADI.AI's diagnostic identifies that a student's struggles with Grade 4 content are rooted in unmastered Grade 3 concepts, the system automatically loads Grade 3 Oregon Math Standards content and sequences it before the Grade 4 concept. For example, a student who cannot access 4.NF (fractions) because they never mastered 3.NF.A.1 (understanding fractions as part of a whole) will receive targeted 3.NF practice first — invisible to the student, who simply sees "today's math challenge," but critical to building the cognitive foundation for Grade 4 fraction operations.

**Why no competitor does this well:** This is the most important differentiator and the one most clearly explained by incentive structures. IXL, Khan Academy, and DreamBox are all designed around grade-level content. Their business model is "4th grade math for 4th graders." Systematically routing a 4th grader to 3rd grade content creates three problems for them: (1) parents perceive it as regression and may cancel subscriptions, (2) their standards alignment is designed for single-grade use, not cross-grade prerequisite chains, and (3) their content libraries, while broad, are not designed with explicit prerequisite relationships between Grade 3 and Grade 4 standards.

PADI.AI solves this by: (a) building the prerequisite graph explicitly as a data structure (not an implicit assumption), where each Grade 4 standard has a documented set of Grade 3 (and in some cases Grade 2) prerequisites; (b) framing prerequisite remediation as "building your math foundation" rather than "going back to easier content," which preserves student motivation; and (c) making the prerequisite chain visible in parent and teacher dashboards so adults understand the pedagogical rationale. This is the mechanism by which we expect to beat the "5% problem" — the prerequisite gap is the primary driver of stalled progress, and we are the only platform that addresses it structurally.

---

## 4. Go-to-Market Strategy

### Phase 1: Concept Validation (Months 1–6)

**Objective:** Prove that the diagnostic assessment accurately identifies student knowledge levels, that the AI-generated questions meet quality standards, and that the learning plan produces meaningful engagement.

**Target:** 10–50 Oregon 4th grade students (hand-selected beta testers from personal network, parent Facebook groups, and 1–2 individual classroom teachers in the Lake Oswego, Beaverton, and Portland metro area).

**Channel strategy:**
- Founder-led direct outreach: Personal LinkedIn/email connections to parents and teachers in the Portland metro area
- Oregon education Facebook groups: "Oregon Moms Network," "Portland Parents," school-specific parent groups
- Individual teacher outreach: Email to 20–30 4th grade teachers in Lake Oswego SD, Beaverton SD, Portland Public Schools offering free access in exchange for feedback
- Nextdoor postings in Portland/Beaverton neighborhoods: "Looking for 4th graders to beta test a new Oregon math app"

**What we offer beta testers:** Free full access, direct line to the founder for feedback, and a $25 Amazon gift card for families who complete the 6-week beta program and provide a detailed NPS survey.

**Goals:**
- 10–50 active beta students completing the diagnostic assessment
- Validate that diagnostic results correlate with parent/teacher perception of student ability (target: 80%+ parent agreement that diagnostic results "accurately reflect where my child is in math")
- Validate that AI-generated questions have ≤10% "bad question" rate as reported by students/parents
- Validate that students engage with the platform for ≥3 sessions/week without external prompting

**Key metrics:**
| Metric | Target | Method |
|--------|--------|--------|
| Diagnostic completion rate | ≥80% of students who start | App analytics |
| Diagnostic accuracy agreement | ≥80% parent agreement | Post-diagnostic survey |
| AI question quality (parent-reported) | ≤10% "bad" questions | In-app flag + survey |
| Weekly active sessions per student | ≥3 sessions/week | App analytics |
| Parent NPS | ≥40 | Post-month-1 survey |
| Learning gain (pre/post) | ≥1 standard mastery gained per 4 weeks | BKT model output |

**Key activities:**
- Weeks 1–4: Onboard first 10 students, conduct weekly 30-minute parent calls
- Weeks 5–12: Expand to 50 students, shift to async feedback via weekly email surveys
- Weeks 13–24: Analyze data, fix top 10 issues by frequency, prepare MVP spec

**Exit criteria for Phase 1:** Parent NPS ≥40, diagnostic accuracy agreement ≥80%, and at least 3 students showing measurable learning gains (1+ additional standard mastered vs. diagnostic baseline) within 6 weeks.

---

### Phase 2: MVP Launch (Months 7–12)

**Objective:** Acquire the first 500 active monthly students, generate initial revenue, and collect outcome data to support school/district sales conversations.

**Target:** Oregon families with 4th graders statewide — particularly families whose children scored below proficient on the most recent Oregon state assessment (SBAC results released annually in fall; target families who receive "below proficient" score reports in September/October).

**Channel strategy:**
- **Oregon education Facebook groups** (primary): "Oregon Parents for Public Education," "Beaverton School District Parents," "Portland Public Schools Families" — post outcome data from beta, offer first-month free trial
- **Nextdoor** (primary): Geo-targeted posts in Oregon cities with large elementary school populations (Portland, Salem, Eugene, Beaverton, Hillsboro, Bend)
- **School newsletters** (secondary): Partner with 5–10 individual teachers from Phase 1 beta to include PADI.AI in their class newsletter as a recommended resource
- **Oregon PTA chapters** (secondary): Attend Oregon PTA meetings in Beaverton and Portland; sponsor one Oregon PTA newsletter ad ($500–$1,000 test budget)
- **Google Ads** (test): Small-budget ($1,000/month) test campaign targeting "Oregon math tutor 4th grade," "Oregon SBAC prep math," "math help 4th grade Oregon"
- **SBAC results season (Oct–Nov)**: Heavy push in September–November when families receive state test score reports and urgency is highest

**Pricing model:**

*Freemium model (recommended for Phase 2):*
- **Free tier:** Full diagnostic assessment, student skill map, 2 weeks of adaptive practice (limited to 3 practice sessions)
- **Pro tier ($14.99/month or $99/year):** Unlimited adaptive practice, full learning plan, parent dashboard with weekly progress reports, multi-agent tutoring support, access to all 29 Oregon Grade 4 standards + prerequisite Grade 3 content

*Rationale for freemium vs. subscription-only:*
| Model | Pros | Cons |
|-------|------|------|
| Freemium | Lowers acquisition barrier; diagnostic value drives conversion; viral sharing (parents share diagnostic results); generates free leads from schools | Slower revenue ramp; some families use free tier only; infrastructure cost for non-paying users |
| Subscription-only ($14.99/mo from day 1) | Cleaner revenue model; no free-rider problem; higher average revenue per user | Higher acquisition barrier; harder to demonstrate value before payment; lower top-of-funnel volume |
| Annual subscription only | Predictable revenue; lower churn | Requires strong upfront trust; difficult for families who want to try before committing |

**Recommended: Freemium with $14.99/month Pro tier.** The diagnostic result is the "aha moment" that drives conversion — parents who see a detailed skill map identifying their child's specific gaps are highly motivated to buy the plan to fix those gaps.

**Goals:**
- 500 active monthly students by end of Month 12
- ≥15% free-to-paid conversion (target: 75 paying families by Month 12)
- Monthly Recurring Revenue (MRR): ~$1,125 (75 × $14.99) by Month 12
- Collect 3-month outcome data showing ≥10% average proficiency gain vs. diagnostic baseline
- Establish 1–2 school partnerships (teacher using PADI.AI in classroom, providing school-level outcome data)

---

### Phase 3: MMP & School Partnerships (Months 13–24)

**Objective:** Launch the Minimum Marketable Product (full polish, monetization infrastructure, teacher/school reporting), acquire first paying school partnerships, and build the outcome data required for district-level sales.

**Target:**
- Oregon elementary schools, particularly Title I-designated schools (where federal funds can pay for EdTech tools and equity mission resonates with administrators)
- Oregon elementary instructional coaches and curriculum coordinators (gatekeepers for classroom tool adoption)
- Oregon DOE relationship-building (long-term; no direct revenue expected until Year 3+)

**Channel strategy:**
- **Direct school sales:** Founder-led outreach to principals and instructional coaches in target districts (Beaverton SD, Portland Public, Salem-Keizer, Hillsboro SD, Eugene 4J)
- **EdTech conferences:** Oregon OETC (Oregon Educational Technology Conference, February annually) — exhibit booth + presentation on outcome data; ISTE (national; attend as attendee first year)
- **Title I coordinator outreach:** Email + phone outreach to Title I coordinators in Oregon's 40+ Title I-eligible elementary schools in Portland metro area; position PADI.AI as a ESSA-fundable intervention tool
- **Outcome data PR:** If Phase 2 generates strong outcome data (≥15% proficiency gain), pitch to Oregon newspapers (The Oregonian, Salem Statesman Journal) and education publications (EdSurge)

**School pricing model:**
- **Classroom license:** $8/student/year for 1–2 classrooms (≥20 students; minimum $160/year per classroom)
- **School license:** $6/student/year for full school (25–35 students per grade; target ~$900–$1,260/school/year for one grade)
- **Title I grant-aligned pricing:** Match Title IV-A per-pupil allocation ($~50/student/year available for EdTech) with a premium school license at $12/student/year that includes professional development sessions, monthly outcome reports, and SBAC alignment guarantee
- **Volume discount:** 3+ school district pilot: $5/student/year

**Compliance milestones for Phase 3:**
- FERPA compliance certification (formal legal review + DPA templates ready for district signature)
- COPPA compliance audit (third-party review of data collection, parental consent flows, data retention policies)
- SOC 2 Type I report (optional but required by some districts)

**Goals:**
- 5+ school partnerships (at least 2 paying)
- 1,500+ active monthly students (school + consumer combined)
- MRR: ~$4,000–$6,000 (consumer) + first school license revenue
- Net Promoter Score from teachers: ≥50
- Publishable outcome data: ≥20% average proficiency gain for students with ≥30 hours of PADI.AI use

---

### Phase 4: Expansion (Months 25–36)

**Objective:** Expand to adjacent grades and neighboring states; position for institutional/district licensing and Series A fundraising.

**Grade expansion:**
- **Grade 3** (Month 25): Natural prerequisite layer already partially built; add 3rd-grade full curriculum as standalone product for families with 3rd graders
- **Grade 5** (Month 28): Extend upward; bridges to middle school readiness (fractions → ratios, multiplication → algebraic thinking)
- **Grade 6** (Month 34): Middle school entry; opens new market segment (parents facing pre-algebra wall)

**State expansion:**
- **Washington State** (Month 25): Adjacent state; high alignment with Oregon standards (both adopted modified CC); existing Oregon families with Washington connections provide organic entry; build Washington-specific standards database using same methodology as Oregon
- **California** (Month 31): Largest state elementary market (~3.1M K-6 students); requires California-specific standards work (CA Math Framework 2023 has significant modifications); higher competition (more Bay Area EdTech); position initially through Title I district outreach

**District licensing model:**
- District-level site license: $4/student/year for all elementary students in district with volume ≥500 students
- Includes: Full teacher dashboard, district-level analytics, SBAC alignment reports, PD sessions, dedicated CSM
- Target districts: Districts with 1,000–10,000 students (manageable sales cycle, meaningful revenue)

**Series A readiness criteria (targeting raise at Month 30–36):**
- $500K+ ARR
- 5,000+ active monthly students
- 10+ paying school/district partnerships
- Published outcome data with statistical significance
- Clear unit economics (LTV/CAC ≥ 3:1 for consumer; ≥ 5:1 for school)

---

## 5a. Pedagogical Outcome Hypothesis

### Claim

> PADI.AI will improve student math proficiency rates by **15–25 percentage points** among engaged students (defined as ≥10 completed sessions), compared to the ~5% real-world improvement documented for current platforms (Holt, 2024).

### Why Existing Platforms Achieve Only ~5%

Holt (2024) analyzed 14 studies of platforms including i-Ready, DreamBox, Khan Academy, and IXL. Despite positive controlled-study effect sizes, real-world population-level gains are near zero because only approximately 5% of students use these tools with the frequency and engagement needed to benefit. Korbey (2025) documented that one-third of teachers rate these tools "mediocre or poor" and that gains are concentrated in already-high-performing students — deepening inequity rather than closing gaps.

The root cause: these are **answer-level feedback systems**. VanLehn (2011) showed answer-level systems achieve only d = 0.30 regardless of sophistication. Reaching d = 0.76 (near-equivalent to human tutoring) requires step-level feedback — which requires an AI tutoring agent.

### PADI.AI's Four Evidence-Backed Mechanisms

**Mechanism 1 — Prerequisite Gap Remediation First**

Existing platforms place students into grade-level content regardless of foundational mastery. PADI.AI diagnoses and remediates 3rd-grade prerequisite skills *before* exposing students to 4th-grade content. The What Works Clearinghouse practice guide on elementary math intervention (Fuchs et al., 2021) rates prerequisite-grounded instruction as its highest-evidence recommendation for students struggling with math. Fuchs et al. (2008) demonstrated that unaddressed foundational skill gaps are the primary driver of persistent difficulty across elementary grades.

**Mechanism 2 — Step-Level Socratic Feedback (d = 0.76 vs. d = 0.30)**

VanLehn (2011) compared tutoring modalities across 62 studies:
- Answer-level tutoring systems (IXL, Khan Academy): effect size **d = 0.30**
- Step-level intelligent tutoring systems (ITS with Socratic guidance): effect size **d = 0.76**
- Human tutors: effect size **d = 0.79**

PADI.AI's Tutor Agent guides students through reasoning steps rather than simply marking answers right or wrong — moving from the d = 0.30 to the d = 0.76 band.

**Mechanism 3 — BKT Mastery Gating + Spaced Practice**

PADI.AI prevents students from advancing past a skill until BKT probability of mastery reaches P(mastered) ≥ 0.85. This operationalizes Bloom's (1984) mastery learning approach, which meta-analyses show produces effect sizes of d = 0.5–1.0 (Ma et al., 2014; Kulik & Fletcher, 2016). Combined with spaced re-exposure to previously mastered skills — Cepeda et al. (2006) synthesized 839 assessments showing spaced practice outperforms massed practice in 95% of cases — this creates durable retention rather than shallow fluency.

**Mechanism 4 — Error-Type Classification**

PADI.AI's Assessment Agent classifies error types (procedural vs. conceptual, specific misconception categories) rather than marking responses as correct/incorrect. The IES spaced practice guide (Pashler et al., 2007) identifies targeted error correction as one of the highest-evidence instructional strategies. Different error types require different instructional interventions; PADI.AI routes each error type to a different hint strategy.

### Why We Expect to Beat the 2-Sigma Ceiling

Bloom (1984) identified that one-to-one mastery tutoring produces d ≈ 2.0 vs. conventional classroom instruction — the "2 sigma problem." PADI.AI approximates the components of 1-on-1 tutoring: step-level feedback, error-specific guidance, prerequisite-aware sequencing, and mastery-gated advancement. Recent meta-analyses of intelligent tutoring systems show mean effect sizes of g = 0.42–0.66 vs. conventional instruction (Ma et al., 2014; Kulik & Fletcher, 2016) — well above the ~5% threshold.

### Measurement Plan

| Metric | Target | Method | Timing |
|---|---|---|---|
| Pre/post proficiency rate (pilot cohort) | +15 pp vs. baseline | Oregon OSAS score comparison | End of Stage 4 pilot |
| Engagement (sessions/week) | ≥ 3 sessions/week for 8+ weeks | PostHog analytics | Ongoing from Stage 1 |
| Diagnostic accuracy vs. teacher report | ≥ 85% agreement | Pilot teacher survey (n = 50) | End of Stage 1 pilot |
| BKT mastery → OSAS proficiency correlation | r ≥ 0.70 | Statistical validation study | Stage 4 |

### Sources

- Bloom, B. S. (1984). The 2 sigma problem. *Educational Researcher*, *13*(6), 4–16. https://doi.org/10.3102/0013189X013006004
- Cepeda, N. J., et al. (2006). Distributed practice in verbal recall tasks. *Psychological Bulletin*, *132*(3), 354–380. https://doi.org/10.1037/0033-2909.132.3.354
- Fuchs, L. S., et al. (2008). Intensive intervention for students with mathematics disabilities. *Learning Disability Quarterly*, *31*(2), 79–92.
- Fuchs, L. S., et al. (2021). *Assisting students struggling with mathematics* (WWC 2021006). What Works Clearinghouse, IES. https://ies.ed.gov/ncee/wwc/PracticeGuide/26
- Holt, L. (2024). The 5 percent problem. *Education Next*, *24*(4). https://www.educationnext.org/5-percent-problem-online-mathematics-programs-may-benefit-most-kids-who-need-it-least/
- Korbey, H. (2025). The practice problem. *Education Next*, *25*(4). https://www.educationnext.org/practice-problem-research-shows-students-benefit-digital-math-practice-platforms/
- Kulik, J. A., & Fletcher, J. D. (2016). Effectiveness of intelligent tutoring systems. *Review of Educational Research*, *86*(1), 42–78. https://doi.org/10.3102/0034654315581420
- Ma, W., et al. (2014). Intelligent tutoring systems and learning outcomes. *Journal of Educational Psychology*, *106*(4), 901–918. https://doi.org/10.1037/a0037123
- Pashler, H., et al. (2007). *Organizing instruction and study to improve student learning* (NCER 2007-2004). IES. https://files.eric.ed.gov/fulltext/ED498555.pdf
- VanLehn, K. (2011). The relative effectiveness of human tutoring, intelligent tutoring systems, and other tutoring systems. *Educational Psychologist*, *46*(4), 197–221. https://doi.org/10.1080/00461520.2011.611369

---

## 5. Revenue Model

### Revenue Streams

**Stream 1: Consumer Freemium → Pro Subscription**
- Free tier: Diagnostic + 2-week limited practice (no payment required)
- Pro tier: $14.99/month or $99/year
- Target conversion: 15% of free users to paid within 60 days
- Annual plan discount: $99/year ($8.25/month effective) vs. $14.99/month — incentivize annual to reduce churn

**Stream 2: Classroom License**
- $8/student/year (minimum 20 students per classroom)
- Includes: Teacher dashboard, class-level reporting, standard-by-standard progress tracking
- Annual commitment; invoiced at start of school year (September)

**Stream 3: School License**
- $6/student/year (minimum 1 full grade, ~25–35 students)
- Includes: Principal dashboard, school-wide analytics, monthly outcome reports, quarterly check-in calls
- Annual commitment; requires signed DPA

**Stream 4: District License**
- $4/student/year (minimum 500 students)
- Includes: District analytics, SBAC alignment reporting, professional development (2 sessions/year), dedicated CSM
- Multi-year commitment (2–3 year contracts preferred)
- Eligible for Title I funding (ESSA Title IV-A: Student Support and Academic Enrichment)

**Stream 5: Grant-Funded Access (Non-Revenue; Equity)**
- Apply for Oregon Math Learning grants and federal Math Innovation Zones grants
- Grants fund free access for Title I schools; builds outcome data + case studies
- Not a revenue stream — a market seeding + mission-fulfillment mechanism

### Revenue Model Comparison

| Model | Revenue Potential (Year 2) | Margins | Sales Cycle | Churn Risk | Pros | Cons |
|-------|--------------------------|---------|-------------|------------|------|------|
| Consumer freemium | $150K–$300K | 70%+ | Days | High (monthly cancel) | Fast acquisition, viral potential | Unpredictable; churn-intensive |
| Classroom license | $80K–$150K | 65% | 1–3 months | Low (annual) | Reliable; teacher-driven retention | Requires individual teacher champions |
| School license | $100K–$200K | 60% | 3–9 months | Very low (multi-year) | Predictable ARR; case study fuel | Slow sales; requires principal buy-in |
| District license | $250K–$500K | 55% | 12–24 months | Extremely low | High ACV; institutional validation | Very long sales cycle; procurement complexity |
| Grant-funded | $0 (non-revenue) | N/A | 3–6 months | None | Mission, outcome data, PR | No direct revenue; time-intensive applications |

**Year 1 Revenue Target (Months 1–12):** $15,000–$25,000 (primarily consumer, some classroom pilots)
**Year 2 Revenue Target (Months 13–24):** $150,000–$300,000 (consumer + school licenses)
**Year 3 Revenue Target (Months 25–36):** $500,000–$1,000,000 (consumer + school + first district licenses + expansion states)

---

## 6. Competitive Strategy

### SWOT Analysis

**Strengths:**
1. Oregon-specific 2021 Math Standards database — deepest standards fidelity of any platform in market
2. AI-generated infinite question variety via frontier LLMs — eliminates question bank staleness problem
3. Diagnostic-first prerequisite remediation pipeline — addresses root cause of 4th-grade math failure that no competitor targets systematically
4. BKT+IRT psychometric engine (pyBKT) — mastery measurement based on validated learning science, not arbitrary correct-answer thresholds
5. Multi-agent tutoring architecture (LangGraph) — scalable AI tutoring that can provide hint-by-hint guidance without a human tutor
6. COPPA-first design — trust with parents and districts; competitive necessity that also becomes a differentiator
7. Focused niche (Oregon Grade 4) — enables deep expertise vs. platform breadth competitors; easier to demonstrate outcome data in a specific cohort

**Weaknesses:**
1. No brand recognition vs. IXL, Khan Academy, DreamBox (these brands are household names in parent circles)
2. No existing outcome data at launch — trust gap that takes 6–18 months to fill
3. Single-grade focus limits TAM and revenue in early phases; multi-grade expansion requires significant additional content work
4. Small team — operational risk in every function; no redundancy
5. LLM API cost dependency — question generation at scale has non-trivial variable cost; margins compressed if API costs rise
6. AI question validation not 100% — even with ≥75% first-pass validation, some incorrect questions may reach students and damage trust
7. No existing school/district relationships — school sales require building trust from scratch without existing institutional credibility

**Opportunities:**
1. Oregon's 31% math proficiency rate (NAEP 2024) — crisis creates urgency and willingness to try new solutions
2. Post-COVID math recovery still ongoing — federal ESSER III funds (some extended to 2026) available for math intervention tools
3. AI in EdTech is early — most competitors have not yet deployed frontier LLM question generation; 12–18 month window before major players catch up
4. Parent demand for supplemental math tools is high and growing — tutoring market expanded significantly post-COVID; families already paying $50–$200/month for human tutors
5. Oregon DOE's Math Recovery Initiative — state-level alignment opportunity; PADI.AI could become a recommended tool
6. Title I equity angle — bipartisan political support for equity-focused EdTech; grant funding available
7. Adjacent grade expansion (Grades 3, 5, 6) is relatively fast once Grade 4 content is proven — same platform, same engine, new standards layer
8. Washington and California market entry — two of the largest and most similar state standards markets adjacent to Oregon

**Threats:**
1. IXL adds AI-generated question variation — IXL has the engineering resources; if they ship this in 12 months, our content differentiation weakens
2. Khan Academy (Khanmigo) scales to be truly adaptive — Khan has the brand and the data; if Khanmigo adds standards-exact BKT mastery tracking, competitive threat grows significantly
3. Google/Apple/Microsoft enters EdTech with bundled AI math tools — platform-level competition that could crowd out independent apps
4. LLM API cost increases — if Anthropic/OpenAI raise API prices, our variable cost of question generation increases significantly
5. Regulatory risk — COPPA enforcement, state student privacy laws (Oregon Student Information Protection Act), AI in education regulations are all evolving and could require costly compliance changes
6. School budget cuts — Oregon school budgets are vulnerable to state revenue shortfalls; EdTech is often cut first
7. Teacher/parent AI skepticism — significant portion of the education market remains skeptical of AI-generated content for children; "AI gone wrong" media stories could create reputational risk for the category

### Competitive Response Scenarios

**Scenario 1: IXL copies our AI question generation approach**
- Timeline estimate: 12–18 months to ship a comparable feature
- Our response: (a) Accelerate question bank depth — our advantage shifts from "AI generates questions" to "our question generation is more pedagogically sophisticated because of our prerequisite graph and BKT integration"; (b) emphasize outcome data — IXL will have AI generation but not our diagnostic-first pipeline; our outcome data is the proof point; (c) double down on Oregon-specific fidelity — IXL will generate questions for national standards, not Oregon-specific 2021 standards
- Net assessment: IXL copying AI question generation weakens our content differentiation but does not destroy our moat, because our differentiation is not just question generation — it is the full diagnostic-to-mastery pipeline built on Oregon-specific standards with BKT+IRT measurement.

**Scenario 2: Khan Academy's Khanmigo adds BKT-based adaptive tracking**
- Timeline estimate: 6–12 months (Khan has the ML resources)
- Our response: (a) Khanmigo will remain video-lecture-first with AI tutoring overlay — our platform is practice-first, which better serves the student who already watched the video and needs to build fluency; (b) Khan's standards coverage is national CC, not Oregon-specific; (c) our prerequisite remediation is structural (built into the dependency graph), not prompt-based; (d) accelerate school/district relationships — schools value dedicated vendor relationships, not free tools
- Net assessment: A more capable Khanmigo is a real threat to our consumer market. Our response is to shift emphasis to school/district channels where Khan's free model is actually a weakness (schools want accountability, reporting, outcome data — not free tools they can't hold accountable).

**Scenario 3: A well-funded EdTech startup launches with a similar approach**
- Timeline estimate: Could happen at any time; this is the most acute threat
- Our response: (a) First-mover advantage in Oregon-specific market — we will have 12–18 months of Oregon market presence, outcome data, and school relationships before a competitor can replicate; (b) Oregon identity as brand asset — a startup from San Francisco building "Oregon math" will always be disadvantaged vs. a company that built its product from Oregon, for Oregon; (c) accelerate data flywheel — every student interaction trains our adaptive model; a new entrant starts from zero
- Net assessment: The response is to move fast in Phase 1–2 and build the outcome data and school relationships that create institutional lock-in before a well-funded competitor can establish Oregon presence.

### Moat-Building Strategy

**Moat 1: Data Flywheel**
Every student interaction (question attempt, hint request, time-on-task, error pattern) generates training data for three compounding advantages: (a) improved BKT model calibration specific to Oregon Grade 4 students, (b) improved question generation prompts (we learn which question types generate errors indicating concept gaps vs. careless mistakes), and (c) improved difficulty calibration (we know the exact IRT difficulty parameters for hundreds of generated questions after seeing thousands of student responses). A competitor starting today has zero Oregon-specific student interaction data. We will have 100,000+ question attempts by the end of Year 1, growing to millions in Year 2. This data cannot be replicated without time in market.

**Moat 2: Proprietary Oregon Standards Dependency Graph**
Our standards database is not just a list of Oregon standards — it is a directed dependency graph where every standard has documented prerequisite relationships to prior-grade standards. This graph was built by hand, informed by ODE's grade-level progressions and Oregon's SBAC blueprint. It is the structural foundation of our prerequisite remediation differentiator. While the Oregon standards themselves are CC-licensed, the dependency graph and the pedagogical sequencing logic are proprietary. This graph becomes more sophisticated as we learn which prerequisite gaps most frequently block which Grade 4 standards — a data advantage that grows with use.

**Moat 3: School/District Relationships and Data Sharing Agreements**
Every school that signs a DPA (Data Processing Agreement) with PADI.AI creates institutional switching costs. Districts that use our platform for 2+ years have student progress data, historical outcome reports, and staff familiarity that makes switching to a competitor costly. The relationship itself — with principals, instructional coaches, and curriculum coordinators — is a durable asset.

**Moat 4: Oregon-Specific Brand Identity**
"Built in Oregon, for Oregon" is not just marketing — it is a genuine competitive positioning that a national platform cannot replicate. Oregon teachers and parents feel a connection to a locally-built product. Our presence at OETC, relationships with Oregon DOE, and community-level engagement in Oregon education circles create a brand that national platforms cannot easily displace.

---

## 7. Risk Register

| # | Risk | Category | Probability | Impact | Mitigation Strategy | Owner |
|---|------|----------|-------------|--------|---------------------|-------|
| R01 | AI-generated questions contain mathematical errors that reach students, damaging trust with parents and teachers | Technical / Quality | Medium | High | Multi-layer validation pipeline (LLM validator + SymPy programmatic check + human spot-check 10% sample weekly); student/parent in-app "flag a problem" button; SLA to fix flagged questions within 24 hours | CTO |
| R02 | BKT model miscalibrates student ability, leading to learning plans that are too easy or too hard, reducing engagement | Technical / ML | Medium | High | Validate BKT parameters against IRT holdout data in beta; conduct A/B test of BKT-based vs. fixed-difficulty practice sessions; add explicit parent override ("my child says this is too easy/hard") | CTO / ML Lead |
| R03 | LLM API costs exceed budget projections at scale (e.g., $0.03–$0.05/question at scale = $30–$50 per 1,000 questions) | Financial / Technical | Low | High | Implement aggressive caching (identical standard + difficulty requests return cached questions after validation); use o3-mini for simpler question types, reserve Claude Sonnet for complex multi-step problems; set hard monthly API cost cap with alert at 80% | CTO / CFO |
| R04 | COPPA or FERPA compliance violation — improper collection of student PII under 13 without verifiable parental consent, or unauthorized disclosure of student data | Compliance / Legal | Low | Critical | Engage COPPA compliance attorney in Month 1; Auth0 with COPPA-compliant flows; no third-party tracking pixels on student-facing pages; DPA template reviewed by education attorney before first school contract; conduct annual third-party COPPA audit | CEO / Legal |
| R05 | Oregon state assessment (SBAC) changes standards alignment or format, requiring significant rework of standards database and diagnostic | Market / Regulatory | Low | High | Monitor ODE standards update announcements; design standards database as modular (each standard is a record, not hardcoded); build in 2-month buffer in product roadmap for standards updates; maintain relationship with ODE to get advance notice | CPO |
| R06 | Low beta engagement — students disengage after initial diagnostic, fail to build habit of 3+ sessions/week | Market / Product | High | High | Design habit-forming session structure (clear daily goal, progress celebration, streak mechanics); involve parents as accountability partners via weekly email digest; keep sessions to 15 minutes (not 30+); conduct weekly 1:1 calls with beta families in first 8 weeks | CPO / Head of Design |
| R07 | Inability to acquire first 500 paying students in consumer market (Phase 2 fails) | Market / GTM | Medium | High | Test 3 channels in parallel (Facebook groups, Nextdoor, Google Ads); convert best beta users to paid before public launch (warm leads); ensure freemium diagnostic creates "aha moment" that drives conversion; have 3-month runway if revenue misses target | CEO |
| R08 | School sales cycle longer than 6 months, delaying institutional revenue beyond Month 24 | Market / Sales | High | Medium | Start school outreach in Month 13, not Month 18; target individual classroom teachers before schools (lower barrier to entry); prepare FERPA-compliant DPA template in advance; build case studies from Phase 2 school pilots; identify 3 "champion teachers" from Phase 1 beta | CEO |
| R09 | Key team member (founder/CTO) leaves or becomes incapacitated, stalling development | Operational | Low | Critical | Document all technical architecture decisions; use GitHub with complete commit history; maintain 3-month cash reserve for contractor engagement; cross-train on all critical systems; consider technical co-founder or senior engineering hire by Month 6 | CEO |
| R10 | Competitor (IXL or DreamBox) launches AI question generation feature within 12 months, weakening content differentiation | Competitive | Medium | Medium | Accelerate Phase 2 to get outcome data before competitive response; shift narrative from "AI questions" to "diagnostic-first pipeline + Oregon standards depth"; focus on school channel where brand relationships matter more than feature parity | CEO / CPO |
| R11 | Frontier LLM providers (Anthropic, OpenAI) change pricing, deprecate models, or impose educational content restrictions | Technical / Vendor | Low | High | Design question generation pipeline to be model-agnostic (swap models via config); maintain multi-provider architecture (both Claude and GPT-4o); test open-source models (Llama 3, Mistral) as fallback for simpler question types; avoid vendor lock-in in LangGraph agent definitions | CTO |
| R12 | Oregon DOE or district procurement requires SOC 2 Type II certification, which is time-intensive and costly (~$30K–$50K) | Compliance / Operational | Medium | Medium | Begin SOC 2 Type I preparation in Month 12 (immediately after MVP launch); use automated compliance tool (Vanta or Drata, ~$500/month) to continuously monitor controls; budget $30K for SOC 2 Type II by Month 24 | CTO / CEO |
| R13 | Product fails to demonstrate measurable learning gains above existing tools, eliminating the "outcome advantage" narrative | Product / Market | Medium | High | Run rigorous pre/post assessments with control group comparison where possible; partner with a university researcher (Oregon State, University of Oregon) for independent evaluation; set realistic gain targets (20% proficiency improvement vs. diagnostic baseline over 3 months) and report them transparently | CPO |
| R14 | Cash runway insufficient — burn rate exceeds plan before reaching revenue milestones | Financial | Medium | High | Maintain 6-month runway at all times; delay hires if revenue milestones miss by >30%; apply for SBIR Phase I grant (NSF, ED) in Month 3; target pre-seed round at Month 6 if Phase 1 validation is strong | CEO / CFO |

---

## 8. Success Metrics & OKRs

### Year 1 OKRs (Months 1–12)

**Objective 1: Validate Product-Market Fit**
- KR1.1: Achieve Parent NPS ≥ 50 from beta users (n ≥ 30 respondents) by Month 6
- KR1.2: ≥ 80% of beta parents agree diagnostic results "accurately reflect my child's math level" by Month 5
- KR1.3: ≥ 75% of beta students complete ≥ 3 practice sessions/week for 4 consecutive weeks by Month 5

**Objective 2: Build and Launch MVP**
- KR2.1: Ship MVP with full diagnostic + learning plan + adaptive practice to production by Month 10
- KR2.2: AI question validation pipeline achieving ≥ 75% first-pass accuracy rate by Month 8
- KR2.3: COPPA compliance audit passed (internal review) before MVP launch

**Objective 3: Acquire First Paying Customers**
- KR3.1: 50+ active paying subscribers by end of Month 12
- KR3.2: Free-to-paid conversion rate ≥ 15% within 60 days of free diagnostic
- KR3.3: MRR ≥ $750 by Month 12

**Objective 4: Establish Foundation for School Channel**
- KR4.1: 2+ individual teacher partnerships (classroom pilots, non-paying) by Month 12
- KR4.2: Teacher NPS ≥ 50 from pilot teachers by Month 12
- KR4.3: First signed school DPA (even if non-paying pilot) by Month 12

---

### Year 2 OKRs (Months 13–24)

**Objective 1: Scale Consumer Channel**
- KR1.1: 1,500+ active monthly students (consumer + school combined) by end of Month 24
- KR1.2: Monthly churn rate ≤ 5% for Pro subscribers
- KR1.3: MRR ≥ $5,000 from consumer channel by Month 24

**Objective 2: Launch and Validate MMP**
- KR2.1: MMP launched with full teacher dashboard, parent reporting, and monetization infrastructure by Month 16
- KR2.2: Net Promoter Score from teachers ≥ 55 by Month 20
- KR2.3: ≥ 5 school partnerships (at least 2 paying) by Month 24

**Objective 3: Prove Learning Outcomes**
- KR3.1: Publish internal outcome report showing average ≥ 20% proficiency gain for students with ≥ 30 hours PADI.AI use by Month 20
- KR3.2: Partner with 1 university researcher for independent outcome evaluation by Month 18
- KR3.3: ≥ 70% of students who complete full diagnostic + 8-week learning plan advance at least 3 standard masteries

**Objective 4: Build Revenue and Runway for Series A**
- KR4.1: ARR ≥ $200,000 by Month 24
- KR4.2: Unit economics: Consumer LTV/CAC ≥ 3:1; School LTV/CAC ≥ 5:1
- KR4.3: ≥ 12 months of runway at current burn rate by Month 24

---

### Product KPIs (Ongoing)

**Engagement KPIs:**
| KPI | Target | Measurement Method |
|-----|--------|-------------------|
| Daily Active Users / Monthly Active Users (DAU/MAU) | ≥ 40% | App analytics |
| Average sessions per student per week | ≥ 3 sessions | App analytics |
| Average session duration | 15–20 minutes | App analytics |
| Diagnostic completion rate (of starters) | ≥ 80% | App analytics |
| Learning plan completion rate (students who complete 1 full standard) | ≥ 60% within 4 weeks | BKT model output |

**Learning Outcome KPIs:**
| KPI | Target | Measurement Method |
|-----|--------|-------------------|
| Standards mastered per 10 hours of practice | ≥ 1.5 standards | BKT model output |
| Proficiency gain: diagnostic baseline → 8-week reassessment | ≥ 20% improvement | Pre/post assessment |
| SBAC alignment accuracy (our mastery prediction vs. SBAC result) | ≥ 75% correlation | Post-SBAC survey (annual) |
| Prerequisite gap identification accuracy | ≥ 80% teacher agreement | Teacher survey |

**Question Quality KPIs:**
| KPI | Target | Measurement Method |
|-----|--------|-------------------|
| AI question first-pass validation rate | ≥ 75% | Validation pipeline logging |
| Parent-reported "bad question" rate | ≤ 5% | In-app flag rate |
| Mean time to resolve flagged question | ≤ 24 hours | Issue tracker |
| Question difficulty calibration accuracy (IRT fit) | ≥ 80% within ±0.5 logit of target | IRT model output |

**Business KPIs:**
| KPI | Target | Measurement Method |
|-----|--------|-------------------|
| Free-to-paid conversion rate | ≥ 15% (60-day window) | CRM / payment analytics |
| Monthly churn (Pro subscribers) | ≤ 5% | Payment analytics |
| Customer Acquisition Cost (CAC) — consumer | ≤ $30 | Marketing spend / new paid customers |
| Lifetime Value (LTV) — consumer | ≥ $90 (6-month avg tenure × $14.99) | Cohort analysis |
| School renewal rate | ≥ 85% | CRM |

### Definition of "Success" by Stage

| Stage | "Success" Definition |
|-------|---------------------|
| Concept Validation (PoC) | Parent NPS ≥ 40; diagnostic accuracy ≥ 80%; ≥ 3 students show measurable learning gain in 6 weeks; no critical quality or safety issues reported |
| MVP Launch | 500 active monthly students; ≥ 50 paying Pro subscribers; ≤ 5% bad question rate; 1+ school pilot; MRR ≥ $750 |
| MMP Launch | 1,500 active monthly students; 5+ school partnerships (2+ paying); outcome data showing ≥ 20% proficiency gain; ARR ≥ $100,000; Teacher NPS ≥ 55 |
| Full Product v1.0 | 5,000 active monthly students; 10+ paying school/district partnerships; ARR ≥ $500,000; independent outcome study published; Series A ready |

---

*Document prepared by PADI.AI founding team — April 2026. All financial projections are estimates based on comparable EdTech market data. Outcome projections are targets, not guarantees.*
