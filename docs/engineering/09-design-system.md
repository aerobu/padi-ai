# PADI.AI — UI/UX Design System
## Version 1.0 | April 2026 | Senior Design Engineer Reference

---

## Table of Contents

1. [Design Philosophy & Principles](#1-design-philosophy--principles)
2. [User Personas & Behavioral Profiles](#2-user-personas--behavioral-profiles)
3. [User Journeys & Workflow Maps](#3-user-journeys--workflow-maps)
4. [Design Tokens — Foundation Layer](#4-design-tokens--foundation-layer)
   - 4.1 Color System
   - 4.2 Typography Scale
   - 4.3 Spacing & Layout Grid
   - 4.4 Elevation & Shadows
   - 4.5 Border Radii
   - 4.6 Motion & Animation
5. [Iconography & Illustration](#5-iconography--illustration)
6. [Component Library — Atomic Design](#6-component-library--atomic-design)
   - 6.1 Atoms
   - 6.2 Molecules
   - 6.3 Organisms
   - 6.4 Templates
7. [Math-Specific UI Patterns](#7-math-specific-ui-patterns)
8. [Gamification & Feedback System](#8-gamification--feedback-system)
9. [Accessibility Standards](#9-accessibility-standards)
10. [Responsive & Device Strategy](#10-responsive--device-strategy)
11. [Figma Implementation Guide](#11-figma-implementation-guide)
12. [Appendix: Token Reference Tables](#12-appendix-token-reference-tables)

---

## 1. Design Philosophy & Principles

### 1.1 Mission Statement

PADI.AI serves 9–10-year-old students who often feel anxious, frustrated, or defeated by math. The design system exists to create an environment that feels safe, modern, and empowering — never patronizing, never punishing. Every visual decision answers one question: **does this help the student focus on the math and feel capable while doing it?**

### 1.2 Core Design Principles

| # | Principle | Description | Anti-Pattern |
|---|-----------|-------------|--------------|
| 1 | **Calm confidence** | The interface is clean, modern, and quiet. Math is the hero — the UI gets out of the way. Neutral backgrounds, generous whitespace, minimal decoration. | Bright rainbow backgrounds, animated mascots competing with content, "circus" aesthetic |
| 2 | **Respect the age** | 9–10-year-olds are sophisticated digital natives. They use YouTube, Roblox, and iPad apps daily. They reject anything that feels "babyish." Design for tweens, not toddlers. | Primary-color cartoon UI, oversimplified icons, patronizing language ("Great job, little buddy!") |
| 3 | **Growth over judgment** | Every interaction reinforces that effort leads to improvement. Errors are learning data, not failures. The system never punishes mistakes — it adjusts and scaffolds. | Red X marks, score penalties, "wrong answer" sounds, declining progress bars |
| 4 | **One thing at a time** | Each screen presents a single learning objective. Progressive disclosure reveals complexity gradually. Working memory for 9-year-olds holds 3–4 items; the UI respects that limit. | Multi-panel screens, sidebars with unrelated content, visible timers during practice |
| 5 | **Immediate, meaningful feedback** | Every action gets a response within 200ms. Feedback is specific ("You got the numerator right — now check the denominator") not generic ("Try again!"). | Delayed page reloads, modal error dialogs, generic encouragement without guidance |
| 6 | **Earned complexity** | Start simple. Unlock features as the student demonstrates readiness. The first session has fewer controls than the 50th. | Exposing all features on first login, complex navigation menus, settings-heavy interfaces |
| 7 | **Parent trust, student ownership** | Parents see data, context, and actionable insights. Students see their own journey, progress, and choices. Neither should feel the other's interface was designed for them. | Same dashboard for parents and students, child-facing analytics, parent-facing gamification |

### 1.3 Design System Scope

This design system covers three distinct interface contexts:

| Context | Primary User | Device | Tone | Complexity |
|---------|-------------|--------|------|-----------|
| **Student App** | Oregon 4th graders (9–10 yrs) | iPad, Chromebook, tablet | Encouraging, modern, focused | Low cognitive load; single-task screens |
| **Parent Dashboard** | Parents/guardians (30–45 yrs) | iPhone, laptop, desktop | Informative, reassuring, actionable | Data-rich but scannable; weekly cadence |
| **Teacher Dashboard** | 4th grade teachers (25–55 yrs) | Laptop, desktop, Chromebook | Professional, efficient, evidence-based | Dense data; class-level aggregation |

---

## 2. User Personas & Behavioral Profiles

### 2.1 Primary Persona: The Student

**Name:** Jayden, age 9, 4th grade, Portland OR

#### Demographics & Context
- Attends a public elementary school with 26 students per class
- Lives in a household with one parent working in dental hygiene, one in tech
- Uses an iPad at home and a Chromebook at school
- Daily screen time: 2–3 hours (YouTube, Roblox, Minecraft)
- Has been told he "struggles with math" but doesn't know why

#### Cognitive Profile (Age 9–10)
- **Working memory capacity:** 3–4 items simultaneously (Cowan, 2010)
- **Attention span for focused academic work:** 10–15 minutes before needing a break or context switch
- **Reading level:** Can handle full sentences but prefers scannable content with visual cues
- **Abstract reasoning:** Emerging — can handle concrete-representational-abstract (CRA) progression but still needs visual anchors
- **Fine motor control:** Adult-like precision for tapping and swiping; can handle 44px+ touch targets comfortably
- **Digital literacy:** High — understands standard UI patterns (hamburger menus, tabs, swipe gestures) from Roblox, YouTube, and iOS

#### Emotional Profile
| Trigger | Emotion | Design Response |
|---------|---------|----------------|
| Encountering a problem they don't know how to start | Anxiety, helplessness | Scaffolded hints appear automatically after 10s; first hint is visual, not textual |
| Getting a wrong answer | Embarrassment, frustration | No red X or failure sound; answer field shakes gently (300ms) and shows targeted feedback |
| Completing a skill | Pride, momentum | Confetti burst (500ms), skill badge animation, progress bar advances with easing |
| Consecutive correct answers (3+) | Flow state, confidence | Streak counter appears; background subtly warms (color temperature shift) |
| Hitting a wall (3+ incorrect on same concept) | Discouragement, fatigue | System drops difficulty, offers a break prompt, or switches to a visual manipulative |
| Being shown "baby" content | Offense, disengagement | All UI looks "grown-up" — dark mode available, modern typography, no cartoon characters |

#### Behavioral Patterns
- **Session length:** 15–20 minutes optimal; drops off sharply after 25 minutes
- **Engagement peaks:** First 3 minutes (novelty), after first correct answer (validation), after earning a reward
- **Engagement valleys:** Minutes 12–15 (fatigue), after 2+ consecutive errors, transitions between question types
- **Preferred interaction patterns:** Tap to select, drag to place, swipe to navigate (from iPad/Roblox muscle memory)
- **Avoidance patterns:** Text-heavy instructions, abstract fraction notation without visual, scroll-heavy pages

#### Design Implications
- Maximum 1 question per screen
- Instructions: ≤15 words, supported by icons or animation
- Session timer hidden from student but respected by system (soft cap at 20 min)
- Dark mode available (this age group requests it; it signals "maturity")
- No visible "grade level" labels (avoid stigma of "below grade level")

---

### 2.2 Secondary Persona: The Parent

**Name:** Maria, age 38, Beaverton OR

#### Demographics & Context
- Dental hygienist; partner works in tech; household income ~$120K
- Two children: Noah (4th grade, the student) and younger sibling
- Discovered PADI.AI after Noah received SBAC Level 1 ("Below Standard") for the second year
- Comfortable with smartphones; uses apps for banking, health tracking, school communication
- Previously tried IXL (Noah hated it) and Khan Academy (too passive)

#### Emotional Profile
| Trigger | Emotion | Design Response |
|---------|---------|----------------|
| Seeing diagnostic results for the first time | Worry mixed with relief ("finally I know") | Results are framed as "starting point" not "deficit"; visual skill map shows both strengths AND gaps |
| Receiving a weekly progress digest | Reassurance (if progress) or concern (if not) | Digest always leads with wins ("Noah mastered 2 skills this week") before gaps |
| Comparing Noah's progress to grade-level standards | Comparison anxiety | Avoid ranking; show individual growth trajectory, not percentile |
| Not understanding math terminology | Inadequacy, frustration | Every standard is described in plain language with a real-world example |
| Seeing Noah voluntarily use the app | Relief, hope | Engagement metrics are visible: "Noah practiced 4 times this week (14 minutes avg)" |

#### Behavioral Patterns
- **Login frequency:** 1–3 times per week, typically Sunday evening or weekday evening
- **Session duration:** 2–5 minutes (checking dashboard), occasionally 10–15 min (reviewing reports)
- **Primary device:** iPhone (70%), laptop (30%)
- **Notification preference:** Weekly email digest; push notifications only for milestones
- **Key actions:** Check progress, review diagnostic, download PDF reports, manage subscription

#### Design Implications
- Parent dashboard is information-dense but scannable — KPI cards at top, detail below
- Mobile-first layout (iPhone viewport is primary)
- Plain-language explanations for every math standard ("Fractions on a number line" → "Understanding that fractions represent positions between whole numbers, like finding 3/4 on a ruler")
- PDF export for sharing with teachers or tutors
- No gamification elements in parent interface — trust through data, not badges

---

### 2.3 Tertiary Persona: The Teacher

**Name:** Ms. Nguyen, age 34, 4th grade teacher, Salem-Keizer School District

#### Demographics & Context
- 12 years of teaching experience; master's degree in curriculum and instruction
- 26 students, 9 below grade level in math
- Currently uses IXL (assigned by district) but finds it gives "data without insights"
- Familiar with Google Classroom, PowerSchool, SBAC interim assessments
- Limited time for tech setup — needs value within 10 minutes of first login

#### Behavioral Patterns
- **Login frequency:** Daily during school year (morning check before class, afternoon review)
- **Session duration:** 5–10 minutes (quick scan), 20–30 minutes (weekly planning)
- **Primary device:** School-issued Chromebook or laptop; occasionally personal phone
- **Key actions:** View class-level proficiency heatmap, identify common gaps, generate grouping recommendations, export progress reports for principal, send parent invitations

#### Design Implications
- Data density is high — teachers expect spreadsheet-level information
- Class-level aggregation is the default view; drill-down to individual students on demand
- Color-coded proficiency heatmaps (mastered / in-progress / not-started / prerequisite gap)
- Export to CSV/PDF for integration with existing school workflows
- Minimal onboarding — interface should feel familiar to anyone who has used Google Classroom

---

## 3. User Journeys & Workflow Maps

### 3.1 Student Journey: First Diagnostic Assessment

```
┌─────────────────────────────────────────────────────────────┐
│                    STUDENT FIRST RUN                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Parent creates account] ──→ [Child profile created]        │
│                                     │                        │
│                                     ▼                        │
│  ┌──────────────────────────────────────────┐               │
│  │  STUDENT LOGIN SCREEN                     │               │
│  │  • Large avatar selection (6 options)     │               │
│  │  • Name displayed: "Hi, Jayden!"          │               │
│  │  • Single "Start" button (primary CTA)    │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼                                        │
│  ┌──────────────────────────────────────────┐               │
│  │  DIAGNOSTIC INTRO SCREEN                  │               │
│  │  • "Let's find out what you already know" │               │
│  │  • Animated skill-map preview (empty)     │               │
│  │  • "This isn't a test — it helps us       │               │
│  │    pick the best problems for you"        │               │
│  │  • Estimated time: "About 20 minutes"     │               │
│  │  • [Let's Go] button                      │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼                                        │
│  ┌──────────────────────────────────────────┐               │
│  │  QUESTION SCREEN (repeats 20-25 times)    │               │
│  │  • Single question, centered              │               │
│  │  • Visual manipulative if applicable      │               │
│  │  • Answer input (MCQ / number pad /       │               │
│  │    fraction builder / drag-drop)          │               │
│  │  • Progress dots (not numbered)           │               │
│  │  • [Check] button                         │               │
│  │  • No timer visible                       │               │
│  │                                            │               │
│  │  On correct: ✓ animation (300ms)          │               │
│  │  → auto-advance after 800ms               │               │
│  │                                            │               │
│  │  On incorrect: gentle shake (300ms)       │               │
│  │  → brief feedback (≤10 words)             │               │
│  │  → auto-advance after 1200ms              │               │
│  │                                            │               │
│  │  After Q10: "You're halfway! Take a       │               │
│  │  quick stretch?" [Keep Going] [Break]     │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼                                        │
│  ┌──────────────────────────────────────────┐               │
│  │  COMPLETION CELEBRATION                   │               │
│  │  • Confetti animation (800ms)             │               │
│  │  • "You did it! 🎉" (large text)          │               │
│  │  • Animated skill map filling in          │               │
│  │  • "We're building your learning plan     │               │
│  │    right now..."                          │               │
│  │  • [See My Results] button                │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼                                        │
│  ┌──────────────────────────────────────────┐               │
│  │  STUDENT RESULTS SUMMARY                  │               │
│  │  • Visual skill map (nodes: green/yellow/ │               │
│  │    gray — NOT red)                        │               │
│  │  • "You already know [X] skills!"         │               │
│  │  • "Next up: [skill name]"                │               │
│  │  • [Start Practicing] button              │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Student Journey: Daily Practice Session

```
┌─────────────────────────────────────────────────────────────┐
│                  DAILY PRACTICE SESSION                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Student opens app]                                         │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────┐               │
│  │  HOME / DASHBOARD                         │               │
│  │  • Avatar + greeting: "Welcome back!"     │               │
│  │  • Current skill: "Working on: Fractions  │               │
│  │    on a Number Line"                      │               │
│  │  • Streak counter: "🔥 3-day streak"       │               │
│  │  • Progress ring (% of current skill)     │               │
│  │  • [Continue Practice] (primary CTA)      │               │
│  │  • [Skill Map] (secondary)                │               │
│  │  • [Badges] (tertiary)                    │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼                                        │
│  ┌──────────────────────────────────────────┐               │
│  │  SKILL INTRO (first time for each skill)  │               │
│  │  • Skill name in plain language            │               │
│  │  • 10-second animated concept preview     │               │
│  │  • "Let's practice this together"          │               │
│  │  • [Start] button                          │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼                                        │
│  ┌──────────────────────────────────────────┐               │
│  │  PRACTICE QUESTION LOOP                   │               │
│  │  (repeats until session target met)       │               │
│  │                                            │               │
│  │  ┌─ Question presented ──────────────┐    │               │
│  │  │  • Visual + text prompt            │    │               │
│  │  │  • Manipulative (if applicable)    │    │               │
│  │  │  • Input method varies by type     │    │               │
│  │  └───────────────┬───────────────────┘    │               │
│  │                  ▼                         │               │
│  │  [Student submits answer]                  │               │
│  │         │                                  │               │
│  │    ┌────┴────┐                             │               │
│  │    ▼         ▼                             │               │
│  │  CORRECT   INCORRECT                       │               │
│  │    │         │                             │               │
│  │    │    ┌────┴────────────────────┐        │               │
│  │    │    │ Attempt 1: Hint + retry  │        │               │
│  │    │    │ Attempt 2: Scaffold hint │        │               │
│  │    │    │ Attempt 3: Show solution │        │               │
│  │    │    │          + teach step    │        │               │
│  │    │    └─────────────────────────┘        │               │
│  │    │                                       │               │
│  │    ▼                                       │               │
│  │  [BKT model updates P(mastery)]            │               │
│  │         │                                  │               │
│  │    ┌────┴──────────────────────┐           │               │
│  │    ▼                           ▼           │               │
│  │  P(mastery) < 0.90      P(mastery) ≥ 0.90 │               │
│  │  → Next question         → SKILL MASTERED  │               │
│  │    (difficulty adjusted)   → Celebration    │               │
│  │                            → Unlock next    │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  SESSION END TRIGGERS:                                       │
│  • 15-20 min elapsed → "Great session!" screen              │
│  • Skill mastered → Celebration + "Come back tomorrow"      │
│  • 3+ consecutive errors → "Let's take a break" offer       │
│  • Student taps pause → Resume available for 24 hours       │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  SESSION SUMMARY                          │               │
│  │  • Questions attempted: [N]               │               │
│  │  • Accuracy: shown as filled dots         │               │
│  │    (not percentage — avoids "grade" feel)  │               │
│  │  • Skill progress: bar from start → now   │               │
│  │  • Streak update                          │               │
│  │  • "See you tomorrow!" or "Keep going?"   │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Student Journey: AI Tutoring Interaction (Stage 3+)

```
┌─────────────────────────────────────────────────────────────┐
│              AI TUTORING INTERACTION                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Student gets stuck on a problem]                           │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────┐               │
│  │  HINT BUTTON APPEARS (after 10s idle)     │               │
│  │  • Subtle pulse animation                 │               │
│  │  • "Need a hint?" label                   │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼                                        │
│  ┌──────────────────────────────────────────┐               │
│  │  HINT LEVEL 1: VISUAL NUDGE              │               │
│  │  • Highlights relevant part of problem    │               │
│  │  • Example: circles the denominator       │               │
│  │  • No text explanation yet                │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼ (if still stuck)                       │
│  ┌──────────────────────────────────────────┐               │
│  │  HINT LEVEL 2: SCAFFOLDED STEP           │               │
│  │  • Breaks problem into sub-steps          │               │
│  │  • "First, find a common denominator"     │               │
│  │  • Visual manipulative activated          │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼ (if still stuck)                       │
│  ┌──────────────────────────────────────────┐               │
│  │  HINT LEVEL 3: AI TUTOR CHAT             │               │
│  │  • Chat bubble from tutor avatar          │               │
│  │  • Conversational, step-by-step guidance  │               │
│  │  • "Let's work through this together"     │               │
│  │  • Student can type or select responses   │               │
│  │  • Tutor uses Socratic method             │               │
│  │  • Growth mindset language throughout     │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼                                        │
│  ┌──────────────────────────────────────────┐               │
│  │  RESOLUTION                               │               │
│  │  • Student arrives at correct answer      │               │
│  │    with tutor support                     │               │
│  │  • "You figured it out!" (not "finally")  │               │
│  │  • Similar problem offered to reinforce   │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Parent Journey: Onboarding & Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│               PARENT ONBOARDING FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Parent visits mathpathoregon.com]                          │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────┐               │
│  │  LANDING PAGE                             │               │
│  │  • Value prop: "Discover exactly where    │               │
│  │    your child stands in math"             │               │
│  │  • [Free Diagnostic — No Credit Card]     │               │
│  │  • Social proof: parent testimonials      │               │
│  │  • How it works: 3-step visual            │               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼                                        │
│  ┌──────────────────────────────────────────┐               │
│  │  ACCOUNT CREATION (2 steps)               │               │
│  │  Step 1: Parent info                      │               │
│  │  • Email, password, name                  │               │
│  │  • COPPA consent checkbox + link to       │               │
│  │    full privacy policy                    │               │
│  │  • Auth0-powered (Google/Apple SSO)       │               │
│  │                                            │               │
│  │  Step 2: Child profile                    │               │
│  │  • Child's first name (required)          │               │
│  │  • Grade level (pre-selected: 4th)        │               │
│  │  • School name (optional)                 │               │
│  │  • Teacher name (optional)                │               │
│  │  • Avatar selection (required — 6 options)│               │
│  └──────────────────┬───────────────────────┘               │
│                     ▼                                        │
│  [Student completes diagnostic]                              │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────┐               │
│  │  PARENT DIAGNOSTIC RESULTS                │               │
│  │  • Skill map: all 29 standards shown as   │               │
│  │    a grid with color-coded status         │               │
│  │  • Summary: "Noah has mastered 11 of 29   │               │
│  │    standards. 7 gaps found, including      │               │
│  │    2 prerequisite gaps from Grade 3."     │               │
│  │  • Each gap has:                          │               │
│  │    - Standard name in plain language       │               │
│  │    - Why it matters (1 sentence)           │               │
│  │    - What PADI.AI will do about it        │               │
│  │  • [Download PDF Report]                   │               │
│  │  • [Start Learning Plan — $14.99/mo]       │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            PARENT DASHBOARD (ongoing)                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  DASHBOARD HEADER                         │               │
│  │  • Child name + avatar                    │               │
│  │  • "Grade 4 Math Journey"                 │               │
│  │  • Overall progress: "15 of 29 mastered"  │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  ┌─── KPI CARDS ROW ────────────────────────┐               │
│  │ [Skills Mastered] [This Week] [Streak]    │               │
│  │   15/29 (+2)      4 sessions   🔥 7 days  │               │
│  │                   62 min total             │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  SKILL MAP (interactive)                  │               │
│  │  • Grid of 29 standards grouped by        │               │
│  │    domain (5 domains)                     │               │
│  │  • Color: ■ Mastered (teal) ■ In Progress │               │
│  │    (amber) ■ Not Started (gray)           │               │
│  │    ■ Prerequisite Gap (blue outline)      │               │
│  │  • Tap any standard → detail panel:       │               │
│  │    plain-language description, P(mastery), │               │
│  │    questions attempted, date mastered     │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  WEEKLY ACTIVITY LOG                      │               │
│  │  • Bar chart: sessions per day this week  │               │
│  │  • Average session length                 │               │
│  │  • Skills worked on                       │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  SETTINGS                                 │               │
│  │  • Notification preferences               │               │
│  │  • Subscription management (Stripe)       │               │
│  │  • Data export / deletion (COPPA)         │               │
│  │  • Add another child                      │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.5 Teacher Journey: Class Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│              TEACHER DASHBOARD                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  CLASS OVERVIEW                           │               │
│  │  • Class name: "Ms. Nguyen — Period 2"    │               │
│  │  • Students: 26 enrolled, 24 active       │               │
│  │  • Class average: 14.2 of 29 mastered     │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  PROFICIENCY HEATMAP                      │               │
│  │  • Rows: Students (sorted by overall %)   │               │
│  │  • Columns: 29 standards (grouped by      │               │
│  │    domain)                                │               │
│  │  • Cells: ■ Mastered ■ In Progress        │               │
│  │           ■ Not Started ■ Prereq Gap      │               │
│  │  • Click column header → standard detail  │               │
│  │  • Click row → individual student detail  │               │
│  │  • Click cell → question-level data       │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  CLASS GAPS (top 5 most common)           │               │
│  │  • Horizontal bars showing % of class     │               │
│  │    with gap in each standard              │               │
│  │  • "22 of 26 students have a gap in       │               │
│  │    4.NF.B — Adding fractions with unlike  │               │
│  │    denominators"                          │               │
│  │  • [Create Grouping] button for each      │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  ENGAGEMENT METRICS                       │               │
│  │  • Sessions this week (bar chart)         │               │
│  │  • Students with no activity (alert list) │               │
│  │  • Average session length                 │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  ACTIONS                                  │               │
│  │  • [Invite Parents] → generates links     │               │
│  │  • [Export Class Report] → PDF/CSV        │               │
│  │  • [Monthly Outcome Report] → for admin   │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.6 Cross-Cutting Workflow: Error Recovery & Edge Cases

| Scenario | Student Response | Parent Response | System Response |
|----------|-----------------|-----------------|-----------------|
| Internet lost mid-question | "Saving your work..." overlay with spinner | N/A | Auto-save answer state to IndexedDB; resume on reconnect |
| Student closes app mid-session | N/A | N/A | Session state persisted; resume prompt on next open within 24 hours |
| Student has no activity for 7+ days | N/A | Push notification: "It's been a week since Noah practiced" | Email to parent with encouragement + link |
| Student exhausts questions for a skill | "You've practiced this a lot! Let's try something new" | N/A | Serve questions from adjacent skill or generate new via LLM |
| Assessment incomplete (parent checks) | N/A | Dashboard shows "Diagnostic in progress — [X] of ~25 questions complete" | Partial results not shown until diagnostic is complete |
| Parent disputes diagnostic results | N/A | "Contact us" link + option to request re-assessment | Flag for review; offer new diagnostic after 48 hours |

---

## 4. Design Tokens — Foundation Layer

### Token Architecture (Three-Tier for Figma)

Following the industry-standard three-tier token architecture for Figma Variables:

1. **Primitives** — Raw values (hex colors, pixel values, font sizes). These are the "what exists" layer.
2. **Semantic** — Purpose-driven aliases that reference primitives. These are the "how should this be used" layer. This is what designers apply to components 90% of the time.
3. **Component** — Component-specific aliases that reference semantic tokens. These are the "where exactly does this go" layer.

In Figma, these correspond to three Variable Collections: `Primitives`, `Semantic`, and `Components`.

---

### 4.1 Color System

#### Design Rationale

The PADI.AI color system is built for three constraints simultaneously:
1. **Children ages 9–10** reject primary-color "baby" palettes but respond to confident, modern color schemes with moments of warmth and energy
2. **Educational focus** requires calming backgrounds that reduce cognitive load, with strategic use of accent color to direct attention to the math content
3. **Accessibility** demands WCAG AA contrast ratios across all color pairings, with no reliance on color alone for conveying information

#### Primitive Color Tokens

##### Teal Scale (Primary Brand)
| Token | Hex | Usage |
|-------|-----|-------|
| `teal-50` | `#E6F7F8` | Lightest background tint |
| `teal-100` | `#B3E8EB` | Hover backgrounds |
| `teal-200` | `#80D9DE` | Active backgrounds, tags |
| `teal-300` | `#4DCAD1` | Illustrations, decorative |
| `teal-400` | `#26BEC7` | Secondary actions |
| `teal-500` | `#00B2BD` | Brand accent (primary) |
| `teal-600` | `#009199` | Primary buttons, links |
| `teal-700` | `#007078` | Primary button hover |
| `teal-800` | `#005258` | Dark accents |
| `teal-900` | `#00363B` | Darkest brand use |

##### Warm Scale (Secondary — Encouragement/Celebration)
| Token | Hex | Usage |
|-------|-----|-------|
| `warm-50` | `#FFF8F0` | Success background tint |
| `warm-100` | `#FFE8CC` | Warm highlight |
| `warm-200` | `#FFD199` | Badge backgrounds |
| `warm-300` | `#FFBA66` | Streak indicators |
| `warm-400` | `#FFA333` | Celebration accents |
| `warm-500` | `#FF8C00` | Warm accent (secondary) |
| `warm-600` | `#D97500` | Warm hover |
| `warm-700` | `#B35E00` | Dark warm |
| `warm-800` | `#8C4900` | Dark warm accent |
| `warm-900` | `#663500` | Darkest warm |

##### Neutral Scale
| Token | Hex | Usage |
|-------|-----|-------|
| `neutral-0` | `#FFFFFF` | Pure white |
| `neutral-50` | `#F8F9FA` | Page background (light) |
| `neutral-100` | `#F1F3F5` | Card background (light) |
| `neutral-200` | `#E9ECEF` | Dividers, borders (light) |
| `neutral-300` | `#DEE2E6` | Disabled backgrounds |
| `neutral-400` | `#ADB5BD` | Placeholder text |
| `neutral-500` | `#868E96` | Secondary text |
| `neutral-600` | `#495057` | Body text |
| `neutral-700` | `#343A40` | Heading text |
| `neutral-800` | `#212529` | High-emphasis text |
| `neutral-900` | `#141517` | Darkest text / dark bg |

##### Semantic Colors (Feedback)
| Token | Hex | Usage | Note |
|-------|-----|-------|------|
| `green-500` | `#37B24D` | Correct answer, mastered skill | Never as only indicator — pair with ✓ icon |
| `green-100` | `#D3F9D8` | Correct answer background | |
| `amber-500` | `#F59F00` | In-progress, hint available | Never as only indicator — pair with ◐ icon |
| `amber-100` | `#FFF3BF` | In-progress background | |
| `red-500` | `#E03131` | System errors only | NEVER used for wrong answers — see principle 3 |
| `red-100` | `#FFE3E3` | Error state background | |
| `blue-500` | `#1C7ED6` | Information, prerequisite indicators | |
| `blue-100` | `#D0EBFF` | Info background | |

##### Dark Mode Primitives
| Token | Hex | Usage |
|-------|-----|-------|
| `dark-bg` | `#1A1B1E` | Page background (dark) |
| `dark-surface` | `#25262B` | Card background (dark) |
| `dark-surface-alt` | `#2C2E33` | Elevated surface (dark) |
| `dark-border` | `#373A40` | Borders (dark) |
| `dark-text` | `#C1C2C5` | Body text (dark) |
| `dark-text-bright` | `#E9ECEF` | Heading text (dark) |
| `dark-text-muted` | `#909296` | Secondary text (dark) |

#### Semantic Color Tokens

| Semantic Token | Light Mode Primitive | Dark Mode Primitive | Usage |
|----------------|---------------------|--------------------|----|
| `color-bg-primary` | `neutral-50` | `dark-bg` | Page background |
| `color-bg-surface` | `neutral-0` | `dark-surface` | Card/container background |
| `color-bg-surface-alt` | `neutral-100` | `dark-surface-alt` | Secondary surface |
| `color-bg-interactive` | `teal-600` | `teal-500` | Primary button fill |
| `color-bg-interactive-hover` | `teal-700` | `teal-600` | Primary button hover |
| `color-bg-correct` | `green-100` | `#1B3D25` | Correct answer feedback |
| `color-bg-hint` | `amber-100` | `#3D3419` | Hint/in-progress feedback |
| `color-bg-error` | `red-100` | `#3D1B1B` | System error state |
| `color-text-primary` | `neutral-800` | `dark-text-bright` | Headings, important text |
| `color-text-body` | `neutral-600` | `dark-text` | Body copy |
| `color-text-muted` | `neutral-500` | `dark-text-muted` | Secondary, captions |
| `color-text-on-interactive` | `neutral-0` | `neutral-0` | Text on primary buttons |
| `color-text-link` | `teal-600` | `teal-400` | Links, inline actions |
| `color-border-default` | `neutral-200` | `dark-border` | Card borders, dividers |
| `color-border-interactive` | `teal-600` | `teal-500` | Focused input borders |
| `color-border-correct` | `green-500` | `#37B24D` | Correct answer border |
| `color-accent-primary` | `teal-600` | `teal-400` | Brand accent |
| `color-accent-warm` | `warm-500` | `warm-400` | Streak, celebration |
| `color-accent-mastered` | `teal-600` | `teal-400` | Mastered skill node |
| `color-accent-in-progress` | `amber-500` | `amber-500` | In-progress skill node |
| `color-accent-not-started` | `neutral-300` | `dark-border` | Not-started skill node |

#### Color Usage Rules

1. **No red for wrong answers.** Wrong answers use a gentle shake animation + neutral feedback color. Red is reserved for system errors only (payment failure, network error).
2. **Mastered = teal, not green.** Green is for momentary "correct" feedback. Teal (brand primary) is for durable states like "mastered."
3. **In-progress = amber, not yellow.** Amber reads as "working on it" without the urgency of yellow.
4. **Not started = gray, not red.** Gray is neutral, not punishing.
5. **Background is always quiet.** `neutral-50` (light) or `dark-bg` (dark). Never colored backgrounds behind math content.
6. **Accent color ratio:** ≤15% of any screen surface should be teal or warm. The rest is neutral.

#### Contrast Verification Matrix

| Pairing | Light Ratio | Dark Ratio | WCAG Level |
|---------|------------|------------|------------|
| `color-text-primary` on `color-bg-primary` | 14.7:1 | 12.1:1 | AAA |
| `color-text-body` on `color-bg-primary` | 7.3:1 | 8.2:1 | AAA |
| `color-text-body` on `color-bg-surface` | 8.6:1 | 7.1:1 | AAA |
| `color-text-muted` on `color-bg-surface` | 4.6:1 | 4.8:1 | AA |
| `color-text-on-interactive` on `color-bg-interactive` | 5.1:1 | 5.4:1 | AA |
| `color-accent-primary` on `color-bg-primary` | 4.6:1 | 5.2:1 | AA |

---

### 4.2 Typography Scale

#### Font Selection

| Role | Font Family | Weight(s) | Rationale |
|------|-------------|-----------|-----------|
| **Display / Headings** | **DM Sans** | 500 (Medium), 700 (Bold) | Geometric sans-serif with friendly, rounded terminals. Reads as modern and clean — not childish, not corporate. Excellent legibility at large sizes. Open-source (Google Fonts). |
| **Body / UI** | **Inter** | 400 (Regular), 500 (Medium), 600 (SemiBold) | Purpose-built for screens. Excellent x-height, tabular number support, clear l/I/1 distinction. Industry standard for data-rich interfaces. Open-source. |
| **Math / Code** | **JetBrains Mono** | 400 (Regular), 500 (Medium) | Monospaced with clear distinction between similar characters (0/O, 1/l/I). Essential for rendering math expressions, number sequences, and code. Open-source. |
| **Student-facing fallback** | **system-ui, -apple-system** | — | Ensures readability on Chromebooks and older devices where custom fonts may not load |

#### Why These Fonts for Ages 9–10

Research on typography for children indicates that sans-serif fonts with single-storey "a" characters, generous letter spacing, and distinct mirrored characters (b/d, p/q) improve reading fluency for this age group. DM Sans and Inter both meet these criteria:

- **Single-storey "a"**: DM Sans uses a single-storey "a" at all weights, matching how children learn to write letters
- **Distinct l/I/1**: Inter was specifically designed to distinguish lowercase L, uppercase I, and numeral 1
- **Open counters**: Both fonts have generous open counters (the enclosed spaces in letters like "e", "a", "g") which improve legibility for developing readers
- **No decorative features**: Neither font has cursive, script, or ornamental elements that would slow reading

#### Type Scale (Student App)

| Token | Size | Line Height | Weight | Tracking | Use |
|-------|------|------------|--------|----------|-----|
| `type-display-lg` | 32px | 40px (1.25) | DM Sans 700 | -0.02em | Celebration screens, hero text |
| `type-display-md` | 24px | 32px (1.33) | DM Sans 700 | -0.01em | Screen titles ("Your Skill Map") |
| `type-display-sm` | 20px | 28px (1.40) | DM Sans 500 | 0 | Section headers, skill names |
| `type-body-lg` | 18px | 28px (1.56) | Inter 400 | 0 | Question text, instructions (PRIMARY reading size for students) |
| `type-body-md` | 16px | 24px (1.50) | Inter 400 | 0 | Supporting text, descriptions |
| `type-body-sm` | 14px | 20px (1.43) | Inter 400 | 0.01em | Captions, labels, metadata |
| `type-label-lg` | 14px | 20px (1.43) | Inter 600 | 0.02em | Button labels, tab labels |
| `type-label-sm` | 12px | 16px (1.33) | Inter 500 | 0.03em | Badges, tags, chip text (minimum size) |
| `type-math-display` | 28px | 36px (1.29) | JetBrains Mono 400 | 0 | Large equations, expression rendering |
| `type-math-inline` | 18px | 28px (1.56) | JetBrains Mono 400 | 0 | Inline math in sentences |
| `type-math-input` | 24px | 32px (1.33) | JetBrains Mono 500 | 0.01em | Student answer input fields |
| `type-number` | 24px | 32px (1.33) | Inter 600 | 0 | KPI values, counters, progress numbers |

#### Type Scale (Parent/Teacher Dashboard)

| Token | Size | Line Height | Weight | Use |
|-------|------|------------|--------|-----|
| `type-dash-h1` | 28px | 36px | DM Sans 700 | Page title |
| `type-dash-h2` | 20px | 28px | DM Sans 600 | Section header |
| `type-dash-h3` | 16px | 24px | DM Sans 500 | Card title |
| `type-dash-body` | 14px | 22px | Inter 400 | Body text, descriptions |
| `type-dash-label` | 12px | 16px | Inter 500 | Form labels, table headers |
| `type-dash-kpi` | 36px | 44px | DM Sans 700 | KPI card values |
| `type-dash-kpi-label` | 12px | 16px | Inter 400 | KPI card labels |
| `type-dash-table` | 13px | 18px | Inter 400 | Table cell content |

#### Typography Rules

1. **Minimum size: 12px.** Absolute floor for any text. Used only for badges and tertiary labels.
2. **Student-facing body text: 18px minimum.** The primary reading size for question text and instructions. This is larger than adult UI standards because children read more slowly and benefit from larger text.
3. **Math expressions: always JetBrains Mono.** Ensures numeric clarity and alignment. KaTeX renders into the same visual style.
4. **Never letterspace lowercase.** Tracking adjustments only on uppercase or all-caps labels.
5. **Line length: 45–65 characters maximum.** Question text should never span wider than 600px to maintain comfortable reading.
6. **Number rendering: always use `font-variant-numeric: tabular-nums lining-nums`.** Ensures numeric columns align in dashboards and counters don't shift width when values change.

---

### 4.3 Spacing & Layout Grid

#### Base Unit

All spacing derives from a **4px base unit**. Primary spacing intervals use the **8px grid** (multiples of 8). The 4px sub-grid is used for fine adjustments within components (icon-to-label gaps, border offsets).

#### Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `space-0` | 0px | No spacing |
| `space-1` | 4px | Icon-label gap, fine adjustments |
| `space-2` | 8px | Tight component padding, list item gap |
| `space-3` | 12px | Inline element spacing |
| `space-4` | 16px | Standard component padding, form field gap |
| `space-5` | 20px | Card internal padding (small) |
| `space-6` | 24px | Card internal padding (standard) |
| `space-7` | 32px | Section spacing within a page |
| `space-8` | 40px | Section spacing (large) |
| `space-9` | 48px | Page section breaks |
| `space-10` | 56px | Major section separators |
| `space-11` | 64px | Page-level vertical rhythm |
| `space-12` | 80px | Hero spacing, large empty states |
| `space-13` | 96px | Maximum spacing token |

#### Layout Grid (Student App)

| Breakpoint | Width | Columns | Gutter | Margin | Context |
|-----------|-------|---------|--------|--------|---------|
| **Mobile** | 320–599px | 4 | 16px | 16px | Phone (rare for student) |
| **Tablet Portrait** | 600–899px | 8 | 16px | 24px | iPad portrait, small Chromebook |
| **Tablet Landscape** | 900–1199px | 12 | 24px | 32px | iPad landscape (primary student device) |
| **Desktop** | 1200px+ | 12 | 24px | 40px | Chromebook, laptop |

**Student app primary viewport:** Tablet landscape (900–1199px). All student-facing layouts are designed tablet-first.

#### Layout Grid (Parent/Teacher Dashboard)

| Breakpoint | Width | Columns | Gutter | Margin | Context |
|-----------|-------|---------|--------|--------|---------|
| **Mobile** | 320–599px | 4 | 16px | 16px | iPhone (primary parent device) |
| **Tablet** | 600–1023px | 8 | 20px | 24px | iPad |
| **Desktop** | 1024–1439px | 12 | 24px | 32px | Laptop (primary teacher device) |
| **Wide** | 1440px+ | 12 | 24px | Max 1280px centered | Large monitor |

**Parent dashboard primary viewport:** Mobile (320–599px). Mobile-first design.
**Teacher dashboard primary viewport:** Desktop (1024–1439px). Desktop-first design.

#### Student Question Screen Layout

The question screen is the most-viewed screen in the app. Its layout is intentionally constrained:

```
┌──────────────────────────────────────────────┐
│  [← Back]          Progress Dots         [⚙] │  ← Nav bar: 56px height
├──────────────────────────────────────────────┤
│                                              │
│                 QUESTION AREA                 │  ← Max width: 640px
│              (centered on screen)             │     Centered vertically
│                                              │     Minimum: space-8 (40px)
│  ┌──────────────────────────────────────┐    │     from nav and input area
│  │  Question text (18px, max 600px)     │    │
│  │                                      │    │
│  │  Visual / Manipulative area          │    │
│  │  (if applicable, max 480px × 320px)  │    │
│  │                                      │    │
│  └──────────────────────────────────────┘    │
│                                              │
├──────────────────────────────────────────────┤
│                                              │
│              ANSWER INPUT AREA               │  ← Fixed to bottom third
│        (MCQ buttons / number pad /            │     of screen
│         fraction builder / drag zone)         │     Padding: space-6 (24px)
│                                              │
│          ┌──────────────────────┐            │
│          │   [Check Answer]     │            │  ← Primary CTA: full width
│          └──────────────────────┘            │     within content area
│                                              │
└──────────────────────────────────────────────┘
```

---

### 4.4 Elevation & Shadows

Elevation creates hierarchy between surfaces. PADI.AI uses a restrained elevation system — most content sits on a flat surface with subtle shadow separation.

| Token | Shadow Value | Usage |
|-------|-------------|-------|
| `elevation-0` | none | Flat surfaces, inline content |
| `elevation-1` | `0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)` | Cards at rest, skill map nodes |
| `elevation-2` | `0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)` | Cards on hover, dropdown menus |
| `elevation-3` | `0 10px 15px rgba(0,0,0,0.07), 0 4px 6px rgba(0,0,0,0.05)` | Modals, floating panels |
| `elevation-4` | `0 20px 25px rgba(0,0,0,0.08), 0 10px 10px rgba(0,0,0,0.04)` | Tooltips, popovers |

**Dark mode shadows:** Replace `rgba(0,0,0,...)` with `rgba(0,0,0,0.3–0.5)` for more pronounced separation on dark backgrounds.

**Rule:** Student-facing screens use `elevation-0` and `elevation-1` only. The question screen is intentionally flat — no card shadows compete with the math content.

---

### 4.5 Border Radii

| Token | Value | Usage |
|-------|-------|-------|
| `radius-none` | 0px | Table cells, sharp edges |
| `radius-sm` | 4px | Small inputs, tags, chips |
| `radius-md` | 8px | Cards, buttons, input fields |
| `radius-lg` | 12px | Modal dialogs, large cards |
| `radius-xl` | 16px | Featured content, hero cards |
| `radius-2xl` | 24px | Pill shapes (streak badge, avatar border) |
| `radius-full` | 9999px | Circles (avatars, dot indicators, FAB) |

**Student app default:** `radius-md` (8px) for cards and buttons. Rounded enough to feel friendly; not so rounded it looks like a children's toy.

**Dashboard default:** `radius-md` (8px) for cards. Standard professional appearance.

---

### 4.6 Motion & Animation

#### Design Rationale

Motion in PADI.AI serves three functions:
1. **Feedback** — Confirming an action happened (button press, answer submission)
2. **Continuity** — Connecting states (question → answer → next question) to reduce cognitive disorientation
3. **Celebration** — Rewarding achievement (skill mastery, streak milestones)

Motion must NEVER be decorative. Every animation answers "what did the user just do?" or "what just changed?" Decorative animations increase extraneous cognitive load and impair recall, particularly for students with ADHD or cognitive processing differences.

#### Duration Tokens

| Token | Duration | Easing | Usage |
|-------|----------|--------|-------|
| `duration-instant` | 100ms | `ease-out` | Micro-interactions: toggle, checkbox, hover color |
| `duration-fast` | 200ms | `ease-out` | Button press feedback, input focus ring, icon swap |
| `duration-normal` | 300ms | `ease-in-out` | Card transitions, answer feedback (shake/glow), page element enter |
| `duration-slow` | 500ms | `ease-in-out` | Screen transitions, modal enter/exit, progress bar fill |
| `duration-celebration` | 800ms | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Confetti, badge earned, skill mastered — the "bounce" easing creates excitement |
| `duration-manipulative` | 400ms | `ease-out` | Drag-snap for manipulatives, number line jump, fraction bar fill |

#### Easing Functions

| Token | CSS Value | Feel |
|-------|-----------|------|
| `ease-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | Standard Material easing — natural, expected |
| `ease-enter` | `cubic-bezier(0, 0, 0.2, 1)` | Elements entering the screen — decelerating |
| `ease-exit` | `cubic-bezier(0.4, 0, 1, 1)` | Elements leaving the screen — accelerating |
| `ease-bounce` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Celebration moments — playful overshoot |
| `ease-spring` | `cubic-bezier(0.175, 0.885, 0.32, 1.275)` | Manipulative snap-to-grid — satisfying precision |

#### Animation Specifications

| Animation | Trigger | Duration | Properties | Notes |
|-----------|---------|----------|------------|-------|
| **Button press** | `onPointerDown` | `duration-fast` | `scale: 1 → 0.96 → 1` | Subtle depth feel without layout shift |
| **Correct answer** | Answer validated as correct | `duration-normal` | Input border → `green-500`, ✓ icon fades in, background → `green-100` | Followed by 800ms pause then auto-advance |
| **Incorrect answer** | Answer validated as incorrect | `duration-normal` | Input field `translateX: 0 → -6px → 6px → -4px → 4px → 0` (gentle shake) | NO red color, NO failure sound |
| **Question transition** | After answer feedback | `duration-slow` | Current question `opacity: 1→0, translateY: 0→-20px`; new question `opacity: 0→1, translateY: 20px→0` | Staggered: old out 200ms, new in 300ms after 100ms delay |
| **Progress dot fill** | Question completed | `duration-slow` | Dot `scale: 0→1.2→1`, `fill: transparent → teal-600` | Bounce easing for micro-celebration |
| **Skill mastered** | BKT P(mastery) ≥ 0.90 | `duration-celebration` | Confetti particles (20–30), badge scale-up with bounce, skill map node glow | Full-screen overlay for 1.5s |
| **Streak counter** | 3+ correct in a row | `duration-normal` | Counter `scale: 1→1.15→1`, warm glow behind | Only on reaching 3; subsequent correct answers update counter without animation |
| **Hint appear** | After 10s idle or student request | `duration-slow` | Slide up from bottom, `opacity: 0→1` | Gentle pulse on hint icon beforehand (3 pulses, 500ms each) |
| **Manipulative drag** | `onDrag` | Real-time | Follow pointer with 1-frame lag; snap to grid on release (`duration-manipulative` with `ease-spring`) | Haptic feedback on snap (if supported) |
| **Dashboard card enter** | Page load | `duration-slow` per card | `opacity: 0→1, translateY: 16px→0` | Stagger 50ms per card for cascade effect |
| **Progress bar fill** | Data loaded | `duration-slow` | `width: 0% → X%`, eased | Count-up animation for the number label (600ms) |

#### Reduced Motion

All animations MUST respect `prefers-reduced-motion: reduce`:
- **Replace** all transforms with instant opacity changes
- **Remove** celebration confetti — replace with a static badge appearance
- **Remove** shake animation — replace with border color change to `amber-500`
- **Keep** progress bar fills but make them instant (no duration)
- **Keep** screen transitions but reduce to simple crossfade

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 5. Iconography & Illustration

### 5.1 Icon System

**Icon library:** [Phosphor Icons](https://phosphoricons.com/) — open source, consistent weight system, comprehensive math/education coverage.

**Why Phosphor:**
- 6 weight variants (thin, light, regular, bold, fill, duotone) from a single icon set — ensures visual consistency
- Includes math-relevant icons: calculator, number-circle, chart-line, star, trophy, lightning, brain, book
- Clean, modern aesthetic that doesn't read as "childish" or "corporate"
- MIT license, React component library available

| Context | Weight | Size | Usage |
|---------|--------|------|-------|
| Student navigation | Bold | 24px | Nav bar icons, primary actions |
| Student inline | Regular | 20px | Within text, labels, hints |
| Dashboard navigation | Regular | 20px | Sidebar nav, tabs |
| Dashboard inline | Light | 16px | Table cells, metadata |
| Buttons (with text) | Bold | 20px | Left of button label |
| Buttons (icon-only) | Bold | 24px | Minimum 48×48 touch target |

### 5.2 Illustration Style

PADI.AI does NOT use mascots, cartoon characters, or decorative illustrations. Visual identity comes from:

1. **Data visualization** — Skill maps, progress charts, and proficiency heatmaps are the primary visual elements
2. **Math manipulatives** — Fraction bars, number lines, base-ten blocks, and area models are the "illustrations" — they are functional, not decorative
3. **Iconography** — Phosphor icons provide visual interest without adding cognitive load
4. **Avatar system** — Students select from 6 abstract geometric avatars (not cartoon characters). These are identity markers, not mascots.

#### Avatar Specifications

| Property | Value |
|----------|-------|
| Shape | Geometric (circle, rounded square, hexagon variants) |
| Colors | Each avatar uses 2 colors from the teal and warm palettes |
| Size: Student app | 48px (nav), 80px (profile), 120px (selection screen) |
| Size: Parent dashboard | 32px (list), 48px (header) |
| Style | Flat, no gradient, no face, no body — abstract identity symbol |
| Count | 6 options (expandable to 12 in later stages) |
| Customization | Color pair swappable (from preset pairs, not free-form) |

---

## 6. Component Library — Atomic Design

### 6.1 Atoms

#### Button

| Variant | Background | Text | Border | Height | Min Width | Radius | Usage |
|---------|-----------|------|--------|--------|-----------|--------|-------|
| **Primary** | `teal-600` | `neutral-0` | none | 48px (student) / 40px (dashboard) | 120px | `radius-md` | Main CTA: "Check Answer", "Start", "Continue" |
| **Primary (disabled)** | `neutral-300` | `neutral-500` | none | 48px / 40px | 120px | `radius-md` | Disabled state |
| **Secondary** | `neutral-0` | `teal-600` | 1px `teal-600` | 48px / 40px | 120px | `radius-md` | Alternative actions: "Skip", "See Hint" |
| **Ghost** | transparent | `teal-600` | none | 48px / 40px | — | `radius-md` | Low-emphasis: "Cancel", "Back" |
| **Danger** | `red-500` | `neutral-0` | none | 40px | 120px | `radius-md` | Destructive (dashboard only): "Delete Account" |
| **Icon-only** | varies | varies | varies | 48px × 48px | — | `radius-full` | Nav icons, close buttons |

**Student button specifics:**
- Height: 48px minimum (matches Apple's 44pt recommendation + padding)
- Touch target: 48×48px minimum (exceeds WCAG 2.5.8 requirement of 24×24px CSS pixels)
- Font: `type-label-lg` (14px Inter 600, uppercase tracking +0.02em)
- Padding: `space-4` (16px) horizontal, centered vertical
- Press feedback: `scale(0.96)` for `duration-fast` (200ms)
- Focus ring: 2px `teal-400` offset 2px (keyboard focus only, not on tap)

**States:**
| State | Change | Duration |
|-------|--------|----------|
| Default | — | — |
| Hover | Background lightens 10% | `duration-instant` |
| Active/Pressed | `scale(0.96)` | `duration-fast` |
| Focused (keyboard) | 2px teal ring, 2px offset | `duration-instant` |
| Disabled | `opacity: 0.5`, no pointer events | — |
| Loading | Label replaced by 20px spinner | — |

---

#### Input Field

| Property | Value |
|----------|-------|
| Height | 48px (student) / 40px (dashboard) |
| Border | 1px `neutral-200` (rest), 2px `teal-600` (focused), 2px `green-500` (correct), 2px `amber-500` (hint) |
| Radius | `radius-md` (8px) |
| Background | `neutral-0` (light) / `dark-surface` (dark) |
| Font (student) | `type-math-input` (24px JetBrains Mono 500) for number inputs; `type-body-lg` (18px Inter 400) for text |
| Font (dashboard) | `type-dash-body` (14px Inter 400) |
| Padding | `space-3` (12px) horizontal |
| Label | Above field, `type-body-sm` (14px), `neutral-600` |
| Placeholder | `type-body-lg`, `neutral-400` |
| Error text | Below field, `type-body-sm`, `red-500` (dashboard only — students don't see error text) |

---

#### Progress Indicators

**Progress Dots (Diagnostic/Assessment)**
| Property | Value |
|----------|-------|
| Size | 8px diameter |
| Spacing | 6px between dots |
| Inactive | `neutral-300` fill |
| Active/Current | `teal-600` fill, `scale(1.25)` |
| Completed | `teal-600` fill |
| Total visible | Max 25 dots; if more, show "12 of 25" text instead |

**Progress Ring (Skill Mastery)**
| Property | Value |
|----------|-------|
| Size | 64px diameter (student home), 48px (skill map node), 32px (dashboard) |
| Track | 4px stroke, `neutral-200` |
| Fill | 4px stroke, `teal-600` |
| Center | Percentage or icon |
| Animation | Fill from 0° clockwise, `duration-slow` with `ease-default` |

**Progress Bar (Session/Overall)**
| Property | Value |
|----------|-------|
| Height | 8px (standard), 12px (featured) |
| Track | `neutral-200`, `radius-full` |
| Fill | `teal-600` (gradient: `teal-500` → `teal-600`), `radius-full` |
| Animation | Width from 0% → value%, `duration-slow` |
| Label | Optional; above bar, `type-body-sm` |

---

#### Badge / Tag

| Variant | Background | Text | Border | Radius | Usage |
|---------|-----------|------|--------|--------|-------|
| **Skill mastered** | `teal-100` | `teal-700` | none | `radius-sm` | Mastered skill label |
| **In progress** | `amber-100` | `amber-700` | none | `radius-sm` | Working-on skill label |
| **Not started** | `neutral-100` | `neutral-600` | none | `radius-sm` | Future skill label |
| **Prereq gap** | `blue-100` | `blue-600` | 1px `blue-300` dashed | `radius-sm` | Grade 3 prerequisite |
| **Streak** | `warm-100` | `warm-700` | none | `radius-2xl` | Streak counter (pill shape) |
| **Domain** | `neutral-100` | `neutral-700` | 1px `neutral-200` | `radius-sm` | Math domain grouping |

Size: Height 24px (student), 20px (dashboard). Font: `type-label-sm` (12px Inter 500). Padding: `space-1` (4px) vertical, `space-2` (8px) horizontal.

---

### 6.2 Molecules

#### Question Card

The question card is the most important molecule in the system. It contains the math problem, any associated visuals, and the answer input area.

```
┌────────────────────────────────────────────────┐
│                                                  │
│  Question text (type-body-lg, 18px)              │  ← Max 2 lines; if longer,
│  "What fraction of this shape is shaded?"        │     reduce to fit with
│                                                  │     line clamping
│  ┌────────────────────────────────────┐          │
│  │                                    │          │  ← Visual area:
│  │     [Visual Manipulative]          │          │     Max 480 × 320px
│  │     (fraction bar, number line,    │          │     Centered
│  │      area model, etc.)             │          │     Responsive within
│  │                                    │          │     container
│  └────────────────────────────────────┘          │
│                                                  │
│  ┌────────────────────────────────────┐          │
│  │     [Answer Input]                 │          │  ← Type varies:
│  │     (MCQ grid / number pad /       │          │     see Section 7
│  │      fraction builder / drag zone) │          │     for math-specific
│  │                                    │          │     inputs
│  └────────────────────────────────────┘          │
│                                                  │
│  ┌────────────────────────────────────┐          │
│  │         [Check Answer]             │          │  ← Primary button
│  └────────────────────────────────────┘          │     Full width within
│                                                  │     content column
└────────────────────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Max content width | 640px |
| Background | `color-bg-primary` (no card — content sits directly on page) |
| Question text | `type-body-lg` (18px), `color-text-primary` |
| Visual area | Max 480×320px, centered, responsive |
| Answer area | Determined by question type (see Section 7) |
| Button | Primary, full width within content column |
| Vertical spacing | `space-7` (32px) between question text, visual, input, button |

---

#### KPI Card (Dashboard)

```
┌──────────────────────────────────┐
│  [icon]  Label (type-dash-label) │  ← 12px, neutral-500
│                                  │
│  Value (type-dash-kpi)           │  ← 36px, DM Sans 700
│                                  │     teal-700 or neutral-800
│  Delta: ↑ +2 this week          │  ← 12px, green-500 (up)
│                                  │     or neutral-500 (flat)
│  [Optional sparkline]            │  ← 32px height, teal-400
│                                  │
└──────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Width | Flexible; typically 1/3 of container on desktop, full on mobile |
| Padding | `space-5` (20px) |
| Background | `color-bg-surface` |
| Border | 1px `color-border-default` |
| Radius | `radius-lg` (12px) |
| Elevation | `elevation-1` |
| Icon | Phosphor Regular 20px, `teal-600` |
| Value animation | Count-up from 0, `600ms` duration, on first render |

---

#### Skill Map Node

The skill map is a grid of interconnected nodes representing the 29 Grade 4 standards (plus up to 9 Grade 3 prerequisites). Each node is a molecule.

```
┌───────────────────────────┐
│  ┌─────┐                  │
│  │ 72% │  Standard name   │  ← Progress ring + label
│  └─────┘  (type-body-sm)  │
│           "Fractions on    │  ← Max 2 lines
│            a Number Line"  │
│                            │
│  [Mastered] or [In Progress│  ← Badge variant
│   ] or [Not Started]      │
│                            │
└───────────────────────────┘
  ↓ (connecting line to dependent standards)
```

| Property | Value |
|----------|-------|
| Size | 120 × 100px (student), 80 × 64px (dashboard compact) |
| Background | `color-bg-surface` |
| Border | 2px solid, color varies by status (teal/amber/gray/blue dashed) |
| Radius | `radius-lg` (12px) |
| Elevation | `elevation-1` (rest), `elevation-2` (hover) |
| Progress ring | 48px (student), 32px (dashboard) |
| Connection lines | 1px `neutral-300`, straight or elbow connectors |
| Tap/click | Expands to detail panel |

**Skill Map Layout:**
- Grid arrangement: 5 columns (one per math domain), rows by dependency depth
- Domains: Operations & Algebraic Thinking, Number & Operations in Base Ten, Number & Operations — Fractions, Measurement & Data, Geometry
- Connection lines show prerequisite dependencies
- Grade 3 prerequisites are displayed below/beside their dependent Grade 4 standard with a dashed border

---

#### MCQ Answer Grid

For multiple-choice questions, answers are presented in a 2×2 grid (4 options) or vertical list (2–3 options).

```
┌─── 2×2 Grid (4 options) ───────────────────┐
│                                              │
│  ┌───────────────┐  ┌───────────────┐       │
│  │               │  │               │       │
│  │   Option A    │  │   Option B    │       │
│  │   (text/img)  │  │   (text/img)  │       │
│  │               │  │               │       │
│  └───────────────┘  └───────────────┘       │
│                                              │
│  ┌───────────────┐  ┌───────────────┐       │
│  │               │  │               │       │
│  │   Option C    │  │   Option D    │       │
│  │   (text/img)  │  │   (text/img)  │       │
│  │               │  │               │       │
│  └───────────────┘  └───────────────┘       │
│                                              │
└──────────────────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Option card size | Minimum 140 × 64px; grows with content |
| Gap | `space-3` (12px) |
| Border | 2px `neutral-200` (rest), 2px `teal-600` (selected), 2px `green-500` (correct) |
| Radius | `radius-md` (8px) |
| Background | `neutral-0` (rest), `teal-50` (selected), `green-100` (correct) |
| Font | `type-body-lg` (18px) for text options; `type-math-inline` (18px JetBrains Mono) for numeric |
| Touch target | Entire card is tappable — minimum 140 × 64px |
| Selection feedback | Border color change + background fill, `duration-fast` |
| Correct feedback | Border → `green-500`, background → `green-100`, ✓ icon appears top-right |
| Incorrect feedback | Card shakes (`duration-normal`), border returns to `neutral-200` |

---

#### Navigation Bar (Student)

```
┌──────────────────────────────────────────────────┐
│                                                    │
│  [← Back]     [Progress Dots]     [Settings ⚙]   │
│                                                    │
│  Height: 56px                                      │
│  Background: color-bg-primary                      │
│  Border-bottom: 1px color-border-default           │
│                                                    │
└──────────────────────────────────────────────────┘
```

For the student home screen, a bottom navigation bar with 3–4 tabs:

```
┌──────────────────────────────────────────────────┐
│  SCREEN CONTENT                                    │
│                                                    │
│                                                    │
├──────────────────────────────────────────────────┤
│                                                    │
│  [🏠 Home]   [🗺 Skill Map]   [🏆 Badges]   [👤]  │
│                                                    │
│  Height: 64px (accounts for bottom safe area)      │
│  Active: teal-600 icon + label                     │
│  Inactive: neutral-400 icon + label                │
│  Background: color-bg-surface                      │
│  Border-top: 1px color-border-default              │
│                                                    │
└──────────────────────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Tab count | 3–4 (Home, Skill Map, Badges, Profile) |
| Icon size | 24px (Phosphor Bold) |
| Label | `type-label-sm` (12px), below icon |
| Active color | `teal-600` (icon + label) |
| Inactive color | `neutral-400` |
| Touch target | Each tab fills equal width, minimum 48px height |
| Safe area padding | Bottom padding accounts for iOS home indicator (34px) |

---

### 6.3 Organisms

#### Student Home Screen

```
┌──────────────────────────────────────────────────┐
│  [Avatar 48px]   Good morning, Jayden!    [⚙]   │  ← Header
├──────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────────────────────────────┐    │
│  │  Current Skill Card                       │    │  ← Featured card
│  │  ┌────────┐                               │    │     elevation-1
│  │  │Progress│  "Fractions on a Number Line" │    │     radius-lg
│  │  │  Ring  │   Domain: Number & Ops—Fract  │    │
│  │  │  68%   │   3 sessions completed         │    │
│  │  └────────┘                               │    │
│  │                                            │    │
│  │  [Continue Practice] ← Primary CTA         │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
│  ┌─ Streak Banner ──────────────────────────┐    │  ← warm-50 bg
│  │  🔥 7-day streak! Keep it going!          │    │     radius-md
│  └──────────────────────────────────────────┘    │
│                                                    │
│  ┌─ Recent Activity ────────────────────────┐    │
│  │  Yesterday: 12 questions, 83% accuracy    │    │
│  │  Tuesday:   8 questions,  75% accuracy    │    │
│  │  Monday:    15 questions, 90% accuracy    │    │
│  └──────────────────────────────────────────┘    │
│                                                    │
├──────────────────────────────────────────────────┤
│  [🏠 Home]   [🗺 Map]   [🏆 Badges]   [👤 Me]   │  ← Bottom nav
└──────────────────────────────────────────────────┘
```

---

#### Proficiency Heatmap (Teacher Dashboard)

The heatmap is the centerpiece of the teacher experience. It must render efficiently with 26 students × 29 standards = 754 cells.

```
                    ┌─ Standards (columns, grouped by domain) ─┐
                    │ OA  │  NBT  │  NF   │  MD   │  G  │
┌───────────┬───────┼─────┼───────┼───────┼───────┼─────┤
│ Students  │ Avg % │ 1 2 │ 1 2 3 │ 1 2 3 │ 1 2 3 │ 1 2 │
├───────────┼───────┼─────┼───────┼───────┼───────┼─────┤
│ Emma T.   │  72%  │ ■ ■ │ ■ ◐ ◐ │ ◐ □ □ │ ■ ■ ◐ │ ■ ◐ │
│ Jayden K. │  58%  │ ■ ◐ │ ◐ □ □ │ □ □ □ │ ■ ◐ ◐ │ ◐ □ │
│ Sofia R.  │  84%  │ ■ ■ │ ■ ■ ◐ │ ■ ◐ ◐ │ ■ ■ ■ │ ■ ■ │
│ ...       │       │     │       │       │       │     │
└───────────┴───────┴─────┴───────┴───────┴───────┴─────┘

Legend: ■ Mastered  ◐ In Progress  □ Not Started  ◇ Prereq Gap
```

| Property | Value |
|----------|-------|
| Cell size | 24 × 24px |
| Cell gap | 2px |
| Cell radius | `radius-sm` (4px) |
| Cell colors | Mastered: `teal-600`; In Progress: `amber-500`; Not Started: `neutral-300`; Prereq Gap: `blue-500` with dashed border |
| Row height | 32px (cell + padding) |
| Column header | Rotated 45°, `type-dash-label` (12px) |
| Row header (student name) | `type-dash-body` (14px), truncated at 120px |
| Sticky header | Column headers stick on vertical scroll |
| Sticky first column | Student names stick on horizontal scroll |
| Hover | Cell expands to tooltip showing standard name + P(mastery) % |
| Click | Opens detail panel for that student × standard combination |

---

#### Feedback Overlay

When a student answers a question, a brief feedback overlay appears before transitioning to the next question.

**Correct Answer:**
```
┌──────────────────────────────────────────────┐
│                                                │
│           ✓  (48px, teal-600, animated)       │
│                                                │
│        "Nice work!"                            │
│        (type-display-sm, 20px, teal-700)      │
│                                                │
│  [auto-advance in 800ms]                       │
│                                                │
└──────────────────────────────────────────────┘
```

**Incorrect Answer:**
```
┌──────────────────────────────────────────────┐
│                                                │
│  Feedback text:                                │
│  "Almost! Check the denominator."              │
│  (type-body-lg, 18px, neutral-700)            │
│                                                │
│  [auto-advance in 1200ms]                      │
│  or [Try Again] if attempts remain             │
│                                                │
└──────────────────────────────────────────────┘
```

| Property | Correct | Incorrect |
|----------|---------|-----------|
| Background | `green-100` → 10% opacity overlay | No background change |
| Icon | ✓ checkmark, `green-500`, scale-up animation | None (no X icon ever) |
| Border | Input border flashes `green-500` | Input shakes + border `amber-500` |
| Text | Randomized from 8 encouragements: "Nice work!", "Got it!", "Exactly right!", "You know this!", "Spot on!", "Nailed it!", "That's it!", "Perfect!" | Specific to error type: "Check the denominator", "Count the parts again", "Remember: numerator goes on top" |
| Duration | 800ms total, then auto-advance | 1200ms total, then advance or retry |
| Sound | Soft "ding" (optional; respects system mute) | No sound |

---

### 6.4 Templates

Templates are full page layouts composed of organisms.

#### Template: Question Screen (Student)

| Zone | Content | Dimensions |
|------|---------|------------|
| Nav bar | Back button + progress dots + settings | 100% × 56px, fixed top |
| Content area | Question card (text + visual + input) | Max 640px centered, flex-grow |
| CTA area | Check Answer button | Max 640px centered, fixed bottom with `space-6` padding |

#### Template: Student Home

| Zone | Content | Dimensions |
|------|---------|------------|
| Header | Avatar + greeting + settings | 100% × 64px |
| Feature card | Current skill with progress ring + CTA | Full width, ~180px height |
| Streak banner | Streak counter and message | Full width, 48px |
| Activity feed | Recent session summaries | Full width, scrollable |
| Bottom nav | Home / Skill Map / Badges / Profile | 100% × 64px, fixed bottom |

#### Template: Parent Dashboard

| Zone | Content | Dimensions |
|------|---------|------------|
| Header | Child name/avatar + overall progress | 100% × 80px |
| KPI row | 3 KPI cards | 3-col grid (desktop), vertical stack (mobile) |
| Skill map | Interactive 29-standard grid | Full width, ~400px height |
| Activity chart | Weekly bar chart | Full width, 200px height |
| Settings link | Bottom of page | Full width |

#### Template: Teacher Dashboard

| Zone | Content | Dimensions |
|------|---------|------------|
| Sidebar | Class selector, nav links | 240px fixed left (desktop), drawer (mobile) |
| Header | Class name + summary stats | 100% × 64px |
| Heatmap | Proficiency heatmap (students × standards) | Full width, scrollable both axes |
| Gap analysis | Top 5 common gaps bar chart | Full width, 200px height |
| Engagement | Session metrics | Full width, 200px height |
| Actions | Export, invite parents, generate report | Toolbar at top or bottom |

---

## 7. Math-Specific UI Patterns

### 7.1 Number Pad

Custom on-screen number pad for numeric answer entry. Replaces the system keyboard to provide a controlled, math-optimized input experience.

```
┌───────────────────────────────────────┐
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  [Answer display: 24px mono]    │   │  ← Input display
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────┐  ┌─────┐  ┌─────┐           │
│  │  7  │  │  8  │  │  9  │           │  ← Number keys
│  └─────┘  └─────┘  └─────┘           │     48 × 48px each
│  ┌─────┐  ┌─────┐  ┌─────┐           │     12px gap
│  │  4  │  │  5  │  │  6  │           │
│  └─────┘  └─────┘  └─────┘           │
│  ┌─────┐  ┌─────┐  ┌─────┐           │
│  │  1  │  │  2  │  │  3  │           │
│  └─────┘  └─────┘  └─────┘           │
│  ┌─────┐  ┌─────┐  ┌─────┐           │
│  │  0  │  │  .  │  │  ⌫  │           │  ← Decimal + backspace
│  └─────┘  └─────┘  └─────┘           │
│                                         │
└───────────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Key size | 48 × 48px minimum (56 × 48px preferred for comfortable tapping) |
| Key gap | `space-3` (12px) |
| Key background | `neutral-100` (rest), `neutral-200` (pressed) |
| Key text | `type-math-input` (24px JetBrains Mono 500), `neutral-800` |
| Key radius | `radius-md` (8px) |
| Key press feedback | Background darken + `scale(0.96)`, `duration-instant` |
| Display field | 48px height, `type-math-input`, right-aligned, `neutral-0` background |
| Backspace icon | Phosphor `Backspace` Bold 24px |
| Optional keys | `−` (negative), `/` (division), shown contextually per question type |
| Layout | 4 rows × 3 columns, centered in answer area |

---

### 7.2 Fraction Builder

Interactive component for entering or constructing fractions. Used for all fraction-related questions.

```
┌───────────────────────────────────────────┐
│                                             │
│            ┌───────────┐                   │
│            │     3     │ ← Numerator       │
│            │  (tappable)│   input field     │
│            └───────────┘                   │
│         ─────────────────  ← Fraction bar  │
│            ┌───────────┐    (vinculum)     │
│            │     4     │ ← Denominator     │
│            │  (tappable)│   input field     │
│            └───────────┘                   │
│                                             │
│       [Number pad appears below when       │
│        a field is tapped/focused]          │
│                                             │
└───────────────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Numerator field | 64 × 48px, centered, `type-math-display` (28px), `color-text-primary` |
| Denominator field | 64 × 48px, centered, `type-math-display` (28px), `color-text-primary` |
| Fraction bar (vinculum) | 80px width, 2px height, `neutral-700` |
| Active field | 2px `teal-600` border; inactive field: 1px `neutral-300` border |
| Field background | `neutral-0` (light), `dark-surface` (dark) |
| Field radius | `radius-sm` (4px) |
| Tab order | Numerator first → Denominator → Check Answer |
| Mixed number support | Optional whole-number field to the left of the fraction, same style |
| Animation | On correct: both fields + bar flash `green-500` border, `duration-normal` |

#### Mixed Number Variant

```
┌──────┐   ┌───────────┐
│  2   │   │     3     │
│      │   └───────────┘
│(whole)│  ─────────────
│      │   ┌───────────┐
│      │   │     4     │
└──────┘   └───────────┘
```

---

### 7.3 Number Line

Interactive number line for ordering, comparing, and placing fractions and whole numbers.

```
┌────────────────────────────────────────────────────┐
│                                                      │
│  0         ¼         ½         ¾         1          │
│  ├─────────┼─────────┼─────────┼─────────┤          │
│                 ▲                                     │
│                 │                                     │
│            [Draggable                                │
│             marker]                                  │
│                                                      │
│  Instructions: "Place 2/8 on the number line"       │
│                                                      │
└────────────────────────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Line width | Full content width (max 560px), 2px height, `neutral-600` |
| Tick marks | Major: 16px height, 2px width, `neutral-600`; Minor: 8px height, 1px width, `neutral-400` |
| Labels | Below ticks, `type-body-sm` (14px), `neutral-600` |
| Draggable marker | 24px diameter circle, `teal-600` fill, `elevation-2` when dragging |
| Drag behavior | Horizontal only; snaps to nearest valid position with `ease-spring` |
| Snap zones | Based on denominator of the question (e.g., eighths = 8 snap points between whole numbers) |
| Correct feedback | Marker pulses `green-500`, snaps to exact position |
| Incorrect feedback | Marker returns to start position with `duration-normal` |
| Zoom | Pinch-to-zoom supported on touch devices (up to 4× zoom for detailed fractions) |
| Accessibility | Arrow keys move marker by one snap unit; screen reader announces position |

---

### 7.4 Visual Manipulatives

#### Fraction Bar (Area Model)

```
┌──────────────────────────────────────────┐
│  ┌────┬────┬────┬────┬────┬────┬────┬────┐│
│  │████│████│████│    │    │    │    │    ││  ← 3 of 8 parts shaded
│  │████│████│████│    │    │    │    │    ││     teal-400 fill
│  └────┴────┴────┴────┴────┴────┴────┴────┘│     neutral-100 empty
│                                            │
│  "3/8 of the bar is shaded"               │
└──────────────────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Bar width | Max 480px, responsive |
| Bar height | 48px (student) |
| Partition border | 1px `neutral-300` |
| Shaded fill | `teal-400` (interactive: student can tap to shade/unshade) |
| Empty fill | `neutral-100` |
| Outer border | 2px `neutral-600`, `radius-sm` |
| Interaction | Tap a segment to toggle shaded/unshaded; drag to shade multiple |
| Label | Below bar, auto-updates: "[n]/[d] shaded" in `type-body-sm` |

#### Base-Ten Blocks

For place value and multi-digit operations:

| Block | Visual | Size | Color |
|-------|--------|------|-------|
| Ones (unit cube) | Single small square | 16 × 16px | `teal-300` |
| Tens (rod) | Vertical rectangle = 10 unit cubes | 16 × 160px | `teal-400` |
| Hundreds (flat) | 10 × 10 grid of unit cubes | 160 × 160px | `teal-500` |

- Blocks are draggable
- Snap to grid when placed in a work area
- Can be grouped (drag 10 ones together → automatically merge to 1 ten rod, with animation)
- Breaking apart: tap a ten rod → it splits into 10 ones with `duration-manipulative` animation

#### Circle Model (Fractions)

- Full circle divided into equal sectors
- Tap a sector to shade it
- Denominator set by question (2, 3, 4, 5, 6, 8, 10, 12)
- Shaded sectors: `teal-400`; unshaded: `neutral-100`
- Outline: 2px `neutral-600`
- Size: 200 × 200px (student), 120 × 120px (dashboard)

---

### 7.5 Equation Rendering (KaTeX)

PADI.AI uses KaTeX for all rendered mathematical expressions. KaTeX produces high-quality TeX-based typesetting that renders synchronously without page reflow.

#### KaTeX Configuration

```javascript
katex.render(expression, element, {
  displayMode: true,          // Block-level rendering
  throwOnError: false,        // Graceful fallback
  errorColor: '#E03131',      // red-500 for render errors
  minRuleThickness: 0.06,     // Thicker fraction bars for visibility
  strict: false,              // Lenient parsing
  trust: false,               // No HTML injection
  macros: {
    '\\placeholder': '\\boxed{\\phantom{00}}',  // Answer placeholder
  }
});
```

#### Styling Overrides for Student Context

| Property | Default KaTeX | PADI.AI Override | Rationale |
|----------|--------------|-------------------|-----------|
| Font size | 1em (inherits) | 1.5em (`type-math-display` = 28px for block, 18px for inline) | Larger for young readers |
| Color | black | `color-text-primary` | Respects dark mode |
| Fraction bar thickness | 0.04em | 0.06em | More visible for developing eyes |
| Delimiter size | auto | `\left` and `\right` forced at 1.2× | Clearer grouping |
| Placeholder boxes | N/A | `\boxed{\phantom{00}}` renders as teal-outlined empty box | Answer target |

---

### 7.6 Drag-and-Drop Interactions

Used for ordering, sorting, and matching exercises.

| Property | Value |
|----------|-------|
| Draggable item | Card with `elevation-1` at rest; `elevation-3` when grabbed |
| Grab animation | `scale(1.05)` + `elevation-3`, `duration-fast` |
| Drop zone | Dashed 2px `teal-300` border when active; solid `teal-600` when valid target |
| Drop animation | Item snaps to center of zone, `duration-manipulative` with `ease-spring` |
| Invalid drop | Item returns to origin, `duration-normal` |
| Reorder | Items in a list; grab handle on left (Phosphor `DotsSixVertical`); other items slide apart to show insertion point |
| Touch tolerance | 20px slop before drag starts (prevents accidental drags) |
| Keyboard alternative | Tab to item → Space to grab → Arrow keys to move → Space to drop |

---

## 8. Gamification & Feedback System

### 8.1 Design Philosophy

PADI.AI's gamification system is designed around **intrinsic motivation** — the rewards signal real learning progress, not arbitrary achievements. Every gamified element maps to a genuine learning milestone. There are no loot boxes, no premium currency, no variable-ratio reward schedules. The gamification system does NOT use:
- Punitive mechanics (losing points, losing streaks)
- Social comparison (leaderboards, rankings)
- FOMO mechanics (limited-time rewards)
- Dark patterns (pay-to-skip, streak anxiety)

### 8.2 Reward Elements

| Element | Trigger | Visual | Animation | Notes |
|---------|---------|--------|-----------|-------|
| **Correct answer** | Each correct answer | ✓ icon + encouraging text | Scale-up + color flash, `duration-normal` | Randomized encouragement text (8 variants) |
| **Streak counter** | 3+ correct in a row | 🔥 + number, `warm-500` | Counter bounce, background glow | Visible only during active streak; resets quietly (no "streak lost" message) |
| **Skill progress** | After each question | Progress ring fills | Smooth fill animation, `duration-slow` | Always shows forward movement, even on incorrect (BKT still learns from errors) |
| **Skill mastered** | BKT P(mastery) ≥ 0.90 | Full-screen celebration | Confetti (20 particles, 1.5s) + badge reveal + skill map update | The "big moment" — earn it, celebrate it |
| **Daily practice** | Completing a session | Session summary card | Card slides up, stats count up | Shows questions done, accuracy (as dots, not %), skills practiced |
| **Streak milestone** | 7, 14, 30 day streaks | Special streak badge | Badge reveal with `ease-bounce` | Badge persists in badge collection; if streak breaks, badge remains earned |
| **Domain mastered** | All standards in a domain | Domain badge (unique design per domain) | Extended celebration (2.5s) | 5 domain badges total — visible on student profile |

### 8.3 Badge System

5 domain-specific badges + 3 streak badges + 1 diagnostic complete badge = 9 total badges at launch.

| Badge | Name | Visual Description | Trigger |
|-------|------|--------------------|---------|
| 1 | **Explorer** | Compass rose in teal | Complete diagnostic assessment |
| 2 | **Operations Pro** | Calculator icon in teal-600 | Master all OA standards |
| 3 | **Number Champion** | Base-ten block stack in teal-500 | Master all NBT standards |
| 4 | **Fraction Master** | Fraction bar in warm-500 | Master all NF standards |
| 5 | **Data Detective** | Chart-bar icon in teal-400 | Master all MD standards |
| 6 | **Shape Expert** | Hexagon in teal-300 | Master all G standards |
| 7 | **Week Warrior** | 🔥 in warm circle | 7-day streak |
| 8 | **Fortnight Flame** | 🔥🔥 in warm circle | 14-day streak |
| 9 | **Month Master** | 🔥🔥🔥 in warm circle | 30-day streak |

**Badge specifications:**
- Size: 64 × 64px (collection), 48 × 48px (earned popup), 24 × 24px (inline)
- Unearned state: Grayscale silhouette, 40% opacity
- Earned state: Full color, `elevation-1`
- Earn animation: Scale from 0 → 1.2 → 1, rotate 15° → 0°, `duration-celebration` with `ease-bounce`

### 8.4 Growth Mindset Language

All student-facing text follows growth mindset principles. The system never attributes success to innate ability ("You're so smart!") — it attributes success to effort and strategy ("Your practice is paying off!").

| Situation | Do | Don't |
|-----------|----|----|
| Correct answer | "You got it!", "Nice thinking!", "Your practice shows!" | "You're so smart!", "Easy, right?", "Perfect!" (avoid perfection framing) |
| Incorrect answer | "Not quite — let's look at this together", "Almost! Check the denominator" | "Wrong!", "Incorrect!", "Try harder", "That's not right" |
| Streak | "You're on a roll — 5 in a row!", "Consistent effort!" | "You're a genius!", "You never make mistakes!" |
| Skill mastered | "You've mastered this! All that practice paid off." | "You're the best at fractions!" |
| Returning after absence | "Welcome back! Ready to pick up where you left off?" | "You've been gone for 5 days" (guilt), "You lost your streak" (punishment) |
| Struggling (3+ errors) | "This is a tough one. Want a hint?", "Let's try a different approach" | "Keep trying!" (vague), "You can do it!" (without help) |

---

## 9. Accessibility Standards

### 9.1 Compliance Targets

| Standard | Level | Status |
|----------|-------|--------|
| WCAG 2.2 | AA (all criteria) | Required for launch |
| WCAG 2.2 | AAA (1.4.6 Enhanced Contrast, 2.5.5 Target Size) | Targeted — children's apps benefit from exceeding AA |
| Section 508 | Full compliance | Required for school district adoption |
| COPPA | Full compliance | Required — children under 13 |
| FERPA | Full compliance | Required for teacher/school features |

### 9.2 Specific Requirements

#### Visual

| Requirement | Specification | Verification |
|-------------|---------------|-------------|
| Text contrast (body) | ≥4.5:1 against background | Automated: axe-core |
| Text contrast (large text, 18px+) | ≥3:1 against background | Automated: axe-core |
| Non-text contrast (icons, borders) | ≥3:1 against background | Manual check |
| Color independence | No information conveyed by color alone — always paired with icon, text, or pattern | Manual review + automated |
| Focus indicator | 2px solid `teal-400`, 2px offset, on all interactive elements (keyboard focus only) | Keyboard testing |
| Minimum text size | 12px absolute floor; 18px for student-facing body text | Design review |
| Text resizing | Up to 200% zoom without loss of content or functionality | Browser zoom testing |
| Dark mode | Full support; all semantic tokens have dark-mode variants | Theme toggle testing |
| Reduced motion | All animations suppressed when `prefers-reduced-motion: reduce` is set | OS setting + CSS audit |
| High contrast | Windows High Contrast mode supported via `forced-colors` media query | Manual testing |

#### Motor / Touch

| Requirement | Specification | Verification |
|-------------|---------------|-------------|
| Touch target size (student) | ≥48 × 48px (exceeds WCAG 2.5.8 minimum of 24 × 24px and Apple's 44pt guideline) | Design specs + device testing |
| Touch target size (dashboard) | ≥40 × 40px | Design specs + device testing |
| Touch target spacing | ≥8px between adjacent targets | Layout review |
| Drag alternatives | All drag-and-drop has keyboard alternative (Tab → Space → Arrows → Space) | Keyboard-only testing |
| Gesture alternatives | All swipe/pinch actions have button alternatives | Testing |
| Timeout | No time limits on any student interaction; assessments have no visible timer | Product spec review |

#### Cognitive

| Requirement | Specification | Verification |
|-------------|---------------|-------------|
| Reading level | Student-facing text at 3rd–4th grade reading level (Flesch-Kincaid) | Automated readability check |
| Instructions | ≤15 words per instruction; supported by icon or visual | Content review |
| Cognitive load | 1 task per screen; progressive disclosure for complexity | Design review |
| Error recovery | All errors are recoverable; no dead ends | User testing |
| Consistency | Same interactions work the same way everywhere | Heuristic evaluation |
| Predictability | No unexpected changes; all actions are user-initiated | Heuristic evaluation |

#### Assistive Technology

| Requirement | Specification | Verification |
|-------------|---------------|-------------|
| Screen reader | Full ARIA labels on all interactive elements; math expressions have text alternatives | VoiceOver + NVDA testing |
| KaTeX accessibility | KaTeX renders MathML alongside visual output; `aria-label` on all expressions | Screen reader testing |
| Keyboard navigation | Full tab order through all interactive elements; visible focus ring | Keyboard-only testing |
| Live regions | Answer feedback announced via `aria-live="polite"` | Screen reader testing |
| Headings | Semantic heading hierarchy (h1 → h2 → h3) on all pages | axe-core |
| Alt text | All images, icons, and manipulatives have descriptive alt text | Automated + manual |

### 9.3 Accessibility Testing Cadence

| Test | Tool | Frequency |
|------|------|-----------|
| Automated scan | axe-core (integrated in CI/CD) | Every commit |
| Keyboard navigation | Manual (every page) | Every sprint |
| Screen reader | VoiceOver (macOS/iOS) + NVDA (Windows) | Every release |
| Color contrast | Stark plugin (Figma) + axe-core | Every component update |
| Readability | Hemingway / Flesch-Kincaid on all student-facing text | Every content change |
| User testing | Testing with children (ages 9–10) including children with IEPs | Every major release |

---

## 10. Responsive & Device Strategy

> **Updated April 2026 — Tablet-First Mandate:** The primary student device is an iPad (Safari) or school-issued Chromebook (Chrome). All design and development work uses **768px (iPad portrait) as the primary design breakpoint**, not 1440px desktop. Desktop is a secondary target. This section supersedes any prior desktop-first assumptions.

#### Device Priority Stack

| Priority | Device | Browser | Resolution | Notes |
|---|---|---|---|---|
| **Primary** | iPad (any generation, 2020+) | Safari 17/18 | 768×1024 | Majority of at-home student use |
| **Primary** | Chromebook | Chrome | 1280×800 | Majority of school-issued device use |
| **Secondary** | iPhone (13+) | Safari | 390×844 | Parent access; some student use |
| **Secondary** | Android tablet | Chrome | 800×1280 | Minority student use |
| **Tertiary** | MacBook/Windows laptop | Any modern | 1440×900 | Parent/teacher dashboard primary |
| **Tertiary** | Desktop | Any modern | 1920×1080 | Teacher dashboard secondary |

#### Critical Platform-Specific Requirements

**iPad Safari — Known Issues to Validate at Every Stage Gate:**
1. **KaTeX math rendering**: Test fractions (½, ¾, mixed numbers) at every Stage 1–4 release; Safari has historically had layout bugs with KaTeX inline rendering
2. **Touch targets**: All interactive elements ≥44×44px (Apple HIG requirement, also WCAG 2.1 AA)
3. **Math input fields**: Fraction builder, number input, and multi-digit entry must all be validated on iOS virtual keyboard (no physical keyboard assumption)
4. **Scroll behavior**: Assessment question screens must not have nested scroll containers (iOS Safari scroll rubber-banding breaks nested scrollable areas)
5. **Viewport units**: Avoid `100vh` — use `100dvh` (dynamic viewport height) or `svh` to handle Safari address bar height correctly

**Chromebook Chrome — Known Issues:**
1. **Keyboard navigation**: Chromebooks have physical keyboards; ensure all interactive elements are keyboard-accessible (Tab order, focus rings)
2. **GPU acceleration**: Some Chromebook models have limited GPU; avoid heavy CSS animations in the practice session screen
3. **Touch + keyboard hybrid**: Chromebook touch screens exist; design must work for both input modalities

#### Stage Gate QA Requirement

Every stage gate milestone (Stage 1 through Stage 5) must include a manual QA pass that explicitly verifies:
- [ ] KaTeX renders correctly on iPad Safari 18 (real device or BrowserStack)
- [ ] KaTeX renders correctly on Chromebook Chrome (real device or BrowserStack)
- [ ] All touch targets ≥44×44px (verify with browser accessibility inspector)
- [ ] Math input fields work on iOS virtual keyboard
- [ ] No horizontal scroll on 768px viewport
- [ ] Assessment progress bar renders correctly on small viewport

#### PWA Strategy (Stage 2–3)

Add Progressive Web App support in Stage 2 to provide near-native experience before React Native:

| Feature | Implementation | Stage |
|---|---|---|
| Service Worker | Cache questions for current skill offline | Stage 2 |
| Web App Manifest | Allow home screen install on iOS/Android | Stage 2 |
| Offline indicator | Show "Offline — answers will sync when reconnected" | Stage 3 |
| Background sync | Queue BKT updates for submission when back online | Stage 3 |

PWA eliminates the need for a native app for most use cases. Pursue native React Native with Expo only if: (a) school/district contracts require App Store distribution, or (b) PWA performance on target devices is unacceptable.

### 10.1 Target Devices

| Priority | Device | Screen | Resolution | Context |
|----------|--------|--------|------------|---------|
| P0 | iPad (9th–10th gen) | 10.2" | 2160 × 1620 | Primary student device at home |
| P0 | Chromebook (11.6–14") | 11.6–14" | 1366 × 768 to 1920 × 1080 | Primary student device at school |
| P0 | iPhone (12–15) | 6.1" | 2532 × 1170 | Primary parent device |
| P1 | iPad Air / Pro | 10.9–12.9" | Various | Alternate student device |
| P1 | Desktop browser | 15"+ | 1920 × 1080+ | Primary teacher device |
| P2 | Android tablet | 10" | Various | Secondary student device |
| P2 | Android phone | 6"+ | Various | Secondary parent device |

### 10.2 Orientation Strategy

| Interface | Preferred Orientation | Forced? |
|-----------|----------------------|---------|
| Student: Question screen | Landscape | No, but layout optimized for landscape on tablet |
| Student: Home / badges | Portrait or landscape | Fluid |
| Parent dashboard | Portrait (mobile) | No |
| Teacher dashboard | Landscape (desktop) | No |

### 10.3 Responsive Behavior Summary

| Component | Mobile (≤599px) | Tablet (600–1199px) | Desktop (1200px+) |
|-----------|----------------|--------------------|--------------------|
| Question card | Full-width, stacked | Centered, max 640px | Centered, max 640px |
| Number pad | Full-width, bottom-fixed | Inline below question | Inline below question |
| Skill map | Single column, scrollable | Grid, 3 columns | Grid, 5 columns |
| KPI cards | Vertical stack | 3-column grid | 3-column grid |
| Heatmap | Horizontal scroll | Horizontal scroll | Full visible (with scroll for >20 students) |
| Navigation (student) | Bottom tab bar | Bottom tab bar | Side navigation (optional) |
| Navigation (parent) | Bottom tab bar | Top navigation | Top navigation |
| Navigation (teacher) | Hamburger → drawer | Sidebar (collapsible) | Sidebar (persistent) |

---

## 11. Figma Implementation Guide

### 11.1 File Structure

Organize the Figma project into the following pages:

```
PADI.AI Design System
├── 📄 Cover (project info, version, links)
├── 📄 Foundations
│   ├── Color System (all primitives + semantic tokens)
│   ├── Typography Scale (all type styles)
│   ├── Spacing & Grid (spacing tokens + layout grids)
│   ├── Elevation (shadow styles)
│   ├── Iconography (Phosphor icon set + usage guidelines)
│   └── Motion (animation specs — documented, not animated)
├── 📄 Components
│   ├── Atoms (Buttons, Inputs, Progress indicators, Badges)
│   ├── Molecules (Question Card, KPI Card, Skill Map Node, MCQ Grid, Nav Bar)
│   ├── Organisms (Student Home, Feedback Overlay, Proficiency Heatmap)
│   └── Math Components (Number Pad, Fraction Builder, Number Line, Manipulatives)
├── 📄 Templates
│   ├── Student — Question Screen
│   ├── Student — Home
│   ├── Student — Skill Map
│   ├── Student — Badge Collection
│   ├── Parent — Dashboard
│   ├── Parent — Diagnostic Results
│   ├── Teacher — Class Overview
│   └── Teacher — Student Detail
├── 📄 Workflows
│   ├── Student: First Run / Diagnostic
│   ├── Student: Daily Practice
│   ├── Student: AI Tutoring
│   ├── Parent: Onboarding
│   ├── Parent: Weekly Check-in
│   └── Teacher: Class Review
└── 📄 Prototyping
    ├── Student Flow Prototype (connected screens)
    ├── Parent Flow Prototype
    └── Teacher Flow Prototype
```

### 11.2 Variable Collections Setup

Create three Variable Collections in Figma:

#### Collection 1: Primitives

| Group | Variables |
|-------|-----------|
| `color/teal` | `teal-50` through `teal-900` (10 values) |
| `color/warm` | `warm-50` through `warm-900` (10 values) |
| `color/neutral` | `neutral-0` through `neutral-900` (11 values) |
| `color/green` | `green-100`, `green-500` |
| `color/amber` | `amber-100`, `amber-500` |
| `color/red` | `red-100`, `red-500` |
| `color/blue` | `blue-100`, `blue-500` |
| `color/dark` | `dark-bg`, `dark-surface`, `dark-surface-alt`, `dark-border`, `dark-text`, `dark-text-bright`, `dark-text-muted` |
| `space` | `space-0` through `space-13` (14 values) |
| `radius` | `radius-none` through `radius-full` (8 values) |

#### Collection 2: Semantic (with Light/Dark Modes)

Create two modes in this collection: **Light** and **Dark**.

| Variable | Light Mode Reference | Dark Mode Reference |
|----------|---------------------|---------------------|
| `bg/primary` | `neutral-50` | `dark-bg` |
| `bg/surface` | `neutral-0` | `dark-surface` |
| `bg/surface-alt` | `neutral-100` | `dark-surface-alt` |
| `bg/interactive` | `teal-600` | `teal-500` |
| `bg/interactive-hover` | `teal-700` | `teal-600` |
| `bg/correct` | `green-100` | `#1B3D25` |
| `bg/hint` | `amber-100` | `#3D3419` |
| `text/primary` | `neutral-800` | `dark-text-bright` |
| `text/body` | `neutral-600` | `dark-text` |
| `text/muted` | `neutral-500` | `dark-text-muted` |
| `text/on-interactive` | `neutral-0` | `neutral-0` |
| `text/link` | `teal-600` | `teal-400` |
| `border/default` | `neutral-200` | `dark-border` |
| `border/interactive` | `teal-600` | `teal-500` |
| `accent/primary` | `teal-600` | `teal-400` |
| `accent/warm` | `warm-500` | `warm-400` |

#### Collection 3: Components (Optional — for Scale)

| Variable | Reference |
|----------|-----------|
| `button/primary/bg` | `bg/interactive` |
| `button/primary/text` | `text/on-interactive` |
| `button/primary/hover` | `bg/interactive-hover` |
| `button/secondary/bg` | `bg/surface` |
| `button/secondary/text` | `text/link` |
| `button/secondary/border` | `border/interactive` |
| `input/bg` | `bg/surface` |
| `input/border` | `border/default` |
| `input/border-focus` | `border/interactive` |
| `card/bg` | `bg/surface` |
| `card/border` | `border/default` |
| `skill-node/mastered` | `accent/primary` |
| `skill-node/in-progress` | `amber-500` |
| `skill-node/not-started` | `neutral-300` |

### 11.3 Text Styles

Create Figma Text Styles for each type token:

| Style Name | Font | Size | Line Height | Weight | Tracking |
|-----------|------|------|-------------|--------|----------|
| `Display/Large` | DM Sans | 32px | 40px | Bold (700) | -0.02em |
| `Display/Medium` | DM Sans | 24px | 32px | Bold (700) | -0.01em |
| `Display/Small` | DM Sans | 20px | 28px | Medium (500) | 0 |
| `Body/Large` | Inter | 18px | 28px | Regular (400) | 0 |
| `Body/Medium` | Inter | 16px | 24px | Regular (400) | 0 |
| `Body/Small` | Inter | 14px | 20px | Regular (400) | 0.01em |
| `Label/Large` | Inter | 14px | 20px | SemiBold (600) | 0.02em |
| `Label/Small` | Inter | 12px | 16px | Medium (500) | 0.03em |
| `Math/Display` | JetBrains Mono | 28px | 36px | Regular (400) | 0 |
| `Math/Inline` | JetBrains Mono | 18px | 28px | Regular (400) | 0 |
| `Math/Input` | JetBrains Mono | 24px | 32px | Medium (500) | 0.01em |
| `Number` | Inter | 24px | 32px | SemiBold (600) | 0 |
| `Dashboard/H1` | DM Sans | 28px | 36px | Bold (700) | 0 |
| `Dashboard/H2` | DM Sans | 20px | 28px | SemiBold (600) | 0 |
| `Dashboard/H3` | DM Sans | 16px | 24px | Medium (500) | 0 |
| `Dashboard/Body` | Inter | 14px | 22px | Regular (400) | 0 |
| `Dashboard/Label` | Inter | 12px | 16px | Medium (500) | 0 |
| `Dashboard/KPI` | DM Sans | 36px | 44px | Bold (700) | 0 |
| `Dashboard/Table` | Inter | 13px | 18px | Regular (400) | 0 |

### 11.4 Component Organization

Use Figma's component naming convention with slashes for hierarchy:

```
Button / Primary / Default
Button / Primary / Hover
Button / Primary / Active
Button / Primary / Disabled
Button / Primary / Loading
Button / Secondary / Default
Button / Secondary / Hover
...
Input / Text / Default
Input / Text / Focused
Input / Text / Filled
Input / Text / Error
Input / Number / Default (with number pad)
Input / Fraction / Default (fraction builder)
...
Card / Question / MCQ
Card / Question / Number Input
Card / Question / Fraction Input
Card / Question / Number Line
Card / Question / Drag and Drop
Card / KPI / Default
Card / Skill Node / Mastered
Card / Skill Node / In Progress
Card / Skill Node / Not Started
Card / Skill Node / Prerequisite Gap
...
Nav / Student / Bottom Bar
Nav / Student / Top Bar (question screen)
Nav / Parent / Mobile Bottom
Nav / Parent / Desktop Top
Nav / Teacher / Sidebar
...
Feedback / Correct
Feedback / Incorrect
Feedback / Hint
Feedback / Celebration
...
Math / Number Pad
Math / Fraction Builder
Math / Fraction Builder Mixed
Math / Number Line
Math / Fraction Bar
Math / Base Ten Blocks
Math / Circle Model
```

### 11.5 Auto Layout Conventions

All components should use Figma Auto Layout with these conventions:

| Property | Student Components | Dashboard Components |
|----------|-------------------|---------------------|
| Padding (internal) | `space-4` (16px) or `space-6` (24px) | `space-4` (16px) or `space-5` (20px) |
| Gap (between children) | `space-3` (12px) or `space-4` (16px) | `space-2` (8px) or `space-3` (12px) |
| Alignment | Center for question content; Start for lists | Start for data; Center for KPIs |
| Sizing | Fill container (width), Hug contents (height) | Fill container (both for grids) |

### 11.6 Prototyping Notes

When building interactive prototypes in Figma:

1. **Student diagnostic flow**: Connect 5–6 representative question screens to show the full loop (question → answer → feedback → next question → halfway break → completion)
2. **Answer feedback**: Use Smart Animate between "default" and "correct"/"incorrect" variants of the question card
3. **Celebration**: Use the Figma prototype "overlay" trigger for the confetti/badge celebration
4. **Dark mode**: Duplicate key frames and apply the Dark mode variables collection to demonstrate theme switching
5. **Skill map interaction**: Use overlay prototyping to show tap → detail panel expansion

---

## 12. Appendix: Token Reference Tables

### Complete Color Token Map

| Primitive | Hex | Semantic (Light) | Semantic (Dark) |
|-----------|-----|-------------------|-----------------|
| `teal-50` | `#E6F7F8` | — | — |
| `teal-100` | `#B3E8EB` | Selected option bg | Selected option bg |
| `teal-200` | `#80D9DE` | — | — |
| `teal-300` | `#4DCAD1` | Decorative / illustration | Decorative / illustration |
| `teal-400` | `#26BEC7` | Focus ring, sparklines | `accent/primary` (dark), links (dark) |
| `teal-500` | `#00B2BD` | Brand accent (secondary) | `bg/interactive` (dark), borders (dark) |
| `teal-600` | `#009199` | `bg/interactive`, `accent/primary`, links, mastered | Mastered node, primary hover (dark) |
| `teal-700` | `#007078` | `bg/interactive-hover` | — |
| `teal-800` | `#005258` | Dark brand accent | — |
| `teal-900` | `#00363B` | — | — |
| `warm-50` | `#FFF8F0` | Streak banner bg | — |
| `warm-100` | `#FFE8CC` | Badge bg, warm highlights | — |
| `warm-400` | `#FFA333` | — | `accent/warm` (dark) |
| `warm-500` | `#FF8C00` | `accent/warm`, streak counter | — |
| `neutral-0` | `#FFFFFF` | `bg/surface`, `text/on-interactive` | `text/on-interactive` |
| `neutral-50` | `#F8F9FA` | `bg/primary` | — |
| `neutral-100` | `#F1F3F5` | `bg/surface-alt` | — |
| `neutral-200` | `#E9ECEF` | `border/default` | — |
| `neutral-300` | `#DEE2E6` | Disabled bg, not-started nodes | — |
| `neutral-400` | `#ADB5BD` | Placeholder text, inactive icons | — |
| `neutral-500` | `#868E96` | `text/muted` | — |
| `neutral-600` | `#495057` | `text/body` | — |
| `neutral-700` | `#343A40` | — | — |
| `neutral-800` | `#212529` | `text/primary` | — |
| `neutral-900` | `#141517` | — | — |
| `dark-bg` | `#1A1B1E` | — | `bg/primary` |
| `dark-surface` | `#25262B` | — | `bg/surface` |
| `dark-surface-alt` | `#2C2E33` | — | `bg/surface-alt` |
| `dark-border` | `#373A40` | — | `border/default` |
| `dark-text` | `#C1C2C5` | — | `text/body` |
| `dark-text-bright` | `#E9ECEF` | — | `text/primary` |
| `dark-text-muted` | `#909296` | — | `text/muted` |
| `green-100` | `#D3F9D8` | `bg/correct` | — |
| `green-500` | `#37B24D` | Correct answer indicator | Correct answer indicator |
| `amber-100` | `#FFF3BF` | `bg/hint` | — |
| `amber-500` | `#F59F00` | In-progress indicator | In-progress indicator |
| `red-100` | `#FFE3E3` | System error bg | — |
| `red-500` | `#E03131` | System errors ONLY | System errors ONLY |
| `blue-100` | `#D0EBFF` | Info/prereq bg | — |
| `blue-500` | `#1C7ED6` | Info, prerequisite nodes | Info, prerequisite nodes |

### Complete Spacing Token Map

| Token | Value | Figma Variable Name |
|-------|-------|---------------------|
| `space-0` | 0px | `space/0` |
| `space-1` | 4px | `space/1` |
| `space-2` | 8px | `space/2` |
| `space-3` | 12px | `space/3` |
| `space-4` | 16px | `space/4` |
| `space-5` | 20px | `space/5` |
| `space-6` | 24px | `space/6` |
| `space-7` | 32px | `space/7` |
| `space-8` | 40px | `space/8` |
| `space-9` | 48px | `space/9` |
| `space-10` | 56px | `space/10` |
| `space-11` | 64px | `space/11` |
| `space-12` | 80px | `space/12` |
| `space-13` | 96px | `space/13` |

### Complete Border Radius Token Map

| Token | Value | Figma Variable Name |
|-------|-------|---------------------|
| `radius-none` | 0px | `radius/none` |
| `radius-sm` | 4px | `radius/sm` |
| `radius-md` | 8px | `radius/md` |
| `radius-lg` | 12px | `radius/lg` |
| `radius-xl` | 16px | `radius/xl` |
| `radius-2xl` | 24px | `radius/2xl` |
| `radius-full` | 9999px | `radius/full` |

### Complete Elevation Token Map

| Token | Value | Figma Style Name |
|-------|-------|------------------|
| `elevation-0` | none | `Elevation/0` |
| `elevation-1` | `0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)` | `Elevation/1` |
| `elevation-2` | `0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)` | `Elevation/2` |
| `elevation-3` | `0 10px 15px rgba(0,0,0,0.07), 0 4px 6px rgba(0,0,0,0.05)` | `Elevation/3` |
| `elevation-4` | `0 20px 25px rgba(0,0,0,0.08), 0 10px 10px rgba(0,0,0,0.04)` | `Elevation/4` |

### Complete Duration Token Map

| Token | Value | Easing | Figma Prototype Setting |
|-------|-------|--------|------------------------|
| `duration-instant` | 100ms | ease-out | Smart Animate, 100ms |
| `duration-fast` | 200ms | ease-out | Smart Animate, 200ms |
| `duration-normal` | 300ms | ease-in-out | Smart Animate, 300ms |
| `duration-slow` | 500ms | ease-in-out | Smart Animate, 500ms |
| `duration-celebration` | 800ms | cubic-bezier(0.34,1.56,0.64,1) | Smart Animate, 800ms |
| `duration-manipulative` | 400ms | ease-out | Smart Animate, 400ms |

---

## Research Sources

This design system was informed by research and best practices from the following areas:

- Children's cognitive development and working memory capacity for ages 9–12, including the 3–4 item working memory limit and attention span research
- UX design guidelines for children's apps spanning age-appropriate design patterns, touch target sizing, and motor skill considerations from multiple UX research studios
- Color psychology in educational technology, including the impact of warm vs. cool colors on attention, retention, and emotional state during learning
- Typography best practices for educational digital products, including sans-serif preference, single-storey character forms, and minimum size requirements for developing readers
- Math-specific UI patterns including virtual manipulatives (fraction bars, number lines, base-ten blocks, circle models), KaTeX equation rendering, and concrete-representational-abstract (CRA) pedagogical strategy
- Gamification principles in educational technology, focusing on intrinsic motivation, growth mindset language, and ethical reward design that avoids dark patterns
- WCAG 2.2 accessibility standards for mobile apps, including touch target requirements (SC 2.5.5, 2.5.8), gesture alternatives, cognitive accessibility, and assistive technology support
- Figma design system architecture including three-tier token structures, variable collections with multi-mode support, and the 2025–2026 Figma Variables API
- Parent and teacher dashboard design patterns from EdTech platforms, including KPI cards, progress heatmaps, and actionable data presentation
- Material Design principles for spacing (8dp grid), elevation systems, and cross-platform consistency
- Cognitive load theory as applied to educational interface design, including the role of animation in reducing vs. increasing extraneous cognitive load, and the importance of `prefers-reduced-motion` support

---

*Document version: 1.0 | Created: April 2026 | Authored for PADI.AI project*
*Design system scope: Web application (React 19 / Next.js 15) with responsive tablet-first student interface and mobile-first parent interface*
