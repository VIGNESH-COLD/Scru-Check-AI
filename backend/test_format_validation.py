"""
Test: Format Validation — Pattern Comparison

Tests that FormatValidator correctly compares the user-SELECTED pattern
against the DETECTED pattern from the uploaded paper.

Test cases (as required):
  1. Paper follows Pattern 1 + Pattern 1 selected  => PASS
  2. Paper follows Pattern 1 + Pattern 2 selected  => FAIL
  3. Paper follows Pattern 2 + Pattern 1 selected  => FAIL
  4. Paper follows Pattern 2 + Pattern 2 selected  => PASS

Run with:
    .\\venv\\Scripts\\python.exe test_format_validation.py
"""

import asyncio
import sys

sys.path.insert(0, ".")  # Make sure backend package is importable

from services.analyzers.format_validator import FormatValidator

validator = FormatValidator()

# ── Pattern definitions (mirror university_patterns.json) ─────────────────────

PATTERN_1 = {
    "name": "University Pattern 1",
    "exam_type": "University",
    "sections": [
        {"name": "Part A", "questions": 10, "marks_per_question": 2,
         "description": "Short Answer (2 from each Unit)"},
        {"name": "Part B", "questions": 5, "marks_per_question": 13,
         "description": "Long Answer (1 from each Unit)"},
        {"name": "Part C", "questions": 1, "marks_per_question": 15,
         "description": "Application/Case Study (Unit V)"},
    ],
    "total_marks": 100,
    "time_minutes": 180,
}

PATTERN_2 = {
    "name": "University Pattern 2",
    "exam_type": "University",
    "sections": [
        {"name": "Part A", "questions": 10, "marks_per_question": 2,
         "description": "Short Answer (2 from each Unit)"},
        {"name": "Part B", "questions": 5, "marks_per_question": 16,
         "description": "Long Answer (1 from each Unit)"},
    ],
    "total_marks": 100,
    "time_minutes": 180,
}

# ── Synthetic "uploaded paper" content ────────────────────────────────────────

# A paper that structurally matches University Pattern 1
# (Part A: 10x2=20, Part B: 5x13=65, Part C: 1x15=15  => total 100)
PAPER_PATTERN_1 = {
    "filename": "test_paper_pattern1.pdf",
    "raw_text": (
        "DEPARTMENT OF COMPUTER SCIENCE\n"
        "END SEMESTER EXAMINATION\n"
        "Max. Marks: 100  Time: 3 Hours\n\n"
        "PART A (10 x 2 = 20)\n"
        "1. Define algorithm.\n"
        "2. What is time complexity?\n"
        "3. State the properties of Big-O notation.\n"
        "4. Define divide and conquer.\n"
        "5. What is dynamic programming?\n"
        "6. Define greedy algorithm.\n"
        "7. What is backtracking?\n"
        "8. Define NP-completeness.\n"
        "9. What is a spanning tree?\n"
        "10. Define minimum spanning tree.\n\n"
        "PART B (5 x 13 = 65)\n"
        "11. Explain merge sort with an example.\n"
        "12. Describe Dijkstra's shortest path algorithm.\n"
        "13. Explain the knapsack problem using dynamic programming.\n"
        "14. Describe Prim's algorithm for MST.\n"
        "15. Explain the travelling salesman problem.\n\n"
        "PART C (1 x 15 = 15)\n"
        "16. Design an efficient algorithm for the given case study on graph traversal.\n"
    ),
    "questions": [{"number": i, "text": f"Q{i}"} for i in range(1, 17)],
    "sections": [
        {"name": "PART A"},
        {"name": "PART B"},
        {"name": "PART C"},
    ],
    "image_info": {"has_images": False, "image_count": 0, "broken_images": 0},
}

# A paper that structurally matches University Pattern 2
# (Part A: 10x2=20, Part B: 5x16=80  => total 100, no Part C)
PAPER_PATTERN_2 = {
    "filename": "test_paper_pattern2.pdf",
    "raw_text": (
        "DEPARTMENT OF COMPUTER SCIENCE\n"
        "END SEMESTER EXAMINATION\n"
        "Max. Marks: 100  Time: 3 Hours\n\n"
        "PART A (10 x 2 = 20)\n"
        "1. Define algorithm.\n"
        "2. What is time complexity?\n"
        "3. State the properties of Big-O notation.\n"
        "4. Define divide and conquer.\n"
        "5. What is dynamic programming?\n"
        "6. Define greedy algorithm.\n"
        "7. What is backtracking?\n"
        "8. Define NP-completeness.\n"
        "9. What is a spanning tree?\n"
        "10. Define minimum spanning tree.\n\n"
        "PART B (5 x 16 = 80)\n"
        "11. Explain merge sort with an example.\n"
        "12. Describe Dijkstra's shortest path algorithm.\n"
        "13. Explain the knapsack problem using dynamic programming.\n"
        "14. Describe Prim's algorithm for MST.\n"
        "15. Explain the travelling salesman problem.\n"
    ),
    "questions": [{"number": i, "text": f"Q{i}"} for i in range(1, 16)],
    "sections": [
        {"name": "PART A"},
        {"name": "PART B"},
    ],
    "image_info": {"has_images": False, "image_count": 0, "broken_images": 0},
}

# ── Test runner ───────────────────────────────────────────────────────────────

PASS_MARK = "[PASS]"
FAIL_MARK = "[FAIL]"


async def run_tests():
    results = []

    tests = [
        {
            "id": 1,
            "description": "Paper follows Pattern 1  +  Pattern 1 selected  =>  PASS",
            "paper": PAPER_PATTERN_1,
            "selected_pattern": PATTERN_1,
            "expected_status": "PASS",
        },
        {
            "id": 2,
            "description": "Paper follows Pattern 1  +  Pattern 2 selected  =>  FAIL",
            "paper": PAPER_PATTERN_1,
            "selected_pattern": PATTERN_2,
            "expected_status": "FAIL",
        },
        {
            "id": 3,
            "description": "Paper follows Pattern 2  +  Pattern 1 selected  =>  FAIL",
            "paper": PAPER_PATTERN_2,
            "selected_pattern": PATTERN_1,
            "expected_status": "FAIL",
        },
        {
            "id": 4,
            "description": "Paper follows Pattern 2  +  Pattern 2 selected  =>  PASS",
            "paper": PAPER_PATTERN_2,
            "selected_pattern": PATTERN_2,
            "expected_status": "PASS",
        },
    ]

    print("=" * 70)
    print("  ScruCheck AI -- Format Validation Tests")
    print("=" * 70)
    print()

    for t in tests:
        result = await validator.analyze(
            question_paper=t["paper"],
            expected_pattern_obj=t["selected_pattern"],
        )

        actual_status = result["status"]
        passed = actual_status == t["expected_status"]
        icon = PASS_MARK if passed else FAIL_MARK
        results.append(passed)

        print(f"Test {t['id']}: {t['description']}")
        print(f"  Selected pattern : {t['selected_pattern']['name']}")
        print(f"  Detected pattern : {result['evidence']['detected_pattern']}")
        print(f"  Expected status  : {t['expected_status']}")
        print(f"  Actual status    : {actual_status}")
        print(f"  Result           : {icon}")
        print(f"  Remarks          : {result['remarks'][:120]}")
        print()

    passed_count = sum(results)
    total = len(results)
    print("=" * 70)
    if passed_count == total:
        print(f"ALL {total} TESTS PASSED")
    else:
        print(f"{total - passed_count}/{total} TESTS FAILED")
    print("=" * 70)

    return passed_count == total


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
