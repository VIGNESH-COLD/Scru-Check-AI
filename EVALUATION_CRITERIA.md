# ScruCheckAI Evaluation Criteria & Metrics

ScruCheckAI uses a strict two-section evaluation model. This separates basic institutional compliance from academic quality, ensuring that critical rules are enforced while providing a nuanced, mathematically defensible quality assessment.

---

## 1. Overall Decision Logic

The system evaluates the paper sequentially. The final decision is determined by the lowest triggered threshold:

1. **REJECTED** ❌ 
   - Any Mandatory Compliance check returns `FAIL`.
   - Syllabus Coverage score is `< 40` (critical violation).
2. **CONDITIONAL** ⚠️
   - Syllabus Coverage score is `< 50` (insufficient coverage).
   - The Average Quality Score across applicable metrics is `< 60`.
3. **APPROVED** ✅
   - All Mandatory Compliance checks return `PASS`.
   - Syllabus Coverage is `≥ 50`.
   - The Average Quality Score is `≥ 60`.

---

## 2. Section 1: Mandatory Compliance (Pass/Fail)

These metrics evaluate whether the paper adheres to institutional rules. A failure in any of these immediately marks the paper as **REJECTED**.

1. **Format Compliance:** Checks section structure, numbering conventions, and overall layout.
2. **Regulation Compliance:** Verifies course code, regulation year, semester, and subject details.
3. **Mark & Time Distribution:** Strictly validates section arithmetic, total marks, and allowed mark values (e.g., 2, 13, 15, 16). Also provides an academic complexity-based estimation of expected completion time.
4. **Permitted Aids:** Ensures adherence to rules regarding calculators, charts, and formula sheets.

---

## 3. Section 2: Quality Metrics (Weighted Scoring)

These metrics evaluate the academic rigor and linguistic quality of the question paper. Scores are combined using a **weighted average** to produce the **Overall Quality Score**. `N/A` scores are strictly excluded and their weights are redistributed proportionally to remaining criteria.

### Weights

| Criterion | Weight | Rationale |
|-----------|--------|----------|
| Syllabus Coverage | **35%** | Most critical academic metric — directly measures curriculum alignment |
| Bloom's Distribution | **25%** | Measures cognitive rigor of the paper |
| Grammar & Clarity | **15%** | Linguistic quality, important but not decisive |
| Repetition Risk | **15%** | Protects against recycled questions |
| Diagram Quality | **10%** | Contextual — `N/A` for theory papers with no symbols |

**Formula:**
```
Overall Quality = Σ(weight_i × score_i) / Σ(weight_i for applicable criteria)
```

**Example with a low syllabus score:**
```
Syllabus (35%): 40    → 40 × 0.35 = 14.0
Bloom's  (25%): 100   → 100 × 0.25 = 25.0
Grammar  (15%): 100   → 100 × 0.15 = 15.0
Repetition(15%): 100  → 100 × 0.15 = 15.0
Diagram  (10%): 100   → 100 × 0.10 = 10.0
                               ──────────
Overall Quality = 79 / 1.00 = 79   (not 88 as a simple average would give)
```

### Confidence Levels

Each quality metric exposes a confidence score (0.0–1.0) reflecting how certain the system is about its result. This is displayed as a badge in the UI:

| Badge | Confidence Range | Meaning |
|-------|------|--------|
| 🟢 **High** | ≥ 0.80 | Result is reliable; based on strong evidence |
| 🟡 **Medium** | 0.60–0.79 | Result is plausible; some ambiguity exists |
| 🔴 **Low** | < 0.60 | Result is uncertain; manual review recommended |

### 3.1 Syllabus Coverage
Evaluates semantic similarity between the question paper and the uploaded syllabus, enforcing scope boundaries based on exam type (e.g., CAT-1 limits questions to Units 1 & 2).

* **Formula:** `Score = max(0, ((Total Questions - Out of Scope Questions) / Total Questions) * 100)`
* **Fact:** Syllabus coverage is heavily weighted in the status engine. A score below 40 instantly rejects the paper, overriding any high scores in grammar or formatting.

### 3.2 Bloom's Taxonomy Distribution
Measures the cognitive complexity of the paper by mapping question verbs to Bloom's Taxonomy, comparing the actual distribution against an academically standard target.

* **Target Distribution:**
  * Lower-order (Remember + Understand) = **30%**
  * Apply = **30%**
  * Higher-order (Analyze + Evaluate + Create) = **40%**
* **Formula:** Target deviation model.
  * `Total Deviation = |actual_lower - 0.30| + |actual_apply - 0.30| + |actual_higher - 0.40|`
  * `Score = max(0, round(100 × (1 - Total Deviation / 1.4)))`
* **Fact:** The theoretical maximum deviation is ~1.4. This formula penalizes deviations in *any* direction, meaning a paper composed of 100% higher-order questions will score poorly because it lacks necessary foundational questions.

### 3.3 Grammar & Clarity
Detects linguistic issues such as poor punctuation, repeated verbs, ambiguous phrasing, and unclear quantifiers.

* **Formula:** `Score = round(100 - (Problematic Questions / Total Questions) * 100)`
* **Fact:** The score is calculated based on the *proportion of flawed questions*, rather than raw issue counts. A single badly written question with 10 grammar mistakes only penalizes the paper as 1 flawed question, preventing harsh, skewed scoring.

### 3.4 Repetition Risk
Compares the current paper against historical question banks to prevent excessive recycling of questions.

* **Formula:** `Score = 100 - min(60, (15 × Exact Matches) + (8 × Conceptual Matches))`
  * *Exact Match:* >85% semantic similarity.
  * *Conceptual Match:* 70% - 85% semantic similarity.
* **Fact:** The maximum penalty is capped at **60 points**. A paper that is heavily plagiarized from past years will score a 40 on this metric, ensuring it heavily drags down the average quality without generating a negative or mathematically destructive score.

### 3.5 Diagram & Symbol Quality
Verifies the integrity of mathematical symbols (e.g., `∑`, `∫`, `±`) and embedded images.

* **Formula / Logic:** 
  * `100` — All diagrams and mathematical symbols are perfectly readable.
  * `0` — Broken symbols, corrupted images, or unreadable equations are detected.
  * `N/A` — **No images and no special symbols are present.**
* **Fact:** If a paper has no diagrams or symbols (e.g., a pure theory paper), the score becomes `N/A` (null) rather than defaulting to `100`. This prevents artificial inflation of the Overall Quality Score.
