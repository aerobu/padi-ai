# MathPath Oregon — Multi-Grade Expansion Document
## PRD & Architecture Plan: Grades 1, 2, 3, and 5

> **Document Version:** 1.0  
> **Date:** April 2026  
> **Status:** Final Draft — Internal Planning  
> **Owner:** Product & Engineering Leadership  
> **Audience:** Senior PM, Design Engineer, Backend Engineer, AI/ML Engineer, QA Lead  
> **Predecessor Document:** PRD Stage 1 (03-prd-stage1.md) — Grade 4 product specification  

> **Development Timeline Note (Updated April 2026):** This multi-grade expansion is planned for Stage 6 (post-MMP). Under solo development with AI agents, MMP is projected at Month 30–36 (optimistic: 30, realistic: 36). Stage 6 / multi-grade expansion therefore begins at Month 31–37 at the earliest. All expansion plans in this document remain valid; only the start dates shift. Budget an additional 200–280 agent-hours and 8–12 months for full Grades 1, 2, 3, 5 expansion as described here.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Oregon 2021 Math Standards — Complete Catalog](#2-oregon-2021-math-standards--complete-catalog)
3. [Prerequisite Relationship Graphs](#3-prerequisite-relationship-graphs)
4. [Question Bank Requirements](#4-question-bank-requirements)
5. [Diagnostic Assessment Parameters](#5-diagnostic-assessment-parameters)
6. [Age-Appropriate UI/UX Requirements](#6-age-appropriate-uiux-requirements)
7. [Architecture & Database Expansion Plan](#7-architecture--database-expansion-plan)
8. [Expansion Rollout Strategy](#8-expansion-rollout-strategy)
9. [Future Extensibility Considerations](#9-future-extensibility-considerations)
10. [Appendix: Kindergarten Standards Reference](#10-appendix-kindergarten-standards-reference)

---

# 1. Executive Summary

## 1.1 Overview

MathPath Oregon launched as a Grade 4-only adaptive math platform. The Grade 4 application will be fully built and validated across five development stages spanning approximately 20 months. This document defines the complete product requirements, content architecture, user experience specifications, and technical expansion plan for extending MathPath Oregon to cover **Grades 1, 2, 3, and 5** — encompassing the full Oregon elementary math curriculum from first grade through fifth grade.

The expansion is not a rewrite. It builds directly on the Grade 4 infrastructure: the same standards database schema (with the `grade` field already typed as `SMALLINT`), the same BKT mastery-tracking pipeline (parameterized per grade), the same question generation architecture (with grade-context injected into LLM prompts), and the same design system (extended with grade-band-specific theme tokens). The work is additive, not architectural, with the significant exception of Grade 1 — where pre-literacy design requirements mandate a dedicated TTS integration layer, enlarged touch targets, and interaction patterns that eliminate keyboard input entirely.

Oregon elementary students deserve a tool that meets them where they are. A 6-year-old first grader and an 11-year-old fifth grader are not the same learner. This document treats them as distinct audiences with distinct cognitive profiles, distinct accessibility needs, and distinct interaction affordances — while sharing a unified standards data model, a unified AI question generation pipeline, and a unified parent-facing reporting layer.

## 1.2 Standards Coverage Summary

The following table summarizes the complete Oregon 2021 Math Standards coverage across all grades supported after expansion, mapped by domain.

| Grade | Age Range | OA | NCC | NBT | NF | GM | DR | **Total** |
|-------|-----------|-----|-----|-----|-----|-----|-----|-----------|
| K (Prerequisite Pool) | 5–6 | 5 | 7 | 1 | — | 8 | 2 | **23** |
| 1 *(new)* | 6–7 | 8 | — | 6 | — | 6 | 2 | **22** |
| 2 *(new)* | 7–8 | 4 | — | 9 | — | 11 | 2 | **26** |
| 3 *(new)* | 8–9 | 9 | — | 3 | 3 | 8 | 2 | **25** |
| 4 *(existing)* | 9–10 | 5 | — | 6 | 7 | 9 | 3 | **29** |
| 5 *(new)* | 10–11 | 3 | — | 7 | 7 | 7 | 2 | **26** |
| **Expansion Total** | — | 24 | — | 25 | 10 | 32 | 8 | **102 new standards** |
| **Grand Total (all grades)** | — | — | — | — | — | — | — | **131 standards** |

**Domain Key:**
- **OA** — Algebraic Reasoning: Operations
- **NCC** — Numeric Reasoning: Counting and Cardinality (Kindergarten only)
- **NBT** — Numeric Reasoning: Base Ten Arithmetic
- **NF** — Numeric Reasoning: Fractions (Grades 3–5 only)
- **GM** — Geometric Reasoning and Measurement
- **DR** — Data Reasoning

## 1.3 Architecture Extensibility Assessment

The table below identifies each major Grade 4 system component and its readiness for multi-grade expansion without modification (green), requiring minor extension (yellow), or requiring significant new work (red).

| Component | Multi-Grade Ready? | Notes |
|-----------|-------------------|-------|
| `standards` table schema | ✅ Ready | `grade` field is `SMALLINT NOT NULL` — already accommodates any grade |
| `prerequisite_relationships` table | ✅ Ready | Directed edges are grade-agnostic; just add new rows |
| `questions` table schema | ✅ Ready | `standard_code` FK is already grade-aware via code prefix (e.g., `1.OA.A.1`) |
| BKT model (pyBKT) | ⚠️ Needs parameterization | Separate prior/learn/guess/slip values needed per grade; model loading logic needs `grade` parameter |
| Assessment engine (CAT) | ⚠️ Needs adjustment | Assessment length, difficulty stepping, and sampling strategy must be configurable per grade |
| LLM question generation prompts | ⚠️ Needs grade context | Grade-specific system prompts required; reading level, number ranges, context vocabulary all differ |
| API endpoints (standards, questions, sessions) | ⚠️ Grade param needed | Most endpoints need `grade` as a query/path parameter; student enrollment model needs grade scoping |
| Student skill map UI | ⚠️ Adapts needed | Domain layout, color coding, and mastery indicators carry over; grade-specific ordering |
| Parent dashboard | ⚠️ Multi-child/multi-grade | Parent with children in G1 and G3 needs aggregated view; "grade" label logic per child |
| Teacher dashboard | ⚠️ Multi-grade class support | Some teachers span multiple grade levels; class filter by grade needed |
| Design system tokens | 🔴 Significant new work | Grade 1–2 require enlarged touch targets (60px/48px), larger font minimums, brighter palette extensions |
| TTS integration | 🔴 New subsystem | Grade 1 requires mandatory TTS for all question text; Grade 2–3 need on-demand TTS; not in Grade 4 system |
| Drag-and-drop interaction engine | 🔴 New subsystem | Grade 1–2 require drag counters, picture-based manipulatives; no keyboard input; new component family |
| Interactive clock / coin UI | 🔴 New component | Grade 2 clock interactions and coin denomination UI are novel; no Grade 4 equivalent |
| Fraction visual models | ⚠️ Extend existing | `FractionBuilder.tsx` exists; needs pie, bar, and number line modes for Grade 3; Grade 5 needs mixed number input |
| Coordinate plane | 🔴 New component | Grade 5 graphing on (x,y) coordinate plane; no Grade 4 equivalent |
| Volume manipulative (3D cube builder) | 🔴 New component | Grade 5 volume builder; three.js or CSS 3D transform approach |
| Mascot (Pip) dialogue scripting | ⚠️ Grade 1 expansion | Pip talks more and guides more in Grade 1; existing Pip system needs "verbose mode" and TTS-synced dialogue |
| Session length enforcement | ⚠️ Configurable | Per-grade session caps (12–15 min G1 vs. 35–40 min G5) need grade-aware soft-stop logic |
| Alembic migration pipeline | ✅ Ready | Migration files already structured; add new versions for new grade seed data |

**Summary:** 7 components are fully ready, 8 require moderate extension, and 6 require significant new work. The significant new work is concentrated in Grade 1 (TTS, drag-and-drop engine, picture-based interactions) and Grade 5 (coordinate plane, volume manipulative, complex fraction input). Grades 3 and 5 share the most infrastructure with Grade 4 and should be delivered first.

## 1.4 Estimated Expansion Timeline

This timeline assumes the Grade 4 application is fully built and the team has full context on the codebase. It does not include PoC or MVP phases for Grade 4 itself.

| Phase | Grades | Duration | Key Dependencies |
|-------|--------|----------|-----------------|
| **Phase 1** | Grade 3 + Grade 5 | 5–6 months | Grade 4 fully deployed; BKT parameterization framework |
| **Phase 2** | Grade 2 | 4–5 months | Phase 1 complete; on-demand TTS subsystem; coin/clock UI components |
| **Phase 3** | Grade 1 | 6–7 months | Phase 2 complete; mandatory TTS; drag-and-drop engine; picture-based question formats |
| **Buffer / QA** | All grades | 2 months | Cross-grade regression suite; accessibility audit all grade bands |
| **Total Expansion** | Grades 1–3, 5 | **~17–20 months** | Running parallel to ongoing Grade 4 improvement |

---

# 2. Oregon 2021 Math Standards — Complete Catalog

This section is the authoritative standards reference for the MathPath multi-grade expansion. Every standard is listed with its full official text from the 2021 Oregon Math Standards (v5.2), its domain, cluster, an estimated Depth of Knowledge (DOK) level, and the standards count per domain. No standard text has been abbreviated.

**DOK Level Key (Webb's Framework):**
- **DOK 1** — Recall and Reproduction: Identify, recall, recognize, use, measure
- **DOK 2** — Skills and Concepts: Apply procedure, classify, organize, estimate, interpret, compare
- **DOK 3** — Strategic Thinking: Plan, justify, assess reasonableness, formulate, analyze, multi-step
- **DOK 4** — Extended Thinking: Design, connect, synthesize across contexts (rarely in elementary; noted where applicable)

---

## 2.1 Grade 1 Standards (22 Standards)

### Grade 1 Overview — Critical Areas of Focus

The four critical areas of focus for Grade 1 mathematics, as defined by the Oregon Department of Education, are:

1. **Developing understanding of addition and subtraction strategies for addition and subtraction within 20.** Students develop, discuss, and use efficient, accurate, and generalizable methods to add within 100 and subtract multiples of 10. They use properties of addition (commutativity and associativity) and the relationship between addition and subtraction to solve problems.

2. **Developing understanding of whole-number relationships and place value, including grouping in tens and ones.** Students compare two two-digit numbers and understand that the two digits of a two-digit number represent amounts of tens and ones.

3. **Developing understanding of linear measurement and measuring lengths as iterating length units.** Students develop an understanding of the meaning and processes of measurement, expressing the length of an object as a whole number of length units.

4. **Reasoning about attributes of, and composing and decomposing geometric shapes.** Students compose and decompose plane or solid figures and understand that the figures may retain their overall size during such transformations.

### Grade 1 Standards — Full Listing

#### Domain: 1.OA — Algebraic Reasoning: Operations (8 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 1.OA.A.1 | Represent and solve problems involving addition and subtraction | Use addition and subtraction within 20 to solve and represent problems in authentic contexts involving situations of adding to, taking from, putting together, taking apart, and comparing, with unknowns in all positions. | 2 |
| 1.OA.A.2 | Represent and solve problems involving addition and subtraction | Solve problems that call for addition of three whole numbers whose sum is less than or equal to 20, using concrete objects, drawings, and equations with a symbol for the unknown number to represent the problem. | 2 |
| 1.OA.B.3 | Understand and apply properties of operations and the relationship between addition and subtraction | Apply properties of operations as strategies to add and subtract. Examples: If 8 + 3 = 11 is known, then 3 + 8 = 11 is also known (Commutative property of addition). To add 2 + 6 + 4, the second two numbers can be added to make a ten, so 2 + 6 + 4 = 2 + 10 = 12 (Associative property of addition). | 2 |
| 1.OA.B.4 | Understand and apply properties of operations and the relationship between addition and subtraction | Understand subtraction as an unknown-addend problem. For example, subtract 10 – 8 by finding the number that makes 10 when added to 8. | 2 |
| 1.OA.C.5 | Add and subtract within 20 | Relate counting to addition and subtraction (e.g., by counting on 2 to add 2). | 1 |
| 1.OA.C.6 | Add and subtract within 20 | Add and subtract within 20, demonstrating fluency for addition and subtraction within 10. Use strategies such as counting on; making ten (e.g., 8 + 6 = 8 + 2 + 4 = 10 + 4 = 14); decomposing a number leading to a ten (e.g., 13 – 4 = 13 – 3 – 1 = 10 – 1 = 9); using the relationship between addition and subtraction (e.g., knowing that 8 + 4 = 12, one knows 12 – 8 = 4); and creating equivalent but easier or known sums (e.g., adding 6 + 7 by creating the known equivalent 6 + 6 + 1 = 12 + 1 = 13). Use accurate, efficient, and flexible strategies. | 2 |
| 1.OA.D.7 | Work with addition and subtraction equations | Use the meaning of the equal sign to determine whether equations involving addition and subtraction are true or false. For example, which of the following equations are true and which are false? 6 = 6, 7 = 8 – 1, 5 + 2 = 2 + 5, 4 + 1 = 5 + 2. | 2 |
| 1.OA.D.8 | Work with addition and subtraction equations | Determine the unknown whole number in an addition or subtraction equation relating three whole numbers. For example, determine the unknown number that makes the equation true in each of the equations 8 + ? = 11, 5 = ? – 3, 6 + 6 = ?. | 2 |

**Domain Total: 8 standards**

#### Domain: 1.NBT — Numeric Reasoning: Base Ten Arithmetic (6 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 1.NBT.A.1 | Extend the counting sequence | Count to 120, starting at any number less than 120. In this range, read and write numerals and represent a number of objects with a written numeral. | 1 |
| 1.NBT.B.2 | Understand place value | Understand that the two digits of a two-digit number represent amounts of tens and ones. Understand the following as special cases: (a) 10 can be thought of as a bundle of ten ones — called a "ten"; (b) The numbers from 11 to 19 are composed of a ten and one, two, three, four, five, six, seven, eight, or nine ones; (c) The numbers 10, 20, 30, 40, 50, 60, 70, 80, 90 refer to one, two, three, four, five, six, seven, eight, or nine tens (and 0 ones). | 2 |
| 1.NBT.B.3 | Understand place value | Compare two two-digit numbers based on meanings of the tens and ones digits, recording the results of comparisons with the symbols >, =, and <. | 2 |
| 1.NBT.C.4 | Use place value understanding and properties of operations to add and subtract | Add within 100, including adding a two-digit number and a one-digit number, and adding a two-digit number and a multiple of 10, using concrete models or drawings and strategies based on place value, properties of operations, and/or the relationship between addition and subtraction; relate the strategy to a written method and explain the reasoning used. Understand that in adding two-digit numbers, one adds tens and tens, ones and ones; and sometimes it is necessary to compose a ten. | 2 |
| 1.NBT.C.5 | Use place value understanding and properties of operations to add and subtract | Given a two-digit number, mentally find 10 more or 10 less than the number, without having to count; explain the reasoning used. | 2 |
| 1.NBT.C.6 | Use place value understanding and properties of operations to add and subtract | Subtract multiples of 10 in the range 10–90 from multiples of 10 in the range 10–90 (positive or zero differences), using concrete models or drawings and strategies based on place value, properties of operations, and/or the relationship between addition and subtraction; relate the strategy to a written method and explain the reasoning used. | 2 |

**Domain Total: 6 standards**

#### Domain: 1.GM — Geometric Reasoning and Measurement (6 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 1.GM.A.1 | Reason with shapes and their attributes | Distinguish between defining attributes (e.g., triangles are closed and three-sided) versus non-defining attributes (e.g., color, orientation, overall size); build and draw shapes to possess defining attributes. | 2 |
| 1.GM.A.2 | Reason with shapes and their attributes | Compose two-dimensional shapes (rectangles, squares, trapezoids, triangles, half-circles, and quarter-circles) or three-dimensional shapes (cubes, right rectangular prisms, right circular cones, and right circular cylinders) to create a composite shape, and compose new shapes from the composite shape. | 2 |
| 1.GM.A.3 | Reason with shapes and their attributes | Partition circles and rectangles into two and four equal shares, describe the shares using the words halves, fourths, and quarters, and use the phrases half of, fourth of, and quarter of. Describe the whole as two of, or four of the shares. Understand for these examples that decomposing into more equal shares creates smaller shares. | 2 |
| 1.GM.B.4 | Measure lengths indirectly and by iterating length units | Order three objects by length; compare the lengths of two objects indirectly by using a third object. | 2 |
| 1.GM.B.5 | Measure lengths indirectly and by iterating length units | Express the length of an object as a whole number of length units, by laying multiple copies of a shorter object (the length unit) end to end; understand that the length measurement of an object is the number of same-size length units that span it with no gaps or overlaps. | 2 |
| 1.GM.C.6 | Tell and write time | Tell and write time in hours and half-hours using analog and digital clocks. | 1 |

**Domain Total: 6 standards**

#### Domain: 1.DR — Data Reasoning (2 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 1.DR.A.1 | Formulate questions and collect data | Generate questions to investigate situations within the classroom. Collect and consider data visually by organizing and sorting data up to three categories to answer investigative questions. | 2 |
| 1.DR.B.2 | Analyze data and interpret results | Analyze data sets with up to three categories by interpreting picture graphs and tally charts. Interpret information presented to answer investigative questions about "how many more" and "how many less." | 2 |

**Domain Total: 2 standards**

### Grade 1 Domain Summary

| Domain | Standards Count |
|--------|----------------|
| OA — Algebraic Reasoning: Operations | 8 |
| NBT — Numeric Reasoning: Base Ten Arithmetic | 6 |
| GM — Geometric Reasoning and Measurement | 6 |
| DR — Data Reasoning | 2 |
| **Total** | **22** |

---

## 2.2 Grade 2 Standards (26 Standards)

### Grade 2 Overview — Critical Areas of Focus

The four critical areas of focus for Grade 2 mathematics, as defined by the Oregon Department of Education, are:

1. **Extending understanding of base-ten notation.** Students extend their understanding of the base-ten system. This includes ideas of counting in fives, tens, and multiples of hundreds, tens, and ones, as well as number relationships involving these units, including comparing. Students understand multidigit numbers (up to 1000) written in base-ten notation, recognizing that the digits in each place represent amounts of thousands, hundreds, tens, or ones (e.g., 853 is 8 hundreds + 5 tens + 3 ones).

2. **Building fluency with addition and subtraction.** Students use their understanding of addition to develop fluency with addition and subtraction within 100. They solve problems within 1000 by applying their understanding of models for addition and subtraction, and they develop, discuss, and use efficient, accurate, and generalizable methods to compute sums and differences of whole numbers in base-ten notation, using their understanding of place value and the properties of operations.

3. **Using standard units of measure.** Students recognize the need for standard length measures. They use rulers and other measurement tools with the understanding that linear measure involves an iteration of units. They recognize that the smaller the unit, the more iterations they need to cover a given length.

4. **Describing and analyzing shapes.** Students describe and analyze shapes by examining their sides and angles. Students investigate, describe, and reason about decomposing and combining shapes to make other shapes. Through building, drawing, and analyzing two- and three-dimensional shapes, students develop a foundation for understanding area, volume, congruence, similarity, and symmetry.

### Grade 2 Standards — Full Listing

#### Domain: 2.OA — Algebraic Reasoning: Operations (4 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 2.OA.A.1 | Represent and solve problems involving addition and subtraction | Use addition and subtraction within 100 to solve one- and two-step problems in authentic contexts involving situations of adding to, taking from, putting together, taking apart, and comparing, with unknowns in all positions, e.g., by using drawings and equations with a symbol for the unknown number to represent the problem. | 2 |
| 2.OA.B.2 | Add and subtract within 20 | Fluently add and subtract within 20 using accurate, efficient, and flexible strategies. By end of Grade 2, know from memory all sums of two one-digit numbers. | 1 |
| 2.OA.C.3 | Work with equal groups of objects to gain foundations for multiplication | Determine whether a group of objects (up to 20) has an odd or even number of members, e.g., by pairing objects or counting them by 2s; record the answer using a drawing or equation with a symbol for an unknown. | 2 |
| 2.OA.C.4 | Work with equal groups of objects to gain foundations for multiplication | Use addition to find the total number of objects arranged in rectangular arrays with up to 5 rows and up to 5 columns; write an equation to express the total as a sum of equal addends. | 2 |

**Domain Total: 4 standards**

#### Domain: 2.NBT — Numeric Reasoning: Base Ten Arithmetic (9 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 2.NBT.A.1 | Understand place value | Understand that the three digits of a three-digit number represent amounts of hundreds, tens, and ones; e.g., 706 equals 7 hundreds, 0 tens, and 6 ones. Understand the following as special cases: (a) 100 can be thought of as a bundle of ten tens — called a "hundred"; (b) The numbers 100, 200, 300, 400, 500, 600, 700, 800, 900 refer to one, two, three, four, five, six, seven, eight, or nine hundreds (and 0 tens and 0 ones). | 2 |
| 2.NBT.A.2 | Understand place value | Count within 1000; skip-count by 5s, 10s, and 100s. | 1 |
| 2.NBT.A.3 | Understand place value | Read and write numbers to 1000 using base-ten numerals, number names, and expanded form. | 1 |
| 2.NBT.A.4 | Understand place value | Compare two three-digit numbers based on meanings of the hundreds, tens, and ones digits, using >, =, and < symbols to record the results of comparisons. | 2 |
| 2.NBT.B.5 | Use place value understanding and properties of operations to add and subtract | Fluently add and subtract within 100 using strategies based on place value, properties of operations, and/or the relationship between addition and subtraction. | 1 |
| 2.NBT.B.6 | Use place value understanding and properties of operations to add and subtract | Add up to four two-digit numbers using strategies based on place value and properties of operations. | 2 |
| 2.NBT.B.7 | Use place value understanding and properties of operations to add and subtract | Add and subtract within 1000, using concrete models or drawings and strategies based on place value, properties of operations, and/or the relationship between addition and subtraction; relate the strategy to a written method. Understand that in adding or subtracting three-digit numbers, one adds or subtracts hundreds and hundreds, tens and tens, ones and ones; and sometimes it is necessary to compose or decompose tens or hundreds. | 2 |
| 2.NBT.B.8 | Use place value understanding and properties of operations to add and subtract | Mentally add 10 or 100 to a given number 100–900, and mentally subtract 10 or 100 from a given number 100–900. | 2 |
| 2.NBT.B.9 | Use place value understanding and properties of operations to add and subtract | Explain why addition and subtraction strategies work, using place value and the properties of operations. | 3 |

**Domain Total: 9 standards**

#### Domain: 2.GM — Geometric Reasoning and Measurement (11 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 2.GM.A.1 | Reason with shapes and their attributes | Recognize and draw shapes having specified attributes, such as a given number of angles or a given number of equal faces. Identify triangles, quadrilaterals, pentagons, hexagons, and cubes. | 2 |
| 2.GM.A.2 | Reason with shapes and their attributes | Partition a rectangle into rows and columns of same-size squares and count to find the total number of them. | 2 |
| 2.GM.A.3 | Reason with shapes and their attributes | Partition circles and rectangles into two, three, or four equal parts, describe the parts using the words halves, thirds, half of, a third of, etc., and describe the whole as two halves, three thirds, four fourths. Recognize that equal parts of identical wholes need not have the same shape. | 2 |
| 2.GM.B.4 | Measure and estimate lengths in standard units | Measure the length of an object by selecting and using appropriate tools such as rulers, yardsticks, meter sticks, and measuring tapes. | 1 |
| 2.GM.B.5 | Measure and estimate lengths in standard units | Measure the length of an object twice, using length units of different lengths for the two measurements; describe how the two measurements relate to the size of the unit chosen. | 2 |
| 2.GM.B.6 | Measure and estimate lengths in standard units | Estimate lengths using units of inches, feet, yards, centimeters, and meters. | 2 |
| 2.GM.B.7 | Measure and estimate lengths in standard units | Measure to determine how much longer one object is than another, expressing the length difference in terms of a standard length unit. | 2 |
| 2.GM.C.8 | Relate addition and subtraction to length | Use addition and subtraction within 100 to solve word problems involving lengths that are given in the same units, e.g., by using drawings (such as drawings of rulers) and equations with a symbol for the unknown number to represent the problem. | 2 |
| 2.GM.C.9 | Relate addition and subtraction to length | Represent whole numbers as lengths from 0 on a number line diagram with equally spaced points corresponding to the numbers 0, 1, 2, …, and represent whole-number sums and differences within 100 on a number line diagram. | 2 |
| 2.GM.D.10 | Work with time and money | Tell and write time from analog and digital clocks to the nearest five minutes, using a.m. and p.m. | 1 |
| 2.GM.D.11 | Work with time and money | Solve problems involving dollar bills, quarters, dimes, nickels, and pennies, using $ and ¢ symbols appropriately. Example: If you have 2 dimes and 3 pennies, how many cents do you have? | 2 |

**Domain Total: 11 standards**

#### Domain: 2.DR — Data Reasoning (2 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 2.DR.A.1 | Formulate questions and collect data | Generate questions to investigate situations within the classroom; collect and consider data using measurements with whole-number units. Draw a picture graph and a bar graph (with single-unit scale) to represent a data set with up to four categories. | 2 |
| 2.DR.B.2 | Analyze data and interpret results | Analyze data by interpreting picture graphs and bar graphs with a single-unit scale. Interpret information presented to answer investigative questions, including "how many more" and "how many less." | 2 |

**Domain Total: 2 standards**

### Grade 2 Domain Summary

| Domain | Standards Count |
|--------|----------------|
| OA — Algebraic Reasoning: Operations | 4 |
| NBT — Numeric Reasoning: Base Ten Arithmetic | 9 |
| GM — Geometric Reasoning and Measurement | 11 |
| DR — Data Reasoning | 2 |
| **Total** | **26** |

---

## 2.3 Grade 3 Standards (25 Standards)

### Grade 3 Overview — Critical Areas of Focus

The four critical areas of focus for Grade 3 mathematics, as defined by the Oregon Department of Education, are:

1. **Developing understanding of multiplication and division and strategies for multiplication and division within 100.** Students develop an understanding of the meanings of multiplication and division of whole numbers through activities and problems involving equal-sized groups, arrays, and area models; multiplication is finding an unknown product, and division is finding an unknown factor in these situations.

2. **Developing understanding of fractions, especially unit fractions (fractions with numerator 1).** Students develop an understanding of fractions, beginning with unit fractions. Students view fractions in general as being built out of unit fractions, and they use fractions along with visual fraction models to represent parts of a whole.

3. **Developing understanding of the structure of rectangular arrays and of area.** Students recognize area as an attribute of two-dimensional regions. They measure the area of a shape by finding the total number of same-size units of area required to cover the shape without gaps or overlaps.

4. **Describing and analyzing two-dimensional shapes.** Students describe, analyze, and compare properties of two-dimensional shapes. They compare and classify shapes by their sides and angles, and connect these with definitions of shapes.

### Grade 3 Standards — Full Listing

#### Domain: 3.OA — Algebraic Reasoning: Operations (9 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 3.OA.A.1 | Represent and solve problems involving multiplication and division | Represent and interpret multiplication of two factors as repeated addition of equal groups, e.g., describe a context in which a total number of things can be expressed as 5 × 7. | 2 |
| 3.OA.A.2 | Represent and solve problems involving multiplication and division | Represent and interpret whole-number quotients of whole numbers as the result of dividing into equal-sized groups, e.g., describe a context in which a number of shares or a number of groups can be expressed as 56 ÷ 8. | 2 |
| 3.OA.A.3 | Represent and solve problems involving multiplication and division | Use multiplication and division within 100 to solve word problems in situations involving equal groups, arrays, and measurement quantities, e.g., by using drawings and equations with a symbol for the unknown number to represent the problem. | 2 |
| 3.OA.A.4 | Represent and solve problems involving multiplication and division | Determine the unknown whole number in a multiplication or division equation relating three whole numbers. For example, determine the unknown number that makes the equation true in each of the equations 8 × ? = 48, 5 = ? ÷ 3, 6 × 6 = ?. | 2 |
| 3.OA.B.5 | Understand properties of multiplication and the relationship between multiplication and division | Apply properties of operations as strategies to multiply and divide. Examples: If 6 × 4 = 24 is known, then 4 × 6 = 24 is also known (Commutative property of multiplication). 3 × 5 × 2 can be found by 3 × 5 = 15, then 15 × 2 = 30, or by 5 × 2 = 10, then 3 × 10 = 30 (Associative property of multiplication). Knowing that 8 × 5 = 40 and 8 × 2 = 16, one can find 8 × 7 as 8 × (5 + 2) = (8 × 5) + (8 × 2) = 40 + 16 = 56 (Distributive property). | 2 |
| 3.OA.B.6 | Understand properties of multiplication and the relationship between multiplication and division | Understand division as an unknown-factor problem. For example, find 32 ÷ 8 by finding the number that makes 32 when multiplied by 8. | 2 |
| 3.OA.C.7 | Multiply and divide within 100 | Fluently multiply and divide within 100, using strategies such as the relationship between multiplication and division (e.g., knowing that 8 × 5 = 40, one knows 40 ÷ 5 = 8) or properties of operations. By the end of Grade 3, know from memory all products of two one-digit numbers. Use accurate, efficient, and flexible strategies. | 1 |
| 3.OA.D.8 | Solve problems involving the four operations, and identify and explain patterns in arithmetic | Solve two-step word problems posed in authentic contexts using the four operations, representing these problems using equations with a letter standing for the unknown quantity. Assess the reasonableness of answers using mental computation and estimation strategies including rounding. | 3 |
| 3.OA.D.9 | Solve problems involving the four operations, and identify and explain patterns in arithmetic | Identify arithmetic patterns (including patterns in the addition table or multiplication table), and explain them using properties of operations. For example, observe that 4 times a number is always even, and explain why 4 times a number can be decomposed into two equal addends. | 3 |

**Domain Total: 9 standards**

#### Domain: 3.NBT — Numeric Reasoning: Base Ten Arithmetic (3 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 3.NBT.A.1 | Use place value understanding and properties of operations to perform multi-digit arithmetic | Use place value understanding to round whole numbers to the nearest 10 or 100. Apply rounding to estimate solutions to authentic problems within 1000. | 2 |
| 3.NBT.A.2 | Use place value understanding and properties of operations to perform multi-digit arithmetic | Fluently add and subtract within 1000 using strategies and algorithms based on place value, properties of operations, and/or the relationship between addition and subtraction. Use accurate, efficient, and flexible strategies. | 1 |
| 3.NBT.A.3 | Use place value understanding and properties of operations to perform multi-digit arithmetic | Multiply one-digit whole numbers by multiples of 10 in the range 10–90 (e.g., 9 × 80, 5 × 60) using strategies based on place value and properties of operations. | 2 |

**Domain Total: 3 standards**

#### Domain: 3.NF — Numeric Reasoning: Fractions (3 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 3.NF.A.1 | Develop understanding of fractions as numbers | Understand the concept of a unit fraction. Explain that a unit fraction represents one part of a whole that has been partitioned into equal parts. Explain how multiple copies of a unit fraction are put together to form a non-unit fraction. For example, 1/4 is the unit fraction that represents one part when a whole is partitioned into 4 equal parts, and 3/4 is the fraction that represents 3 copies of 1/4. | 2 |
| 3.NF.A.2 | Develop understanding of fractions as numbers | Understand a fraction as a number on the number line; represent fractions on a number line diagram. (a) Represent a fraction 1/b on a number line diagram by defining the interval from 0 to 1 as the whole and partitioning it into b equal parts. Recognize that each part has size 1/b and that the endpoint of the part based at 0 locates the number 1/b on the number line. (b) Represent a fraction a/b on a number line diagram by marking off a lengths 1/b from 0. Recognize that the resulting interval has size a/b and that its endpoint locates the number a/b on the number line. | 2 |
| 3.NF.A.3 | Develop understanding of fractions as numbers | Explain equivalence of fractions in special cases, and compare fractions by reasoning about their size. (a) Understand two fractions as equivalent (equal) if they are the same size, or the same point on a number line. (b) Recognize and generate simple equivalent fractions, e.g., 1/2 = 2/4, 4/6 = 2/3. Explain why the fractions are equivalent, e.g., by using a visual fraction model. (c) Express whole numbers as fractions, and recognize fractions that are equivalent to whole numbers. Examples: Express 3 in the form 3 = 3/1; recognize that 6/1 = 6; locate 4/4 and 1 at the same point of a number line diagram. (d) Compare two fractions with the same numerator or the same denominator by reasoning about their size. Recognize that comparisons are valid only when the two fractions refer to the same whole. Record the results of comparisons with the symbols >, =, or <, and justify the conclusions, e.g., by using a visual fraction model. | 3 |

**Domain Total: 3 standards**

#### Domain: 3.GM — Geometric Reasoning and Measurement (8 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 3.GM.A.1 | Reason with shapes and their attributes | Understand that shapes in different categories (e.g., rhombuses, rectangles, and others) may share attributes (e.g., having four sides), and that the shared attributes can define a larger category (e.g., quadrilaterals). Recognize rhombuses, rectangles, and squares as examples of quadrilaterals, and draw examples of quadrilaterals that do not belong to any of these subcategories. | 2 |
| 3.GM.A.2 | Reason with shapes and their attributes | Partition shapes into parts with equal areas. Express the area of each part as a unit fraction of the whole. For example, partition a shape into 4 parts with equal area, and describe the area of each part as 1/4 of the area of the shape. | 2 |
| 3.GM.B.3 | Solve problems involving measurement and estimation of intervals of time, liquid volumes, and masses of objects | Tell and write time to the nearest minute and measure time intervals in minutes. Solve word problems involving addition and subtraction of time intervals in minutes, e.g., by representing the problem on a number line diagram. | 2 |
| 3.GM.B.4 | Solve problems involving measurement and estimation of intervals of time, liquid volumes, and masses of objects | Measure and estimate liquid volumes and masses of objects using standard units of grams (g), kilograms (kg), and liters (l). Add, subtract, multiply, or divide to solve one-step word problems involving masses or volumes that are given in the same units, e.g., by using drawings (such as a beaker with a measurement scale) to represent the problem. | 2 |
| 3.GM.C.5 | Geometric measurement: understand concepts of area and relate area to multiplication and to addition | Recognize area as an attribute of plane figures and understand concepts of area measurement. (a) A square with side length 1 unit, called "a unit square," is said to have "one square unit" of area, and can be used to measure area. (b) A plane figure which can be covered without gaps or overlaps by n unit squares is said to have an area of n square units. | 2 |
| 3.GM.C.6 | Geometric measurement: understand concepts of area and relate area to multiplication and to addition | Measure areas by counting unit squares (square cm, square m, square in, square ft, and improvised units). Measure areas of rectangles and other rectilinear figures by counting and using standard and non-standard unit squares. | 1 |
| 3.GM.C.7 | Geometric measurement: understand concepts of area and relate area to multiplication and to addition | Relate area to the operations of multiplication and addition. (a) Find the area of a rectangle with whole-number side lengths by tiling it, and show that the area is the same as would be found by multiplying the side lengths. (b) Multiply side lengths to find areas of rectangles with whole-number side lengths in the context of solving real world and mathematical problems, and represent whole-number products as rectangular areas in mathematical reasoning. (c) Use tiling to show in a concrete case that the area of a rectangle with whole-number side lengths a and b + c is the sum of a × b and a × c. Use area models to represent the distributive property in mathematical reasoning. (d) Recognize area as additive. Find areas of rectilinear figures by decomposing them into non-overlapping rectangles and adding the areas of the non-overlapping parts, applying this technique to solve real world problems. | 2 |
| 3.GM.D.8 | Geometric measurement: recognize perimeter as an attribute of plane figures and distinguish between linear and area measures | Solve real world and mathematical problems involving perimeters of polygons, including finding the perimeter given the side lengths, finding an unknown side length, and exhibiting rectangles with the same perimeter and different areas or with the same area and different perimeters. | 3 |

**Domain Total: 8 standards**

#### Domain: 3.DR — Data Reasoning (2 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 3.DR.A.1 | Formulate questions and collect data | Generate questions to investigate situations within the classroom. Collect and consider measurement data using scaled picture graphs and scaled bar graphs with several categories. | 2 |
| 3.DR.B.2 | Analyze data and interpret results | Analyze measurement data represented in a scaled picture graph or scaled bar graph with several categories, by interpreting information presented to answer investigative questions. Solve one- and two-step "how many more" and "how many less" problems using information presented in scaled bar graphs. | 2 |

**Domain Total: 2 standards**

### Grade 3 Domain Summary

| Domain | Standards Count |
|--------|----------------|
| OA — Algebraic Reasoning: Operations | 9 |
| NBT — Numeric Reasoning: Base Ten Arithmetic | 3 |
| NF — Numeric Reasoning: Fractions | 3 |
| GM — Geometric Reasoning and Measurement | 8 |
| DR — Data Reasoning | 2 |
| **Total** | **25** |

---

## 2.4 Grade 5 Standards (26 Standards)

### Grade 5 Overview — Critical Areas of Focus

The three critical areas of focus for Grade 5 mathematics, as defined by the Oregon Department of Education, are:

1. **Developing fluency with addition and subtraction of fractions, and developing understanding of the multiplication of fractions and of division of fractions in limited cases (unit fractions divided by whole numbers and whole numbers divided by unit fractions).** Students apply their understanding of fractions and fraction models to represent the addition and subtraction of fractions with unlike denominators as equivalent calculations with like denominators. They develop fluency in calculating sums and differences of fractions, and make reasonable estimates of them.

2. **Extending division to 2-digit divisors, integrating decimal fractions into the place value system and developing understanding of operations with decimals to hundredths, and developing fluency with whole number and decimal operations.** Students develop understanding of why division procedures work based on the meaning of base-ten numerals and properties of operations.

3. **Developing understanding of volume.** Students recognize volume as an attribute of three-dimensional space. They understand that volume can be measured by finding the total number of same-size units of volume required to fill the space without gaps or overlaps. They understand that a 1-unit by 1-unit by 1-unit cube is the standard unit for measuring volume.

### Grade 5 Standards — Full Listing

#### Domain: 5.OA — Algebraic Reasoning: Operations (3 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 5.OA.A.1 | Write and interpret numerical expressions | Write and evaluate numerical expressions that include parentheses, brackets, or braces in numerical expressions, and evaluate expressions with these symbols. | 2 |
| 5.OA.A.2 | Write and interpret numerical expressions | Write simple expressions that record calculations with numbers, and interpret numerical expressions without evaluating them. For example, express the calculation "add 8 and 7, then multiply by 2" as 2 × (8 + 7). Recognize that 3 × (18932 + 921) is three times as large as 18932 + 921, without having to calculate the indicated sum or product. | 2 |
| 5.OA.B.3 | Analyze patterns and relationships | Generate two numerical patterns using two given rules. Identify apparent relationships between corresponding terms. Form ordered pairs consisting of corresponding terms from the two patterns, and graph the ordered pairs on a coordinate plane. For example, given the rule "Add 3" and the starting number 0, and given the rule "Add 6" and the starting number 0, generate terms in the resulting sequences, and observe that the terms in one sequence are twice the corresponding terms in the other sequence. Explain informally why this is so. | 3 |

**Domain Total: 3 standards**

#### Domain: 5.NBT — Numeric Reasoning: Base Ten Arithmetic (7 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 5.NBT.A.1 | Understand the place value system | Recognize that in a multi-digit number, a digit in one place represents 10 times as much as it represents in the place to its right and 1/10 of what it represents in the place to its left. | 2 |
| 5.NBT.A.2 | Understand the place value system | Explain patterns in the number of zeros of the product when multiplying a number by powers of 10, and explain patterns in the placement of the decimal point when a decimal is multiplied or divided by a power of 10. Use whole-number exponents to denote powers of 10. | 2 |
| 5.NBT.A.3 | Understand the place value system | Read, write, and compare decimals to thousandths. (a) Read and write decimals to thousandths using base-ten numerals, number names, and expanded form, e.g., 347.392 = 3 × 100 + 4 × 10 + 7 × 1 + 3 × (1/10) + 9 × (1/100) + 2 × (1/1000). (b) Compare two decimals to thousandths based on meanings of the digits in each place, using >, =, and < symbols to record the results of comparisons. | 2 |
| 5.NBT.A.4 | Understand the place value system | Use place value understanding to round decimals to any place. | 2 |
| 5.NBT.B.5 | Perform operations with multi-digit whole numbers and with decimals to hundredths | Fluently multiply multi-digit whole numbers using the standard algorithm. Use accurate, efficient, and flexible strategies. | 1 |
| 5.NBT.B.6 | Perform operations with multi-digit whole numbers and with decimals to hundredths | Find whole-number quotients and remainders of whole numbers with up to four-digit dividends and two-digit divisors, using strategies based on place value, the properties of operations, and/or the relationship between multiplication and division. Illustrate and explain the calculation by using equations, rectangular arrays, and/or area models. | 2 |
| 5.NBT.B.7 | Perform operations with multi-digit whole numbers and with decimals to hundredths | Add, subtract, multiply, and divide decimals to hundredths, using concrete models or drawings and strategies based on place value, properties of operations, and/or the relationship between addition and subtraction; relate the strategy to a written method and explain the reasoning used. | 2 |

**Domain Total: 7 standards**

#### Domain: 5.NF — Numeric Reasoning: Fractions (7 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 5.NF.A.1 | Use equivalent fractions as a strategy to add and subtract fractions | Add and subtract fractions with unlike denominators (including mixed numbers) by replacing given fractions with equivalent fractions in such a way as to produce an equivalent sum or difference of fractions with like denominators. For example, 2/3 + 5/4 = 8/12 + 15/12 = 23/12. (In general, a/b + c/d = (ad + bc)/bd.) | 2 |
| 5.NF.A.2 | Use equivalent fractions as a strategy to add and subtract fractions | Solve word problems involving addition and subtraction of fractions referring to the same whole, including cases of unlike denominators, e.g., by using visual fraction models or equations to represent the problem. Use benchmark fractions and number sense of fractions to estimate mentally and assess the reasonableness of answers. For example, recognize an incorrect result 2/5 + 1/2 = 3/7, by observing that 3/7 < 1/2. | 3 |
| 5.NF.B.3 | Apply and extend previous understandings of multiplication and division to multiply and divide fractions | Interpret a fraction as division of the numerator by the denominator (a/b = a ÷ b). Solve word problems involving division of whole numbers leading to answers in the form of fractions or mixed numbers, e.g., by using visual fraction models or equations to represent the problem. For example, interpret 3/4 as the result of dividing 3 by 4, noting that 3/4 multiplied by 4 equals 3, and that when 3 wholes are shared equally among 4 people each person has a share of size 3/4. | 3 |
| 5.NF.B.4 | Apply and extend previous understandings of multiplication and division to multiply and divide fractions | Apply and extend previous understandings of multiplication to multiply a fraction or whole number by a fraction. (a) Interpret the product (a/b) × q as a parts of a partition of q into b equal parts; equivalently, as the result of a sequence of operations a × q ÷ b. For example, use a visual fraction model to show (2/3) × 4 = 8/3, and create a story context for this equation. Do the same with (2/3) × (4/5) = 8/15. (In general, (a/b) × (c/d) = ac/bd.) (b) Find the area of a rectangle with fractional side lengths by tiling it with unit squares of the appropriate unit fraction side lengths, and show that the area is the same as would be found by multiplying the side lengths. Multiply fractional side lengths to find areas of rectangles, and represent fraction products as rectangular areas. | 3 |
| 5.NF.B.5 | Apply and extend previous understandings of multiplication and division to multiply and divide fractions | Interpret multiplication as scaling (resizing), by: (a) Comparing the size of a product to the size of one factor on the basis of the size of the other factor, without performing the indicated multiplication. (b) Explaining why multiplying a given number by a fraction greater than 1 results in a product greater than the given number (recognizing multiplication by whole numbers greater than 1 as a familiar case); explaining why multiplying a given number by a fraction less than 1 results in a product smaller than the given number; and relating the principle of fraction equivalence a/b = (n × a)/(n × b) to the effect of multiplying a/b by 1. | 3 |
| 5.NF.B.6 | Apply and extend previous understandings of multiplication and division to multiply and divide fractions | Solve real world problems involving multiplication of fractions and mixed numbers, e.g., by using visual fraction models or equations to represent the problem. | 3 |
| 5.NF.B.7 | Apply and extend previous understandings of multiplication and division to multiply and divide fractions | Apply and extend previous understandings of division to divide unit fractions by whole numbers and whole numbers by unit fractions. (a) Interpret division of a unit fraction by a non-zero whole number, and compute such quotients. For example, create a story context for (1/3) ÷ 4, and use a visual fraction model to show the quotient. Use the relationship between multiplication and division to explain that (1/3) ÷ 4 = 1/12 because (1/12) × 4 = 1/3. (b) Interpret division of a whole number by a unit fraction, and compute such quotients. For example, create a story context for 4 ÷ (1/5), and use a visual fraction model to show the quotient. Use the relationship between multiplication and division to explain that 4 ÷ (1/5) = 20 because 20 × (1/5) = 4. (c) Solve real world problems involving division of unit fractions by non-zero whole numbers and division of whole numbers by unit fractions, e.g., by using visual fraction models and equations to represent the problem. For example, how much chocolate will each person get if 3 people share 1/2 lb of chocolate equally? How many 1/3-cup servings are in 2 cups of raisins? | 3 |

**Domain Total: 7 standards**

#### Domain: 5.GM — Geometric Reasoning and Measurement (7 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 5.GM.A.1 | Graph points on the coordinate plane to solve real-world and mathematical problems | Use a pair of perpendicular number lines, called axes, to define a coordinate system, with the intersection of the lines (the origin) arranged to coincide with the 0 on each line and a given point in the plane located by using an ordered pair of numbers, called its coordinates. Understand that the first number indicates how far to travel from the origin in the direction of one axis, and the second number indicates how far to travel in the direction of the second axis, with the convention that the names of the two axes and the coordinates correspond (e.g., x-axis and x-coordinate, y-axis and y-coordinate). | 2 |
| 5.GM.A.2 | Graph points on the coordinate plane to solve real-world and mathematical problems | Represent authentic contexts and mathematical problems by graphing points in the first quadrant of the coordinate plane, and interpret coordinate values of points in the context of the situation. | 3 |
| 5.GM.B.3 | Classify two-dimensional figures into categories based on their properties | Understand that attributes belonging to a category of two-dimensional figures also belong to all subcategories of that category. For example, all rectangles have four right angles and squares are rectangles, so all squares have four right angles. | 2 |
| 5.GM.C.4 | Convert like measurement units within a given measurement system | Convert among different-sized standard measurement units within a given measurement system (e.g., convert 5 cm to 0.05 m), and use these conversions in solving multi-step, real world problems. | 2 |
| 5.GM.D.5 | Geometric measurement: understand concepts of volume and relate volume to multiplication and to addition | Recognize volume as an attribute of solid figures and understand concepts of volume measurement. (a) A cube with side length 1 unit, called a "unit cube," is said to have "one cubic unit" of volume, and can be used to measure volume. (b) A solid figure which can be packed without gaps or overlaps using n unit cubes is said to have a volume of n cubic units. | 2 |
| 5.GM.D.6 | Geometric measurement: understand concepts of volume and relate volume to multiplication and to addition | Measure volumes by counting unit cubes, using cubic cm, cubic in, cubic ft, and improvised units. | 1 |
| 5.GM.D.7 | Geometric measurement: understand concepts of volume and relate volume to multiplication and to addition | Relate volume to the operations of multiplication and addition and solve real world and mathematical problems involving volume. (a) Find the volume of a right rectangular prism with whole-number side lengths by packing it with unit cubes, and show that the volume is the same as would be found by multiplying the edge lengths, equivalently by multiplying the height by the area of the base. Represent threefold whole-number products as volumes, e.g., to represent the associative property of multiplication. (b) Apply the formulas V = l × w × h and V = b × h for rectangular prisms to find volumes of right rectangular prisms with whole-number edge lengths in the context of solving real world and mathematical problems. (c) Recognize volume as additive. Find volumes of solid figures composed of two non-overlapping right rectangular prisms by adding the volumes of the non-overlapping parts, applying this technique to solve real world problems. | 3 |

**Domain Total: 7 standards**

#### Domain: 5.DR — Data Reasoning (2 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| 5.DR.A.1 | Formulate questions and collect data | Generate questions to investigate situations within the classroom. Determine strategies to collect, consider, and display data, including data involving fractions (e.g., 1/2, 1/4, 1/8), using line plots. | 2 |
| 5.DR.B.2 | Analyze data and interpret results | Analyze graphical representations including line plots showing data with fractional increments. Describe the distribution of the data and interpret information presented to answer investigative questions. | 3 |

**Domain Total: 2 standards**

### Grade 5 Domain Summary

| Domain | Standards Count |
|--------|----------------|
| OA — Algebraic Reasoning: Operations | 3 |
| NBT — Numeric Reasoning: Base Ten Arithmetic | 7 |
| NF — Numeric Reasoning: Fractions | 7 |
| GM — Geometric Reasoning and Measurement | 7 |
| DR — Data Reasoning | 2 |
| **Total** | **26** |

---

# 3. Prerequisite Relationship Graphs (Per Grade)

The prerequisite relationship graph is the core data structure that powers MathPath's adaptive sequencing. Every edge in this graph represents a pedagogically validated dependency: a student who has not mastered the prerequisite standard should not be presented with the dependent standard in their learning plan. The Grade 4 PRD (FR-2.4) established this pattern with 9 inter-grade edges and approximately 20 intra-grade edges. This section extends that graph to all expansion grades using the same directed edge format.

**Edge notation:** `[prerequisite_code] → [dependent_code]  (rationale)`

A directed edge `A → B` means: *"Standard A must be mastered before Standard B is attempted."*

**Strength classification:**
- **HARD** — the dependent standard is mathematically impossible without the prerequisite (e.g., fractions on a number line requires understanding the number line)
- **SOFT** — the dependent standard is much harder without the prerequisite but not impossible with scaffolding

---

## 3.1 Grade 1 Prerequisite Graph

### Inter-Grade Prerequisites: Kindergarten → Grade 1 (8 edges)

These 8 Kindergarten standards serve as the prerequisite gate for the Grade 1 diagnostic. When a student enters MathPath at Grade 1, the diagnostic samples these K skills alongside Grade 1 content to establish an accurate starting BKT state.

```
K.OA.A.2 → 1.OA.A.1  (HARD — add/subtract within 10 is the foundation for extending to within 20; without K.OA.A.2, 1.OA.A.1 problems are inaccessible)
K.OA.A.5 → 1.OA.C.6  (HARD — fluency within 5 is the entry point for building fluency within 10, which is the core target of 1.OA.C.6)
K.OA.A.4 → 1.OA.C.6  (SOFT — "make 10" strategy is explicitly named in 1.OA.C.6's strategy list; student without K.OA.A.4 lacks a key tool)
K.NCC.A.3 → 1.NBT.A.1  (HARD — reading/writing numbers 0–20 is prerequisite for extending to 120; numeral recognition is foundational)
K.NCC.B.4 → 1.OA.A.1  (SOFT — connecting counting to cardinality is needed to represent addition/subtraction problems using objects)
K.NCC.C.7 → 1.NBT.B.3  (HARD — comparing numbers 1–10 as written numerals is the prerequisite for comparing two-digit numbers)
K.NBT.A.1 → 1.NBT.B.2  (HARD — composing/decomposing 11–19 as "ten and some ones" directly feeds understanding of tens and ones in any two-digit number)
K.GM.B.6 → 1.GM.A.2   (SOFT — composing common shapes to form larger shapes is the K-level entry to the Grade 1 composite shape standard)
```

### Intra-Grade Prerequisites: Grade 1 Internal Edges (18 edges)

These edges define the sequencing within Grade 1 content. They govern the order in which standards appear in a student's learning plan once Grade 1 content begins.

```
1.OA.B.4 → 1.OA.D.8  (HARD — understanding subtraction as unknown-addend is prerequisite for determining unknown in addition/subtraction equations)
1.OA.C.5 → 1.OA.C.6  (HARD — relating counting to addition/subtraction is the conceptual bridge before developing fluency strategies)
1.OA.B.3 → 1.OA.C.6  (SOFT — applying properties of operations is needed to use efficient strategies in 1.OA.C.6)
1.OA.A.1 → 1.OA.A.2  (HARD — solving problems within 20 with two numbers before extending to three-number addition)
1.OA.C.6 → 1.OA.D.7  (SOFT — fluency with operations informs ability to evaluate whether equations are true or false)
1.OA.C.6 → 1.OA.D.8  (HARD — solving for unknowns requires operational fluency so cognitive load remains on the equation structure)
1.NBT.B.2 → 1.NBT.B.3  (HARD — understanding tens and ones is prerequisite for comparing two-digit numbers based on place value meaning)
1.NBT.A.1 → 1.NBT.B.2  (SOFT — counting and writing numerals to 120 provides the range within which place value understanding is developed)
1.NBT.B.2 → 1.NBT.C.4  (HARD — understanding that tens and ones compose numbers is prerequisite for adding within 100 using place value strategies)
1.NBT.B.2 → 1.NBT.C.5  (HARD — mental +10/−10 requires understanding of what "one ten" means in a two-digit number)
1.NBT.C.4 → 1.NBT.C.6  (SOFT — adding using place value sets up the analogous reasoning for subtracting multiples of 10)
1.NBT.B.3 → 1.NBT.C.5  (SOFT — comparison of two-digit numbers reinforces place value reasoning needed for mental ten-more/ten-less)
1.GM.A.1 → 1.GM.A.2  (HARD — distinguishing defining vs. non-defining attributes is prerequisite for intentionally composing shapes with specific properties)
1.GM.A.2 → 1.GM.A.3  (SOFT — composing shapes into larger shapes provides spatial reasoning foundation before partitioning)
1.GM.B.4 → 1.GM.B.5  (HARD — ordering objects by length is conceptually prerequisite for expressing length as a count of units)
1.OA.A.1 → 1.DR.A.1  (SOFT — representing addition/subtraction situations supports formulating investigative questions about data)
1.DR.A.1 → 1.DR.B.2  (HARD — formulating questions and collecting data must precede analysis and interpretation)
1.GM.C.6 → 1.DR.B.2  (SOFT — reading a clock is used as context in data displays; time awareness supports data interpretation)
```

### Visual Dependency Summary — Grade 1

The Grade 1 skill graph has three major "gateway" standards that gate large portions of the learning sequence:

1. **K.OA.A.2 / K.OA.A.5** (Kindergarten prerequisites) → gates all of 1.OA.A and 1.OA.C
2. **1.NBT.B.2** (Understanding tens and ones) → gates 1.NBT.B.3, 1.NBT.C.4, 1.NBT.C.5, and 1.NBT.C.6. This is the single most critical Grade 1 standard for downstream readiness.
3. **1.OA.C.6** (Fluency within 20, within 10) → gates 1.OA.D.7 and 1.OA.D.8

If a student shows a gap in **1.NBT.B.2**, the adaptive engine should immediately back-remediate to **K.NBT.A.1** before proceeding with any NBT strand standards.

---

## 3.2 Grade 2 Prerequisite Graph

### Inter-Grade Prerequisites: Grade 1 → Grade 2 (8 edges)

```
1.OA.C.6 → 2.OA.B.2  (HARD — Grade 2 requires fluency within 20 as a recalled fact; 1.OA.C.6 is the development standard for that fluency)
1.OA.D.8 → 2.OA.A.1  (SOFT — determining unknowns in three-number equations is direct preparation for setting up one/two-step word problems)
1.NBT.B.2 → 2.NBT.A.1  (HARD — understanding ten ones as a "ten" is the conceptual prerequisite for understanding ten tens as a "hundred")
1.NBT.C.4 → 2.NBT.B.5  (HARD — adding within 100 using place value strategies in Grade 1 is the prerequisite for fluency within 100 in Grade 2)
1.NBT.C.5 → 2.NBT.B.8  (HARD — mental +10/−10 for two-digit numbers directly extends to mental +10/+100/−10/−100 for three-digit numbers)
1.GM.A.3 → 2.GM.A.3  (HARD — partitioning circles and rectangles into halves and fourths is prerequisite for extending to thirds and other equal parts)
1.GM.B.5 → 2.GM.B.4  (HARD — expressing length in non-standard units establishes the concept of iteration; measuring with standard tools requires this foundation)
1.GM.C.6 → 2.GM.D.10  (HARD — telling time to hours and half-hours is prerequisite for extending to nearest 5 minutes)
```

### Intra-Grade Prerequisites: Grade 2 Internal Edges (20 edges)

```
2.OA.B.2 → 2.OA.A.1  (HARD — fluency within 20 enables the computation needed for one/two-step problems within 100)
2.OA.C.3 → 2.OA.C.4  (SOFT — odd/even understanding through pairing provides foundational thinking for rectangular arrays as equal groups)
2.NBT.A.1 → 2.NBT.A.2  (SOFT — understanding three-digit place value supports skip-counting by 5s, 10s, and 100s within 1000)
2.NBT.A.1 → 2.NBT.A.3  (HARD — reading and writing numbers to 1000 requires understanding what each digit position represents)
2.NBT.A.3 → 2.NBT.A.4  (HARD — must be able to read three-digit numbers to compare them using >, =, <)
2.NBT.A.1 → 2.NBT.B.7  (HARD — adding/subtracting within 1000 using place value requires understanding hundreds/tens/ones)
2.NBT.B.5 → 2.NBT.B.6  (SOFT — fluency within 100 supports adding up to four two-digit numbers efficiently)
2.NBT.B.5 → 2.NBT.B.7  (SOFT — fluency within 100 is the foundation before extending to within 1000)
2.NBT.A.4 → 2.NBT.B.7  (SOFT — comparing three-digit numbers informs the reasonableness check when adding/subtracting within 1000)
2.NBT.B.7 → 2.NBT.B.8  (SOFT — understanding how to add/subtract within 1000 supports mental +10/+100 generalization)
2.NBT.B.5 → 2.NBT.B.9  (HARD — explaining why strategies work requires first being able to execute the strategies reliably)
2.GM.A.1 → 2.GM.A.2  (SOFT — recognizing shapes with specified attributes is prerequisite for partitioning a rectangle into rows and columns)
2.GM.A.2 → 2.GM.A.3  (SOFT — partitioning a rectangle into same-size squares provides the spatial model for equal-share partitioning into halves/thirds/fourths)
2.GM.B.4 → 2.GM.B.5  (HARD — measuring with appropriate tools is prerequisite for comparing measurements across different unit sizes)
2.GM.B.4 → 2.GM.B.6  (HARD — measuring actual lengths provides referents needed for estimation)
2.GM.B.4 → 2.GM.B.7  (HARD — measuring individual objects with standard units is prerequisite for comparing two measurements)
2.GM.C.9 → 2.GM.C.8  (SOFT — representing lengths on a number line supports the addition/subtraction of lengths as a number line operation)
2.OA.A.1 → 2.GM.C.8  (HARD — solving word problems with addition/subtraction within 100 is the computational core of length problem-solving)
2.GM.D.10 → 2.GM.D.11  (SOFT — time and money are co-located as measurement topics; procedural fluency with time supports fluency with money conventions)
2.DR.A.1 → 2.DR.B.2  (HARD — collecting and displaying data must precede analysis and interpretation)
```

### Visual Dependency Summary — Grade 2

Three gateway standards dominate Grade 2:

1. **2.NBT.A.1** (Understanding hundreds/tens/ones) → gates the entire NBT strand (2.NBT.A.2 through 2.NBT.B.9). This is Grade 2's structural foundation.
2. **2.OA.B.2** (Fluency within 20) → gates 2.OA.A.1, which in turn gates 2.GM.C.8. A student without fact fluency cannot access multi-step word problems.
3. **2.GM.B.4** (Measure with standard tools) → gates 2.GM.B.5, B.6, and B.7. All measurement comparison standards depend on basic measurement tool proficiency.

If a student in Grade 2 shows a gap in **1.NBT.B.2** (tens and ones), the system must immediately remediate before attempting any 2.NBT content.

---

## 3.3 Grade 3 Prerequisite Graph

### Inter-Grade Prerequisites: Grade 2 → Grade 3 (8 edges)

```
2.OA.B.2 → 3.OA.D.8  (HARD — two-step problems with four operations require fact fluency within 20 so cognitive load can focus on problem structure)
2.OA.C.4 → 3.OA.A.1  (HARD — understanding rectangular arrays as sums of equal addends is the direct conceptual bridge to multiplication as repeated addition)
2.NBT.A.4 → 3.NBT.A.1  (HARD — comparing three-digit numbers is prerequisite for rounding within 1000; rounding requires understanding relative magnitude)
2.NBT.B.5 → 3.NBT.A.2  (HARD — fluency within 100 is the prerequisite layer for developing fluency within 1000)
2.NBT.B.7 → 3.NBT.A.2  (SOFT — experience adding/subtracting within 1000 provides the base for fluency at that same range)
2.GM.A.3 → 3.NF.A.1  (HARD — partitioning shapes into equal parts in Grade 2 is the geometric foundation for the unit fraction concept)
2.GM.C.9 → 3.NF.A.2  (HARD — representing whole-number lengths on a number line is prerequisite for placing fractions on a number line)
2.GM.B.4 → 3.GM.B.4  (SOFT — measuring with standard measurement tools is prerequisite for measuring liquid volumes and masses with standard units)
```

### Intra-Grade Prerequisites: Grade 3 Internal Edges (22 edges)

```
3.OA.A.1 → 3.OA.A.3  (HARD — representing multiplication as equal groups is prerequisite for using multiplication to solve word problems)
3.OA.A.2 → 3.OA.A.3  (HARD — representing division as equal groups is prerequisite for using division to solve word problems)
3.OA.A.1 → 3.OA.A.4  (HARD — understanding multiplication as equal groups is prerequisite for identifying the unknown factor in a multiplication equation)
3.OA.A.2 → 3.OA.A.4  (HARD — understanding division as equal groups is prerequisite for identifying the unknown factor in a division equation)
3.OA.B.5 → 3.OA.C.7  (SOFT — applying properties of operations enables more efficient and flexible strategies for fluency)
3.OA.B.6 → 3.OA.C.7  (HARD — understanding division as unknown-factor is prerequisite for the relationship-based strategies in 3.OA.C.7)
3.OA.A.3 → 3.OA.C.7  (SOFT — using multiplication/division in word problem contexts builds exposure needed for fluency)
3.OA.C.7 → 3.OA.D.8  (HARD — fluent multiplication/division facts are prerequisite for multi-step problems involving four operations)
3.OA.D.8 → 3.OA.D.9  (SOFT — solving problems with four operations provides the computational experience to identify and explain arithmetic patterns)
3.OA.A.1 → 3.NBT.A.3  (HARD — multiplication as repeated addition is prerequisite for multiplying one-digit numbers by multiples of 10)
3.NBT.A.2 → 3.OA.D.8  (SOFT — fluency within 1000 enables the addition/subtraction components of two-step problems)
3.NF.A.1 → 3.NF.A.2  (HARD — understanding unit fractions as equal parts is prerequisite for placing those fractions on a number line)
3.NF.A.1 → 3.NF.A.3  (HARD — understanding what a fraction represents is prerequisite for reasoning about equivalence)
3.NF.A.2 → 3.NF.A.3  (HARD — number line representation supports the point-on-number-line definition of fraction equivalence)
3.GM.A.1 → 3.GM.A.2  (SOFT — understanding shared attributes of shapes supports partitioning shapes with understanding of equal areas)
3.NF.A.1 → 3.GM.A.2  (HARD — expressing area of equal parts as a unit fraction requires understanding unit fractions)
3.GM.C.5 → 3.GM.C.6  (HARD — understanding the concept of area is prerequisite for measuring area by counting unit squares)
3.GM.C.6 → 3.GM.C.7  (HARD — measuring area by counting is prerequisite for relating area to multiplication)
3.OA.A.1 → 3.GM.C.7  (HARD — multiplication as repeated equal groups is the mathematical basis for the area formula)
3.GM.C.7 → 3.GM.D.8  (SOFT — area problems and perimeter problems co-occur in Grade 3; area mastery enables combined area/perimeter reasoning)
3.DR.A.1 → 3.DR.B.2  (HARD — collecting and displaying data must precede analysis and interpretation)
3.OA.A.3 → 3.DR.B.2  (SOFT — solving "how many more/less" problems using multiplication/division applies directly to scaled graph problems)
```

### Visual Dependency Summary — Grade 3

Grade 3 has the most complex internal dependency graph of any expansion grade due to the introduction of both multiplication and fractions.

The three critical gateway chains:

1. **Multiplication chain:** `3.OA.A.1 + 3.OA.A.2 → 3.OA.A.3 → 3.OA.A.4 → 3.OA.B.5/B.6 → 3.OA.C.7 → 3.OA.D.8`
   This is the spine of Grade 3. Every other Grade 3 standard in OA depends on the multiplication conceptual chain. 3.OA.C.7 (fluency) is the most critical single standard in Grade 3 because it is also a prerequisite for Grade 4 (see existing PRD FR-2.4).

2. **Fractions chain:** `2.GM.A.3 (prerequisite) → 3.NF.A.1 → 3.NF.A.2 → 3.NF.A.3`
   Fractions begin in Grade 3 and the conceptual chain is linear. A student who cannot partition shapes equally (2.GM.A.3) will be blocked from the entire NF strand.

3. **Area chain:** `3.GM.C.5 → 3.GM.C.6 → 3.GM.C.7`
   This chain culminates in a standard that is also a prerequisite for Grade 4 (3.GM.C.7 → 4.GM.D.9).

---

## 3.4 Grade 5 Prerequisite Graph

### Inter-Grade Prerequisites: Grade 4 → Grade 5 (9 edges)

These edges match the pattern documented in the expansion research data and mirror the structure used for Grade 4's 9 Grade 3 prerequisite edges.

```
4.OA.A.3  → 5.OA.A.1  (HARD — solving multistep problems with the four operations is prerequisite for writing and evaluating expressions with parentheses)
4.NBT.B.5 → 5.NBT.B.5  (HARD — multiplying up to 4 digits by 1 digit and two 2-digit numbers is prerequisite for fluent multi-digit multiplication)
4.NBT.B.6 → 5.NBT.B.6  (HARD — long division with 1-digit divisors is the direct prerequisite for extending to 2-digit divisors)
4.NF.A.1  → 5.NF.A.1  (HARD — generating equivalent fractions is the core tool for converting unlike denominators before adding/subtracting)
4.NF.A.2  → 5.NF.B.5  (SOFT — comparing fractions by reasoning about size provides the conceptual basis for understanding multiplication as scaling)
4.NF.B.3  → 5.NF.A.1  (HARD — adding/subtracting fractions with like denominators is prerequisite for extending to unlike denominators)
4.NF.B.4  → 5.NF.B.4  (HARD — multiplying a fraction by a whole number is the prerequisite before multiplying fraction by fraction)
4.NF.C.7  → 5.NBT.A.3  (HARD — comparing decimals to hundredths is prerequisite for reading/writing/comparing decimals to thousandths)
4.GM.D.9  → 5.GM.D.7  (SOFT — area and perimeter formulas for rectangles provide the reasoning foundation for extending to volume problems)
```

### Intra-Grade Prerequisites: Grade 5 Internal Edges (20 edges)

```
5.OA.A.1 → 5.OA.A.2  (SOFT — writing and evaluating expressions with parentheses is prerequisite for writing expressions that record calculations)
5.OA.A.2 → 5.OA.B.3  (SOFT — interpreting expressions without evaluating them supports identifying relationships between two numerical patterns)
5.NBT.A.1 → 5.NBT.A.2  (HARD — understanding place value relationships between adjacent places is prerequisite for explaining powers-of-10 patterns)
5.NBT.A.2 → 5.NBT.A.3  (SOFT — understanding decimal placement from powers of 10 supports reading and writing decimals to thousandths)
5.NBT.A.3 → 5.NBT.A.4  (HARD — must be able to read and understand decimal place values before rounding to any decimal place)
5.NBT.A.4 → 5.NBT.B.7  (SOFT — rounding decimals to any place supports estimation and reasonableness checking in decimal operations)
5.NBT.B.5 → 5.NBT.B.6  (SOFT — fluency with multi-digit whole-number multiplication supports the multiplication component within long division)
5.NBT.B.5 → 5.NBT.B.7  (SOFT — fluent whole-number multiplication is prerequisite for extending multiplication to decimals)
5.NF.A.1 → 5.NF.A.2  (HARD — computing sums/differences of fractions with unlike denominators is prerequisite for solving word problems requiring those computations)
5.NF.B.3 → 5.NF.B.4  (SOFT — interpreting fractions as division prepares conceptual ground for multiplying fraction by fraction)
5.NF.B.4 → 5.NF.B.5  (HARD — understanding how to multiply fractions is prerequisite for interpreting multiplication as scaling/resizing)
5.NF.B.4 → 5.NF.B.6  (HARD — multiplying fractions and whole numbers by fractions is prerequisite for solving real-world multiplication problems)
5.NF.B.5 → 5.NF.B.6  (SOFT — understanding scaling supports modeling real-world fraction multiplication problems)
5.NF.A.1 → 5.NF.B.7  (SOFT — fraction fluency with unlike denominators provides computational readiness for division of unit fractions)
5.GM.A.1 → 5.GM.A.2  (HARD — understanding the coordinate system (x-axis, y-axis, ordered pairs) is prerequisite for graphing points in authentic contexts)
5.OA.B.3 → 5.GM.A.2  (HARD — generating ordered pairs from numerical patterns is the computational content that feeds into coordinate graphing)
5.GM.D.5 → 5.GM.D.6  (HARD — understanding the concept of volume is prerequisite for measuring volume by counting unit cubes)
5.GM.D.6 → 5.GM.D.7  (HARD — measuring volume by counting cubes is prerequisite for connecting that counting to the multiplication formula)
5.DR.A.1 → 5.DR.B.2  (HARD — collecting and displaying fractional data using line plots is prerequisite for analyzing and describing the distribution)
5.NF.A.1 → 5.DR.A.1  (SOFT — adding and subtracting fractions with unlike denominators supports working with fractional data in line plots)
```

### Visual Dependency Summary — Grade 5

Grade 5 has three parallel conceptual tracks that converge in complex multi-domain applications:

1. **Decimal/place value track:** `5.NBT.A.1 → 5.NBT.A.2 → 5.NBT.A.3 → 5.NBT.A.4 → 5.NBT.B.7`
   This is Grade 5's NBT spine. Students who lack Grade 4 decimal foundations (4.NF.C.7) will be blocked immediately.

2. **Fraction operations track:** `5.NF.A.1 → 5.NF.A.2 → 5.NF.B.3 → 5.NF.B.4 → 5.NF.B.5/B.6 → 5.NF.B.7`
   This is the deepest dependency chain in Grade 5. Every NF standard feeds the next. Fraction mastery from Grade 4 (4.NF.A.1 and 4.NF.B.3) are hard prerequisites that gate this entire chain.

3. **Coordinate/volume track:** `5.OA.B.3 + 5.GM.A.1 → 5.GM.A.2` and `5.GM.D.5 → 5.GM.D.6 → 5.GM.D.7`
   These converge in the GM strand. The volume chain is linear and conceptually clean. The coordinate plane chain requires both algebraic pattern generation (OA) and geometric understanding (GM).

---

# 4. Question Bank Requirements (Per Grade)

## 4.1 Methodology: Scaling from Grade 4 Baseline

The Grade 4 Stage 1 PRD established a seed question bank of **132 questions** for 29 Grade 4 standards plus 9 prerequisite standards (38 total). This yields approximately **3.47 questions per standard** as the baseline seed density.

For expansion grades, we apply a grade-adjusted formula:

**Questions per standard (seed):** 3.5–5 questions per standard, with the following adjustments:
- More questions per standard for DOK 1 (recall) standards that require many format variants
- More questions per standard for heavy-traffic prerequisite standards (those with 3+ dependent edges)
- Fewer questions for DOK 3 standards where LLM generation fills the gap after initial seed

**Target seed question counts:**

| Grade | Standards (incl. prereqs from prior grade) | Base Density | **Target Seed Questions** |
|-------|---------------------------------------------|-------------|---------------------------|
| 1 | 22 grade + 8 K prereqs = 30 total | 4.0/std | **120 questions** |
| 2 | 26 grade + 8 G1 prereqs = 34 total | 4.0/std | **136 questions** |
| 3 | 25 grade + 8 G2 prereqs = 33 total | 4.5/std | **148 questions** |
| 5 | 26 grade + 9 G4 prereqs = 35 total | 4.5/std | **158 questions** |
| **Total new seed questions** | | | **562 questions** |

Grade 3 and Grade 5 receive a slightly higher density (4.5 vs. 4.0) because their content is more complex and requires more format variety, especially for multiplication facts and multi-step fraction problems.

---

## 4.2 Grade 1 Question Bank

**Target: 120 seed questions across 30 standards (22 Grade 1 + 8 K prerequisites)**

### Question Type Distribution

| Question Type | % of Bank | Question Count | Example |
|--------------|-----------|---------------|---------|
| Picture-based tap-to-select | 35% | 42 | "How many apples are there? Tap the number." (image of 7 apples, answer tiles 5/6/7/8) |
| Drag-and-drop (objects/counters) | 25% | 30 | "Drag 4 more frogs into the pond." (8 frogs already shown; student drags 4 more from a bank) |
| Number tile tap (select the answer) | 20% | 24 | "What is 6 + 3? Tap the right number." (no typing; large tile buttons with numerals) |
| True/false tap | 10% | 12 | "Is 5 + 3 = 9? Tap YES or NO." (large tap targets) |
| Audio-first ordering | 10% | 12 | Pip says: "Put these numbers in order from smallest to biggest." (student drags number tiles) |

**No keyboard text entry for Grade 1.** All input is tap or drag. All question text is TTS-read by Pip automatically before the student can interact.

### Reading Level Requirements
- **Flesch-Kincaid Grade Level: ≤1.0** for written text (written text is supplementary to images/audio, not primary)
- Word count per question stem: ≤8 words
- No multi-clause sentences
- All numbers written as numerals (not words) in question text
- Context words drawn from: school, food, toys, animals, nature — familiar objects visible in the accompanying image

### Domain Distribution

| Domain | Standards | Target Questions | Notes |
|--------|-----------|-----------------|-------|
| 1.OA | 8 | 42 | Highest volume; addition/subtraction is Grade 1's core |
| 1.NBT | 6 | 30 | Place value concepts need visual tens/ones frames |
| 1.GM | 6 | 30 | Shapes, measurement, clocks — highly visual |
| 1.DR | 2 | 10 | Picture graphs, tally charts |
| K prereqs | 8 | 8 | 1 question per K prerequisite for diagnostic sampling |
| **Total** | **30** | **120** | |

### LLM Question Generation Prompt Requirements for Grade 1

When the LLM pipeline (via LangGraph) generates additional Grade 1 questions beyond the seed bank, the system prompt for `question_gen_v1.0.jinja2` MUST enforce:

1. **Reading level enforcement:** "This question is for a 6–7 year old child in Grade 1 who may not yet be able to read. The question stem MUST be no longer than 8 words. Use the simplest possible English words (Dolch sight word list). Do not assume the child can read the question — Pip will read it aloud via text-to-speech."
2. **Image description requirement:** "For every Grade 1 question, you MUST include an `image_description` field in your JSON output. This field describes the accompanying visual that the UI will render. Example: '7 cartoon apples arranged in two rows on a white background.' Visual must directly support answering the question."
3. **Number range enforcement:** "All numbers in this question MUST be within the range 0–20 for OA standards, and 0–120 for NBT standards."
4. **Answer format restriction:** "Answer options MUST be presented as 4 large selectable tiles (not text input). For drag-and-drop questions, specify the draggable objects and target zone in the question JSON."
5. **No fractions or decimals:** "Grade 1 does not include fractions or decimals. Do not use any fractional notation."
6. **Context vocabulary:** "Use only these context types: counting objects (animals, toys, fruit, shapes), simple story problems with named characters (Pip, Sam, Maya), classroom scenarios. Never use abstract notation without a picture."

---

## 4.3 Grade 2 Question Bank

**Target: 136 seed questions across 34 standards (26 Grade 2 + 8 Grade 1 prerequisites)**

### Question Type Distribution

| Question Type | % of Bank | Question Count | Example |
|--------------|-----------|---------------|---------|
| Simple text + image hybrid | 30% | 41 | "Sam has 34 apples. He gets 28 more. How many does he have now?" (with apple image) |
| Typed numeric entry (1–3 digits) | 25% | 34 | Student types answer using a numpad overlay (no full keyboard needed) |
| Number line drag | 20% | 27 | "Drag the marker to 47 on the number line." (number line from 40–60) |
| Multiple choice (4 tiles) | 15% | 20 | "Which number is greater?" (two three-digit numbers; tap the larger one) |
| Interactive clock/coin | 10% | 14 | Clock: "Set the hands to 3:35." Coins: "Tap the coins that equal 37¢." |

**TTS available on-demand (speaker icon tap)** — not auto-play. Word problems ≤15 words per sentence.

### Reading Level Requirements
- **Flesch-Kincaid Grade Level: 1.5–2.5**
- Sentences: ≤15 words each
- Maximum 2 sentences per question stem
- Numbers: single and double-digit mostly; up to three-digit for comparison and place value standards
- Context: money, time, measurement (rulers, measurement tape), simple arrays

### Domain Distribution

| Domain | Standards | Target Questions | Notes |
|--------|-----------|-----------------|-------|
| 2.OA | 4 | 20 | Word problems; includes two-step |
| 2.NBT | 9 | 45 | Largest domain; place value and computation |
| 2.GM | 11 | 55 | Measurement-heavy; clocks and coins need interactive UI |
| 2.DR | 2 | 8 | Bar graphs and picture graphs |
| G1 prereqs | 8 | 8 | 1 question per G1 prerequisite |
| **Total** | **34** | **136** | |

### LLM Question Generation Prompt Requirements for Grade 2

1. **Reading level enforcement:** "Grade 2 student (age 7–8), Flesch-Kincaid ≤2.5. Each sentence ≤15 words. Maximum 2 sentences per question stem. Use simple vocabulary; avoid compound/complex sentences."
2. **Number range:** "OA: within 100. NBT: three-digit numbers up to 1000. GM lengths: realistic inches/feet/centimeters. Time: to nearest 5 minutes. Money: combinations of coins up to $1.00."
3. **No fractions:** "Grade 2 does not include fraction arithmetic. You may use the words 'halves' and 'thirds' in context of partitioning shapes only."
4. **Interactive elements:** "For clock questions, output a `clock_config` JSON object specifying hour and minute hands in degrees. For coin questions, output a `coin_array` specifying denominations and counts. For number line questions, output `number_line_config` with start, end, and target values."
5. **Context vocabulary:** "Use real-world contexts: going to the store, measuring classroom objects, telling time at school, collecting data about pets or sports. Keep characters diverse and inclusive."

---

## 4.4 Grade 3 Question Bank

**Target: 148 seed questions across 33 standards (25 Grade 3 + 8 Grade 2 prerequisites)**

### Question Type Distribution

| Question Type | % of Bank | Question Count | Example |
|--------------|-----------|---------------|---------|
| Word problems (text, 2–4 sentences) | 35% | 52 | "A bakery bakes 8 trays of cookies. Each tray has 9 cookies. How many cookies in all?" |
| Fraction visual models | 20% | 30 | Pie/bar/number line fraction representations; student selects or places fractions |
| Multiplication grid | 15% | 22 | Interactive times table grid; student fills in missing products or factors |
| Numeric entry (multi-digit) | 15% | 22 | "What is 347 + 268? Type your answer." |
| Multiple choice (4 options) | 10% | 15 | "Which fraction is equivalent to 2/4?" (four fraction options displayed as bar models) |
| True/false / yes/no | 5% | 7 | "Is this shape partitioned into equal areas? Tap YES or NO." |

### Reading Level Requirements
- **Flesch-Kincaid Grade Level: 2.0–3.0**
- Word problems: 2–4 sentences; up to 20 words per sentence
- Multiplication vocabulary: "groups of," "rows," "columns," "arrays," "total"
- Fraction vocabulary: "equal parts," "unit fraction," "numerator," "denominator," "equivalent" (with visual support)
- Area/perimeter vocabulary: "square units," "rows," "columns," "side length," "perimeter"

### Domain Distribution

| Domain | Standards | Target Questions | Notes |
|--------|-----------|-----------------|-------|
| 3.OA | 9 | 55 | Multiplication/division is the Grade 3 core; most questions needed |
| 3.NBT | 3 | 15 | Rounding and large arithmetic |
| 3.NF | 3 | 20 | Visual fraction models essential |
| 3.GM | 8 | 40 | Area, perimeter, time, measurement |
| 3.DR | 2 | 10 | Scaled bar/picture graphs |
| G2 prereqs | 8 | 8 | 1 question per G2 prerequisite |
| **Total** | **33** | **148** | |

### LLM Question Generation Prompt Requirements for Grade 3

1. **Reading level:** "Grade 3 student (age 8–9), Flesch-Kincaid 2.0–3.0. Students can read short word problems independently. Use complete sentences with varied structure. Maximum 4 sentences per question."
2. **Multiplication/division context:** "For OA questions, use realistic contexts: equal groups of objects (chairs in rows, eggs in cartons, students in teams), measurement division (sharing equally), arrays (tiles on a floor, seats in a theater). Avoid abstract notation without context."
3. **Fraction visual requirements:** "For every NF question, include a `fraction_visual` field in the JSON output. Specify visual type: 'pie', 'bar_model', or 'number_line'. Specify the whole, numerator, denominator, and any equivalent fraction shown. The UI renders this visual from the JSON spec."
4. **Multiplication table range:** "All multiplication/division facts must be within 100 (products of two single-digit numbers). Do not introduce multi-digit multiplication (that is Grade 4)."
5. **Area/perimeter:** "For area/perimeter questions, specify a `grid_config` JSON object with rows, columns, and unit size. The UI renders an interactive unit square grid."
6. **Authentic context:** "Oregon-specific contexts welcome: Crater Lake, the Columbia River, Oregon Trail history, Portland's farmers markets, coastal tide pools. Do not use brand names."

---

## 4.5 Grade 5 Question Bank

**Target: 158 seed questions across 35 standards (26 Grade 5 + 9 Grade 4 prerequisites)**

### Question Type Distribution

| Question Type | % of Bank | Question Count | Example |
|--------------|-----------|---------------|---------|
| Complex word problems (multi-step) | 35% | 55 | "A recipe uses 2/3 cup of flour per batch. If Amara makes 4½ batches, how many cups of flour does she need?" |
| Fraction/decimal input (including mixed numbers) | 25% | 40 | Fraction builder with mixed number support; decimal input to thousandths |
| Coordinate plane graphing | 15% | 24 | "Graph the point (3, 7) on the coordinate plane. Then plot the next point if the rule is 'add 2 to x and add 4 to y.'" |
| Volume manipulative | 10% | 16 | "Build a rectangular prism that has a volume of 24 cubic units." (3D cube builder) |
| Multiple choice (complex) | 10% | 16 | "Which expression is equivalent to 3 × (18 + 7)?" (four algebraic expressions) |
| Data interpretation (line plots) | 5% | 7 | Fractional line plot with ≥4 data points; student answers comparison/sum/difference questions |

### Reading Level Requirements
- **Flesch-Kincaid Grade Level: 3.5–5.0**
- Word problems: 3–6 sentences; complex vocabulary introduced in context
- Mathematical vocabulary: "exponent," "coordinate plane," "ordered pair," "volume," "unit fraction," "mixed number," "unlike denominators," "scaling"
- Multi-step problems may span a short scenario paragraph before the question

### Domain Distribution

| Domain | Standards | Target Questions | Notes |
|--------|-----------|-----------------|-------|
| 5.OA | 3 | 15 | Expressions with parentheses; coordinate patterns |
| 5.NBT | 7 | 35 | Decimals and multi-digit operations |
| 5.NF | 7 | 50 | Largest content volume; deep fraction work |
| 5.GM | 7 | 40 | Coordinate plane + volume = two major new UI components |
| 5.DR | 2 | 9 | Fractional line plots |
| G4 prereqs | 9 | 9 | 1 question per G4 prerequisite |
| **Total** | **35** | **158** | |

### LLM Question Generation Prompt Requirements for Grade 5

1. **Reading level:** "Grade 5 student (age 10–11), Flesch-Kincaid 3.5–5.0. Students can read multi-sentence word problems. Use complete, varied sentences. May include scenario paragraphs of 2–3 sentences before the question."
2. **Fraction complexity:** "For NF standards, use unlike denominators (not just halves and fourths). Mixed numbers are appropriate. Mixed number input UI supports: whole number field + numerator field + denominator field. Specify `fraction_input_type`: 'simple', 'mixed_number', or 'unlike_denominator'."
3. **Coordinate plane:** "For GM.A standards, include a `coordinate_config` JSON specifying: x-axis range, y-axis range, points to pre-plot (as [(x,y), ...] list), and the student's task (plot, identify, or connect). The UI renders an SVG interactive grid."
4. **Volume:** "For GM.D standards, include a `volume_config` JSON specifying the prism dimensions (l, w, h). The UI renders a 3D CSS-transform cube builder that students interact with to count or build."
5. **Powers of 10:** "For NBT.A.2, use proper superscript notation in the LaTeX output field: 10^2, 10^3, etc. (KaTeX renders this as `10^{2}`). Do not spell out 'ten squared.'"
6. **Authentic complexity:** "Avoid trivial applications. Grade 5 students can handle: multi-step problems requiring two or more operations, problems where reasonableness must be assessed, problems where the solution path is not immediately obvious."

---

# 5. Diagnostic Assessment Parameters (Per Grade)

## 5.1 Overview

The Grade 4 diagnostic is a 35–45 question adaptive assessment that uses Computerized Adaptive Testing (CAT) to estimate BKT initial states across all 29 Grade 4 standards plus 9 Grade 3 prerequisites. The expansion grades follow the same architecture — CAT-based, BKT-initialized — but with grade-specific parameters for assessment length, sampling strategy, difficulty stepping, and accessibility accommodations.

The diagnostic system is implemented in `assessment_service.py`. Grade-specific parameters are loaded from a configuration store (PostgreSQL `assessment_configs` table) keyed by grade level, not hardcoded. This means adding a new grade requires a database INSERT, not a code change.

---

## 5.2 Grade 1 Diagnostic Parameters

**Assessment Length:** 20–25 questions
**Target Duration:** 15–18 minutes
**Attention Span Accommodation:** Maximum 5 consecutive questions before a mandatory "rest point" (Pip celebrates, short animation plays, progress shown visually as stars collected). No timer visible to student.

### Standards Sampling Strategy

| Domain | Standards in Grade | Questions Sampled | Notes |
|--------|-------------------|------------------|-------|
| 1.OA | 8 | 7–8 | OA is Grade 1's heaviest domain; sample all clusters |
| 1.NBT | 6 | 5–6 | Place value is critical for downstream grades |
| 1.GM | 6 | 3–4 | Sample time (1.GM.C.6) and measurement (1.GM.B.4, B.5); shapes optional |
| 1.DR | 2 | 1–2 | Sample 1.DR.B.2 only; 1.DR.A.1 handled implicitly |
| K prereqs | 8 | 4–5 | K.OA.A.2, K.NCC.A.3, K.NBT.A.1, K.NCC.C.7 are critical |
| **Total** | 30 | **20–25** | |

### BKT Initialization Parameters — Grade 1

Grade 1 students have high prior uncertainty — the diagnostic may be their first structured assessment. Parameters reflect conservative priors and slower learning rates typical of early elementary learners.

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `p_prior` (prior mastery) | 0.10 | Grade 1 content is new; assume low baseline mastery |
| `p_learn` (learn rate) | 0.15 | Young learners show strong gains session-to-session but slower within-session learning |
| `p_guess` | 0.25 | Higher than Grade 4 (0.20) because tap-to-select with 4 options = 25% random chance |
| `p_slip` | 0.15 | Young learners have higher slip rates due to attention and fine-motor imprecision |
| Mastery threshold | P(mastery) ≥ 0.80 | Lower threshold than Grade 4 (0.90) to account for higher measurement uncertainty in young learners; confirmed by consecutive correct responses |
| Mastery confirmation | 3 consecutive correct | Require streak before marking mastered |

### CAT Difficulty Stepping

- **Starting difficulty:** DOK 1 always (no entry at DOK 2 for Grade 1)
- **Step up:** 2 consecutive correct → increase to next DOK level or harder problem variant
- **Step down:** 1 incorrect → step back to DOK 1 or simpler variant; never present 2 consecutive DOK 2 questions if student failed previous DOK 2
- **Maximum consecutive same-type questions:** 3 (then switch domain/format to maintain engagement)

### Accessibility Considerations

- **TTS mandatory:** All question text read aloud automatically before interaction is enabled; repeat button always visible
- **Touch targets:** 60px minimum for all interactive elements
- **Visual progress:** Stars collected (not percentage); Pip's facial expression changes with progress
- **Audio:** Correct sound (cheerful chime), incorrect sound (soft neutral tone — not a buzzer); both sounds can be muted by parent
- **Session abort:** If student exits early, diagnostic state is saved; can resume within 48 hours
- **Emoji/image support:** All numbers in questions accompanied by a quantity illustration for DOK 1 OA questions

---

## 5.3 Grade 2 Diagnostic Parameters

**Assessment Length:** 25–30 questions
**Target Duration:** 18–22 minutes
**Attention Span Accommodation:** Rest point every 7 questions; student can tap "Keep Going" to skip

### Standards Sampling Strategy

| Domain | Standards in Grade | Questions Sampled | Notes |
|--------|-------------------|------------------|-------|
| 2.OA | 4 | 4 | Sample all four OA standards |
| 2.NBT | 9 | 8–9 | Full coverage; NBT is Grade 2's dominant domain |
| 2.GM | 11 | 8–9 | Prioritize measurement (B.4–B.7) and time/money (D.10, D.11) |
| 2.DR | 2 | 2 | One picture graph, one bar graph question |
| G1 prereqs | 8 | 3–4 | 1.OA.C.6, 1.NBT.B.2, 1.NBT.C.4 are critical |
| **Total** | 34 | **25–30** | |

### BKT Initialization Parameters — Grade 2

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `p_prior` | 0.12 | Slightly higher than Grade 1; some prior learning assumed |
| `p_learn` | 0.18 | Grade 2 learners show moderate within-session learning gains |
| `p_guess` | 0.22 | Mix of MC (25% chance) and numeric entry (near-zero chance); blended estimate |
| `p_slip` | 0.12 | Attention and fine-motor improving vs. Grade 1 |
| Mastery threshold | P(mastery) ≥ 0.82 | Slightly higher than Grade 1 |
| Mastery confirmation | 3 consecutive correct | |

### CAT Difficulty Stepping

- **Starting difficulty:** DOK 1 or DOK 2 depending on domain (OA starts DOK 2; NBT comparison starts DOK 1)
- **Step up:** 2 consecutive correct → increase difficulty or add numeric entry variant
- **Step down:** 1 incorrect → revert to simpler format (MC instead of numeric entry)
- **Time/money questions:** Adaptive between "read the clock" (DOK 1) and "calculate elapsed time" (DOK 2)

### Accessibility Considerations

- **TTS on-demand:** Speaker icon always visible; tap to hear question read aloud
- **Touch targets:** 48px minimum
- **Numpad overlay:** For numeric entry, a large numpad (not the device keyboard) is shown; digits 0–9, backspace, enter
- **Number line:** Finger-drag interaction; snap to integer positions
- **Clock interaction:** Large analog clock with draggable hour and minute hands; digital readout updates in real time as student adjusts hands

---

## 5.4 Grade 3 Diagnostic Parameters

**Assessment Length:** 28–35 questions
**Target Duration:** 22–28 minutes
**Attention Span Accommodation:** Optional break prompt at midpoint (question 14–17); student can decline

### Standards Sampling Strategy

| Domain | Standards in Grade | Questions Sampled | Notes |
|--------|-------------------|------------------|-------|
| 3.OA | 9 | 9–10 | Multiplication/division must be fully sampled; 3.OA.C.7 gets 2 questions |
| 3.NBT | 3 | 3 | One question per standard |
| 3.NF | 3 | 4 | Fraction domain is new and high-diagnostic-value; 3.NF.A.3 gets 2 questions |
| 3.GM | 8 | 7–8 | Area (3.GM.C.5/C.6/C.7) and perimeter (3.GM.D.8) are critical |
| 3.DR | 2 | 2 | One scaled picture graph, one scaled bar graph |
| G2 prereqs | 8 | 3–4 | 2.OA.C.4, 2.GM.A.3, 2.NBT.B.5 are critical |
| **Total** | 33 | **28–35** | |

### BKT Initialization Parameters — Grade 3

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `p_prior` | 0.15 | Grade 3 students have 2 years of math schooling; more baseline assumed |
| `p_learn` | 0.20 | Learning rates increase with age and cognitive maturity |
| `p_guess` | 0.20 | Standard 4-option MC; numeric entry for computation |
| `p_slip` | 0.10 | Older students show lower slip rates |
| Mastery threshold | P(mastery) ≥ 0.85 | Higher than Grades 1–2 |
| Mastery confirmation | 3 consecutive correct | |

**Separate BKT parameters for multiplication facts (3.OA.C.7):**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `p_prior` | 0.30 | Students entering Grade 3 diagnostic have had some exposure to multiplication |
| `p_learn` | 0.25 | Multiplication facts respond strongly to practice in short bursts |
| `p_guess` | 0.05 | Numeric entry; near-zero guessing |
| `p_slip` | 0.08 | Recall slips are common for partially learned facts |

### CAT Difficulty Stepping

- **Starting difficulty:** DOK 2 for OA (multiplication is the entry); DOK 1 for NBT recall
- **Fraction questions:** Always shown with a visual model first; if student masters visual → abstract notation
- **Step up for multiplication:** Add larger factors (e.g., facts within 25, then within 50, then within 100)
- **Step down:** Revert to visual model support or reduce number range

### Accessibility Considerations

- **TTS on-demand:** Standard speaker icon
- **Fraction visual always shown:** For all NF diagnostic questions, a fraction visual (pie, bar, or number line) accompanies the question even at DOK 2/3 levels
- **Multiplication grid available as reference:** Students may view a partial multiplication table as a hint (tracked as "hint used" in the assessment log)
- **Touch targets:** 44px standard

---

## 5.5 Grade 5 Diagnostic Parameters

**Assessment Length:** 35–45 questions
**Target Duration:** 30–40 minutes
**Attention Span Accommodation:** Optional break prompt at question 20; student can decline; soft session cap at 45 minutes

### Standards Sampling Strategy

| Domain | Standards in Grade | Questions Sampled | Notes |
|--------|-------------------|------------------|-------|
| 5.OA | 3 | 3 | One per standard; 5.OA.B.3 requires coordinate plane |
| 5.NBT | 7 | 7–8 | Decimals are high-priority diagnostic content |
| 5.NF | 7 | 10–12 | Fraction operations are Grade 5's dominant challenge area; oversample |
| 5.GM | 7 | 7–8 | Coordinate plane + volume both need direct sampling |
| 5.DR | 2 | 2 | One fractional line plot interpretation |
| G4 prereqs | 9 | 6–7 | 4.NF.A.1, 4.NF.B.3, 4.NBT.B.5, 4.NF.C.7 are critical |
| **Total** | 35 | **35–45** | |

### BKT Initialization Parameters — Grade 5

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `p_prior` | 0.20 | Aligned with Grade 4 parameters; Grade 5 students have strong prior math experience |
| `p_learn` | 0.22 | Similar to Grade 4; older learners show stable learning rates |
| `p_guess` | 0.18 | Mix of numeric entry and MC; lower than younger grades |
| `p_slip` | 0.08 | Matches Grade 4 slip rate |
| Mastery threshold | P(mastery) ≥ 0.90 | Matches Grade 4; high confidence required |
| Mastery confirmation | 3 consecutive correct | |

**Separate parameters for fraction operations (5.NF standards):**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `p_prior` | 0.15 | Fraction operations with unlike denominators are new and challenging |
| `p_learn` | 0.18 | Fraction mastery is slower to develop than whole-number mastery |
| `p_guess` | 0.05 | Numeric entry primarily; near-zero guessing |
| `p_slip` | 0.10 | Procedure complexity increases slip rate for fractions |

### CAT Difficulty Stepping

- **Starting difficulty:** DOK 2 for most domains; DOK 1 for decimal recognition (5.NBT.A.3)
- **Fraction pathway:** Start with unlike denominator addition (5.NF.A.1) → if mastered, advance to multiplication (5.NF.B.4) → if mastered, advance to division (5.NF.B.7)
- **Step up:** 2 consecutive correct → increase to multi-step problem or remove visual scaffold
- **Step down:** 1 incorrect → add visual model; 2 consecutive incorrect → drop one DOK level

### Accessibility Considerations

- **TTS on-demand:** Identical to Grade 4 experience
- **Fraction builder:** Mixed number input with three separate fields (whole number, numerator, denominator); visual preview of the fraction as a bar model updates as student types
- **Coordinate plane:** Accessible by keyboard (tab to move, arrow keys to adjust coordinates, enter to place point) in addition to touch/mouse
- **Volume builder:** 3D CSS cube builder; can be navigated by keyboard for assistive technology compliance
- **Session resume:** Full state persistence; student can abandon and resume within 7 days

---

# 6. Age-Appropriate UI/UX Requirements

## 6.1 Design System Philosophy for Multi-Grade Support

The Grade 4 design system (docs/09-design-system.md) was built for 9–10-year-old students — sophisticated digital natives who would reject anything "babyish." The Grade 4 principle "Respect the age" manifests as a calm, modern, tween-appropriate aesthetic.

Multi-grade expansion requires that the design system support a **grade-band token layer** — a set of CSS custom properties and Tailwind config extensions that override the base Grade 4 tokens for younger or older grade bands, while sharing the same component architecture. This is implemented as a `GradeThemeProvider` React context that wraps the student app and injects grade-band tokens at the `:root` level.

The principle is: **same components, different tokens.** A `<QuestionCard>` renders identically in every grade; but its font size, touch target size, and color palette variant are controlled by the grade-band token layer injected by `GradeThemeProvider`.

---

## 6.2 Grade 1 UI/UX Requirements (Ages 6–7)

### Core Mandate

Grade 1 students are pre-literate or early readers. The UI cannot assume reading ability. Every piece of text-based content must be accompanied by audio, visual support, or both. This is not a minor accessibility accommodation — it is the fundamental design constraint for Grade 1.

### Text-to-Speech (TTS) Integration

- **Automatic TTS playback** for all question stems, answer labels, and Pip's dialogue — begins 500ms after the question card renders (gives student time to visually orient)
- **Repeat button** (speaker icon, 60px tap target) is always visible and tappable during a question
- **TTS engine:** Amazon Polly (Neural voice: "Joanna" for standard narration, "Matthew" for Pip's voice) — neural voices are significantly more natural than standard for young listeners
- **Read rate:** 85% of standard Polly speed — slightly slower for age-appropriate comprehension
- **Highlighted text sync:** As Polly reads, each word is highlighted in real time (using SSML marks) so emerging readers can follow along
- **Answer tile TTS:** Each answer tile also reads aloud when the student taps it (before confirming) — student hears the answer option before selecting it

### Touch Targets

- **Minimum interactive element size:** 60px × 60px (vs. 44px standard)
- **Minimum spacing between interactive elements:** 16px (to prevent fat-finger errors)
- **Drag targets:** 80px × 80px minimum for drag-and-drop objects; drop zones: 100px × 100px minimum
- **Confirm button:** 80px tall, full width of content area (no missing the confirmation)

### Question Format Requirements

All Grade 1 questions must be one of:

| Format | Description | Implementation |
|--------|-------------|---------------|
| **Picture tap** | Image shows a quantity/shape/scenario; student taps correct answer tile | `<PictureTapQuestion>` component; 4 answer tiles minimum 60px |
| **Drag counter** | Student drags virtual objects (counters, blocks) to fill a ten-frame or sort into groups | `<DragCounterQuestion>` component; drag objects 80px |
| **Number tile tap** | Large numeral tiles; student taps the correct number | `<NumberTileQuestion>` component; tiles 80px × 80px |
| **True/false tap** | Large YES/NO buttons; Pip asks a yes/no question | `<TrueFalseQuestion>` component; YES/NO each 80px × 80px |
| **Ordering drag** | Student drags 3–4 items into sequence (numbers, length order) | `<OrderingDragQuestion>` component |

**Absolutely no keyboard input for Grade 1.** No text fields, no number input boxes.

### Progress Visualization

- **Stars collected:** Each correct answer fills a star on Pip's path; 5 stars = a section complete → confetti animation + Pip dances
- **Path visualization:** Pip walks a winding path through an Oregon-themed scene (forest, coast, mountain); stars glow along the path
- **No numeric percentages, no score counters** — fully visual progress only
- **Session length:** Soft cap at 12 minutes; at 12 minutes, Pip says "You're doing amazing! Let's take a quick break." Break prompt offers: "Keep going" or "Rest now." If student is mid-question, completes the question first.

### Mascot (Pip) — Grade 1 "Verbose Mode"

In Grade 4, Pip appears on significant moments (correct answers, mastery, hints). In Grade 1, Pip is an active co-participant in every question.

- Pip appears in a persistent panel at the top of every question screen (not a popup)
- **Before question:** Pip narrates the question via TTS ("Let's count these apples together!")
- **After correct:** Pip celebrates with an animation + voice ("You got it! That's 7 apples!")
- **After incorrect (first attempt):** Pip offers a scaffold ("Let's count them one by one. Point to each apple with me.") — hint is given automatically, no "ask for hint" required
- **After incorrect (second attempt):** Pip shows the answer with a walkthrough animation ("Watch: 1, 2, 3, 4, 5, 6, 7. There are 7 apples!")
- Pip's voice lines are pre-recorded TTS strings stored in the question bank `pip_dialogue` field

### Color Palette Extensions — Grade 1

The Grade 4 palette uses calm, teal-forward tones. Grade 1 extends the palette with brighter variants while maintaining WCAG AA compliance.

| Token | Grade 4 Value | Grade 1 Override | Purpose |
|-------|--------------|-----------------|---------|
| `--color-primary` | `#01696F` | `#0B8A91` | Slightly brighter teal; still accessible |
| `--color-accent-success` | `#437A22` | `#3DAA1A` | Brighter green for correct feedback |
| `--color-bg-question` | `#F9F8F5` | `#FDFCF8` | Warmer, slightly creamier background |
| `--color-pip-bg` | `#F0F0EB` | `#FFF8E8` | Warm golden background for Pip's panel (friendlier) |
| `--color-star-fill` | N/A | `#F5B400` | Star progress indicators; high saturation |
| `--color-star-empty` | N/A | `#E0DDD5` | Empty star slots |

All color overrides pass WCAG AA contrast checks against the backgrounds on which they appear.

### Typography — Grade 1

| Token | Grade 4 Value | Grade 1 Override |
|-------|--------------|-----------------|
| `--font-size-body` | 16px | **20px** |
| `--font-size-question-number` | 28px | **36px** |
| `--font-size-answer-tile` | 22px | **28px** |
| `--font-weight-body` | 400 | **500** (slightly bolder for readability) |
| `--letter-spacing-body` | 0 | **0.02em** (slightly wider; improves early reader tracking) |
| `--line-height-body` | 1.5 | **1.65** |

Font family unchanged from Grade 4 design system (Inter/system sans-serif).

### Encouragement Timing

- **Frequency:** Every 3 correct answers (vs. every 5 for Grade 4)
- **After every incorrect (first attempt):** Immediate soft encouragement ("That was a hard one! Let's try again.")
- **After correct on retry:** Extra encouragement ("You kept trying — that's what learning looks like!")
- No visible "wrong answer" counts, no progress bars that go backward

---

## 6.3 Grade 2 UI/UX Requirements (Ages 7–8)

### Core Mandate

Grade 2 students are emerging readers. Most can read simple sentences independently, but multi-clause or abstract text remains challenging. TTS is available on-demand (not automatic) — the design assumes the student can attempt reading first, with audio as a fallback.

### TTS Integration

- **On-demand:** Speaker icon (48px) visible on every question; student taps to hear question read aloud
- **NOT auto-play** (unlike Grade 1) — students this age often prefer to read independently
- **TTS still available** for all content; reads the full question including answer options if student taps the speaker icon on an answer tile
- **TTS engine:** Same Amazon Polly Neural configuration as Grade 1, but standard speed (100%)

### Touch Targets

- **Minimum interactive element size:** 48px × 48px
- **Minimum spacing:** 12px between interactive elements
- **Number line handle:** 56px diameter (larger than standard for drag precision)
- **Clock hands (interactive clock):** 48px circular grab area at the end of each hand

### Question Formats

| Format | Description |
|--------|-------------|
| **Simple text + image** | Short word problem (≤2 sentences) with supporting image; 4-option MC or numeric input |
| **Numpad numeric entry** | Student types 1–3 digit answer using a large numpad overlay (NOT device keyboard) |
| **Number line drag** | Student drags a point to the correct position on a labeled number line; line labeled at intervals |
| **Interactive clock** | Student drags clock hands to the correct time; digital readout updates in real time |
| **Coin selection** | Student taps individual coins from a display to select a total value; running total shown |
| **Multiple choice (4 tiles)** | Standard 4-option MC; tiles are 48px minimum height |

**No full-device keyboard for Grade 2.** Numeric input uses the app's numpad overlay. Text is never typed by Grade 2 students.

### Progress Visualization

- Stars and path remain (same as Grade 1) but now also shows a session question counter ("Question 8 of 20")
- Numeric progress is visible but framed positively ("8 questions answered!")
- Session length: soft cap at 15–20 minutes

### Mascot (Pip) — Grade 2 Mode

- Pip appears on a sidebar (not dominant panel) — less intrusive than Grade 1
- **Before question:** Pip says nothing by default; student reads question
- **After correct:** Pip celebrates (animation + short phrase)
- **After incorrect (first attempt):** Pip offers a hint automatically on second attempt (not required to ask)
- **After incorrect (second attempt):** Pip shows a walkthrough
- Pip hints are contextual to the question type (e.g., for clock: "Look at the short hand first — that's the hour hand")

### Typography — Grade 2

| Token | Grade 4 Value | Grade 2 Override |
|-------|--------------|-----------------|
| `--font-size-body` | 16px | **18px** |
| `--font-size-question-number` | 28px | **30px** |
| `--font-size-answer-tile` | 22px | **24px** |
| `--font-weight-body` | 400 | **400** (normal) |
| `--line-height-body` | 1.5 | **1.6** |

### Encouragement Timing

- Every 4–5 correct answers
- After each mastery milestone
- After incorrect on retry: neutral, forward-looking ("Let's try a different approach")

---

## 6.4 Grade 3 UI/UX Requirements (Ages 8–9)

### Core Mandate

Grade 3 students are developing readers who can handle short math word problems independently. The UI transitions toward the Grade 4 pattern while retaining visual supports for the new content domains (fractions, multiplication).

### TTS Integration

- On-demand only (identical to Grade 2)
- Speaker icon standard size (44px)

### Touch Targets

- Standard 44px minimum — matches Grade 4
- Exception: fraction visual models maintain 48px interaction zones (fraction pieces are small; needs precision)

### Question Formats

| Format | Description |
|--------|-------------|
| **Word problem (text)** | Standard word problem; 2–4 sentences; MC or numeric entry |
| **Fraction visual models** | Pie, bar model, or number line fraction; student taps a segment, drags a point, or selects a fraction tile |
| **Multiplication grid** | Interactive times table grid; student taps cells to fill in products or factors |
| **Area grid** | Interactive square-unit grid; student counts or fills units; area displays in real time |
| **Scaled graph** | Bar or picture graph with scale factor (e.g., each picture = 5 items); student reads and interprets |
| **Multi-digit computation** | Full numpad entry for 3–4 digit answers |
| **True/false (statement)** | Written mathematical statement; student evaluates and taps TRUE/FALSE |

### Fraction Visual Standards

For every 3.NF standard question:
- A fraction visual is ALWAYS displayed (even for DOK 2–3 questions)
- Three visual types cycle based on standard: `3.NF.A.1` → pie model; `3.NF.A.2` → number line; `3.NF.A.3` → bar model comparison
- Student can switch visual type using a toggle (pie/bar/number line) — this is a scaffolding choice, not a setting
- Fraction notation (`a/b`) always displayed alongside the visual once introduced; never visual-only after initial introduction

### Typography — Grade 3

| Token | Grade 4 Value | Grade 3 Override |
|-------|--------------|-----------------|
| `--font-size-body` | 16px | **16px** (same as Grade 4) |
| `--font-size-question-number` | 28px | **28px** (same) |
| `--font-size-fraction-numerals` | 22px | **20px** |
| `--font-weight-body` | 400 | **400** |

Grade 3 is effectively at parity with Grade 4 for typography — the transition is complete by this grade band.

### Session Length

- Soft cap at 20–25 minutes
- Break prompt at 20 minutes if session is still active
- Can be extended by parent in account settings (useful for homework sessions)

### Mascot (Pip) — Grade 3 Mode

- Pip is a sidebar widget (same as Grade 2)
- Pip's hints for fraction and multiplication questions are more contextual and structured:
  - Fraction hint: "Look at how many equal pieces the whole is cut into — that's your denominator"
  - Multiplication hint: "Think of 6 × 7 as 6 groups of 7 — or use the grid to find it"
- Pip does NOT narrate every question — only on hint and mastery events

---

## 6.5 Grade 5 UI/UX Requirements (Ages 10–11)

### Core Mandate

Grade 5 students are fully literate and use the same core UI patterns as Grade 4. The UI/UX differences are driven entirely by content requirements (coordinate plane, volume builder, complex fraction input) rather than reading level or attention span accommodations.

### TTS Integration

- Same as Grade 4: on-demand, speaker icon, no auto-play
- TTS usage expected to be low at this grade — students prefer to read independently

### Touch Targets

- Standard 44px minimum — identical to Grade 4
- Coordinate plane points: 44px snap zones for placing/moving points
- Volume cubes: 44px cube faces for click/tap interaction

### New Components Required for Grade 5

#### Coordinate Plane Component (`<CoordinatePlane>`)
- First-quadrant only (x: 0–10, y: 0–10 by default; configurable per question)
- SVG-based, fully accessible (ARIA labels for each axis, point coordinates announced on placement)
- Interaction: tap or click to place a point; existing points are draggable
- Labels: x-axis and y-axis labeled; gridlines at integer positions; major gridlines every 5 units
- Point labels: optional; when enabled, shows (x, y) coordinates adjacent to placed point
- Connection mode: when question requires connecting points, student can tap "Connect" then tap two points to draw a line segment
- Export: `{points: [{x: 3, y: 7, label: "A"}, ...], connections: [[0, 1], ...]}`

#### Volume Builder Component (`<VolumeBuilder3D>`)
- CSS 3D transforms (no WebGL dependency — better accessibility and performance)
- 3D isometric grid of unit cubes; student clicks faces to add or remove cubes
- Real-time volume counter displays current cubic unit count
- Maximum dimensions: 5 × 5 × 5 (125 cubes); questions will not exceed L=5, W=5, H=5
- Keyboard accessible: tab navigation between cube faces; space to toggle
- Mobile: pinch-to-zoom the 3D view; two-finger drag to rotate; single-tap to add/remove

#### Mixed Number Fraction Input (`<MixedNumberInput>`)
- Three separate fields: whole number + fraction numerator + fraction denominator
- Fields displayed as: `[  ] + [  ] / [  ]` with visual fraction bar between numerator/denominator
- Validation: denominator cannot be 0; numerator ≥ 0; whole number ≥ 0
- Visual preview: bar model of the entered fraction updates as student types (fraction < 1) or shows whole + fraction bar
- For simple fractions (no mixed number): whole number field hidden; shows `[  ] / [  ]` only
- For decimal entry: separate `<DecimalInput>` component showing place value positions up to thousandths

### Pip — Grade 5 Mode

- Pip is minimized by default (collapsed icon in corner); student taps to expand for hints
- Matches Grade 4 behavior exactly: 3-level hint system (conceptual → procedural → worked example)
- No automatic hints; student must explicitly request via Pip
- Pip's tone matches Grade 4: peer-like, not didactic ("Here's how I think about it…")

### Session Length

- Soft cap at 35–40 minutes (matching Grade 4)
- Break prompt at 30 minutes
- No hard cutoff; student can complete a session in progress

### Typography — Grade 5

- Identical to Grade 4 design system
- No overrides

---

## 6.6 Grade-Band Token Summary

The following table summarizes all grade-band CSS token overrides relative to the Grade 4 baseline. These are loaded by `GradeThemeProvider` based on the student's enrolled grade.

| CSS Token | Grade 1 | Grade 2 | Grade 3 | Grade 4 (base) | Grade 5 |
|-----------|---------|---------|---------|----------------|---------|
| `--min-touch-target` | 60px | 48px | 44px | 44px | 44px |
| `--font-size-body` | 20px | 18px | 16px | 16px | 16px |
| `--font-size-question-stem` | 24px | 20px | 18px | 18px | 18px |
| `--font-size-answer-tile` | 28px | 24px | 22px | 22px | 22px |
| `--font-size-numeral-display` | 36px | 30px | 28px | 28px | 28px |
| `--line-height-body` | 1.65 | 1.60 | 1.55 | 1.50 | 1.50 |
| `--letter-spacing-body` | 0.02em | 0.01em | 0 | 0 | 0 |
| `--color-primary` | `#0B8A91` | `#068089` | `#01696F` | `#01696F` | `#01696F` |
| `--encouragement-frequency` | every 3 | every 4–5 | every 5 | every 5 | every 5–6 |
| `--session-soft-cap` | 12 min | 17 min | 22 min | 25 min | 37 min |
| `--tts-mode` | auto | on-demand | on-demand | on-demand | on-demand |
| `--pip-mode` | verbose | sidebar | sidebar | minimal | minimal |
| `--drag-object-size` | 80px | 64px | 52px | 48px | 44px |

---

# 7. Architecture & Database Expansion Plan

## 7.1 Standards Database Expansion

### Schema Assessment

The existing `standards` table (from PRD FR-2.1) already supports multi-grade expansion without structural changes:

```sql
-- Existing schema from 03-prd-stage1.md (FR-2.1) — NO CHANGES REQUIRED
CREATE TABLE standards (
    standard_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grade           SMALLINT NOT NULL,           -- Already accepts 1, 2, 3, 5
    domain          VARCHAR(10) NOT NULL,         -- '1.OA', '2.NBT', '3.NF', etc.
    cluster         VARCHAR(255) NOT NULL,
    code            VARCHAR(20) UNIQUE NOT NULL,  -- '1.OA.A.1', '2.NBT.B.5', etc.
    description     TEXT NOT NULL,
    dok_level       SMALLINT NOT NULL CHECK (dok_level BETWEEN 1 AND 4),
    strand          VARCHAR(50),
    is_prerequisite BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    version_tag     VARCHAR(20) NOT NULL DEFAULT 'OAS-2021',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**The only required change to the `standards` table is updating the inline comment on the `grade` field** to reflect the expanded range (no functional change, documentation only).

The `prerequisite_relationships` table is also schema-complete; new edges are added as new rows.

### New Tables Required

Three new tables are required to support multi-grade operations:

```sql
-- Grade-specific assessment configuration (assessment_configs)
-- Stores per-grade diagnostic parameters; loaded by assessment_service.py
CREATE TABLE assessment_configs (
    config_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grade               SMALLINT NOT NULL UNIQUE,
    min_questions       SMALLINT NOT NULL,
    max_questions       SMALLINT NOT NULL,
    target_duration_sec INTEGER NOT NULL,
    break_interval      SMALLINT NOT NULL,        -- questions between optional break prompts
    bkt_p_prior         NUMERIC(4,3) NOT NULL,
    bkt_p_learn         NUMERIC(4,3) NOT NULL,
    bkt_p_guess         NUMERIC(4,3) NOT NULL,
    bkt_p_slip          NUMERIC(4,3) NOT NULL,
    mastery_threshold   NUMERIC(4,3) NOT NULL,
    mastery_streak      SMALLINT NOT NULL,
    tts_mode            VARCHAR(20) NOT NULL CHECK (tts_mode IN ('auto', 'on_demand', 'none')),
    min_touch_target_px SMALLINT NOT NULL,
    pip_mode            VARCHAR(20) NOT NULL CHECK (pip_mode IN ('verbose', 'sidebar', 'minimal')),
    session_soft_cap_sec INTEGER NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_assessment_configs_grade ON assessment_configs(grade);

-- Grade-specific BKT model parameter overrides per standard
-- Allows certain standards (e.g., 3.OA.C.7) to have different BKT params
CREATE TABLE bkt_standard_params (
    param_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    standard_code   VARCHAR(20) NOT NULL REFERENCES standards(code),
    grade           SMALLINT NOT NULL,
    p_prior         NUMERIC(4,3) NOT NULL,
    p_learn         NUMERIC(4,3) NOT NULL,
    p_guess         NUMERIC(4,3) NOT NULL,
    p_slip          NUMERIC(4,3) NOT NULL,
    mastery_threshold NUMERIC(4,3) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (standard_code, grade)
);

-- Grade-band UI theme tokens (used by GradeThemeProvider via API)
CREATE TABLE grade_ui_themes (
    theme_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grade                   SMALLINT NOT NULL UNIQUE,
    min_touch_target_px     SMALLINT NOT NULL DEFAULT 44,
    font_size_body_px       SMALLINT NOT NULL DEFAULT 16,
    font_size_question_px   SMALLINT NOT NULL DEFAULT 18,
    font_size_answer_px     SMALLINT NOT NULL DEFAULT 22,
    font_size_numeral_px    SMALLINT NOT NULL DEFAULT 28,
    line_height_body        NUMERIC(3,2) NOT NULL DEFAULT 1.50,
    letter_spacing_body_em  NUMERIC(4,3) NOT NULL DEFAULT 0.000,
    color_primary           VARCHAR(7) NOT NULL DEFAULT '#01696F',
    encouragement_frequency SMALLINT NOT NULL DEFAULT 5,
    session_soft_cap_sec    INTEGER NOT NULL DEFAULT 1500,
    tts_mode                VARCHAR(20) NOT NULL DEFAULT 'on_demand',
    pip_mode                VARCHAR(20) NOT NULL DEFAULT 'minimal',
    drag_object_size_px     SMALLINT NOT NULL DEFAULT 48,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Database Migration SQL Script

The following Alembic-compatible SQL migration inserts all new Grade 1, 2, 3, and 5 standards into the existing `standards` table, seeds the `assessment_configs`, `bkt_standard_params`, and `grade_ui_themes` tables, and adds all prerequisite edges.

This script corresponds to a new Alembic revision file: `alembic/versions/0004_multigrade_expansion.py`

```sql
-- ============================================================
-- MIGRATION: 0004_multigrade_expansion
-- Description: Add Grades 1, 2, 3, 5 standards and supporting
--              multi-grade configuration tables
-- Generated: 2026-04-08
-- ============================================================

-- SECTION 1: GRADE 1 STANDARDS (22 standards)
-- ============================================================

INSERT INTO standards (grade, domain, cluster, code, description, dok_level, strand, is_prerequisite, version_tag) VALUES

-- 1.OA (8 standards)
(1, '1.OA', 'Represent and solve problems involving addition and subtraction',
 '1.OA.A.1',
 'Use addition and subtraction within 20 to solve and represent problems in authentic contexts involving situations of adding to, taking from, putting together, taking apart, and comparing, with unknowns in all positions.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(1, '1.OA', 'Represent and solve problems involving addition and subtraction',
 '1.OA.A.2',
 'Solve problems that call for addition of three whole numbers whose sum is less than or equal to 20, using concrete objects, drawings, and equations with a symbol for the unknown number to represent the problem.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(1, '1.OA', 'Understand and apply properties of operations and the relationship between addition and subtraction',
 '1.OA.B.3',
 'Apply properties of operations as strategies to add and subtract. Examples: If 8 + 3 = 11 is known, then 3 + 8 = 11 is also known (Commutative property of addition). To add 2 + 6 + 4, the second two numbers can be added to make a ten, so 2 + 6 + 4 = 2 + 10 = 12 (Associative property of addition).',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(1, '1.OA', 'Understand and apply properties of operations and the relationship between addition and subtraction',
 '1.OA.B.4',
 'Understand subtraction as an unknown-addend problem. For example, subtract 10 – 8 by finding the number that makes 10 when added to 8.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(1, '1.OA', 'Add and subtract within 20',
 '1.OA.C.5',
 'Relate counting to addition and subtraction (e.g., by counting on 2 to add 2).',
 1, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(1, '1.OA', 'Add and subtract within 20',
 '1.OA.C.6',
 'Add and subtract within 20, demonstrating fluency for addition and subtraction within 10. Use strategies such as counting on; making ten (e.g., 8 + 6 = 8 + 2 + 4 = 10 + 4 = 14); decomposing a number leading to a ten (e.g., 13 – 4 = 13 – 3 – 1 = 10 – 1 = 9); using the relationship between addition and subtraction (e.g., knowing that 8 + 4 = 12, one knows 12 – 8 = 4); and creating equivalent but easier or known sums (e.g., adding 6 + 7 by creating the known equivalent 6 + 6 + 1 = 12 + 1 = 13). Use accurate, efficient, and flexible strategies.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(1, '1.OA', 'Work with addition and subtraction equations',
 '1.OA.D.7',
 'Use the meaning of the equal sign to determine whether equations involving addition and subtraction are true or false. For example, which of the following equations are true and which are false? 6 = 6, 7 = 8 – 1, 5 + 2 = 2 + 5, 4 + 1 = 5 + 2.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(1, '1.OA', 'Work with addition and subtraction equations',
 '1.OA.D.8',
 'Determine the unknown whole number in an addition or subtraction equation relating three whole numbers. For example, determine the unknown number that makes the equation true in each of the equations 8 + ? = 11, 5 = ? – 3, 6 + 6 = ?.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

-- 1.NBT (6 standards)
(1, '1.NBT', 'Extend the counting sequence',
 '1.NBT.A.1',
 'Count to 120, starting at any number less than 120. In this range, read and write numerals and represent a number of objects with a written numeral.',
 1, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(1, '1.NBT', 'Understand place value',
 '1.NBT.B.2',
 'Understand that the two digits of a two-digit number represent amounts of tens and ones. Understand the following as special cases: (a) 10 can be thought of as a bundle of ten ones — called a "ten"; (b) The numbers from 11 to 19 are composed of a ten and one, two, three, four, five, six, seven, eight, or nine ones; (c) The numbers 10, 20, 30, 40, 50, 60, 70, 80, 90 refer to one, two, three, four, five, six, seven, eight, or nine tens (and 0 ones).',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(1, '1.NBT', 'Understand place value',
 '1.NBT.B.3',
 'Compare two two-digit numbers based on meanings of the tens and ones digits, recording the results of comparisons with the symbols >, =, and <.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(1, '1.NBT', 'Use place value understanding and properties of operations to add and subtract',
 '1.NBT.C.4',
 'Add within 100, including adding a two-digit number and a one-digit number, and adding a two-digit number and a multiple of 10, using concrete models or drawings and strategies based on place value, properties of operations, and/or the relationship between addition and subtraction; relate the strategy to a written method and explain the reasoning used. Understand that in adding two-digit numbers, one adds tens and tens, ones and ones; and sometimes it is necessary to compose a ten.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(1, '1.NBT', 'Use place value understanding and properties of operations to add and subtract',
 '1.NBT.C.5',
 'Given a two-digit number, mentally find 10 more or 10 less than the number, without having to count; explain the reasoning used.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(1, '1.NBT', 'Use place value understanding and properties of operations to add and subtract',
 '1.NBT.C.6',
 'Subtract multiples of 10 in the range 10–90 from multiples of 10 in the range 10–90 (positive or zero differences), using concrete models or drawings and strategies based on place value, properties of operations, and/or the relationship between addition and subtraction; relate the strategy to a written method and explain the reasoning used.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

-- 1.GM (6 standards)
(1, '1.GM', 'Reason with shapes and their attributes',
 '1.GM.A.1',
 'Distinguish between defining attributes (e.g., triangles are closed and three-sided) versus non-defining attributes (e.g., color, orientation, overall size); build and draw shapes to possess defining attributes.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(1, '1.GM', 'Reason with shapes and their attributes',
 '1.GM.A.2',
 'Compose two-dimensional shapes (rectangles, squares, trapezoids, triangles, half-circles, and quarter-circles) or three-dimensional shapes (cubes, right rectangular prisms, right circular cones, and right circular cylinders) to create a composite shape, and compose new shapes from the composite shape.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(1, '1.GM', 'Reason with shapes and their attributes',
 '1.GM.A.3',
 'Partition circles and rectangles into two and four equal shares, describe the shares using the words halves, fourths, and quarters, and use the phrases half of, fourth of, and quarter of. Describe the whole as two of, or four of the shares. Understand for these examples that decomposing into more equal shares creates smaller shares.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(1, '1.GM', 'Measure lengths indirectly and by iterating length units',
 '1.GM.B.4',
 'Order three objects by length; compare the lengths of two objects indirectly by using a third object.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(1, '1.GM', 'Measure lengths indirectly and by iterating length units',
 '1.GM.B.5',
 'Express the length of an object as a whole number of length units, by laying multiple copies of a shorter object (the length unit) end to end; understand that the length measurement of an object is the number of same-size length units that span it with no gaps or overlaps.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(1, '1.GM', 'Tell and write time',
 '1.GM.C.6',
 'Tell and write time in hours and half-hours using analog and digital clocks.',
 1, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

-- 1.DR (2 standards)
(1, '1.DR', 'Formulate questions and collect data',
 '1.DR.A.1',
 'Generate questions to investigate situations within the classroom. Collect and consider data visually by organizing and sorting data up to three categories to answer investigative questions.',
 2, 'Data Reasoning', false, 'OAS-2021'),

(1, '1.DR', 'Analyze data and interpret results',
 '1.DR.B.2',
 'Analyze data sets with up to three categories by interpreting picture graphs and tally charts. Interpret information presented to answer investigative questions about "how many more" and "how many less."',
 2, 'Data Reasoning', false, 'OAS-2021');

-- ============================================================
-- SECTION 2: GRADE 2 STANDARDS (26 standards)
-- ============================================================

INSERT INTO standards (grade, domain, cluster, code, description, dok_level, strand, is_prerequisite, version_tag) VALUES

-- 2.OA (4 standards)
(2, '2.OA', 'Represent and solve problems involving addition and subtraction',
 '2.OA.A.1',
 'Use addition and subtraction within 100 to solve one- and two-step problems in authentic contexts involving situations of adding to, taking from, putting together, taking apart, and comparing, with unknowns in all positions, e.g., by using drawings and equations with a symbol for the unknown number to represent the problem.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(2, '2.OA', 'Add and subtract within 20',
 '2.OA.B.2',
 'Fluently add and subtract within 20 using accurate, efficient, and flexible strategies. By end of Grade 2, know from memory all sums of two one-digit numbers.',
 1, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(2, '2.OA', 'Work with equal groups of objects to gain foundations for multiplication',
 '2.OA.C.3',
 'Determine whether a group of objects (up to 20) has an odd or even number of members, e.g., by pairing objects or counting them by 2s; record the answer using a drawing or equation with a symbol for an unknown.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(2, '2.OA', 'Work with equal groups of objects to gain foundations for multiplication',
 '2.OA.C.4',
 'Use addition to find the total number of objects arranged in rectangular arrays with up to 5 rows and up to 5 columns; write an equation to express the total as a sum of equal addends.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

-- 2.NBT (9 standards)
(2, '2.NBT', 'Understand place value',
 '2.NBT.A.1',
 'Understand that the three digits of a three-digit number represent amounts of hundreds, tens, and ones; e.g., 706 equals 7 hundreds, 0 tens, and 6 ones. Understand the following as special cases: (a) 100 can be thought of as a bundle of ten tens — called a "hundred"; (b) The numbers 100, 200, 300, 400, 500, 600, 700, 800, 900 refer to one, two, three, four, five, six, seven, eight, or nine hundreds (and 0 tens and 0 ones).',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(2, '2.NBT', 'Understand place value',
 '2.NBT.A.2',
 'Count within 1000; skip-count by 5s, 10s, and 100s.',
 1, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(2, '2.NBT', 'Understand place value',
 '2.NBT.A.3',
 'Read and write numbers to 1000 using base-ten numerals, number names, and expanded form.',
 1, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(2, '2.NBT', 'Understand place value',
 '2.NBT.A.4',
 'Compare two three-digit numbers based on meanings of the hundreds, tens, and ones digits, using >, =, and < symbols to record the results of comparisons.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(2, '2.NBT', 'Use place value understanding and properties of operations to add and subtract',
 '2.NBT.B.5',
 'Fluently add and subtract within 100 using strategies based on place value, properties of operations, and/or the relationship between addition and subtraction.',
 1, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(2, '2.NBT', 'Use place value understanding and properties of operations to add and subtract',
 '2.NBT.B.6',
 'Add up to four two-digit numbers using strategies based on place value and properties of operations.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(2, '2.NBT', 'Use place value understanding and properties of operations to add and subtract',
 '2.NBT.B.7',
 'Add and subtract within 1000, using concrete models or drawings and strategies based on place value, properties of operations, and/or the relationship between addition and subtraction; relate the strategy to a written method. Understand that in adding or subtracting three-digit numbers, one adds or subtracts hundreds and hundreds, tens and tens, ones and ones; and sometimes it is necessary to compose or decompose tens or hundreds.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(2, '2.NBT', 'Use place value understanding and properties of operations to add and subtract',
 '2.NBT.B.8',
 'Mentally add 10 or 100 to a given number 100–900, and mentally subtract 10 or 100 from a given number 100–900.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(2, '2.NBT', 'Use place value understanding and properties of operations to add and subtract',
 '2.NBT.B.9',
 'Explain why addition and subtraction strategies work, using place value and the properties of operations.',
 3, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

-- 2.GM (11 standards)
(2, '2.GM', 'Reason with shapes and their attributes',
 '2.GM.A.1',
 'Recognize and draw shapes having specified attributes, such as a given number of angles or a given number of equal faces. Identify triangles, quadrilaterals, pentagons, hexagons, and cubes.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(2, '2.GM', 'Reason with shapes and their attributes',
 '2.GM.A.2',
 'Partition a rectangle into rows and columns of same-size squares and count to find the total number of them.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(2, '2.GM', 'Reason with shapes and their attributes',
 '2.GM.A.3',
 'Partition circles and rectangles into two, three, or four equal parts, describe the parts using the words halves, thirds, half of, a third of, etc., and describe the whole as two halves, three thirds, four fourths. Recognize that equal parts of identical wholes need not have the same shape.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(2, '2.GM', 'Measure and estimate lengths in standard units',
 '2.GM.B.4',
 'Measure the length of an object by selecting and using appropriate tools such as rulers, yardsticks, meter sticks, and measuring tapes.',
 1, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(2, '2.GM', 'Measure and estimate lengths in standard units',
 '2.GM.B.5',
 'Measure the length of an object twice, using length units of different lengths for the two measurements; describe how the two measurements relate to the size of the unit chosen.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(2, '2.GM', 'Measure and estimate lengths in standard units',
 '2.GM.B.6',
 'Estimate lengths using units of inches, feet, yards, centimeters, and meters.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(2, '2.GM', 'Measure and estimate lengths in standard units',
 '2.GM.B.7',
 'Measure to determine how much longer one object is than another, expressing the length difference in terms of a standard length unit.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(2, '2.GM', 'Relate addition and subtraction to length',
 '2.GM.C.8',
 'Use addition and subtraction within 100 to solve word problems involving lengths that are given in the same units, e.g., by using drawings (such as drawings of rulers) and equations with a symbol for the unknown number to represent the problem.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(2, '2.GM', 'Relate addition and subtraction to length',
 '2.GM.C.9',
 'Represent whole numbers as lengths from 0 on a number line diagram with equally spaced points corresponding to the numbers 0, 1, 2, …, and represent whole-number sums and differences within 100 on a number line diagram.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(2, '2.GM', 'Work with time and money',
 '2.GM.D.10',
 'Tell and write time from analog and digital clocks to the nearest five minutes, using a.m. and p.m.',
 1, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(2, '2.GM', 'Work with time and money',
 '2.GM.D.11',
 'Solve problems involving dollar bills, quarters, dimes, nickels, and pennies, using $ and ¢ symbols appropriately. Example: If you have 2 dimes and 3 pennies, how many cents do you have?',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

-- 2.DR (2 standards)
(2, '2.DR', 'Formulate questions and collect data',
 '2.DR.A.1',
 'Generate questions to investigate situations within the classroom; collect and consider data using measurements with whole-number units. Draw a picture graph and a bar graph (with single-unit scale) to represent a data set with up to four categories.',
 2, 'Data Reasoning', false, 'OAS-2021'),

(2, '2.DR', 'Analyze data and interpret results',
 '2.DR.B.2',
 'Analyze data by interpreting picture graphs and bar graphs with a single-unit scale. Interpret information presented to answer investigative questions, including "how many more" and "how many less."',
 2, 'Data Reasoning', false, 'OAS-2021');

-- ============================================================
-- SECTION 3: GRADE 3 STANDARDS (25 standards)
-- ============================================================

INSERT INTO standards (grade, domain, cluster, code, description, dok_level, strand, is_prerequisite, version_tag) VALUES

-- 3.OA (9 standards)
(3, '3.OA', 'Represent and solve problems involving multiplication and division',
 '3.OA.A.1',
 'Represent and interpret multiplication of two factors as repeated addition of equal groups, e.g., describe a context in which a total number of things can be expressed as 5 × 7.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(3, '3.OA', 'Represent and solve problems involving multiplication and division',
 '3.OA.A.2',
 'Represent and interpret whole-number quotients of whole numbers as the result of dividing into equal-sized groups, e.g., describe a context in which a number of shares or a number of groups can be expressed as 56 ÷ 8.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(3, '3.OA', 'Represent and solve problems involving multiplication and division',
 '3.OA.A.3',
 'Use multiplication and division within 100 to solve word problems in situations involving equal groups, arrays, and measurement quantities, e.g., by using drawings and equations with a symbol for the unknown number to represent the problem.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(3, '3.OA', 'Represent and solve problems involving multiplication and division',
 '3.OA.A.4',
 'Determine the unknown whole number in a multiplication or division equation relating three whole numbers. For example, determine the unknown number that makes the equation true in each of the equations 8 × ? = 48, 5 = ? ÷ 3, 6 × 6 = ?.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(3, '3.OA', 'Understand properties of multiplication and the relationship between multiplication and division',
 '3.OA.B.5',
 'Apply properties of operations as strategies to multiply and divide. Examples: If 6 × 4 = 24 is known, then 4 × 6 = 24 is also known (Commutative property of multiplication). 3 × 5 × 2 can be found by 3 × 5 = 15, then 15 × 2 = 30, or by 5 × 2 = 10, then 3 × 10 = 30 (Associative property of multiplication). Knowing that 8 × 5 = 40 and 8 × 2 = 16, one can find 8 × 7 as 8 × (5 + 2) = (8 × 5) + (8 × 2) = 40 + 16 = 56 (Distributive property).',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(3, '3.OA', 'Understand properties of multiplication and the relationship between multiplication and division',
 '3.OA.B.6',
 'Understand division as an unknown-factor problem. For example, find 32 ÷ 8 by finding the number that makes 32 when multiplied by 8.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(3, '3.OA', 'Multiply and divide within 100',
 '3.OA.C.7',
 'Fluently multiply and divide within 100, using strategies such as the relationship between multiplication and division (e.g., knowing that 8 × 5 = 40, one knows 40 ÷ 5 = 8) or properties of operations. By the end of Grade 3, know from memory all products of two one-digit numbers. Use accurate, efficient, and flexible strategies.',
 1, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(3, '3.OA', 'Solve problems involving the four operations, and identify and explain patterns in arithmetic',
 '3.OA.D.8',
 'Solve two-step word problems posed in authentic contexts using the four operations, representing these problems using equations with a letter standing for the unknown quantity. Assess the reasonableness of answers using mental computation and estimation strategies including rounding.',
 3, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(3, '3.OA', 'Solve problems involving the four operations, and identify and explain patterns in arithmetic',
 '3.OA.D.9',
 'Identify arithmetic patterns (including patterns in the addition table or multiplication table), and explain them using properties of operations. For example, observe that 4 times a number is always even, and explain why 4 times a number can be decomposed into two equal addends.',
 3, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

-- 3.NBT (3 standards)
(3, '3.NBT', 'Use place value understanding and properties of operations to perform multi-digit arithmetic',
 '3.NBT.A.1',
 'Use place value understanding to round whole numbers to the nearest 10 or 100. Apply rounding to estimate solutions to authentic problems within 1000.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(3, '3.NBT', 'Use place value understanding and properties of operations to perform multi-digit arithmetic',
 '3.NBT.A.2',
 'Fluently add and subtract within 1000 using strategies and algorithms based on place value, properties of operations, and/or the relationship between addition and subtraction. Use accurate, efficient, and flexible strategies.',
 1, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(3, '3.NBT', 'Use place value understanding and properties of operations to perform multi-digit arithmetic',
 '3.NBT.A.3',
 'Multiply one-digit whole numbers by multiples of 10 in the range 10–90 (e.g., 9 × 80, 5 × 60) using strategies based on place value and properties of operations.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

-- 3.NF (3 standards)
(3, '3.NF', 'Develop understanding of fractions as numbers',
 '3.NF.A.1',
 'Understand the concept of a unit fraction. Explain that a unit fraction represents one part of a whole that has been partitioned into equal parts. Explain how multiple copies of a unit fraction are put together to form a non-unit fraction. For example, 1/4 is the unit fraction that represents one part when a whole is partitioned into 4 equal parts, and 3/4 is the fraction that represents 3 copies of 1/4.',
 2, 'Numeric Reasoning: Fractions', false, 'OAS-2021'),

(3, '3.NF', 'Develop understanding of fractions as numbers',
 '3.NF.A.2',
 'Understand a fraction as a number on the number line; represent fractions on a number line diagram. (a) Represent a fraction 1/b on a number line diagram by defining the interval from 0 to 1 as the whole and partitioning it into b equal parts. Recognize that each part has size 1/b and that the endpoint of the part based at 0 locates the number 1/b on the number line. (b) Represent a fraction a/b on a number line diagram by marking off a lengths 1/b from 0. Recognize that the resulting interval has size a/b and that its endpoint locates the number a/b on the number line.',
 2, 'Numeric Reasoning: Fractions', false, 'OAS-2021'),

(3, '3.NF', 'Develop understanding of fractions as numbers',
 '3.NF.A.3',
 'Explain equivalence of fractions in special cases, and compare fractions by reasoning about their size. (a) Understand two fractions as equivalent (equal) if they are the same size, or the same point on a number line. (b) Recognize and generate simple equivalent fractions, e.g., 1/2 = 2/4, 4/6 = 2/3. Explain why the fractions are equivalent, e.g., by using a visual fraction model. (c) Express whole numbers as fractions, and recognize fractions that are equivalent to whole numbers. Examples: Express 3 in the form 3 = 3/1; recognize that 6/1 = 6; locate 4/4 and 1 at the same point of a number line diagram. (d) Compare two fractions with the same numerator or the same denominator by reasoning about their size. Recognize that comparisons are valid only when the two fractions refer to the same whole. Record the results of comparisons with the symbols >, =, or <, and justify the conclusions, e.g., by using a visual fraction model.',
 3, 'Numeric Reasoning: Fractions', false, 'OAS-2021'),

-- 3.GM (8 standards)
(3, '3.GM', 'Reason with shapes and their attributes',
 '3.GM.A.1',
 'Understand that shapes in different categories (e.g., rhombuses, rectangles, and others) may share attributes (e.g., having four sides), and that the shared attributes can define a larger category (e.g., quadrilaterals). Recognize rhombuses, rectangles, and squares as examples of quadrilaterals, and draw examples of quadrilaterals that do not belong to any of these subcategories.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(3, '3.GM', 'Reason with shapes and their attributes',
 '3.GM.A.2',
 'Partition shapes into parts with equal areas. Express the area of each part as a unit fraction of the whole. For example, partition a shape into 4 parts with equal area, and describe the area of each part as 1/4 of the area of the shape.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(3, '3.GM', 'Solve problems involving measurement and estimation of intervals of time, liquid volumes, and masses of objects',
 '3.GM.B.3',
 'Tell and write time to the nearest minute and measure time intervals in minutes. Solve word problems involving addition and subtraction of time intervals in minutes, e.g., by representing the problem on a number line diagram.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(3, '3.GM', 'Solve problems involving measurement and estimation of intervals of time, liquid volumes, and masses of objects',
 '3.GM.B.4',
 'Measure and estimate liquid volumes and masses of objects using standard units of grams (g), kilograms (kg), and liters (l). Add, subtract, multiply, or divide to solve one-step word problems involving masses or volumes that are given in the same units, e.g., by using drawings (such as a beaker with a measurement scale) to represent the problem.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(3, '3.GM', 'Geometric measurement: understand concepts of area and relate area to multiplication and to addition',
 '3.GM.C.5',
 'Recognize area as an attribute of plane figures and understand concepts of area measurement. (a) A square with side length 1 unit, called "a unit square," is said to have "one square unit" of area, and can be used to measure area. (b) A plane figure which can be covered without gaps or overlaps by n unit squares is said to have an area of n square units.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(3, '3.GM', 'Geometric measurement: understand concepts of area and relate area to multiplication and to addition',
 '3.GM.C.6',
 'Measure areas by counting unit squares (square cm, square m, square in, square ft, and improvised units). Measure areas of rectangles and other rectilinear figures by counting and using standard and non-standard unit squares.',
 1, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(3, '3.GM', 'Geometric measurement: understand concepts of area and relate area to multiplication and to addition',
 '3.GM.C.7',
 'Relate area to the operations of multiplication and addition. (a) Find the area of a rectangle with whole-number side lengths by tiling it, and show that the area is the same as would be found by multiplying the side lengths. (b) Multiply side lengths to find areas of rectangles with whole-number side lengths in the context of solving real world and mathematical problems, and represent whole-number products as rectangular areas in mathematical reasoning. (c) Use tiling to show in a concrete case that the area of a rectangle with whole-number side lengths a and b + c is the sum of a × b and a × c. Use area models to represent the distributive property in mathematical reasoning. (d) Recognize area as additive. Find areas of rectilinear figures by decomposing them into non-overlapping rectangles and adding the areas of the non-overlapping parts, applying this technique to solve real world problems.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(3, '3.GM', 'Geometric measurement: recognize perimeter as an attribute of plane figures and distinguish between linear and area measures',
 '3.GM.D.8',
 'Solve real world and mathematical problems involving perimeters of polygons, including finding the perimeter given the side lengths, finding an unknown side length, and exhibiting rectangles with the same perimeter and different areas or with the same area and different perimeters.',
 3, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

-- 3.DR (2 standards)
(3, '3.DR', 'Formulate questions and collect data',
 '3.DR.A.1',
 'Generate questions to investigate situations within the classroom. Collect and consider measurement data using scaled picture graphs and scaled bar graphs with several categories.',
 2, 'Data Reasoning', false, 'OAS-2021'),

(3, '3.DR', 'Analyze data and interpret results',
 '3.DR.B.2',
 'Analyze measurement data represented in a scaled picture graph or scaled bar graph with several categories, by interpreting information presented to answer investigative questions. Solve one- and two-step "how many more" and "how many less" problems using information presented in scaled bar graphs.',
 2, 'Data Reasoning', false, 'OAS-2021');

-- ============================================================
-- SECTION 4: GRADE 5 STANDARDS (26 standards)
-- ============================================================

INSERT INTO standards (grade, domain, cluster, code, description, dok_level, strand, is_prerequisite, version_tag) VALUES

-- 5.OA (3 standards)
(5, '5.OA', 'Write and interpret numerical expressions',
 '5.OA.A.1',
 'Write and evaluate numerical expressions that include parentheses, brackets, or braces in numerical expressions, and evaluate expressions with these symbols.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(5, '5.OA', 'Write and interpret numerical expressions',
 '5.OA.A.2',
 'Write simple expressions that record calculations with numbers, and interpret numerical expressions without evaluating them. For example, express the calculation "add 8 and 7, then multiply by 2" as 2 × (8 + 7). Recognize that 3 × (18932 + 921) is three times as large as 18932 + 921, without having to calculate the indicated sum or product.',
 2, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

(5, '5.OA', 'Analyze patterns and relationships',
 '5.OA.B.3',
 'Generate two numerical patterns using two given rules. Identify apparent relationships between corresponding terms. Form ordered pairs consisting of corresponding terms from the two patterns, and graph the ordered pairs on a coordinate plane. For example, given the rule "Add 3" and the starting number 0, and given the rule "Add 6" and the starting number 0, generate terms in the resulting sequences, and observe that the terms in one sequence are twice the corresponding terms in the other sequence. Explain informally why this is so.',
 3, 'Algebraic Reasoning: Operations', false, 'OAS-2021'),

-- 5.NBT (7 standards)
(5, '5.NBT', 'Understand the place value system',
 '5.NBT.A.1',
 'Recognize that in a multi-digit number, a digit in one place represents 10 times as much as it represents in the place to its right and 1/10 of what it represents in the place to its left.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(5, '5.NBT', 'Understand the place value system',
 '5.NBT.A.2',
 'Explain patterns in the number of zeros of the product when multiplying a number by powers of 10, and explain patterns in the placement of the decimal point when a decimal is multiplied or divided by a power of 10. Use whole-number exponents to denote powers of 10.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(5, '5.NBT', 'Understand the place value system',
 '5.NBT.A.3',
 'Read, write, and compare decimals to thousandths. (a) Read and write decimals to thousandths using base-ten numerals, number names, and expanded form, e.g., 347.392 = 3 × 100 + 4 × 10 + 7 × 1 + 3 × (1/10) + 9 × (1/100) + 2 × (1/1000). (b) Compare two decimals to thousandths based on meanings of the digits in each place, using >, =, and < symbols to record the results of comparisons.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(5, '5.NBT', 'Understand the place value system',
 '5.NBT.A.4',
 'Use place value understanding to round decimals to any place.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(5, '5.NBT', 'Perform operations with multi-digit whole numbers and with decimals to hundredths',
 '5.NBT.B.5',
 'Fluently multiply multi-digit whole numbers using the standard algorithm. Use accurate, efficient, and flexible strategies.',
 1, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(5, '5.NBT', 'Perform operations with multi-digit whole numbers and with decimals to hundredths',
 '5.NBT.B.6',
 'Find whole-number quotients and remainders of whole numbers with up to four-digit dividends and two-digit divisors, using strategies based on place value, the properties of operations, and/or the relationship between multiplication and division. Illustrate and explain the calculation by using equations, rectangular arrays, and/or area models.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

(5, '5.NBT', 'Perform operations with multi-digit whole numbers and with decimals to hundredths',
 '5.NBT.B.7',
 'Add, subtract, multiply, and divide decimals to hundredths, using concrete models or drawings and strategies based on place value, properties of operations, and/or the relationship between addition and subtraction; relate the strategy to a written method and explain the reasoning used.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', false, 'OAS-2021'),

-- 5.NF (7 standards)
(5, '5.NF', 'Use equivalent fractions as a strategy to add and subtract fractions',
 '5.NF.A.1',
 'Add and subtract fractions with unlike denominators (including mixed numbers) by replacing given fractions with equivalent fractions in such a way as to produce an equivalent sum or difference of fractions with like denominators. For example, 2/3 + 5/4 = 8/12 + 15/12 = 23/12. (In general, a/b + c/d = (ad + bc)/bd.)',
 2, 'Numeric Reasoning: Fractions', false, 'OAS-2021'),

(5, '5.NF', 'Use equivalent fractions as a strategy to add and subtract fractions',
 '5.NF.A.2',
 'Solve word problems involving addition and subtraction of fractions referring to the same whole, including cases of unlike denominators, e.g., by using visual fraction models or equations to represent the problem. Use benchmark fractions and number sense of fractions to estimate mentally and assess the reasonableness of answers. For example, recognize an incorrect result 2/5 + 1/2 = 3/7, by observing that 3/7 < 1/2.',
 3, 'Numeric Reasoning: Fractions', false, 'OAS-2021'),

(5, '5.NF', 'Apply and extend previous understandings of multiplication and division to multiply and divide fractions',
 '5.NF.B.3',
 'Interpret a fraction as division of the numerator by the denominator (a/b = a ÷ b). Solve word problems involving division of whole numbers leading to answers in the form of fractions or mixed numbers, e.g., by using visual fraction models or equations to represent the problem. For example, interpret 3/4 as the result of dividing 3 by 4, noting that 3/4 multiplied by 4 equals 3, and that when 3 wholes are shared equally among 4 people each person has a share of size 3/4.',
 3, 'Numeric Reasoning: Fractions', false, 'OAS-2021'),

(5, '5.NF', 'Apply and extend previous understandings of multiplication and division to multiply and divide fractions',
 '5.NF.B.4',
 'Apply and extend previous understandings of multiplication to multiply a fraction or whole number by a fraction. (a) Interpret the product (a/b) × q as a parts of a partition of q into b equal parts; equivalently, as the result of a sequence of operations a × q ÷ b. For example, use a visual fraction model to show (2/3) × 4 = 8(5, '5.NF', 'Apply and extend previous understandings of multiplication and division to multiply and divide fractions',
 '5.NF.B.4',
 'Apply and extend previous understandings of multiplication to multiply a fraction or whole number by a fraction. (a) Interpret the product (a/b) × q as a parts of a partition of q into b equal parts; equivalently, as the result of a sequence of operations a × q ÷ b. For example, use a visual fraction model to show (2/3) × 4 = 8/3, and create a story context for this equation. Do the same with (2/3) × (4/5) = 8/15. (In general, (a/b) × (c/d) = ac/bd.) (b) Find the area of a rectangle with fractional side lengths by tiling it with unit squares of the appropriate unit fraction side lengths, and show that the area is the same as would be found by multiplying the side lengths. Multiply fractional side lengths to find areas of rectangles, and represent fraction products as rectangular areas.',
 3, 'Numeric Reasoning: Fractions', false, 'OAS-2021'),

(5, '5.NF', 'Apply and extend previous understandings of multiplication and division to multiply and divide fractions',
 '5.NF.B.5',
 'Interpret multiplication as scaling (resizing), by: (a) Comparing the size of a product to the size of one factor on the basis of the size of the other factor, without performing the indicated multiplication. (b) Explaining why multiplying a given number by a fraction greater than 1 results in a product greater than the given number (recognizing multiplication by whole numbers greater than 1 as a familiar case); explaining why multiplying a given number by a fraction less than 1 results in a product smaller than the given number; and relating the principle of fraction equivalence a/b = (n×a)/(n×b) to the effect of multiplying a/b by 1.',
 3, 'Numeric Reasoning: Fractions', false, 'OAS-2021'),

(5, '5.NF', 'Apply and extend previous understandings of multiplication and division to multiply and divide fractions',
 '5.NF.B.6',
 'Solve real-world problems involving multiplication of fractions and mixed numbers, e.g., by using visual fraction models or equations to represent the problem.',
 3, 'Numeric Reasoning: Fractions', false, 'OAS-2021'),

(5, '5.NF', 'Apply and extend previous understandings of multiplication and division to multiply and divide fractions',
 '5.NF.B.7',
 'Apply and extend previous understandings of division to divide unit fractions by whole numbers and whole numbers by unit fractions. (a) Interpret division of a unit fraction by a non-zero whole number, and compute such quotients. For example, create a story context for (1/3) ÷ 4, and use a visual fraction model to show the quotient. Use the relationship between multiplication and division to explain that (1/3) ÷ 4 = 1/12 because (1/12) × 4 = 1/3. (b) Interpret division of a whole number by a unit fraction, and compute such quotients. For example, create a story context for 4 ÷ (1/5), and use a visual fraction model to show the quotient. Use the relationship between multiplication and division to explain that 4 ÷ (1/5) = 20 because 20 × (1/5) = 4. (c) Solve real-world problems involving division of unit fractions by non-zero whole numbers and division of whole numbers by unit fractions, e.g., by using visual fraction models and equations to represent the problem.',
 3, 'Numeric Reasoning: Fractions', false, 'OAS-2021'),

-- 5.GM (7 standards)
(5, '5.GM', 'Graph points on the coordinate plane to solve real-world and mathematical problems',
 '5.GM.A.1',
 'Use a pair of perpendicular number lines, called axes, to define a coordinate system, with the intersection of the lines (the origin) arranged to coincide with the 0 on each line and a given point in the plane located by using an ordered pair of numbers, called its coordinates. Understand that the first number indicates how far to travel from the origin in the direction of one axis, and the second number indicates how far to travel in the direction of the second axis, with the convention that the names of the two axes and the coordinates correspond (e.g., x-axis and x-coordinate, y-axis and y-coordinate). Graph and name coordinate points in the first quadrant using (x, y) notation.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(5, '5.GM', 'Graph points on the coordinate plane to solve real-world and mathematical problems',
 '5.GM.A.2',
 'Represent authentic contexts and mathematical problems by graphing points in the first quadrant of the coordinate plane, and interpret coordinate values of points in the context of the situation.',
 3, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(5, '5.GM', 'Classify two-dimensional figures into categories based on their properties',
 '5.GM.B.3',
 'Classify two-dimensional figures in a hierarchy based on geometrical properties. Understand that attributes belonging to a category of two-dimensional figures also belong to all subcategories of that category. For example, all rectangles have four right angles and squares are rectangles, so all squares have four right angles.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(5, '5.GM', 'Convert like measurement units within a given measurement system',
 '5.GM.C.4',
 'Convert among different-sized standard measurement units within a given measurement system (e.g., convert 5 cm to 0.05 m), and use these conversions in solving multi-step, real-world problems.',
 2, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(5, '5.GM', 'Geometric measurement: understand concepts of volume and relate volume to multiplication and to addition',
 '5.GM.D.5',
 'Recognize volume as an attribute of solid figures and understand concepts of volume measurement. (a) A cube with side length 1 unit, called a "unit cube," is said to have "one cubic unit" of volume, and can be used to measure volume. (b) A solid figure which can be packed without gaps or overlaps using n unit cubes is said to have a volume of n cubic units.',
 1, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(5, '5.GM', 'Geometric measurement: understand concepts of volume and relate volume to multiplication and to addition',
 '5.GM.D.6',
 'Measure volumes by counting unit cubes, using cubic cm, cubic in, cubic ft, and improvised units.',
 1, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

(5, '5.GM', 'Geometric measurement: understand concepts of volume and relate volume to multiplication and to addition',
 '5.GM.D.7',
 'Relate volume to the operations of multiplication and addition and solve real-world and mathematical problems involving volume. (a) Find the volume of a right rectangular prism with whole-number side lengths by packing it with unit cubes, and show that the volume is the same as would be found by multiplying the edge lengths, equivalently by multiplying the height by the area of the base. Represent threefold whole-number products as volumes, e.g., to represent the associative property of multiplication. (b) Apply the formulas V = l × w × h and V = b × h for rectangular prisms to find volumes of right rectangular prisms with whole-number edge lengths in the context of solving real-world and mathematical problems. (c) Recognize volume as additive. Find volumes of solid figures composed of two non-overlapping right rectangular prisms by adding the volumes of the non-overlapping parts, applying this technique to solve real-world problems.',
 3, 'Geometric Reasoning and Measurement', false, 'OAS-2021'),

-- 5.DR (2 standards)
(5, '5.DR', 'Generate and represent data',
 '5.DR.A.1',
 'Generate questions to investigate situations within the classroom or beyond. Determine strategies for collecting and consider data involving fractions using line plots.',
 2, 'Data Reasoning', false, 'OAS-2021'),

(5, '5.DR', 'Analyze data and interpret results',
 '5.DR.B.2',
 'Analyze graphical representations and describe the distribution of the data set. Interpret information presented to answer investigative questions.',
 3, 'Data Reasoning', false, 'OAS-2021');

-- ============================================================
-- SECTION 5: KINDERGARTEN PREREQUISITE STANDARDS (23 standards)
-- Stored with grade=0, is_prerequisite=TRUE
-- ============================================================

INSERT INTO standards (grade, domain, cluster, code, description, dok_level, strand, is_prerequisite, version_tag) VALUES

-- K.OA (5 standards)
(0, 'K.OA', 'Understand addition and subtraction',
 'K.OA.A.1',
 'Represent addition as putting together and adding to, and subtraction as taking apart and taking from, using objects, drawings, physical expressions, numbers or equations to represent authentic contexts.',
 1, 'Algebraic Reasoning: Operations', true, 'OAS-2021'),

(0, 'K.OA', 'Understand addition and subtraction',
 'K.OA.A.2',
 'Add and subtract within 10. Model authentic contexts and solve problems using the strategies of addition and subtraction within 10.',
 1, 'Algebraic Reasoning: Operations', true, 'OAS-2021'),

(0, 'K.OA', 'Understand addition and subtraction',
 'K.OA.A.3',
 'Using objects, drawings, or equations, decompose numbers less than or equal to 10 into pairs in more than one way, and record each decomposition by a drawing or equation (e.g., 5 = 2 + 3 and 5 = 4 + 1).',
 2, 'Algebraic Reasoning: Operations', true, 'OAS-2021'),

(0, 'K.OA', 'Understand addition and subtraction',
 'K.OA.A.4',
 'For any number from 1 to 9, find the number that makes 10 when added to the given number, e.g., by using objects or drawings, and record the answer with a drawing or equation.',
 1, 'Algebraic Reasoning: Operations', true, 'OAS-2021'),

(0, 'K.OA', 'Understand addition and subtraction',
 'K.OA.A.5',
 'Fluently add and subtract within 5 with accurate, efficient, and flexible strategies.',
 1, 'Algebraic Reasoning: Operations', true, 'OAS-2021'),

-- K.NCC (7 standards)
(0, 'K.NCC', 'Know number names and the count sequence',
 'K.NCC.A.1',
 'Orally count to 100 by ones and by tens in sequential order.',
 1, 'Numeric Reasoning: Counting and Cardinality', true, 'OAS-2021'),

(0, 'K.NCC', 'Know number names and the count sequence',
 'K.NCC.A.2',
 'Count forward beginning from a given number within 100 of a known sequence (instead of having to begin at 1).',
 1, 'Numeric Reasoning: Counting and Cardinality', true, 'OAS-2021'),

(0, 'K.NCC', 'Know number names and the count sequence',
 'K.NCC.A.3',
 'Identify number names, write numbers, and the count sequence from 0-20. Represent a number of objects with a written number 0-20 (with 0 representing a count of no objects).',
 1, 'Numeric Reasoning: Counting and Cardinality', true, 'OAS-2021'),

(0, 'K.NCC', 'Count to tell the number of objects',
 'K.NCC.B.4',
 'Understand the relationship between numbers and quantities; connect counting to cardinality. When counting objects, say the number names in the standard order, pairing each object with one and only one number name and each number name with one and only one object (one-to-one correspondence). Understand that the last number name said tells the number of objects counted. Understand that each successive number name refers to a quantity that is one larger.',
 1, 'Numeric Reasoning: Counting and Cardinality', true, 'OAS-2021'),

(0, 'K.NCC', 'Count to tell the number of objects',
 'K.NCC.B.5',
 'Count to answer "how many?" questions about as many as 20 things arranged in a line, a rectangular array, or a circle, or as many as 10 things in a scattered configuration; given a number from 1-20, count out that many objects.',
 1, 'Numeric Reasoning: Counting and Cardinality', true, 'OAS-2021'),

(0, 'K.NCC', 'Compare numbers',
 'K.NCC.C.6',
 'Identify whether the number of objects in one group is greater than, less than, or equal to the number of objects in another group, e.g., by using matching and counting strategies.',
 1, 'Numeric Reasoning: Counting and Cardinality', true, 'OAS-2021'),

(0, 'K.NCC', 'Compare numbers',
 'K.NCC.C.7',
 'Compare two numbers between 1 and 10 presented as written numerals.',
 1, 'Numeric Reasoning: Counting and Cardinality', true, 'OAS-2021'),

-- K.NBT (1 standard)
(0, 'K.NBT', 'Work with numbers 11-19 to gain foundations for place value',
 'K.NBT.A.1',
 'Compose and decompose numbers from 11 to 19 into ten ones and some further ones, e.g., by using objects or drawings, and record each composition or decomposition by a drawing or equation (e.g., 18 = 10 + 8); understand that these numbers are composed of ten ones and one, two, three, four, five, six, seven, eight, or nine ones.',
 2, 'Numeric Reasoning: Base Ten Arithmetic', true, 'OAS-2021'),

-- K.GM (8 standards)
(0, 'K.GM', 'Identify and describe shapes',
 'K.GM.A.1',
 'Describe objects in the environment using names of shapes, and describe the relative positions of these objects using terms such as above, below, beside, in front of, behind, and next to.',
 1, 'Geometric Reasoning and Measurement', true, 'OAS-2021'),

(0, 'K.GM', 'Identify and describe shapes',
 'K.GM.A.2',
 'Correctly name shapes regardless of their orientations or overall size. Common two-dimensional shapes include: square, circle, triangle, rectangle, hexagon. Common three-dimensional shapes include: cube, cone, cylinder, and sphere.',
 1, 'Geometric Reasoning and Measurement', true, 'OAS-2021'),

(0, 'K.GM', 'Identify and describe shapes',
 'K.GM.A.3',
 'Identify shapes as two-dimensional (lying in a plane, "flat") or three-dimensional ("solid").',
 1, 'Geometric Reasoning and Measurement', true, 'OAS-2021'),

(0, 'K.GM', 'Analyze, compare, create, and compose shapes',
 'K.GM.B.4',
 'Analyze and compare two- and three-dimensional shapes, in different sizes and orientations, using informal language to describe their similarities, differences, parts (e.g., number of sides and vertices/corners) and other attributes (e.g., having sides of equal length).',
 2, 'Geometric Reasoning and Measurement', true, 'OAS-2021'),

(0, 'K.GM', 'Analyze, compare, create, and compose shapes',
 'K.GM.B.5',
 'Model shapes in the world by building shapes from components (e.g., sticks and clay balls) and drawing shapes.',
 1, 'Geometric Reasoning and Measurement', true, 'OAS-2021'),

(0, 'K.GM', 'Analyze, compare, create, and compose shapes',
 'K.GM.B.6',
 'Compose simple shapes to form larger shapes. For example, "Can you join these two triangles with full sides touching to make a rectangle?"',
 2, 'Geometric Reasoning and Measurement', true, 'OAS-2021'),

(0, 'K.GM', 'Describe and compare measurable attributes',
 'K.GM.C.7',
 'Describe several measurable attributes of a single object. For example, a ball has a size and a weight.',
 1, 'Geometric Reasoning and Measurement', true, 'OAS-2021'),

(0, 'K.GM', 'Describe and compare measurable attributes',
 'K.GM.C.8',
 'Directly compare two objects with a measurable attribute in common, to see which object has "more of"/"less of" the attribute, and describe the difference. For example, directly compare the heights of two children and describe one child as taller/shorter.',
 1, 'Geometric Reasoning and Measurement', true, 'OAS-2021'),

-- K.DR (2 standards)
(0, 'K.DR', 'Generate and represent data',
 'K.DR.A.1',
 'Generate questions to investigate situations within the classroom. Collect and consider data by sorting and counting objects into categories.',
 1, 'Data Reasoning', true, 'OAS-2021'),

(0, 'K.DR', 'Analyze data and interpret results',
 'K.DR.B.2',
 'Analyze data sets by counting the number of objects in each category and sorting the categories by count. Interpret results by classifying and sorting objects by color, shape, size, and other attributes.',
 2, 'Data Reasoning', true, 'OAS-2021');

-- ============================================================
-- SECTION 6: PREREQUISITE RELATIONSHIP EDGES — ALL NEW GRADES
-- ============================================================

-- Inter-grade prerequisite edges: K → Grade 1
INSERT INTO prerequisite_relationships (prerequisite_code, dependent_code, rationale) VALUES
('K.OA.A.2',  '1.OA.A.1',  'Add/subtract within 10 is prerequisite for add/subtract within 20'),
('K.OA.A.5',  '1.OA.C.6',  'Fluency within 5 is prerequisite for fluency within 10'),
('K.OA.A.4',  '1.OA.C.6',  'Making 10 strategy is prerequisite for adding within 20 fluency'),
('K.NCC.A.3', '1.NBT.A.1', 'Writing numbers 0-20 is prerequisite for counting and writing to 120'),
('K.NCC.B.4', '1.OA.A.1',  'Connecting counting to cardinality is prerequisite for representing addition/subtraction problems'),
('K.NCC.C.7', '1.NBT.B.3', 'Comparing numbers 1-10 is prerequisite for comparing two-digit numbers'),
('K.NBT.A.1', '1.NBT.B.2', 'Composing/decomposing 11-19 is prerequisite for understanding tens and ones place value'),
('K.GM.B.6',  '1.GM.A.2',  'Composing shapes from simpler shapes is prerequisite for composing 2D/3D shapes into composites');

-- Intra-grade prerequisite edges: Grade 1
INSERT INTO prerequisite_relationships (prerequisite_code, dependent_code, rationale) VALUES
('1.OA.A.1',  '1.OA.A.2',  'Single-addend problems prerequisite for three-addend problems'),
('1.OA.B.3',  '1.OA.C.6',  'Properties of operations support fluency strategies'),
('1.OA.B.4',  '1.OA.D.8',  'Subtraction as unknown-addend is prerequisite for unknown-position equations'),
('1.OA.C.5',  '1.OA.C.6',  'Counting strategies prerequisite for fluency development'),
('1.OA.C.6',  '1.OA.A.1',  'Fluency within 10 supports solving problems within 20'),
('1.OA.D.7',  '1.OA.D.8',  'Understanding equal sign prerequisite for finding unknowns in equations'),
('1.NBT.B.2', '1.NBT.B.3', 'Understanding tens/ones prerequisite for comparing two-digit numbers'),
('1.NBT.B.2', '1.NBT.C.4', 'Place value understanding prerequisite for adding within 100'),
('1.NBT.B.3', '1.NBT.C.4', 'Comparing numbers supports understanding of addition strategies'),
('1.NBT.C.4', '1.NBT.C.6', 'Adding within 100 prerequisite for subtracting multiples of 10'),
('1.NBT.C.5', '1.NBT.C.6', 'Mental 10 more/less prerequisite for subtracting multiples of 10'),
('1.GM.A.1',  '1.GM.A.2',  'Understanding defining attributes prerequisite for composing shapes'),
('1.GM.A.2',  '1.GM.A.3',  'Composing shapes prerequisite for partitioning circles/rectangles'),
('1.GM.B.4',  '1.GM.B.5',  'Ordering by length prerequisite for expressing length in units'),
('1.OA.C.6',  '1.NBT.C.4', 'Fluency within 20 supports strategies for adding within 100');

-- Inter-grade prerequisite edges: Grade 1 → Grade 2
INSERT INTO prerequisite_relationships (prerequisite_code, dependent_code, rationale) VALUES
('1.OA.C.6',  '2.OA.B.2',  'Fluency within 20 is prerequisite for fluency within 20 mastery at Grade 2'),
('1.OA.D.8',  '2.OA.A.1',  'Unknown-position equations is prerequisite for one/two-step problems'),
('1.NBT.B.2', '2.NBT.A.1', 'Understanding tens/ones is prerequisite for understanding hundreds/tens/ones'),
('1.NBT.C.4', '2.NBT.B.5', 'Add within 100 is prerequisite for fluent add/subtract within 100'),
('1.NBT.C.5', '2.NBT.B.8', 'Mentally find 10 more/less is prerequisite for 10/100 more/less'),
('1.GM.A.3',  '2.GM.A.3',  'Partitioning into halves/fourths is prerequisite for partitioning into halves/thirds/fourths'),
('1.GM.B.5',  '2.GM.B.4',  'Non-standard length units is prerequisite for standard measurement tools'),
('1.GM.C.6',  '2.GM.D.10', 'Telling time in hours/half-hours is prerequisite for time to nearest 5 minutes');

-- Intra-grade prerequisite edges: Grade 2
INSERT INTO prerequisite_relationships (prerequisite_code, dependent_code, rationale) VALUES
('2.OA.B.2',  '2.OA.A.1',  'Fluency within 20 supports solving one/two-step word problems'),
('2.OA.C.3',  '2.OA.C.4',  'Odd/even understanding supports array patterns'),
('2.NBT.A.1', '2.NBT.A.2', 'Understanding hundreds is prerequisite for counting within 1000'),
('2.NBT.A.1', '2.NBT.A.3', 'Understanding place value is prerequisite for reading/writing numbers to 1000'),
('2.NBT.A.3', '2.NBT.A.4', 'Reading three-digit numbers is prerequisite for comparing them'),
('2.NBT.A.4', '2.NBT.B.7', 'Comparing three-digit numbers supports adding/subtracting within 1000'),
('2.NBT.B.5', '2.NBT.B.6', 'Fluency within 100 is prerequisite for adding four two-digit numbers'),
('2.NBT.B.5', '2.NBT.B.7', 'Fluency within 100 is prerequisite for adding/subtracting within 1000'),
('2.NBT.B.7', '2.NBT.B.8', 'Adding/subtracting within 1000 supports mentally finding 100 more/less'),
('2.NBT.B.7', '2.NBT.B.9', 'Applying strategies is prerequisite for explaining why they work'),
('2.GM.A.2',  '2.GM.A.3',  'Partitioning rectangles into rows/columns supports partitioning into equal parts'),
('2.GM.B.4',  '2.GM.B.5',  'Measuring with one unit is prerequisite for measuring with two units'),
('2.GM.B.4',  '2.GM.B.7',  'Measuring objects is prerequisite for comparing their lengths'),
('2.GM.B.5',  '2.GM.B.6',  'Measuring with tools is prerequisite for estimating lengths'),
('2.GM.B.7',  '2.GM.C.8',  'Comparing lengths is prerequisite for solving subtraction length problems'),
('2.GM.C.8',  '2.GM.C.9',  'Length problems using operations supports number line length representation'),
('2.OA.B.2',  '2.GM.C.8',  'Fluency within 100 is prerequisite for solving length problems with add/subtract'),
('2.GM.D.10', '2.GM.D.11', 'Telling time supports solving time/money mixed word problems');

-- Inter-grade prerequisite edges: Grade 2 → Grade 3
INSERT INTO prerequisite_relationships (prerequisite_code, dependent_code, rationale) VALUES
('2.OA.B.2',  '3.OA.D.8',  'Fluency within 20 is prerequisite for two-step problems with four operations'),
('2.OA.C.4',  '3.OA.A.1',  'Rectangular arrays with equal addends is prerequisite for multiplication as repeated addition'),
('2.NBT.A.4', '3.NBT.A.1', 'Comparing three-digit numbers is prerequisite for rounding within 1000'),
('2.NBT.B.5', '3.NBT.A.2', 'Fluent add/subtract within 100 is prerequisite for fluency within 1000'),
('2.NBT.B.7', '3.NBT.A.2', 'Add/subtract within 1000 is prerequisite for fluency within 1000'),
('2.GM.A.3',  '3.NF.A.1',  'Partitioning into equal parts is prerequisite for understanding unit fractions'),
('2.GM.C.9',  '3.NF.A.2',  'Number line for sums/differences is prerequisite for fractions on number line'),
('2.GM.B.4',  '3.GM.B.4',  'Standard measurement tools is prerequisite for measuring liquid volumes and masses');

-- Intra-grade prerequisite edges: Grade 3
INSERT INTO prerequisite_relationships (prerequisite_code, dependent_code, rationale) VALUES
('3.OA.A.1',  '3.OA.A.2',  'Multiplication as repeated addition is prerequisite for division as equal groups'),
('3.OA.A.1',  '3.OA.A.3',  'Understanding multiplication is prerequisite for applying it in contexts'),
('3.OA.A.2',  '3.OA.A.3',  'Understanding division is prerequisite for applying it in contexts'),
('3.OA.A.3',  '3.OA.A.4',  'Applying multiplication/division is prerequisite for finding unknowns'),
('3.OA.A.4',  '3.OA.B.5',  'Finding unknowns is prerequisite for applying operation properties'),
('3.OA.B.5',  '3.OA.B.6',  'Properties of multiplication are prerequisite for understanding division as unknown factor'),
('3.OA.B.6',  '3.OA.C.7',  'Understanding division structure is prerequisite for fluency'),
('3.OA.C.7',  '3.OA.D.8',  'Multiplication/division fluency is prerequisite for two-step problems'),
('3.OA.D.8',  '3.OA.D.9',  'Solving two-step problems is prerequisite for identifying arithmetic patterns'),
('3.NBT.A.1', '3.NBT.A.2', 'Rounding is prerequisite for checking reasonableness in fluent computation'),
('3.NBT.A.2', '3.NBT.A.3', 'Fluent add/subtract within 1000 supports multiplying multiples of 10'),
('3.NF.A.1',  '3.NF.A.2',  'Unit fraction concept is prerequisite for placing fractions on number line'),
('3.NF.A.2',  '3.NF.A.3',  'Fractions on number line is prerequisite for equivalence and comparison'),
('3.GM.A.1',  '3.GM.A.2',  'Shape category attributes is prerequisite for partitioning shapes into equal areas'),
('3.GM.B.3',  '3.GM.B.4',  'Telling time to nearest minute is prerequisite for solving time interval problems'),
('3.GM.C.5',  '3.GM.C.6',  'Recognizing area attribute is prerequisite for measuring areas by counting'),
('3.GM.C.6',  '3.GM.C.7',  'Measuring areas is prerequisite for relating area to multiplication'),
('3.GM.C.7',  '3.GM.D.8',  'Area calculation supports perimeter reasoning'),
('3.OA.C.7',  '3.GM.C.7',  'Multiplication fluency is prerequisite for area-as-multiplication formula'),
('3.NF.A.1',  '3.GM.A.2',  'Understanding unit fractions supports partitioning shapes into unit fraction areas');

-- Inter-grade prerequisite edges: Grade 4 → Grade 5
INSERT INTO prerequisite_relationships (prerequisite_code, dependent_code, rationale) VALUES
('4.OA.A.3',  '5.OA.A.1',  'Solving multistep problems is prerequisite for writing/evaluating expressions with parentheses'),
('4.NBT.B.5', '5.NBT.B.5', 'Multiplying up to 4 digits × 1 digit is prerequisite for fluent multi-digit multiplication'),
('4.NBT.B.6', '5.NBT.B.6', 'Division with 1-digit divisors is prerequisite for division with 2-digit divisors'),
('4.NF.A.1',  '5.NF.A.1',  'Equivalent fractions is prerequisite for adding fractions with unlike denominators'),
('4.NF.A.2',  '5.NF.B.5',  'Comparing fractions is prerequisite for understanding multiplication as scaling'),
('4.NF.B.3',  '5.NF.A.1',  'Adding fractions with like denominators is prerequisite for unlike denominators'),
('4.NF.B.4',  '5.NF.B.4',  'Multiplying fraction by whole number is prerequisite for multiplying fraction by fraction'),
('4.NF.C.7',  '5.NBT.A.3', 'Comparing decimals to hundredths is prerequisite for comparing decimals to thousandths'),
('4.GM.D.9',  '5.GM.D.7',  'Area and perimeter formulas are prerequisite for volume problem solving');

-- Intra-grade prerequisite edges: Grade 5
INSERT INTO prerequisite_relationships (prerequisite_code, dependent_code, rationale) VALUES
('5.OA.A.1',  '5.OA.A.2',  'Writing/evaluating expressions is prerequisite for interpreting them without evaluating'),
('5.OA.A.2',  '5.OA.B.3',  'Writing expressions is prerequisite for generating patterns and graphing them'),
('5.NBT.A.1', '5.NBT.A.2', 'Place value relationships are prerequisite for powers-of-10 patterns'),
('5.NBT.A.2', '5.NBT.A.3', 'Powers-of-10 patterns support understanding decimal structure'),
('5.NBT.A.3', '5.NBT.A.4', 'Reading/writing decimals is prerequisite for rounding them'),
('5.NBT.B.5', '5.NBT.B.6', 'Multi-digit multiplication is prerequisite for multi-digit division'),
('5.NBT.A.3', '5.NBT.B.7', 'Understanding decimal place value is prerequisite for decimal operations'),
('5.NF.A.1',  '5.NF.A.2',  'Adding fractions with unlike denominators is prerequisite for fraction word problems'),
('5.NF.B.3',  '5.NF.B.4',  'Fraction as division is prerequisite for multiplying fraction by fraction'),
('5.NF.B.4',  '5.NF.B.5',  'Multiplying fractions is prerequisite for interpreting multiplication as scaling'),
('5.NF.B.4',  '5.NF.B.6',  'Multiplying fractions is prerequisite for fraction/mixed number word problems'),
('5.NF.B.3',  '5.NF.B.7',  'Fraction as division supports understanding unit fraction division'),
('5.GM.A.1',  '5.GM.A.2',  'Coordinate plane mechanics is prerequisite for graphing real-world problems'),
('5.OA.B.3',  '5.GM.A.2',  'Generating patterns on coordinate plane is prerequisite for graphing contexts'),
('5.GM.D.5',  '5.GM.D.6',  'Understanding volume concept is prerequisite for measuring by counting unit cubes'),
('5.GM.D.6',  '5.GM.D.7',  'Measuring volumes is prerequisite for relating volume to multiplication/addition formulas');

-- ============================================================
-- SECTION 7: ASSESSMENT CONFIGURATION SEEDING
-- ============================================================

INSERT INTO assessment_configs (grade, assessment_type, min_questions, max_questions, target_duration_minutes, prior_grade_prereq_count, domains_sampled) VALUES
(1, 'DIAGNOSTIC', 20, 25, 15, 8, ARRAY['1.OA', '1.NBT', '1.GM', '1.DR']),
(2, 'DIAGNOSTIC', 25, 30, 20, 8, ARRAY['2.OA', '2.NBT', '2.GM', '2.DR']),
(3, 'DIAGNOSTIC', 28, 35, 22, 8, ARRAY['3.OA', '3.NBT', '3.NF', '3.GM', '3.DR']),
(5, 'DIAGNOSTIC', 35, 45, 38, 9, ARRAY['5.OA', '5.NBT', '5.NF', '5.GM', '5.DR']);

-- ============================================================
-- SECTION 8: BKT PARAMETER SEEDING (per-grade defaults)
-- ============================================================

INSERT INTO bkt_grade_defaults (grade, prior, learn, guess, slip, mastery_threshold, notes) VALUES
(1, 0.20, 0.15, 0.30, 0.08, 0.85, 'Grade 1: lower prior (early learners), higher guess (picture-based), higher learn rate'),
(2, 0.22, 0.18, 0.25, 0.09, 0.87, 'Grade 2: moderate prior, standard learn rate, mixed question types'),
(3, 0.25, 0.20, 0.22, 0.10, 0.90, 'Grade 3: aligns closely with Grade 4 baseline pattern'),
(5, 0.28, 0.22, 0.18, 0.10, 0.90, 'Grade 5: higher prior (near-complete elementary background expected)');

-- ============================================================
-- SECTION 9: GRADE UI THEME SEEDING
-- ============================================================

INSERT INTO grade_ui_themes (grade, min_touch_target_px, body_font_size_px, number_font_size_px, tts_mode, session_max_minutes, encouragement_interval_questions, pip_verbosity, primary_hue_override) VALUES
(1, 60, 20, 28, 'AUTO_PLAY', 15, 3, 'VERBOSE', 'hsl(52, 100%, 58%)'),
(2, 48, 18, 24, 'ON_DEMAND', 20, 4, 'MODERATE', 'hsl(199, 80%, 55%)'),
(3, 44, 16, 20, 'ON_DEMAND', 25, 5, 'STANDARD', NULL),
(5, 44, 16, 18, 'OFF_BY_DEFAULT', 40, 6, 'MINIMAL', NULL);

-- ============================================================
-- END MIGRATION 0004_multigrade_expansion
-- ============================================================
```

## 7.2 Multi-Grade BKT Model Management

### Grade-Partitioned Parameter Sets

The existing Grade 4 BKT implementation in `pyBKT` uses a single parameter set loaded at application startup. For multi-grade support, BKT parameters must be grade-partitioned — each grade maintains its own prior probability, learn rate, guess rate, and slip rate, which differ systematically based on age-group cognitive characteristics and question type distributions.

**Architecture pattern** — grade-aware BKT service:

```python
# apps/api/src/service/bkt_service.py (updated)

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict

class SupportedGrade(IntEnum):
    KINDERGARTEN = 0
    GRADE_1 = 1
    GRADE_2 = 2
    GRADE_3 = 3
    GRADE_4 = 4
    GRADE_5 = 5

@dataclass(frozen=True)
class BKTGradeParams:
    prior: float      # P(mastery | start)
    learn: float      # P(transition to mastered | not mastered)
    guess: float      # P(correct | not mastered)
    slip: float       # P(incorrect | mastered)
    mastery_threshold: float  # P(mastery) at which we declare skill mastered

# Default parameters by grade — loaded from DB at startup, overridden per-standard if calibrated
GRADE_BKT_DEFAULTS: Dict[SupportedGrade, BKTGradeParams] = {
    SupportedGrade.GRADE_1: BKTGradeParams(prior=0.20, learn=0.15, guess=0.30, slip=0.08, mastery_threshold=0.85),
    SupportedGrade.GRADE_2: BKTGradeParams(prior=0.22, learn=0.18, guess=0.25, slip=0.09, mastery_threshold=0.87),
    SupportedGrade.GRADE_3: BKTGradeParams(prior=0.25, learn=0.20, guess=0.22, slip=0.10, mastery_threshold=0.90),
    SupportedGrade.GRADE_4: BKTGradeParams(prior=0.25, learn=0.20, guess=0.20, slip=0.10, mastery_threshold=0.90),
    SupportedGrade.GRADE_5: BKTGradeParams(prior=0.28, learn=0.22, guess=0.18, slip=0.10, mastery_threshold=0.90),
}

class BKTService:
    def __init__(self, db_session, redis_client):
        self._db = db_session
        self._redis = redis_client
        # Load per-standard calibrated params from DB at startup
        self._calibrated_params: Dict[str, BKTGradeParams] = {}

    async def get_params_for_standard(self, standard_code: str, grade: int) -> BKTGradeParams:
        """Returns calibrated params if available, falls back to grade defaults."""
        if standard_code in self._calibrated_params:
            return self._calibrated_params[standard_code]
        return GRADE_BKT_DEFAULTS[SupportedGrade(grade)]

    async def update_mastery_probability(
        self, student_id: str, standard_code: str, grade: int, response_correct: bool
    ) -> float:
        """Standard BKT update equation, grade-parameterized."""
        params = await self.get_params_for_standard(standard_code, grade)
        cache_key = f"bkt:{student_id}:{standard_code}"
        
        # Retrieve current P(mastery) from Redis
        p_mastery_prev = float(await self._redis.get(cache_key) or params.prior)
        
        # BKT update:
        # P(L_t | correct) = P(L_{t-1}) * (1-slip) / [P(L_{t-1}) * (1-slip) + (1-P(L_{t-1})) * guess]
        if response_correct:
            p_evidence = p_mastery_prev * (1 - params.slip) + (1 - p_mastery_prev) * params.guess
            p_mastery_given_response = (p_mastery_prev * (1 - params.slip)) / p_evidence
        else:
            p_evidence = p_mastery_prev * params.slip + (1 - p_mastery_prev) * (1 - params.guess)
            p_mastery_given_response = (p_mastery_prev * params.slip) / p_evidence
        
        # Apply learning rate
        p_mastery_new = p_mastery_given_response + (1 - p_mastery_given_response) * params.learn
        
        # Write back to Redis (TTL = 7 days)
        await self._redis.setex(cache_key, 604800, str(p_mastery_new))
        
        return p_mastery_new
```

### Grade-Specific Calibration Strategy

After collecting sufficient student response data (target: 500+ student-standard interactions per grade per standard), the team runs BKT model fitting via `pyBKT`'s EM algorithm on the accumulated data. Calibrated parameters replace defaults in the `bkt_standard_params` table. The service loads calibrated parameters at startup and applies them preferentially. This calibration cycle should run quarterly once each grade has accumulated sufficient data.

**Calibration priority order:**
1. Per-standard calibrated parameters (highest fidelity)
2. Per-domain defaults within a grade (intermediate)
3. Per-grade defaults (fallback for new standards)

## 7.3 Grade-Aware API Endpoints

The existing API follows a versioned path structure under `/api/v1/`. Grade awareness is added as a **path parameter** (not a query parameter) for resource-scoped operations, enabling clean caching semantics and RESTful resource hierarchies.

### Pattern: Grade as Path Segment

```
GET  /api/v1/grades/{grade}/standards
GET  /api/v1/grades/{grade}/standards/{code}
GET  /api/v1/grades/{grade}/assessment/config
POST /api/v1/grades/{grade}/assessment/sessions
GET  /api/v1/grades/{grade}/question-bank/sample
POST /api/v1/grades/{grade}/questions/generate
```

### Updated Standards Endpoint

```python
# apps/api/src/api/v1/standards.py

from fastapi import APIRouter, Path, Depends, Query
from typing import Optional

router = APIRouter(prefix="/grades/{grade}/standards", tags=["standards"])

@router.get("/", response_model=StandardsListResponse)
async def list_standards_by_grade(
    grade: int = Path(..., ge=0, le=8, description="Grade level (0=K, 1-8)"),
    domain: Optional[str] = Query(None, description="Filter by domain, e.g. '1.OA'"),
    include_prerequisites: bool = Query(False, description="Include prior-grade prerequisite standards"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> StandardsListResponse:
    """
    Returns all active standards for a given grade.
    Grade 0 = Kindergarten (prerequisite pool only).
    If include_prerequisites=True, also returns the prior grade's prerequisite standards
    that are loaded into the system for remediation.
    """
    standards = await StandardsRepository(db).get_by_grade(
        grade=grade,
        domain=domain,
        include_prerequisites=include_prerequisites
    )
    return StandardsListResponse(grade=grade, standards=standards, count=len(standards))
```

### Student Grade Enrollment Endpoint

```python
# apps/api/src/api/v1/students.py

@router.put("/{student_id}/grade-enrollment")
async def update_student_grade(
    student_id: UUID,
    payload: GradeEnrollmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_parent),
):
    """
    Updates the grade a student is enrolled in.
    Changing grade does NOT delete existing skill states — they are archived
    and the student's cross-grade prerequisite gaps remain accessible.
    Only the parent can change grade enrollment (COPPA compliance).
    """
    # Validate parent owns this student_id
    student = await StudentRepository(db).get_with_parent_check(
        student_id=student_id, parent_id=current_user.sub
    )
    old_grade = student.current_grade
    new_grade = payload.grade
    
    # Archive current grade skill states
    await SkillStateRepository(db).archive_for_grade_transition(
        student_id=student_id, from_grade=old_grade, to_grade=new_grade
    )
    
    # Reset diagnostic status for new grade
    await StudentRepository(db).update_grade_enrollment(
        student_id=student_id, grade=new_grade
    )
    
    return GradeEnrollmentResponse(
        student_id=student_id, previous_grade=old_grade, new_grade=new_grade,
        message=f"Enrolled in Grade {new_grade}. Previous Grade {old_grade} progress has been archived."
    )
```

## 7.4 Grade-Aware Question Generation

The LangGraph question generation pipeline (introduced in Stage 2 of the Grade 4 product) uses a Jinja2 template that currently hardcodes Grade 4 context. For multi-grade expansion, grade context is injected dynamically into every prompt, governing vocabulary level, number ranges, question format constraints, visual element requirements, and reading level targets.

### Updated Question Generation Prompt Template

```jinja2
{# apps/api/prompts/question_gen_v2.0.jinja2 #}
You are an expert Oregon elementary mathematics question writer following the 2021 Oregon Math Standards v5.2.

## GRADE CONTEXT
- Target grade: {{ grade }}
- Student age range: {{ age_range }}
- Reading level target: Flesch-Kincaid Grade {{ fk_grade_target }}
- Number range: {{ number_range }}
- Fraction support: {{ fractions_allowed | ternary('YES — use visual fraction models only', 'NO — do not include fractions') }}
- Decimal support: {{ decimals_allowed | ternary('YES — up to ' + decimal_places + ' places', 'NO') }}

## QUESTION FORMAT CONSTRAINTS
Allowed question types for Grade {{ grade }}:
{% for qt in allowed_question_types %}
- {{ qt.name }}: {{ qt.description }}
{% endfor %}

## INTERACTION MODALITY CONSTRAINTS
{% if grade == 1 %}
- NO keyboard text input required. All answers must be: tap-to-select, drag-and-drop, or tap-on-image.
- ALL question text must be readable aloud via TTS. Keep sentences simple: subject + verb + object only.
- NO multi-sentence problem statements.
- Use concrete objects (apples, blocks, dogs) rather than abstract numbers wherever possible.
- Maximum 8 words in question stem.
{% elif grade == 2 %}
- Numeric keyboard input is acceptable for single/two-digit whole numbers only.
- Sentence length: maximum 12 words per sentence. Maximum 1 sentence.
- Use relatable contexts: classroom, playground, home, simple shopping.
- Number line drag interactions are acceptable.
{% elif grade == 3 %}
- Text word problems acceptable; max 2 sentences, Flesch-Kincaid Grade 2-3.
- Fraction visual models (pie chart, bar model, number line) must accompany any fraction question.
- Multiplication grid interactions are acceptable.
- Keyboard input for whole numbers and simple fractions (numerator / denominator fields).
{% elif grade == 4 %}
- Standard Grade 4 format per existing Grade 4 PRD.
{% elif grade == 5 %}
- Multi-sentence word problems acceptable (max 3 sentences).
- Coordinate plane interactions acceptable.
- Mixed number input (whole + numerator/denominator) acceptable.
- Decimal input to thousandths acceptable.
- Volume 3D manipulative descriptions acceptable.
{% endif %}

## TARGET STANDARD
Standard Code: {{ standard_code }}
Standard Text: {{ standard_description }}
DOK Level Target: {{ dok_level }}
Domain: {{ domain }}

## QUESTION REQUIREMENTS
Generate exactly 1 question at DOK {{ dok_level }} that:
1. Directly assesses {{ standard_code }}
2. Uses Oregon-appropriate contexts (Pacific Northwest settings, local names, familiar activities)
3. Has exactly 1 unambiguously correct answer
4. Includes 3 plausible distractors (if multiple choice) that target common misconceptions for this standard
5. Includes a step-by-step solution explanation (for hint generation)
6. Is mathematically accurate — double-check all arithmetic before outputting

## OUTPUT FORMAT
Return valid JSON matching this schema:
{
  "standard_code": "{{ standard_code }}",
  "grade": {{ grade }},
  "question_type": "<type>",
  "stem": "<question text>",
  "answer_options": [{"id": "A", "text": "...", "is_correct": false}, ...],
  "correct_answer": "<answer>",
  "solution_steps": ["step 1", "step 2", ...],
  "distractor_rationale": {"A": "targets misconception X", ...},
  "visual_asset_required": <true|false>,
  "visual_asset_description": "<description if true>",
  "tts_question_text": "<simplified text for TTS if different from stem>",
  "dok_level": {{ dok_level }},
  "estimated_fk_grade": <float>
}
```

### Grade Context Configuration

```python
# apps/api/src/core/grade_question_config.py

GRADE_QUESTION_CONFIGS = {
    1: {
        "age_range": "6-7",
        "fk_grade_target": 1.0,
        "number_range": "0-120 (whole numbers only)",
        "fractions_allowed": False,
        "decimals_allowed": False,
        "allowed_question_types": [
            {"name": "TAP_TO_SELECT", "description": "Student taps one of 3-4 image or text options"},
            {"name": "DRAG_AND_DROP", "description": "Student drags objects to match or count"},
            {"name": "PICTURE_CHOICE", "description": "All answer options are images"},
            {"name": "AUDIO_NUMERIC", "description": "Question read aloud, student taps correct number card"},
            {"name": "TRUE_FALSE", "description": "Simple true/false with visual support"},
        ],
    },
    2: {
        "age_range": "7-8",
        "fk_grade_target": 1.5,
        "number_range": "0-1000 (whole numbers only)",
        "fractions_allowed": False,
        "decimals_allowed": False,
        "allowed_question_types": [
            {"name": "NUMERIC_ENTRY_SHORT", "description": "Typed entry of 1-3 digit whole numbers"},
            {"name": "MULTIPLE_CHOICE", "description": "4 options, simple text + optional image"},
            {"name": "NUMBER_LINE_DRAG", "description": "Student drags a point to correct position on number line"},
            {"name": "CLOCK_INTERACTION", "description": "Student sets clock hands to correct time"},
            {"name": "COIN_SELECTION", "description": "Student selects coins to match an amount"},
        ],
    },
    3: {
        "age_range": "8-9",
        "fk_grade_target": 2.5,
        "number_range": "0-10,000 (whole numbers), unit fractions through eighths",
        "fractions_allowed": True,
        "decimals_allowed": False,
        "allowed_question_types": [
            {"name": "MULTIPLE_CHOICE", "description": "4 options, text word problem"},
            {"name": "NUMERIC_ENTRY", "description": "Typed entry of whole numbers up to 5 digits"},
            {"name": "FRACTION_VISUAL", "description": "Fraction pie/bar/number-line interaction"},
            {"name": "MULTIPLICATION_GRID", "description": "Fill in multiplication array or table"},
            {"name": "AREA_TILING", "description": "Visual rectangle with unit square counting"},
        ],
    },
    5: {
        "age_range": "10-11",
        "fk_grade_target": 4.0,
        "number_range": "Multi-digit whole numbers, decimals to thousandths, common fractions and mixed numbers",
        "fractions_allowed": True,
        "decimals_allowed": True,
        "decimal_places": "thousandths",
        "allowed_question_types": [
            {"name": "MULTIPLE_CHOICE", "description": "4 options, multi-sentence word problems"},
            {"name": "FRACTION_INPUT", "description": "Mixed number input (whole + numerator/denominator)"},
            {"name": "DECIMAL_INPUT", "description": "Decimal input to thousandths place"},
            {"name": "COORDINATE_PLANE", "description": "Plot or identify points on coordinate grid"},
            {"name": "VOLUME_BUILDER", "description": "3D unit cube manipulation for volume"},
            {"name": "LINE_PLOT", "description": "Read and interpret fractional line plot data"},
        ],
    },
}
```

## 7.5 Session Management: Multi-Grade Student Enrollment

### Grade Enrollment Data Model

Each student profile maintains a `current_grade` field and an archived history of prior-grade skill states. This enables:
- Cross-grade prerequisite gap detection (a Grade 4 student with Grade 2 unmastered skills)
- Grade advancement tracking (student completes Grade 3 and moves to Grade 4)
- Grade regression support (student placed in wrong grade gets moved back)

```sql
-- Student grade enrollment history
CREATE TABLE student_grade_enrollments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    grade           SMALLINT NOT NULL,
    enrolled_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,           -- NULL if current enrollment
    completion_reason VARCHAR(50),          -- 'ACADEMIC_PROGRESSION', 'MANUAL_PARENT', 'GRADE_CORRECTION'
    diagnostic_session_id UUID,             -- Diagnostic that established this enrollment
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_enrollments_student ON student_grade_enrollments(student_id);
CREATE INDEX idx_enrollments_grade ON student_grade_enrollments(grade);
```

### Grade Progression Logic

When a student's BKT mastery probability reaches ≥ 0.90 across ≥ 80% of grade-level standards, the system does not automatically advance them to the next grade. Grade advancement is always a **parent-initiated action**, surfaced through the parent dashboard as a recommendation:

> "Excellent news! Emma has mastered 24 of 25 Grade 3 standards. She is ready to begin Grade 4 content. [Review Progress] [Advance to Grade 4]"

On parent confirmation:
1. Current grade enrollment record is closed (`completed_at = NOW()`, `completion_reason = 'ACADEMIC_PROGRESSION'`)
2. New enrollment record is opened for the next grade
3. A new diagnostic assessment is triggered for the next grade
4. Prior grade skill states are archived (not deleted) — accessible for cross-grade gap detection
5. A congratulatory email is sent to the parent summarizing the completed grade journey

### Cross-Grade Prerequisite Resolution

When the adaptive engine determines that a student's gap in a current-grade standard is rooted in an unmastered prerequisite from a prior grade, it inserts a **prerequisite remediation mini-session** before returning to grade-level content. This mechanism, already built for Grade 3 → Grade 4 prerequisites, becomes a generalized pattern across all grade transitions.

```python
# apps/api/src/service/learning_plan_service.py (updated)

async def resolve_prerequisite_gap(
    student_id: UUID, blocked_standard_code: str, student_grade: int
) -> list[str]:
    """
    Returns an ordered list of prerequisite standard codes that must be addressed
    before the blocked_standard_code can be productively practiced.
    Traverses the prerequisite graph recursively, respecting grade boundaries.
    Max depth: 2 prior grades (e.g., Grade 4 student can be traced back to Grade 2).
    """
    prereqs = await PrerequisiteRepository.get_prerequisite_codes(blocked_standard_code)
    unmastered_prereqs = []
    
    for prereq_code in prereqs:
        prereq_grade = int(prereq_code.split('.')[0])
        # Only traverse up to 2 grade levels back
        if student_grade - prereq_grade <= 2:
            p_mastery = await BKTService.get_current_mastery(student_id, prereq_code)
            if p_mastery < 0.70:  # Unmastered threshold for prereq triggering
                unmastered_prereqs.append(prereq_code)
                # Recursively check this prerequisite's own prerequisites
                deeper = await resolve_prerequisite_gap(student_id, prereq_code, student_grade)
                unmastered_prereqs.extend(deeper)
    
    # Topological sort to ensure correct remediation order
    return topological_sort_standards(list(set(unmastered_prereqs)))
```

## 7.6 Parent Dashboard: Multi-Child, Multi-Grade View

The parent dashboard, designed in Stage 1 for a single Grade 4 child, must scale to support multiple children across multiple grades with distinct UI contexts. Key changes:

### Multi-Child Navigation

```
┌─────────────────────────────────────────┐
│  Parent Dashboard — Maria's Family      │
├─────────────────────────────────────────┤
│  [Emma — Grade 2 ●]  [Noah — Grade 4 ●] │  ← Tab bar; active child highlighted
├─────────────────────────────────────────┤
│  Emma | Grade 2 | 12 skills mastered   │
│  ████████░░░░░░░░ 46% complete          │
│                                         │
│  This week: 3 sessions (42 min total)  │
│  Last session: Yesterday               │
│  [View Full Report]  [Start Session]   │
└─────────────────────────────────────────┘
```

- Up to 5 children per parent account (unchanged from Stage 1 limit)
- Tab-based navigation between children; each child's interface adapts to their grade
- Grade label is always shown in parent-facing context (parents need to understand which grade their child is working on)
- Cross-grade vocabulary is normalized: "skill mastered" is consistent language regardless of grade level
- Parent sees grade-appropriate standards descriptions in plain English, auto-generated from the standard text

### Grade-Appropriate Parent Report Language

Standards are surfaced to parents with plain-English descriptions calibrated to the grade. The LLM generates these descriptions once and stores them in the `standards` table's `parent_description` column (added in this migration):

```sql
ALTER TABLE standards ADD COLUMN parent_description TEXT;
-- Populated via one-time LLM generation run after migration
-- Example: "Understanding that 10 tens make 100 (place value for hundreds)"
```

## 7.7 Teacher Dashboard: Multi-Grade Classroom Support

The teacher dashboard (Stage 5 of the existing product plan) requires multi-grade support from the moment it launches, since schools will have MathPath deployed across multiple grade levels simultaneously.

### Class-Level Multi-Grade View

```
┌──────────────────────────────────────────────────────────┐
│  Ms. Chen's Classroom — Grade 4 (26 students)           │
│  Filter: [All Standards ▼]  [All Domains ▼]             │
├──────────────────────────────────────────────────────────┤
│  Standards Mastery Heat Map                              │
│                                                          │
│  4.OA.A.1  ██████████████████░░░░ 22/26 mastered        │
│  4.OA.A.2  ████████████░░░░░░░░░░ 14/26 mastered ⚠      │
│  4.OA.A.3  ██████░░░░░░░░░░░░░░░░  8/26 mastered ⚠      │
│  ...                                                     │
│                                                          │
│  Grade 3 Prerequisite Gaps Detected:                    │
│  3.OA.C.7  ████░░░░░░░░░░░░░░░░░░  5/26 mastered ⚠⚠    │
│  (Blocking 18 students from mastering 4.NBT.B.5)        │
└──────────────────────────────────────────────────────────┘
```

For multi-grade schools (where a teacher manages mixed-grade or looping classrooms), the dashboard supports:
- Filtering by grade level within a classroom roster
- Cross-grade prerequisite gap identification (show which Grade 2 skills are blocking Grade 3 students)
- Group recommendation generation: "Students A, B, C share a gap in 2.NBT.B.5 — consider a small-group re-teach session"

## 7.8 Design System Tokens: Grade-Based Theme Overrides

The Grade 4 design system establishes baseline tokens in `packages/ui/src/tokens/`. Grade-specific theme overrides are applied via a `GradeThemeProvider` context that wraps the student application shell, injecting CSS custom properties that cascade through all child components.

```typescript
// packages/ui/src/tokens/grade-themes.ts

export interface GradeTheme {
  grade: number;
  minTouchTargetPx: number;
  bodyFontSizePx: number;
  numberFontSizePx: number;
  headingFontSizePx: number;
  sessionMaxMinutes: number;
  encouragementIntervalQuestions: number;
  ttsMode: 'AUTO_PLAY' | 'ON_DEMAND' | 'OFF_BY_DEFAULT';
  pipVerbosity: 'VERBOSE' | 'MODERATE' | 'STANDARD' | 'MINIMAL';
  primaryHue: string;
  surfaceHue: string;
  buttonRadius: string;
  iconSize: number;
}

export const GRADE_THEMES: Record<number, GradeTheme> = {
  1: {
    grade: 1,
    minTouchTargetPx: 60,
    bodyFontSizePx: 20,
    numberFontSizePx: 28,
    headingFontSizePx: 26,
    sessionMaxMinutes: 15,
    encouragementIntervalQuestions: 3,
    ttsMode: 'AUTO_PLAY',
    pipVerbosity: 'VERBOSE',
    primaryHue: 'hsl(52, 100%, 50%)',     // Bright warm yellow
    surfaceHue: 'hsl(52, 60%, 97%)',
    buttonRadius: '16px',                  // Rounder for younger students
    iconSize: 32,
  },
  2: {
    grade: 2,
    minTouchTargetPx: 48,
    bodyFontSizePx: 18,
    numberFontSizePx: 24,
    headingFontSizePx: 22,
    sessionMaxMinutes: 20,
    encouragementIntervalQuestions: 4,
    ttsMode: 'ON_DEMAND',
    pipVerbosity: 'MODERATE',
    primaryHue: 'hsl(199, 80%, 48%)',     // Sky blue
    surfaceHue: 'hsl(199, 40%, 97%)',
    buttonRadius: '12px',
    iconSize: 28,
  },
  3: {
    grade: 3,
    minTouchTargetPx: 44,
    bodyFontSizePx: 16,
    numberFontSizePx: 20,
    headingFontSizePx: 20,
    sessionMaxMinutes: 25,
    encouragementIntervalQuestions: 5,
    ttsMode: 'ON_DEMAND',
    pipVerbosity: 'STANDARD',
    primaryHue: 'hsl(160, 70%, 40%)',     // Teal-green (adjacent to Grade 4 base)
    surfaceHue: 'hsl(160, 30%, 97%)',
    buttonRadius: '10px',
    iconSize: 24,
  },
  4: {
    grade: 4,
    minTouchTargetPx: 44,
    bodyFontSizePx: 16,
    numberFontSizePx: 18,
    headingFontSizePx: 20,
    sessionMaxMinutes: 30,
    encouragementIntervalQuestions: 5,
    ttsMode: 'OFF_BY_DEFAULT',
    pipVerbosity: 'STANDARD',
    primaryHue: 'hsl(183, 100%, 22%)',    // Grade 4 existing teal (#01696F)
    surfaceHue: 'hsl(183, 30%, 97%)',
    buttonRadius: '8px',
    iconSize: 24,
  },
  5: {
    grade: 5,
    minTouchTargetPx: 44,
    bodyFontSizePx: 16,
    numberFontSizePx: 18,
    headingFontSizePx: 20,
    sessionMaxMinutes: 40,
    encouragementIntervalQuestions: 6,
    ttsMode: 'OFF_BY_DEFAULT',
    pipVerbosity: 'MINIMAL',
    primaryHue: 'hsl(256, 60%, 48%)',     // Purple — signals advanced content
    surfaceHue: 'hsl(256, 30%, 97%)',
    buttonRadius: '8px',
    iconSize: 24,
  },
};

// React context provider
export function GradeThemeProvider({ grade, children }: { grade: number; children: React.ReactNode }) {
  const theme = GRADE_THEMES[grade] ?? GRADE_THEMES[4];
  
  const cssVars = {
    '--touch-target-min': `${theme.minTouchTargetPx}px`,
    '--font-body': `${theme.bodyFontSizePx}px`,
    '--font-number': `${theme.numberFontSizePx}px`,
    '--font-heading': `${theme.headingFontSizePx}px`,
    '--color-primary': theme.primaryHue,
    '--color-surface': theme.surfaceHue,
    '--button-radius': theme.buttonRadius,
    '--icon-size': `${theme.iconSize}px`,
  } as React.CSSProperties;
  
  return (
    <GradeThemeContext.Provider value={theme}>
      <div style={cssVars}>{children}</div>
    </GradeThemeContext.Provider>
  );
}
```

---

# 8. Expansion Rollout Strategy

## 8.1 Recommended Expansion Order

The multi-grade expansion is sequenced to minimize risk and maximize learning from each phase before committing to the next. Grades that are architecturally closest to the existing Grade 4 implementation ship first; grades that require the most UI rework ship last after lessons from earlier phases are incorporated.

### Phase 1: Grade 3 + Grade 5 (Months 1–8 post-Grade-4-completion)

**Rationale:** Grades 3 and 5 are the most natural extensions of the existing Grade 4 codebase. Grade 3 already exists as the prerequisite content layer for Grade 4 — 9 standards and their questions are already in the database. Grade 5 extends Grade 4 patterns (same design system, same touch target sizes, same session lengths, same UI interaction paradigms) with new content domains (coordinate plane, volume, unlike-denominator fractions). Neither grade requires the TTS integration layer, the enlarged touch target system, or the visual-only interaction paradigm that Grade 1 demands.

| Sub-phase | Duration | Deliverable |
|-----------|----------|-------------|
| 1a: Standards + Question Bank (G3) | Months 1–2 | Full 25 Grade 3 standards in DB; 120 seed questions created and validated |
| 1b: Standards + Question Bank (G5) | Months 1–2 | Full 26 Grade 5 standards in DB; 125 seed questions created and validated |
| 1c: BKT param initialization (G3 + G5) | Month 2 | Default BKT params seeded; per-standard calibration initiated |
| 1d: Diagnostic assessment (G3 + G5) | Month 3 | Adaptive diagnostics built and tested for both grades |
| 1e: New G5 UI components | Months 3–4 | Coordinate plane component, volume builder, mixed-number input |
| 1f: Grade-aware API updates | Month 4 | All endpoints grade-parameterized; multi-grade session management |
| 1g: Parent/teacher dashboard updates | Month 5 | Multi-grade parent dashboard; Grade 3 and 5 reports |
| 1h: Pilot (G3 + G5) | Months 6–7 | 50-student pilot; collect BKT calibration data |
| 1i: GA launch (G3 + G5) | Month 8 | Public release of Grade 3 and Grade 5 |

**Shared infrastructure vs. grade-specific (Phase 1):**
- Shared: standards DB, prerequisite graph, BKT engine, question gen pipeline, parent dashboard
- Grade 3 specific: content only (questions, standards, BKT params, diagnostic config)
- Grade 5 specific: content + 3 new UI components (CoordinatePlane, VolumeBuilder3D, MixedNumberInput)

### Phase 2: Grade 2 (Months 9–16 post-Grade-4-completion)

**Rationale:** Grade 2 introduces moderate UI changes for younger users (ages 7–8): slightly larger touch targets (48px), simpler word problems, number line drag interactions, clock interaction UI, and coin selection UI. The TTS system is added in on-demand mode (not auto-play). These changes are contained — they extend the existing component library rather than replacing it. The primary new build work is the clock interaction widget (`<ClockFace>`) and the coin selection widget (`<CoinTray>`), plus the number line drag interaction (an extension of the existing `<NumberLine>` component in the math-renderer package).

| Sub-phase | Duration | Deliverable |
|-----------|----------|-------------|
| 2a: Standards + Question Bank (G2) | Months 9–10 | Full 26 Grade 2 standards in DB; 125 seed questions |
| 2b: TTS integration (on-demand mode) | Months 9–10 | Web Speech API / Amazon Polly integration; TTS trigger on speaker icon tap |
| 2c: New G2 UI components | Months 10–12 | ClockFace, CoinTray, NumberLineDrag, SimpleTextWordProblem |
| 2d: Grade 2 diagnostic + BKT | Month 12 | Diagnostic with 25–30 items; BKT params seeded |
| 2e: Grade-band theme tokens (G2) | Month 12 | 48px touch targets, 18px body, 24px numbers |
| 2f: Pip — Grade 2 moderate mode | Month 13 | Mascot configured for on-demand guidance |
| 2g: Parent dashboard Grade 2 reports | Month 13 | Plain-language G2 standard descriptions |
| 2h: Pilot (G2) | Months 14–15 | 40-student pilot; ages 7-8 usability testing |
| 2i: GA launch (G2) | Month 16 | Public release of Grade 2 |

**Key UX risk:** 7-year-olds have significantly less fine-motor precision than 9-year-olds. The pilot must include direct observation of students using the clock interaction and coin selection widgets to validate that 48px targets are sufficient. If error rates on these interactions exceed 15% due to touch accuracy issues, targets should be increased to 52px for this grade.

### Phase 3: Grade 1 (Months 17–26 post-Grade-4-completion)

**Rationale:** Grade 1 is the most significant engineering and design challenge in the expansion. It requires: (1) mandatory auto-play TTS for every question (pre-literacy assumption), (2) complete elimination of keyboard input (tap, drag, and select only), (3) 60px minimum touch targets across all interactive elements, (4) picture-based and manipulative-based question formats that have no precedent in the Grade 4 codebase, and (5) the full Pip "verbose mode" with step-by-step audio guidance on every problem. This is approximately 60% new frontend work and represents a materially different interaction paradigm from Grades 3–5.

| Sub-phase | Duration | Deliverable |
|-----------|----------|-------------|
| 3a: Standards + Question Bank (G1) | Months 17–18 | Full 22 Grade 1 standards; 110 seed questions (all visual/audio format) |
| 3b: TTS auto-play architecture | Months 17–19 | Amazon Polly integration; question audio pre-generation pipeline; offline audio caching |
| 3c: Visual question format library | Months 18–21 | PictureChoice, DragCounters, TapToSelect, AudioNumericCard, ObjectGrouping components |
| 3d: Kindergarten prerequisite content | Month 19 | 8 K prerequisite standards + 40 seed questions |
| 3e: Grade 1 diagnostic (audio-first) | Month 21 | 20–25 item diagnostic with all questions delivered via TTS |
| 3f: Pip verbose mode | Months 21–22 | Full audio guidance script; Pip animation states for each hint level |
| 3g: 60px touch target audit | Month 22 | Full accessibility audit: every interactive element ≥ 60px; tap target spacing ≥ 8px |
| 3h: Session break prompts (12-15 min) | Month 22 | Proactive break prompt with animated rest screen |
| 3i: Grade-band theme (G1) | Month 22 | Bright yellow palette; 20px body; 28px numbers; rounder components |
| 3j: Pilot — ages 6-7 | Months 23–24 | 30-student pilot; observational sessions; parent interview |
| 3k: Accessibility audit (WCAG 2.1 AA) | Month 24 | Full accessibility audit specific to pre-reader interaction patterns |
| 3l: GA launch (G1) | Month 26 | Public release of Grade 1 |

**Critical UX risk — TTS audio generation latency:** If TTS is generated on-demand at question delivery time, 6-year-olds will experience a perceptible delay before the question is read. Audio must be pre-generated and cached at question bank build time. The pipeline should:
1. Generate question audio for every seed question at build time (Amazon Polly, `en-US-Joanna` voice, child-friendly pace)
2. Store audio files in S3 with CloudFront CDN distribution
3. Pre-fetch the next 3 questions' audio during each current question session (predictive caching)
4. Fall back to Web Speech API (browser-native TTS) if CDN audio is unavailable

## 8.2 Content Creation Priorities (Question Bank Seeding Order)

Within each phase, question bank seeding follows this priority order:

1. **Standards with the highest prerequisite fan-out** — standards that are prerequisites for many other standards get questions created first, because diagnostic gaps in these standards block the most downstream learning paths.
2. **Standards with DOK 1–2** — lower-complexity standards have more predictable question formats and can be generated by the LLM pipeline with less human validation overhead. Get these into the bank first to enable diagnostic testing.
3. **Standards with DOK 3** — multi-step reasoning standards require more careful human validation and diverse context generation. These are created in batches after the DOK 1–2 bank is established.
4. **Prerequisite standards from prior grade** — the prior grade's prerequisite pool needs at least 4–5 questions per standard before the diagnostic can adequately assess those gaps.

**Minimum viable question bank per standard for launch:**
- DOK 1 standards: 4 questions minimum (ensures adequate variety before LLM generation kicks in)
- DOK 2 standards: 5 questions minimum
- DOK 3 standards: 6 questions minimum (more diversity needed to assess complex reasoning)

**Target question bank at launch per grade:**

| Grade | Standards | Target Questions | Min Questions |
|-------|-----------|-----------------|---------------|
| 1 | 22 (+ 8 K prereqs) | 120 | 100 |
| 2 | 26 (+ 8 G1 prereqs) | 130 | 110 |
| 3 | 25 (+ 8 G2 prereqs) | 125 | 105 |
| 5 | 26 (+ 9 G4 prereqs) | 130 | 110 |

## 8.3 Testing Strategy: Multi-Grade Regression

Every new grade release must pass:

### Automated Test Coverage Requirements

| Test Category | Coverage Target | Tool |
|---------------|-----------------|------|
| Unit tests — BKT per-grade params | 100% of grade configs | pytest |
| Unit tests — grade-aware API endpoints | 100% of new grade path params | pytest + FastAPI TestClient |
| Unit tests — grade theme tokens | 100% of GradeTheme properties | Jest |
| Integration tests — full diagnostic flow per grade | All 4 new grades | pytest + MSW |
| E2E tests — student takes diagnostic (per grade) | All 4 new grades | Playwright |
| E2E regression — Grade 4 unchanged | All existing Grade 4 E2E tests | Playwright |
| Accessibility — WCAG 2.1 AA | All grade student UIs | axe-core + manual |
| LLM contract tests — question format per grade | All 4 grade configs | Custom JSON schema validator |
| Content accuracy — seed questions | 100% of seed questions | Human review + automated math checker |

### Grade Regression Test Matrix

Before any new grade is released, the team runs a full regression test across all previously released grades:

```
Release Grade 3 → Run: G4 regression ✓ + G3 new grade tests ✓
Release Grade 5 → Run: G4 regression ✓ + G3 regression ✓ + G5 new grade tests ✓
Release Grade 2 → Run: G5 ✓ + G4 ✓ + G3 ✓ + G2 new grade tests ✓
Release Grade 1 → Run: G5 ✓ + G4 ✓ + G3 ✓ + G2 ✓ + G1 new grade tests ✓
```

No new grade is released if any prior grade's regression tests are failing. This is enforced as a CI/CD gate in the `deploy-production.yml` workflow.

### Usability Testing Requirements

Each grade must pass a structured usability test with real students before GA launch:

| Grade | Participant Count | Age Range | Session Type | Key Metrics |
|-------|------------------|-----------|--------------|-------------|
| 1 | 30 students minimum | 6.0–7.5 years | In-person observation | Task completion rate ≥ 80%; TTS comprehension ≥ 90% |
| 2 | 30 students minimum | 7.0–8.5 years | In-person + remote | Task completion rate ≥ 85%; clock/coin widget accuracy ≥ 85% |
| 3 | 40 students minimum | 8.0–9.5 years | Remote (video recorded) | Task completion rate ≥ 88%; fraction visual comprehension ≥ 85% |
| 5 | 40 students minimum | 10.0–11.5 years | Remote | Task completion rate ≥ 90%; coordinate plane accuracy ≥ 88% |

---

# 9. Future Extensibility Considerations

## 9.1 Adding Grade 6+ Without Architectural Changes

The multi-grade architecture established by this expansion is specifically designed to accommodate Grade 6 (and beyond, through Grade 8) without schema changes, without new API patterns, and without UI paradigm shifts. Here is the complete checklist for adding Grade 6:

1. **Standards data**: Insert Grade 6 Oregon standards into the `standards` table with `grade = 6`. The schema already supports any `SMALLINT` value. No migration required.
2. **Prerequisite edges**: Insert Grade 5 → Grade 6 prerequisite edges into `prerequisite_relationships`. The graph traversal logic already handles arbitrary grade depths.
3. **Question bank**: Use the existing LangGraph question generation pipeline with Grade 6 context injected via `GRADE_QUESTION_CONFIGS[6]` — add one config entry to the dictionary.
4. **BKT params**: Add `GRADE_BKT_DEFAULTS[SupportedGrade.GRADE_6]` to the BKT service — add one entry to the dictionary.
5. **Assessment config**: Insert one row into `assessment_configs` for Grade 6.
6. **UI theme**: Add `GRADE_THEMES[6]` to the grade themes token file. Grade 6 students (ages 11–12) use the same interaction paradigm as Grade 5 (standard touch targets, keyboard input, no mandatory TTS). Add one entry to the dictionary.
7. **API**: Grade as a path parameter is already unbounded (`ge=0, le=8`). Grade 6 works immediately.
8. **Parent dashboard**: Multi-child, multi-grade view is already built. Grade 6 label renders automatically.
9. **Teacher dashboard**: Grade filtering already supports arbitrary grade values.

**Estimated effort for Grade 6 expansion (after this architecture is in place):** 8–12 weeks for content creation (standards entry, question bank seeding, validation), 2–4 weeks for engineering (config entries, BKT params, diagnostic tuning), 4–6 weeks for pilot and launch. Total: 14–22 weeks, compared to the 26 weeks required for Grade 1 which required new UI paradigm development.

## 9.2 Adding Other States' Standards

The `standards` table's `version_tag` column can be extended to a `state_code + version` pattern to support other states' math standards. The architecture for Oregon's multi-grade system is directly reusable for any state that adopts standards in the OA / NBT / NF / GM / DR domain structure (which mirrors Common Core, followed by most states).

### Schema Extension for Multi-State Support

```sql
-- Add state_code to standards table when expanding beyond Oregon
ALTER TABLE standards ADD COLUMN state_code VARCHAR(2) NOT NULL DEFAULT 'OR';
ALTER TABLE standards ADD COLUMN state_standard_version VARCHAR(20) NOT NULL DEFAULT 'OAS-2021';

-- Composite index for multi-state queries
CREATE INDEX idx_standards_state_grade ON standards(state_code, grade);

-- Update the UNIQUE constraint on code to be per-state
ALTER TABLE standards DROP CONSTRAINT IF EXISTS standards_code_key;
ALTER TABLE standards ADD CONSTRAINT standards_state_code_unique UNIQUE (state_code, code);
```

### State-Aware API Pattern

```
GET /api/v1/states/{state_code}/grades/{grade}/standards
```

This requires no changes to the BKT engine, the question generation pipeline, or the UI — all of these are already grade-and-content-aware. The primary work for a new state is:
1. Standards data entry (can be largely automated with an LLM parsing the state's standards PDF)
2. Prerequisite graph definition (expert review required — approximately 2–3 days per grade)
3. Question bank seeding (same process as Oregon, 8–12 weeks per grade)
4. Any state-specific context in question generation prompts (geography, names, school system references)

### Priority State Targets

After Oregon is fully operational across all grades, the recommended expansion order by state based on market size and standards similarity to Oregon:

| Priority | State | Grades Supported | Standards Similarity to Oregon | Market Size |
|----------|-------|-----------------|--------------------------------|-------------|
| 1 | Washington | K–8 | High (both use CCSS-derived standards) | 1.1M elementary students |
| 2 | California | K–8 | High (CCSS with state additions) | 3.5M elementary students |
| 3 | Colorado | K–8 | High (CCSS-aligned) | 490K elementary students |
| 4 | Idaho | K–8 | High (CCSS-aligned) | 180K elementary students |

## 9.3 Internationalization Beyond English

The existing product plan includes Spanish (Español) localization for Stage 5. The multi-grade expansion must not introduce any internationalization (i18n) technical debt. All user-facing strings — question stems, hint text, encouragement messages, Pip dialogue, UI labels — are externalized into i18n JSON files from the start, enabling Spanish and future language additions without code changes.

### i18n Architecture

```typescript
// apps/web/src/lib/i18n/en.json (excerpt)
{
  "pip": {
    "greeting": "Hi {{name}}! Let's do some math!",
    "grade1_encouragement_correct": "You got it! Great work!",
    "hint_level_1": "Let's look at this together.",
    "break_prompt": "You've been working hard! Want to take a short break?"
  },
  "assessment": {
    "intro_title": "Let's find out what you know!",
    "intro_subtitle": "This isn't a test — it helps us pick the best problems for you.",
    "question_counter": "Question {{current}} of about {{total}}"
  }
}
```

```typescript
// apps/web/src/lib/i18n/es.json (for Stage 5)
{
  "pip": {
    "greeting": "¡Hola {{name}}! ¡Hagamos matemáticas!",
    ...
  }
}
```

**Grade 1 TTS and Spanish:** When Spanish localization is added, Grade 1 TTS must use Spanish voice synthesis. Amazon Polly supports `es-US` locale. The TTS audio pre-generation pipeline must run for each supported language, producing `{question_id}_{locale}.mp3` files. The audio selection follows the student's language preference set in the parent account.

## 9.4 Grade Placement Assessment

A student newly enrolling in MathPath may not know their appropriate grade level — or may be enrolled in a grade that doesn't match their actual skill level. The grade placement assessment is a short (12–15 item) adaptive assessment that spans two adjacent grade levels and recommends the grade at which the student should begin.

### Placement Assessment Design

```
Grade Placement Assessment Flow:

Student enters grade: 3 (self-reported or parent-selected)
↓
Placement assessment samples 4 standards from Grade 2 (prior grade) and 8 standards from Grade 3
↓
Adaptive scoring:
  - If ≥75% correct on Grade 3 content → confirm Grade 3 enrollment
  - If <40% correct on Grade 3 content AND <60% correct on Grade 2 content → recommend Grade 2
  - If >90% correct on Grade 3 content → flag for Grade 4 consideration (parent review)
↓
Parent receives recommendation:
  "Based on the placement assessment, we recommend starting {{name}} in Grade {{recommended_grade}}.
   This grade level will challenge them appropriately and help them build confidence."
↓
Parent confirms or overrides placement → enrollment set
```

The placement assessment uses the same BKT diagnostic engine as the grade-level diagnostic — it is a scoped version with cross-grade item sampling. No new technical infrastructure is required; it is a configuration of the existing diagnostic service with `cross_grade_sampling = True` and `grade_range = [current_grade - 1, current_grade]`.

---

# 10. Appendix: Kindergarten Standards Reference

This appendix provides a complete listing of all Kindergarten Oregon 2021 Math Standards. These standards serve as the prerequisite pool for Grade 1 diagnostic assessment and remediation. Eight of these standards are loaded into the MathPath database as Grade 1 prerequisite standards (flagged `is_prerequisite = TRUE`, `grade = 0`). The full 23-standard listing is provided here for reference and for future Kindergarten product planning.

**Kindergarten Overview — Critical Areas of Focus:**
Kindergarten establishes the entire number sense foundation. The critical areas are: (1) representing, relating, and operating on whole numbers in a concrete setting — with objects and in authentic contexts; (2) describing shapes and space. Much of the Kindergarten curriculum focuses on developing deep understanding of counting and cardinality — the connection between quantities and the numbers that name them — rather than computation. The NCC (Numeric Reasoning: Counting and Cardinality) domain is unique to Kindergarten and has no analog in Grades 1–5.

## K.OA — Algebraic Reasoning: Operations (5 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| K.OA.A.1 | Understand addition and subtraction | Represent addition as putting together and adding to, and subtraction as taking apart and taking from, using objects, drawings, physical expressions, numbers or equations to represent authentic contexts. | 1 |
| K.OA.A.2 | Understand addition and subtraction | Add and subtract within 10. Model authentic contexts and solve problems using the strategies of addition and subtraction within 10. | 1 |
| K.OA.A.3 | Understand addition and subtraction | Using objects, drawings, or equations, decompose numbers less than or equal to 10 into pairs in more than one way, and record each decomposition by a drawing or equation (e.g., 5 = 2 + 3 and 5 = 4 + 1). | 2 |
| K.OA.A.4 | Understand addition and subtraction | For any number from 1 to 9, find the number that makes 10 when added to the given number, e.g., by using objects or drawings, and record the answer with a drawing or equation. | 1 |
| K.OA.A.5 | Understand addition and subtraction | Fluently add and subtract within 5 with accurate, efficient, and flexible strategies. | 1 |

**Domain total: 5 standards**

## K.NCC — Numeric Reasoning: Counting and Cardinality (7 Standards)

*Note: This domain is unique to Kindergarten. It does not appear in any other grade. It establishes the foundational counting principles that underpin all subsequent number work.*

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| K.NCC.A.1 | Know number names and the count sequence | Orally count to 100 by ones and by tens in sequential order. | 1 |
| K.NCC.A.2 | Know number names and the count sequence | Count forward beginning from a given number within 100 of a known sequence (instead of having to begin at 1). | 1 |
| K.NCC.A.3 | Know number names and the count sequence | Identify number names, write numbers, and the count sequence from 0–20. Represent a number of objects with a written number 0–20 (with 0 representing a count of no objects). | 1 |
| K.NCC.B.4 | Count to tell the number of objects | Understand the relationship between numbers and quantities; connect counting to cardinality. When counting objects, say the number names in the standard order, pairing each object with one and only one number name and each number name with one and only one object (one-to-one correspondence). Understand that the last number name said tells the number of objects counted. Understand that each successive number name refers to a quantity that is one larger. | 1 |
| K.NCC.B.5 | Count to tell the number of objects | Count to answer "how many?" questions about as many as 20 things arranged in a line, a rectangular array, or a circle, or as many as 10 things in a scattered configuration; given a number from 1–20, count out that many objects. | 1 |
| K.NCC.C.6 | Compare numbers | Identify whether the number of objects in one group is greater than, less than, or equal to the number of objects in another group, e.g., by using matching and counting strategies. | 1 |
| K.NCC.C.7 | Compare numbers | Compare two numbers between 1 and 10 presented as written numerals. | 1 |

**Domain total: 7 standards**

## K.NBT — Numeric Reasoning: Base Ten Arithmetic (1 Standard)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| K.NBT.A.1 | Work with numbers 11–19 to gain foundations for place value | Compose and decompose numbers from 11 to 19 into ten ones and some further ones, e.g., by using objects or drawings, and record each composition or decomposition by a drawing or equation (e.g., 18 = 10 + 8); understand that these numbers are composed of ten ones and one, two, three, four, five, six, seven, eight, or nine ones. | 2 |

**Domain total: 1 standard**

## K.GM — Geometric Reasoning and Measurement (8 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| K.GM.A.1 | Identify and describe shapes | Describe objects in the environment using names of shapes, and describe the relative positions of these objects using terms such as above, below, beside, in front of, behind, and next to. | 1 |
| K.GM.A.2 | Identify and describe shapes | Correctly name shapes regardless of their orientations or overall size. Common two-dimensional shapes include: square, circle, triangle, rectangle, hexagon. Common three-dimensional shapes include: cube, cone, cylinder, and sphere. | 1 |
| K.GM.A.3 | Identify and describe shapes | Identify shapes as two-dimensional (lying in a plane, "flat") or three-dimensional ("solid"). | 1 |
| K.GM.B.4 | Analyze, compare, create, and compose shapes | Analyze and compare two- and three-dimensional shapes, in different sizes and orientations, using informal language to describe their similarities, differences, parts (e.g., number of sides and vertices/corners) and other attributes (e.g., having sides of equal length). | 2 |
| K.GM.B.5 | Analyze, compare, create, and compose shapes | Model shapes in the world by building shapes from components (e.g., sticks and clay balls) and drawing shapes. | 1 |
| K.GM.B.6 | Analyze, compare, create, and compose shapes | Compose simple shapes to form larger shapes. For example, "Can you join these two triangles with full sides touching to make a rectangle?" | 2 |
| K.GM.C.7 | Describe and compare measurable attributes | Describe several measurable attributes of a single object. For example, a ball has a size and a weight. | 1 |
| K.GM.C.8 | Describe and compare measurable attributes | Directly compare two objects with a measurable attribute in common, to see which object has "more of"/"less of" the attribute, and describe the difference. For example, directly compare the heights of two children and describe one child as taller/shorter. | 1 |

**Domain total: 8 standards**

## K.DR — Data Reasoning (2 Standards)

| Standard ID | Cluster | Full Standard Text | DOK |
|-------------|---------|-------------------|-----|
| K.DR.A.1 | Generate and represent data | Generate questions to investigate situations within the classroom. Collect and consider data by sorting and counting objects into categories. | 1 |
| K.DR.B.2 | Analyze data and interpret results | Analyze data sets by counting the number of objects in each category and sorting the categories by count. Interpret results by classifying and sorting objects by color, shape, size, and other attributes. | 2 |

**Domain total: 2 standards**

## Kindergarten Standards Summary

| Domain | Full Name | Standards Count |
|--------|-----------|-----------------|
| K.OA | Algebraic Reasoning: Operations | 5 |
| K.NCC | Numeric Reasoning: Counting and Cardinality | 7 |
| K.NBT | Numeric Reasoning: Base Ten Arithmetic | 1 |
| K.GM | Geometric Reasoning and Measurement | 8 |
| K.DR | Data Reasoning | 2 |
| **Total** | | **23** |

## Kindergarten → Grade 1 Prerequisite Mapping

Of the 23 Kindergarten standards, 8 are designated as Grade 1 prerequisites and loaded into the MathPath database. The remaining 15 are reference-only at this stage. The 8 loaded prerequisites are:

| Kindergarten Standard | Loads Into MathPath As | Primary Grade 1 Standard Gated |
|-----------------------|----------------------|--------------------------------|
| K.OA.A.2 | Grade 0 prerequisite | 1.OA.A.1 (add/subtract within 20) |
| K.OA.A.5 | Grade 0 prerequisite | 1.OA.C.6 (fluency within 10) |
| K.OA.A.4 | Grade 0 prerequisite | 1.OA.C.6 (make-10 strategies) |
| K.NCC.A.3 | Grade 0 prerequisite | 1.NBT.A.1 (count to 120) |
| K.NCC.B.4 | Grade 0 prerequisite | 1.OA.A.1 (represent problem situations) |
| K.NCC.C.7 | Grade 0 prerequisite | 1.NBT.B.3 (compare two-digit numbers) |
| K.NBT.A.1 | Grade 0 prerequisite | 1.NBT.B.2 (understand place value) |
| K.GM.B.6 | Grade 0 prerequisite | 1.GM.A.2 (compose 2D/3D shapes) |

**Kindergarten prerequisite questions required:** 4–5 questions per standard = 32–40 questions minimum. These questions must be entirely visual/audio-based (same format requirements as Grade 1), as they will be administered to Grade 1 students who are diagnosed with Kindergarten prerequisite gaps.

## Kindergarten as Future Product Tier

When MathPath expands to include Kindergarten as a full product offering (not just a prerequisite pool), the following additional work is required beyond inserting the remaining 15 standards:

1. **NCC domain support**: The Counting and Cardinality domain has no analog in Grades 1–5. It requires entirely new question formats: oral counting (microphone input or tap-to-count), object counting with drag-and-match, number-to-quantity pairing. These are substantially different from any existing component.
2. **Age-appropriate design (ages 5–6)**: Kindergarteners have larger fine-motor variability than first graders. Touch targets should be 72px minimum. Sessions should be 8–10 minutes maximum. All interactions must be audio-first with no reading required whatsoever.
3. **COPPA considerations**: Kindergarteners are typically 5 years old — under COPPA's primary threshold. The existing COPPA consent flow covers this, but special attention is required for any data collection mechanisms (no voice recording can be stored without explicit written consent beyond standard COPPA).
4. **Estimated effort**: 12–16 additional weeks beyond the infrastructure established by Grade 1 expansion, primarily for NCC domain question formats and the more stringent age-appropriate design requirements.

---

*Document revision history:*

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | April 2026 | Product & Engineering Leadership | Initial comprehensive expansion blueprint |

---

*End of Document — MathPath Oregon Multi-Grade Expansion (Grades 1, 2, 3, 5)*
