# Adaptive Math Learning App for Oregon 4th Graders: Deep Viability Research

## Executive Summary

An adaptive math learning app targeting Oregon 4th graders is a viable and high-impact concept with strong market tailwinds but significant execution complexity. Oregon's 4th graders score 8 points below the national average on NAEP math assessments, with only 31% reaching proficiency — a clear signal of unmet need ([NCES 2024 NAEP Snapshot](https://nces.ed.gov/nationsreportcard/subject/publications/stt2024/pdf/2024219OR4.pdf)). The 2021 Oregon Mathematics Standards, adopted by the State Board of Education and closely derived from Common Core, are publicly available under Creative Commons licensing, making standards database construction fully feasible ([Oregon Department of Education](https://www.oregon.gov/ode/educator-resources/standards/mathematics/pages/mathstandards.aspx)). Recent advances in multi-agent AI architectures and LLM-powered question generation provide the technical foundation for the two proposed differentiators — a curated standards database and AI-driven adaptive content generation. However, the app enters a crowded field dominated by IXL, DreamBox, Khan Academy, and Zearn, and must navigate COPPA/FERPA compliance requirements for the under-13 audience.

This report covers the full landscape: Oregon-specific standards mapping, prerequisite skill analysis, competitive dynamics, adaptive learning algorithms, AI-powered question generation feasibility, recommended tech stack, and a risk assessment.

---

## Oregon 4th Grade Math Standards: A Complete Map

### Standards Framework

Oregon adopted revised mathematics standards in October 2021, effective with the 2023-24 school year. These standards reorganize the original Common Core domains into four learning pathways: Algebraic Reasoning, Numeric Reasoning, Geometric Reasoning & Measurement, and Data Reasoning ([Oregon Department of Education](https://www.oregon.gov/ode/educator-resources/standards/mathematics/Documents/2021%20Grade%204%20Mathematics.pdf)).

Grade 4 instructional time focuses on three critical areas:
1. Developing understanding and fluency with multi-digit multiplication, and understanding division with multi-digit dividends
2. Developing understanding of fraction equivalence, addition/subtraction of fractions with like denominators, and multiplication of fractions by whole numbers
3. Analyzing and classifying geometric figures based on properties (parallel/perpendicular sides, angle measures, symmetry)

### Full Standards Inventory

| Domain | Code | Cluster | Standard Count |
|--------|------|---------|---------------|
| Algebraic Reasoning: Operations | 4.OA | Use four operations; factors & multiples; patterns | 5 standards |
| Numeric Reasoning: Base Ten | 4.NBT | Place value understanding; multi-digit arithmetic | 6 standards |
| Numeric Reasoning: Fractions | 4.NF | Fraction equivalence; build from unit fractions; decimals | 7 standards |
| Geometric Reasoning & Measurement | 4.GM | Lines/angles/shapes; measurement conversion; angle measurement | 9 standards |
| Data Reasoning | 4.DR | Investigative questions; analyze/interpret data | 2 standards |

The full standards document contains 29 individual standards across 5 domains and 13 clusters ([Oregon Grade 4 Mathematics Standards](https://www.oregon.gov/ode/educator-resources/standards/mathematics/Documents/2021%20Grade%204%20Mathematics.pdf)). This is a manageable scope for building a comprehensive question database — particularly for an initial 4th-grade Oregon prototype.

### Key Oregon-Specific Differences from Common Core

Oregon's 2021 revision introduced several changes relevant to app design:
- Addition of a **Data Reasoning** domain (4.DR) not present in the original Common Core
- Merging of Measurement and Geometry into a single **Geometric Reasoning & Measurement** domain (4.GM)
- Emphasis on "authentic contexts" throughout (e.g., 4.OA.A.2 specifies problems in "authentic contexts" rather than generic word problems)
- Oregon uses **Smarter Balanced** assessments aligned to these standards, providing a ready source of item types and difficulty calibration ([Oregon OSAS Grade 4 Math Scoring Guide](https://www.oregon.gov/ode/educator-resources/assessment/Documents/OSAS_Math_CAT_Sample_Test_Scoring_Guide_G4.pdf))

---

## Prerequisite Skills: What Students Need Entering 4th Grade

To build a diagnostic assessment for incoming 4th graders, the app must test mastery of 3rd grade exit expectations. Based on Common Core Grade 3 standards and Oregon's aligned expectations:

### Critical Prerequisites (3rd Grade Exit Standards)

| Skill Area | Standard | Expected Mastery |
|-----------|----------|-----------------|
| Multiplication facts | 3.OA.C.7 | Fluently multiply and divide within 100; know from memory all products of two one-digit numbers ([Common Core Grade 3](https://www.commoncoremath.com/3rd-grade-common-core-math-standard)) |
| Division facts | 3.OA.C.7 | Fluently divide within 100 using relationship to multiplication |
| Multi-step word problems | 3.OA.D.8 | Solve two-step word problems using four operations |
| Place value & rounding | 3.NBT.A.1 | Round whole numbers to nearest 10 or 100 |
| Addition/subtraction within 1,000 | 3.NBT.A.2 | Fluently add and subtract within 1,000 |
| Multi-digit multiplication | 3.NBT.A.3 | Multiply one-digit numbers by multiples of 10 |
| Fraction concepts | 3.NF.A.1-3 | Understand fractions as numbers on a number line; compare fractions with same numerator or denominator |
| Area & perimeter | 3.MD.C.5-7 | Understand area as attribute; relate to multiplication; measure areas by counting unit squares |
| Time & measurement | 3.MD.A.1-2 | Tell time to nearest minute; solve elapsed time problems; measure liquid volumes and masses |

According to [Understood.org](https://www.understood.org/en/articles/skills-kids-need-going-into-fourth-grade), students entering 4th grade should: know times tables up to 12, multiply numbers by 10, use all four operations in multi-step word problems, understand fractions as numbers on a number line, and compare fractions.

These prerequisites form the foundation for the **diagnostic entry assessment**. A student deficient in, for example, multiplication facts (3.OA.C.7) would need remediation before attempting 4th grade multi-digit multiplication (4.NBT.B.5).

---

## The Market Opportunity: Oregon 4th Grade Math Proficiency

### Current Performance Data

The 2024 NAEP Mathematics Snapshot for Oregon paints a compelling picture of need:

![NAEP Grade 4 Math Achievement Levels - Oregon vs. National, 2024](https://d2z0o16i8xm8ak.cloudfront.net/76dfede9-b3e5-4606-8aad-8fd50a629121/45455993-ab3a-4c82-992e-8f65e26843f7/oregon-grade4-naep-proficiency.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9kMnowbzE2aTh4bThhay5jbG91ZGZyb250Lm5ldC83NmRmZWRlOS1iM2U1LTQ2MDYtOGFhZC04ZmQ1MGE2MjkxMjEvNDU0NTU5OTMtYWIzYS00YzgyLTk5MmUtOGY2NWUyNjg0M2Y3L29yZWdvbi1ncmFkZTQtbmFlcC1wcm9maWNpZW5jeS5wbmc~KiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc3NjQ1NjU0Mn19fV19&Signature=qLNwJhrTZODSITnS-NhKO12QYsjGMx-dsOltef4lnCuo~s7xf2NcW0n6mI~dfjZfxiBVUr~ukkSqp8CWli0s9GEdEkGgYUdH44ZRcKVt~O7oFYBrZIHV8DydZbcnqs7RgbrXbIlHFrgESdklNKTlfQ7PGQtPanxmmp-bDeaOlZAxGhugbWeDEap7pqN8y1SbmUYo1sFxy3HYzLrCpvB5akW0LcffsG758PKjKDnpBSokUT14uq5-i584M2-devTHv0L~U9lQFVLKw9LQuCODINhJzq~v-qRtUnZLjDhZqBEg2aimFQORhtvHINl3dwoCGghv7ChvL9Tu8h~UPqS7cQ__&Key-Pair-Id=K1BF7XGXAIMYNX)

Key statistics from the [NAEP 2024 Oregon Snapshot](https://nces.ed.gov/nationsreportcard/subject/publications/stt2024/pdf/2024219OR4.pdf):
- Oregon 4th graders averaged **229** vs. the national average of **237** — a statistically significant gap
- Only **31% reached proficiency** (vs. 40% nationally)
- **33% scored Below Basic** (vs. 24% nationally)
- Oregon ranked **lower than 45 states/jurisdictions** in 4th grade math

### Demographic Disparities

| Student Group | Average Score | % Proficient |
|--------------|---------------|-------------|
| Asian | 256 | 62% |
| White | 235 | 36% |
| Two or More Races | 232 | 35% |
| Hispanic | 213 | 16% |
| Economically disadvantaged | 213 | 15% |
| Not economically disadvantaged | 239 | 42% |

The 26-point gap between economically disadvantaged and non-disadvantaged students, and the 21-point gap between Hispanic and White students, represent significant equity opportunities for a well-designed intervention tool.

Oregon statewide assessment data shows similar trends: only **31.5% of students are proficient in math** across all grades ([Jefferson Public Radio](https://www.ijpr.org/education/2025-10-02/oregon-schools-test-scores-takeaways)).

### Market Size

The global adaptive learning market was valued at **USD 4.84 billion in 2024** and is projected to reach **USD 28.36 billion by 2033** at a CAGR of 19.7% ([IMARC Group](https://www.imarcgroup.com/adaptive-learning-market)). The broader EdTech and smart classrooms market is estimated at **USD 197.3 billion in 2025**, projected to reach **USD 353.1 billion by 2030** ([MarketsandMarkets](https://www.marketsandmarkets.com/Market-Reports/educational-technology-ed-tech-market-1066.html)). The academic sector accounts for approximately 78.5% of adaptive learning market share.

---

## Competitive Landscape

### Established Players

![Competitive Feature Matrix](https://d2z0o16i8xm8ak.cloudfront.net/76dfede9-b3e5-4606-8aad-8fd50a629121/b24a93e2-d8de-43d6-8de3-b598d91d97f8/competitive-feature-matrix.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9kMnowbzE2aTh4bThhay5jbG91ZGZyb250Lm5ldC83NmRmZWRlOS1iM2U1LTQ2MDYtOGFhZC04ZmQ1MGE2MjkxMjEvYjI0YTkzZTItZDhkZS00M2Q2LThkZTMtYjU5OGQ5MWQ5N2Y4L2NvbXBldGl0aXZlLWZlYXR1cmUtbWF0cml4LnBuZz8qIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzc2NDU2NTQyfX19XX0_&Signature=adhxKtKzCXP9B7N17XOKlgZoaWu58svkj0pd-k-ZoB-PIqORCMkH09oU5yFBsOzPaLpapY5wzz3riC5F9lHSzlqnSEvErnwPYV-mxYa3GL9~o9aiyA0hh2R5kPPuIVmBI1MIcMqULtcOUGR6fryPZ-vte3Jhni0KgqBOFbcyVsHFD6wCdqz-cVXx3N13TixydF2PUOt39HU827tiSgSE8x0LcvFfUBkXCRrQ5Mninj1nhkK3RlItOcp1HYBdruxCrNs48lflhb9xatbww9hsI3mwlQRUdn2TA9FREIVwaRlIBWcO7gVGhqkbs2irXic~3HiIc28-k41Zi5LoeTPZtQ__&Key-Pair-Id=K1BF7XGXAIMYNX)

| Platform | Pricing | Adaptive Engine | Standards Alignment | Key Strength | Key Weakness |
|----------|---------|----------------|--------------------|--------------|--------------| 
| **Khan Academy** | Free | Basic mastery progression | Common Core mapped | Free, comprehensive video library | Less sophisticated adaptation; requires self-motivation ([Afficient Academy Blog](https://blog.afficienta.com/best-daily-math-practice-programs-that-follow-school-curriculum-in-2025/)) |
| **IXL** | $9.95/mo per subject | Real-time diagnostic (2017+) | Common Core & state standards | Phenomenal data dashboards; 8,000+ skills; real-time adaptiveness ([Room to Discover](https://roomtodiscover.com/adaptive-learning/)) | Can feel repetitive; harsh scoring system criticized by educators |
| **DreamBox** | $19.95/mo | Sophisticated adaptive algorithm tracking misconceptions | Common Core | Identifies specific misconceptions from incorrect answers; conceptual approach ([Room to Discover](https://roomtodiscover.com/adaptive-learning/)) | Higher price; most effective for younger students; activities take longer |
| **Zearn** | Free for families | Moderate | Lesson-by-lesson Common Core | Strong curriculum alignment; combination of digital and hands-on | Best for elementary; requires internet ([Afficient Academy Blog](https://blog.afficienta.com/best-daily-math-practice-programs-that-follow-school-curriculum-in-2025/)) |
| **Prodigy** | Free (premium optional) | Moderate | Standards-aligned | Highly engaging game format | Less rigorous academic focus; gamification can distract ([Afficient Academy Blog](https://blog.afficienta.com/best-daily-math-practice-programs-that-follow-school-curriculum-in-2025/)) |

### Critical Observation: The "5% Problem"

A notable critique of existing platforms comes from education writer Holly Korbey in [Education Next](https://pershmail.substack.com/p/practice-software-is-struggling): DreamBox, Zearn, i-Ready, Khan Academy, ALEKS, and IXL are all "struggling" with what's called the "5 percent problem" — these tools typically only improve student outcomes by about 5%, far below what's needed to close achievement gaps. This suggests room for a fundamentally different approach.

### Where the Proposed App Can Differentiate

1. **Oregon-specific standards database**: No existing platform deeply maps to the 2021 Oregon Math Standards (with its unique Data Reasoning domain and "authentic contexts" emphasis). Most competitors map to generic Common Core.
2. **AI-generated adaptive content**: Existing platforms rely on static, pre-authored question banks. AI-generated content provides infinite practice variety at precisely the right difficulty level.
3. **Structured diagnostic-to-mastery pipeline**: The specific flow — diagnostic assessment → gap analysis → personalized learning plan → targeted remediation → summative assessment → continued remediation — is more structured than competitors' "practice until mastery" models.
4. **Prerequisite remediation**: Explicitly testing and remediating 3rd-grade prerequisites before advancing to 4th-grade content is a pedagogical approach most competitors don't explicitly implement.

---

## Adaptive Learning Algorithms and AI Architecture

### Classical Approaches

The foundation of adaptive learning in education rests on two complementary paradigms:

**Bayesian Knowledge Tracing (BKT)** models student learning as a Hidden Markov Model per skill, tracking binary mastery states ("mastered" or "not mastered") with four key parameters: initial knowledge probability, learning rate, guess rate, and slip rate. BKT dynamically updates mastery estimates as students respond to problems. A recent study demonstrated BKT achieving 63.56% overall predictive accuracy for skill mastery tracking, outperforming Performance Factor Analysis ([Bayesian Knowledge Tracing Research](https://jurnal.polgan.ac.id/index.php/sinkron/article/download/15605/3745/27353)).

**Item Response Theory (IRT)** models student ability and item difficulty simultaneously, placing both on a common scale. While IRT alone cannot model learning over time, combining it with BKT yields a model that captures both student ability and skill acquisition — research shows this combined approach "persistently outperforms Knowledge Tracing" and unlike IRT alone, "is able to model student learning" ([Khajah et al., University of Colorado](https://home.cs.colorado.edu/~mozer/Research/Selected%20Publications/reprints/KhajahHuangGonzalesBrenesMozerBursilovsky2014.pdf)).

Recent extensions include:
- **BKT-LSTM**: Hybrid models combining BKT interpretability with deep learning sequence modeling ([Emergent Mind](https://www.emergentmind.com/topics/bayesian-knowledge-tracing))
- **BBKT**: Bayesian-Bayesian Knowledge Tracing with per-student parameter inference for more equitable mastery outcomes
- **PDT**: Continuous-variable models maintaining beta distributions for real-time, uncertainty-quantified mastery tracking

**Recommendation for the app**: Start with **BKT + IRT** (using the [pyBKT library](https://github.com/CAHLR/pyBKT)) for interpretable, proven skill tracking. The combined model provides both assessment capability (IRT) and learning modeling (BKT), directly supporting the diagnostic → remediation → assessment pipeline.

### Frontier AI: Multi-Agent Architectures for Math Tutoring

Recent research demonstrates how frontier LLMs can power sophisticated tutoring systems:

**Multi-Agent AI Math Tutoring Platform** (2025, [Stanford SCALE/arXiv](https://arxiv.org/html/2507.12484v1)): An open-source multi-agent system built on **LangGraph** with:
- **Tutor Agent** (GPT-4o): Central orchestrator using Socratic questioning, dynamically adjusting support
- **Task Creation Agent** (o3-mini): Generates personalized exercises based on topic, difficulty, and student profile — achieved 90% problem-solving accuracy
- **Dual-memory system**: Long-Term Memory (persistent student traits/mastery) + Working Memory (current session context)
- **GraphRAG**: Textbook material as a knowledge graph for contextual retrieval

**Adaptive Multi-Agent Tutoring** (2025, [UCC/arXiv](https://cora.ucc.ie/server/api/core/bitstreams/517c234e-d5c1-4e75-bbf0-b444c619c722/content)): Five specialized agents (Informer, Verifier, Insight, Practice, Tutor) with multimodal input support (text, speech, image) and proactive weakness detection.

**Key insight for the proposed app**: The multi-agent pattern — separating assessment, tutoring, question generation, and progress tracking into specialized agents — maps directly to the app's requirements and is proven in production-quality research systems.

---

## AI-Powered Question Generation: Feasibility Assessment

### Can LLMs Generate Valid Math Problems?

The MATHWELL system ([arXiv](https://arxiv.org/html/2402.15861v3)) provides the strongest evidence. Using a finetuned Llama-2 (70B) model:

| Metric | MATHWELL Score |
|--------|---------------|
| Solvability | 89.2% |
| Accuracy | 96.9% |
| Appropriateness for K-8 | 86.5% |
| Meets All Criteria | 74.8% |
| Reading Level | All at or below 8th grade (FKGL 2.68 avg) |

MATHWELL generated **20,490 word problems** (the largest public K-8 English math dataset) with a nearly 75% rate of simultaneously solvable, accurate, and age-appropriate problems. The system outperformed general-purpose LLMs by 43.4% on combined quality metrics.

A separate study, MathWiz ([arXiv](https://arxiv.org/html/2506.05950v2)), demonstrated that well-curated prompts can instruct LLMs to generate problems by grade level and operation type (e.g., "Grade 4, Section: Multiplication, Number of questions: 5") with high solvability and accuracy.

### LLM Math Reasoning Capability (2026 State of the Art)

Current frontier models show strong mathematical capability relevant to problem generation and solution verification:
- **Claude Sonnet 4.6**: Recognized for "clarity of solution process" and Learning Mode designed to guide reasoning rather than give answers — particularly suited for tutoring ([Apiyi.com](https://help.apiyi.com/en/best-ai-model-for-math-2026-en.html))
- **GPT-4o**: Strong conversational math tutoring; 78.67% accuracy on benchmark with tool use
- **o3-mini(high)**: 90% accuracy on math problem-solving with SymPy tool integration ([arXiv](https://arxiv.org/html/2507.12484v1))

### Validation Pipeline (Critical Requirement)

LLM-generated questions cannot be trusted blindly. Research on detecting errors in math word problems found that even a small Llama-3.2-3B model achieved 90% accuracy in identifying errors, comparable to the larger Mixtral-8x7B's 90.62% after fine-tuning ([Massey University](https://mro.massey.ac.nz/server/api/core/bitstreams/8ff79c96-1ad9-40b8-9c99-3b6038a75446/content)). 

**Recommended validation pipeline**:
1. LLM generates question + Python solution (Program of Thought)
2. Python solution is executed to verify answer computability
3. Classifier model checks solvability, accuracy, and age-appropriateness
4. Questions matching Oregon standards are tagged to specific skill codes
5. Human review for initial question bank seeding; automated review for ongoing generation

---

## Accessibility of Standards Data and Content Sources

### Standards Data: Fully Accessible

| Source | Accessibility | License |
|--------|-------------|---------|
| [Oregon 2021 Math Standards (Grade 4)](https://www.oregon.gov/ode/educator-resources/standards/mathematics/Documents/2021%20Grade%204%20Mathematics.pdf) | Public PDF, well-structured | Creative Commons Attribution 4.0 International |
| [Common Core State Standards](https://thecorestandards.org/Math/Content/4/OA/) | Public website, granular per standard | Public domain |
| [Oregon OSAS Sample Tests + Scoring Guides](https://www.oregon.gov/ode/educator-resources/assessment/Documents/OSAS_Math_CAT_Sample_Test_Scoring_Guide_G4.pdf) | Public PDF with items, answers, claims, DOK levels | Public |
| [Smarter Balanced Practice Tests](https://smarterbalanced.org/our-system/students-and-families/samples/) | Public online test interface | Public |
| [IXL Common Core Grade 4 Skill Map](https://www.ixl.com/standards/common-core/math/grade-4) | Public skill-to-standard mapping | Reference only |

The Oregon standards are explicitly licensed under **Creative Commons Attribution 4.0**, making them freely usable in commercial products. The Smarter Balanced sample items and scoring guides provide excellent reference material for question format, difficulty calibration, and Depth of Knowledge (DOK) levels.

### Open Educational Resources for Question Banks

- **OATutor**: Fully open-source adaptive tutoring system with Creative Commons-licensed problem library and BKT-based mastery tracking ([OATutor](https://www.oatutor.io); [UC Berkeley](https://bse.berkeley.edu/leveraging-ai-improve-adaptive-tutoring-systems))
- **Khan Academy**: Common Core-aligned exercise database (reference for problem types)
- **Share My Lesson**: Comprehensive aligned lesson plans from multiple sources ([Edutopia](https://www.edutopia.org/blog/common-core-math-elementary-resources-matt-davis))
- **SGSM Dataset**: 20,490 LLM-generated K-8 word problems, publicly available ([arXiv](https://arxiv.org/html/2402.15861v3))

---

## Recommended Tech Stack

![Proposed Architecture](https://d2z0o16i8xm8ak.cloudfront.net/76dfede9-b3e5-4606-8aad-8fd50a629121/27fe66ad-1a66-4341-8597-9c0b4548443e/proposed-architecture.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9kMnowbzE2aTh4bThhay5jbG91ZGZyb250Lm5ldC83NmRmZWRlOS1iM2U1LTQ2MDYtOGFhZC04ZmQ1MGE2MjkxMjEvMjdmZTY2YWQtMWE2Ni00MzQxLTg1OTctOWMwYjQ1NDg0NDNlL3Byb3Bvc2VkLWFyY2hpdGVjdHVyZS5wbmc~KiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc3NjQ1NjU0Mn19fV19&Signature=fUXyhdgFkxwSFpthJSjBpnCWHewwI1wnS-sHVTDTN9csHa7IsNYf~SsUKeen0xA-rNZIBOVAUARS8FN9R5eXNSzP9ML28zFyog2wyOZSugIOoI031JZ9bD6lqc216IwQ4uLVbk872F4B-AZY8-KV43LcRqR3SYMXX1J~g5rAvP-b3bJvsAxDn7gnEfwQ8KSTACOjt-xE41tOT2csK3yraGnlAlpKDuEh7oM-pBjPmmdeRKcPPZNLRlDZF9j6l6VNUmjfknRO0Xsm2z3WQoQTGSCKVyQvF0It7iwgqOf7xlYHihfAWbAac3qcrAoDq8Uw9tvin5aSjkINYIDGUZpTUQ__&Key-Pair-Id=K1BF7XGXAIMYNX)

### Frontend

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Framework | **React / Next.js** | Component-based architecture ideal for reusable quiz/dashboard UI elements; used by Khan Academy; excellent ecosystem ([Arccus Inc](https://arccusinc.com/blog/how-to-build-an-interactive-elearning-platform-with-ai-and-react-js/)) |
| Mobile | **React Native** or **Flutter** | Cross-platform for iOS/Android tablet deployment (critical for classroom use) |
| State Management | **Redux** or **Zustand** | Manage complex student session state |
| Math Rendering | **KaTeX** or **MathJax** | Render fractions, equations, and mathematical notation |

### Backend

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| API Server | **Python (FastAPI or Django)** | Python's AI/ML ecosystem is unmatched; FastAPI for high-performance async APIs; Django for rapid auth/admin development ([Esparkinfo](https://www.esparkinfo.com/software-development/technologies/reactjs/react-with-python)) |
| Agent Framework | **LangGraph** | Proven for multi-agent math tutoring; manages agent orchestration, state, and routing ([arXiv](https://arxiv.org/html/2507.12484v1)) |
| Knowledge Tracing | **pyBKT** + custom IRT | BKT for skill mastery tracking; IRT for item difficulty calibration |
| Question Generation | **Frontier LLMs via API** (Claude Sonnet, GPT-4o, o3-mini) | Claude for explanation quality; o3-mini for problem generation (90% accuracy); GPT-4o for conversational tutoring |
| Question Validation | **Python execution engine** + classifier | Execute PoT solutions; DistilBERT classifier for automated quality scoring |

### Data Layer

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Primary Database | **PostgreSQL** | Relational data for standards, student profiles, assessments, learning plans |
| Student Knowledge Model | **Redis** (real-time) + PostgreSQL (persistent) | Real-time BKT state updates during sessions; persistent mastery records |
| Standards Knowledge Graph | **Neo4j** or **PostgreSQL with ltree** | Model prerequisite relationships between standards/skills |
| Vector Store | **Pinecone** or **pgvector** | RAG for curriculum-aligned content retrieval |

### Infrastructure

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Cloud | **AWS** or **Google Cloud** | GCP offers Vertex AI for model hosting; AWS for breadth |
| Auth | **Auth0** or **Supabase Auth** | COPPA-compliant authentication with parental consent flows |
| Monitoring | **PostHog** or **Mixpanel** | Learning analytics; A/B testing of question formats |

---

## Compliance Requirements: COPPA and FERPA

Since the target users are under 13, compliance is non-negotiable:

### COPPA (Children's Online Privacy Protection Act)

Per the [FTC's COPPA FAQ](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions):
- **Verifiable parental consent** required before collecting any personal information from children under 13
- Applies to photos, videos, audio files with children's images/voices, geolocation, and persistent identifiers
- Website/service "directed to children" must treat all visitors as children — cannot use age-gating to avoid COPPA
- Data collection must be minimized to what's necessary for the activity
- Clear, comprehensive privacy policy required

### FERPA (Family Educational Rights and Privacy Act)

Per [SchoolAI compliance guide](https://schoolai.com/blog/ensuring-ferpa-coppa-compliance-school-ai-infrastructure/):
- Protects student education records in federally funded schools
- Role-based permissions required; data visible only to those with "legitimate educational interest"
- Data-sharing agreements required with vendors specifying what student data is accessed and how it's protected
- Incident-response plan required for handling breaches

### Practical Implications for App Design

- Parent/guardian creates account and provides consent (not the child)
- Minimal data collection: no photos, no voice, no precise geolocation
- Student data stored with encryption at rest and in transit
- Data retention policies with automatic deletion
- Option for schools to provide consent on behalf of parents for classroom use
- Consider pursuing **Student Privacy Pledge** certification for school credibility

---

## Viability Analysis

### Strengths

| Factor | Assessment |
|--------|-----------|
| **Market need** | Oregon 4th graders score 8 points below national average; only 31% proficient; significant equity gaps — the need is quantifiably urgent |
| **Standards accessibility** | Oregon standards are CC-licensed, well-structured, and manageable scope (29 standards, 5 domains for Grade 4) |
| **Technical feasibility** | Multi-agent AI tutoring architectures are proven in research; LLM question generation achieves 75%+ quality rates; BKT/IRT algorithms are mature |
| **Differentiation potential** | Oregon-specific standards mapping + AI-generated adaptive content is a genuine gap in the market |
| **Expansion path** | Grade 4 Oregon → other Oregon grades → other states follows a clear expansion playbook |

### Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **LLM question accuracy** | High | Multi-stage validation pipeline (Python execution + classifier + human review for seed bank); never ship unvalidated questions |
| **COPPA compliance complexity** | High | Engage privacy counsel early; use parent-mediated account creation; minimize data collection; consider COPPA-safe harbor programs |
| **Competition from incumbents** | Medium | IXL, DreamBox have massive content libraries; differentiate on Oregon-specificity and AI adaptiveness, not content volume |
| **LLM cost at scale** | Medium | Use smaller models (o3-mini) for generation; cache generated questions; build reusable question bank over time to reduce API calls |
| **Teacher/school adoption** | Medium | Schools are cautious about new EdTech; pilot with willing Oregon schools; align with Oregon OSAS assessment format for credibility |
| **AI hallucinations in tutoring** | Medium | Constrain tutoring agent to curriculum scope; use RAG grounded in standards documents; log all interactions for review |
| **Math rendering on mobile** | Low | KaTeX/MathJax are mature; extensive testing needed for fractions and multi-step problems |

### Build vs. Buy Assessment

| Component | Recommendation | Rationale |
|-----------|---------------|-----------|
| Standards database | **Build** | Oregon-specific curation is the differentiator; CC-licensed source material |
| Adaptive engine (BKT/IRT) | **Build on pyBKT** | Open-source, well-documented, customizable |
| Question generation | **Build with LLM APIs** | Core differentiator; leverage MATHWELL research approach |
| Agent orchestration | **Build on LangGraph** | Open-source, proven for math tutoring ([GitHub](https://github.com/feilaz/AI_Powered_Math_Tutoring)) |
| Authentication | **Buy (Auth0/Supabase)** | COPPA compliance too risky to build from scratch |
| Frontend | **Build** | Custom UX needed for child-appropriate design |
| Hosting | **Buy (AWS/GCP)** | Standard cloud infrastructure |

---

## Pedagogical Outcome Hypothesis

### Claim

> MathPath Oregon will improve student math proficiency rates by **15–25 percentage points** among engaged students (defined as ≥10 completed sessions), compared to the ~5% real-world improvement documented for current platforms (Holt, 2024).

### Why Existing Platforms Achieve Only ~5%

Holt (2024) analyzed 14 studies of platforms including i-Ready, DreamBox, Khan Academy, and IXL. Despite positive controlled-study effect sizes, real-world population-level gains are near zero because only approximately 5% of students use these tools with the frequency and engagement needed to benefit. Korbey (2025) documented that one-third of teachers rate these tools "mediocre or poor" and that gains are concentrated in already-high-performing students — deepening inequity rather than closing gaps.

The root cause: these are **answer-level feedback systems**. VanLehn (2011) showed answer-level systems achieve only d = 0.30 regardless of sophistication. Reaching d = 0.76 (near-equivalent to human tutoring) requires step-level feedback — which requires an AI tutoring agent.

### MathPath's Four Evidence-Backed Mechanisms

**Mechanism 1 — Prerequisite Gap Remediation First**

Existing platforms place students into grade-level content regardless of foundational mastery. MathPath diagnoses and remediates 3rd-grade prerequisite skills *before* exposing students to 4th-grade content. The What Works Clearinghouse practice guide on elementary math intervention (Fuchs et al., 2021) rates prerequisite-grounded instruction as its highest-evidence recommendation for students struggling with math. Fuchs et al. (2008) demonstrated that unaddressed foundational skill gaps are the primary driver of persistent difficulty across elementary grades.

**Mechanism 2 — Step-Level Socratic Feedback (d = 0.76 vs. d = 0.30)**

VanLehn (2011) compared tutoring modalities across 62 studies:
- Answer-level tutoring systems (IXL, Khan Academy): effect size **d = 0.30**
- Step-level intelligent tutoring systems (ITS with Socratic guidance): effect size **d = 0.76**
- Human tutors: effect size **d = 0.79**

MathPath's Tutor Agent guides students through reasoning steps rather than simply marking answers right or wrong — moving from the d = 0.30 to the d = 0.76 band.

**Mechanism 3 — BKT Mastery Gating + Spaced Practice**

MathPath prevents students from advancing past a skill until BKT probability of mastery reaches P(mastered) ≥ 0.85. This operationalizes Bloom's (1984) mastery learning approach, which meta-analyses show produces effect sizes of d = 0.5–1.0 (Ma et al., 2014; Kulik & Fletcher, 2016). Combined with spaced re-exposure to previously mastered skills — Cepeda et al. (2006) synthesized 839 assessments showing spaced practice outperforms massed practice in 95% of cases — this creates durable retention rather than shallow fluency.

**Mechanism 4 — Error-Type Classification**

MathPath's Assessment Agent classifies error types (procedural vs. conceptual, specific misconception categories) rather than marking responses as correct/incorrect. The IES spaced practice guide (Pashler et al., 2007) identifies targeted error correction as one of the highest-evidence instructional strategies. Different error types require different instructional interventions; MathPath routes each error type to a different hint strategy.

### Why We Expect to Beat the 2-Sigma Ceiling

Bloom (1984) identified that one-to-one mastery tutoring produces d ≈ 2.0 vs. conventional classroom instruction — the "2 sigma problem." MathPath approximates the components of 1-on-1 tutoring: step-level feedback, error-specific guidance, prerequisite-aware sequencing, and mastery-gated advancement. Recent meta-analyses of intelligent tutoring systems show mean effect sizes of g = 0.42–0.66 vs. conventional instruction (Ma et al., 2014; Kulik & Fletcher, 2016) — well above the ~5% threshold.

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

## Recommended MVP Scope

For the initial proof of concept focused on Oregon 4th grade:

### Phase 1: Diagnostic Assessment (Weeks 1-6)
- Build standards database: 29 Oregon 4th grade standards + 15-20 key 3rd grade prerequisites
- Create diagnostic assessment: 3-5 questions per prerequisite skill area (~40-60 questions total)
- Implement BKT model for initial skill estimation
- Build student profile creation with parent consent flow

### Phase 2: Personalized Learning Plan (Weeks 7-12)
- Generate prerequisite skill knowledge graph (what depends on what)
- Build learning plan generator that sequences remediation → new content
- Implement LLM-powered question generation for identified weak areas
- Build question validation pipeline (Python execution + automated scoring)

### Phase 3: Adaptive Practice Engine (Weeks 13-20)
- Implement multi-agent tutoring system (LangGraph-based)
- Add hint/explanation generation using Claude or GPT-4o
- Build real-time difficulty adjustment based on BKT mastery estimates
- Implement progress dashboard for students and parents

### Phase 4: End-of-Grade Assessment & Iteration (Weeks 21-26)
- Build summative assessment aligned to Oregon OSAS format
- Implement continued remediation loop for students below proficiency
- Add parent/teacher reporting dashboards
- Conduct pilot testing with Oregon 4th graders

---

## Conclusion

This app concept sits at the intersection of a documented educational need (Oregon's below-average 4th grade math proficiency), accessible public data (CC-licensed Oregon standards), and maturing AI technology (multi-agent tutoring, LLM question generation, Bayesian knowledge tracing). The two proposed differentiators — a curated Oregon standards database and AI-driven adaptive content — are technically achievable and represent genuine gaps in the current competitive landscape.

The primary risks are execution complexity (multi-agent AI systems require careful engineering), COPPA compliance (non-negotiable for under-13 users), and the inherent challenge of competing for school/parent adoption in a market with well-funded incumbents. A focused MVP scoped to Oregon 4th grade math, validated through pilot testing with real students, provides the fastest path to proving the concept before expanding.

The recommended path forward: build the standards database and diagnostic assessment first (leveraging Oregon's CC-licensed materials), validate the AI question generation pipeline with human expert review, then layer in the adaptive tutoring agent architecture. This approach delivers demonstrable value early while progressively adding AI sophistication.
