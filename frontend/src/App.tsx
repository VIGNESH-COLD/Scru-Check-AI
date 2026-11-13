import React, { useState, useMemo, useEffect } from "react";
import {
  Settings,
  Upload,
  BookOpen,
  CheckCircle2,
  XCircle,
  FileText,
  AlertTriangle,
  Copy,
  Check,
  X,
  Eye,
  ClipboardList,
  Layers,
  Filter,
  Repeat,
  GitCompare,
  BarChart3,
  GraduationCap,
  SpellCheck,
  Calculator,
  Clock,
  Activity,
  FileDown,
  Sun,
  Moon,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

interface PatternItem {
  id: string;
  name: string;
  subtitle: string;
  structure_hint: string;
  total_marks: number;
  time_minutes: number;
  sections: string[];
}

const PATTERNS_DATA: Record<string, PatternItem[]> = {
  "CAT-1": [
    {
      id: "CAT-1 (Unit I & II) - Standard",
      name: "CAT-1 (Unit I & II) - Standard",
      subtitle: "10×2, 2×15",
      structure_hint: "2 × PART A [5×2=10], 2 × PART B [1×15=15]",
      total_marks: 50,
      time_minutes: 90,
      sections: ["Part A", "Part B"],
    },
    {
      id: "CAT-1 (Unit I & II) - Alternate",
      name: "CAT-1 (Unit I & II) - Alternate",
      subtitle: "12×2, 2×13",
      structure_hint: "2 × PART A [6×2=12], 2 × PART B [1×13=13]",
      total_marks: 50,
      time_minutes: 90,
      sections: ["Part A", "Part B"],
    },
  ],
  "CAT-2": [
    {
      id: "CAT-2 (Unit III)",
      name: "CAT-2 (Unit III)",
      subtitle: "5×2, 1×15",
      structure_hint: "1 × PART A [5×2=10], 1 × PART B [1×15=15]",
      total_marks: 25,
      time_minutes: 45,
      sections: ["Part A", "Part B"],
    },
    {
      id: "CAT-2 (Unit III) - Alternate",
      name: "CAT-2 (Unit III) - Alternate",
      subtitle: "6×2, 1×13",
      structure_hint: "1 × PART A [6×2=12], 1 × PART B [1×13=13]",
      total_marks: 25,
      time_minutes: 45,
      sections: ["Part A", "Part B"],
    },
  ],
  "CAT-3": [
    {
      id: "CAT-3 (Unit IV & V) - Standard",
      name: "CAT-3 (Unit IV & V) - Standard",
      subtitle: "10×2, 2×15",
      structure_hint: "2 × PART A [5×2=10], 2 × PART B [1×15=15]",
      total_marks: 50,
      time_minutes: 90,
      sections: ["Part A", "Part B"],
    },
    {
      id: "CAT-3 (Unit IV & V) - Alternate",
      name: "CAT-3 (Unit IV & V) - Alternate",
      subtitle: "12×2, 2×13",
      structure_hint: "2 × PART A [6×2=12], 2 × PART B [1×13=13]",
      total_marks: 50,
      time_minutes: 90,
      sections: ["Part A", "Part B"],
    },
  ],
  "University": [
    {
      id: "University Pattern 1",
      name: "University Pattern 1",
      subtitle: "10×2, 5×13, 1×15",
      structure_hint: "PART A [10×2=20], PART B [5×13=65], PART C [1×15=15]",
      total_marks: 100,
      time_minutes: 180,
      sections: ["Part A", "Part B", "Part C"],
    },
    {
      id: "University Pattern 2",
      name: "University Pattern 2",
      subtitle: "10×2, 5×16",
      structure_hint: "PART A [10×2=20], PART B [5×16=80]",
      total_marks: 100,
      time_minutes: 180,
      sections: ["Part A", "Part B"],
    },
  ],
};

const TABS = ["CAT-1", "CAT-2", "CAT-3", "University"];

const SCRUTINY_STEPS = [
  {
    id: "headers",
    name: "Header & Regulation Verification",
    criterion: "Criteria 1 & 2",
    description: "Validating institutional headers, regulations, course metadata, and exam pattern formulas",
    targetProgress: 18,
  },
  {
    id: "syllabus",
    name: "Syllabus Alignment & Unit Validation",
    criterion: "Criterion 3",
    description: "Checking unit boundaries (e.g., CAT-1 Units I & II), topic relevance, and Course Outcomes",
    targetProgress: 36,
  },
  {
    id: "marks",
    name: "Mark & Time Distribution Audit",
    criterion: "Criterion 4",
    description: "Verifying question mark allocations, sub-division limits, and estimating cognitive answering time",
    targetProgress: 52,
  },
  {
    id: "repetition",
    name: "Repetition Risk & Duplicate Detection",
    criterion: "Criterion 9",
    description: "Analyzing internal question similarity and cross-checking against previous-year archives",
    targetProgress: 68,
  },
  {
    id: "blooms",
    name: "Bloom's Taxonomy & Parity Scrutiny",
    criterion: "Criterion 5",
    description: "Verifying cognitive levels (A1–C2), either/or knowledge parity, and Wh-question avoidance",
    targetProgress: 84,
  },
  {
    id: "grammar",
    name: "Linguistic & Grammar Scrutiny",
    criterion: "Criterion 6",
    description: "Running deep semantic analysis for spelling, grammar, syntax, clarity, and technical whitelist",
    targetProgress: 96,
  },
];

export const App: React.FC = () => {
  // Theme state: defaults to saved preference or OS system preference
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("scrucheck_theme");
      if (saved === "light" || saved === "dark") {
        return saved;
      }
      if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return "dark";
      }
    }
    return "light";
  });

  const isDark = theme === "dark";

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("scrucheck_theme", theme);
  }, [theme]);

  useEffect(() => {
    if (!window.matchMedia) return;
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem("scrucheck_theme")) {
        setTheme(e.matches ? "dark" : "light");
      }
    };
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  const chartTheme = useMemo(() => {
    return isDark
      ? {
          grid: "#1c453d",
          axisText: "#94b9b0",
          tooltipBg: "#0c201c",
          tooltipBorder: "#1c453d",
          tooltipText: "#f0fdf9",
          barPrimary: "#2dd4bf", // bright teal
          barSecondary: "#f59e0b", // bright amber
          barTertiary: "#5eead4",
          pieColors: ["#2dd4bf", "#f59e0b", "#5eead4", "#38bdf8", "#a78bfa"],
        }
      : {
          grid: "#dbe7e2",
          axisText: "#6b7280",
          tooltipBg: "#ffffff",
          tooltipBorder: "#dbe7e2",
          tooltipText: "#111827",
          barPrimary: "#0d6b5c", // deep teal
          barSecondary: "#ea8c00", // warm golden amber
          barTertiary: "#5f8a7e",
          pieColors: ["#0d6b5c", "#ea8c00", "#5f8a7e", "#0284c7", "#db2777"],
        };
  }, [isDark]);

  const [activeTab, setActiveTab] = useState<string>("CAT-1");
  const [selectedPatternId, setSelectedPatternId] = useState<string>(
    PATTERNS_DATA["CAT-1"][0].id
  );
  const [file, setFile] = useState<File | null>(null);
  const [syllabusFile, setSyllabusFile] = useState<File | null>(null);
  // Criterion 5 Bloom's Taxonomy Filters
  const [btQuestionFilter, setBtQuestionFilter] = useState<string>("ALL");
  const [btParityFilter, setBtParityFilter] = useState<string>("ALL");

  // Criterion 6 Grammar, Spelling and Sentence Formation Filters
  const [grammarStatusFilter, setGrammarStatusFilter] = useState<string>("ALL");
  const [grammarCategoryFilter, setGrammarCategoryFilter] = useState<string>("ALL");
  const [grammarSectionFilter, setGrammarSectionFilter] = useState<string>("ALL");

  // Criterion 7 SI Units, Mathematical Symbols and Index Figures Filters
  const [notationStatusFilter, setNotationStatusFilter] = useState<string>("ALL");
  const [notationCategoryFilter, setNotationCategoryFilter] = useState<string>("ALL");
  const [notationSectionFilter, setNotationSectionFilter] = useState<string>("ALL");

  // Criterion 9 Repetition Risk State & Filters
  const [c9FilterStatus, setC9FilterStatus] = useState<string>("ALL");
  const [c9FilterScope, setC9FilterScope] = useState<string>("ALL");
  const [c9ExpandedMatchId, setC9ExpandedMatchId] = useState<string | null>(null);

    const [isLoading, setIsLoading] = useState<boolean>(false);

  // Real-time Execution Tracker state
  const [progress, setProgress] = useState<number>(0);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);

  useEffect(() => {
    if (!isLoading) return;
    const stepIdx = SCRUTINY_STEPS.findIndex((s) => progress <= s.targetProgress);
    if (stepIdx !== -1) {
      setCurrentStepIndex(stepIdx);
    } else {
      setCurrentStepIndex(SCRUTINY_STEPS.length - 1);
    }
  }, [progress, isLoading]);
  const [report, setReport] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState<boolean>(false);
  const [pdfDownloadError, setPdfDownloadError] = useState<string | null>(null);
  const [pdfDownloadSuccess, setPdfDownloadSuccess] = useState<string | null>(null);
  const [showExtractedModal, setShowExtractedModal] = useState<boolean>(false);
  const [activeExtractedTab, setActiveExtractedTab] = useState<"qp" | "syllabus">("qp");
  const [copied, setCopied] = useState<boolean>(false);
  const [expectedRegulationYear, setExpectedRegulationYear] = useState<string>("");
  const [filterUnit, setFilterUnit] = useState<string>("ALL");
  const [filterSection, setFilterSection] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  // Criterion 4 Mark and Time Distribution Filters
  const [c4FilterSection, setC4FilterSection] = useState<string>("ALL");
  const [c4FilterStatus, setC4FilterStatus] = useState<string>("ALL");
  const [c4FilterRule, setC4FilterRule] = useState<string>("ALL");

  const filteredResults = useMemo(() => {
    if (!report?.syllabus_alignment?.results) return [];
    return report.syllabus_alignment.results.filter((item: any) => {
      if (filterUnit !== "ALL" && String(item.required_unit) !== filterUnit) {
        return false;
      }
      if (filterSection !== "ALL") {
        const sec = (item.section || "").toUpperCase();
        if (!sec.includes(filterSection.toUpperCase())) return false;
      }
      if (filterStatus !== "ALL" && item.status !== filterStatus) {
        return false;
      }
      return true;
    });
  }, [report?.syllabus_alignment?.results, filterUnit, filterSection, filterStatus]);

  const filteredC4Evaluations = useMemo(() => {
    if (!report?.mark_distribution?.evaluations) return [];
    return report.mark_distribution.evaluations.filter((item: any) => {
      if (c4FilterSection !== "ALL") {
        const sec = (item.section || "").toUpperCase();
        if (!sec.includes(c4FilterSection.toUpperCase())) return false;
      }
      if (c4FilterStatus !== "ALL" && item.status !== c4FilterStatus) {
        return false;
      }
      if (c4FilterRule !== "ALL" && item.rule_triggered !== c4FilterRule) {
        return false;
      }
      return true;
    });
  }, [report?.mark_distribution?.evaluations, c4FilterSection, c4FilterStatus, c4FilterRule]);

  const filteredC9Evaluations = useMemo(() => {
    if (!report?.repetition_risk?.evaluations) return [];
    return report.repetition_risk.evaluations.filter((item: any) => {
      if (c9FilterStatus !== "ALL" && item.status !== c9FilterStatus) {
        return false;
      }
      if (c9FilterScope !== "ALL") {
        if (c9FilterScope === "INTERNAL" && item.repetition_type !== "INTERNAL") return false;
        if (c9FilterScope === "UNIQUE" && item.repetition_type !== "NONE") return false;
      }
      return true;
    });
  }, [report?.repetition_risk?.evaluations, c9FilterStatus, c9FilterScope]);

  const filteredBtQuestions = useMemo(() => {
    if (!report?.blooms_taxonomy?.questions) return [];
    return report.blooms_taxonomy.questions.filter((item: any) => {
      if (btQuestionFilter === "ALL") return true;
      if (btQuestionFilter === "MISSING_BT") return !item.declared_bt;
      if (btQuestionFilter === "MISMATCH_BT") return item.bt_match_status === "FLAG";
      if (btQuestionFilter === "WH_FLAG") return item.has_wh_question;
      if (btQuestionFilter === "CATEGORY_A") return item.evaluated_category === "Category A";
      if (btQuestionFilter === "CATEGORY_B") return item.evaluated_category === "Category B";
      if (btQuestionFilter === "CATEGORY_C") return item.evaluated_category === "Category C";
      if (btQuestionFilter === "FLAG") return item.overall_status === "FLAG";
      if (btQuestionFilter === "PASS") return item.overall_status === "PASS";
      return true;
    });
  }, [report?.blooms_taxonomy?.questions, btQuestionFilter]);

  const filteredBtParity = useMemo(() => {
    if (!report?.blooms_taxonomy?.choice_pairs_parity) return [];
    return report.blooms_taxonomy.choice_pairs_parity.filter((item: any) => {
      if (btParityFilter === "ALL") return true;
      if (btParityFilter === "FLAG") return item.status === "FLAG";
      if (btParityFilter === "PASS") return item.status === "PASS";
      return true;
    });
  }, [report?.blooms_taxonomy?.choice_pairs_parity, btParityFilter]);

  const filteredGrammarQuestions = useMemo(() => {
    if (!report?.grammar_check?.questions) return [];
    return report.grammar_check.questions.filter((item: any) => {
      if (grammarStatusFilter !== "ALL" && item.status !== grammarStatusFilter) {
        return false;
      }
      if (grammarSectionFilter !== "ALL") {
        const sec = (item.section || "").toUpperCase();
        if (!sec.includes(grammarSectionFilter.toUpperCase())) return false;
      }
      if (grammarCategoryFilter !== "ALL") {
        const hasCategory = (item.issues || []).some(
          (iss: any) => iss.category === grammarCategoryFilter
        );
        if (!hasCategory) return false;
      }
      return true;
    });
  }, [
    report?.grammar_check?.questions,
    grammarStatusFilter,
    grammarCategoryFilter,
    grammarSectionFilter,
  ]);

  const filteredNotationQuestions = useMemo(() => {
    if (!report?.notation_check?.questions) return [];
    return report.notation_check.questions.filter((item: any) => {
      if (notationStatusFilter !== "ALL" && item.status !== notationStatusFilter) {
        return false;
      }
      if (notationSectionFilter !== "ALL") {
        const sec = (item.section || "").toUpperCase();
        if (!sec.includes(notationSectionFilter.toUpperCase())) return false;
      }
      if (notationCategoryFilter !== "ALL") {
        const hasCategory = (item.issues || []).some(
          (iss: any) => iss.category === notationCategoryFilter
        );
        if (!hasCategory) return false;
      }
      return true;
    });
  }, [
    report?.notation_check?.questions,
    notationStatusFilter,
    notationCategoryFilter,
    notationSectionFilter,
  ]);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    if (PATTERNS_DATA[tab] && PATTERNS_DATA[tab].length > 0) {
      setSelectedPatternId(PATTERNS_DATA[tab][0].id);
    }
  };

  const validateSelectedFile = (selected: File): string | null => {
    const ext = selected.name.substring(selected.name.lastIndexOf(".")).toLowerCase();
    if (![".pdf", ".docx"].includes(ext)) {
      return `Security Policy Violation: File format '${ext}' is not permitted. Only PDF (.pdf) and Word (.docx) documents are allowed. Formats like PNG, JPG, TXT, DOC, and ZIP are strictly rejected.`;
    }
    if (selected.size === 0) {
      return "The selected file is empty (0 bytes). Please select a valid document.";
    }
    if (selected.size > 25 * 1024 * 1024) {
      return "The selected file exceeds the maximum permitted limit of 25MB.";
    }
    return null;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      const validationError = validateSelectedFile(selected);
      if (validationError) {
        setError(validationError);
        setFile(null);
        e.target.value = "";
        return;
      }
      setFile(selected);
      setError(null);
      setReport(null);
      setPdfDownloadError(null);
      setPdfDownloadSuccess(null);
      setShowExtractedModal(false);
    }
  };

  const handleClearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setFile(null);
    setReport(null);
    setPdfDownloadError(null);
    setPdfDownloadSuccess(null);
    const input = document.getElementById("file-upload") as HTMLInputElement;
    if (input) input.value = "";
  };

  const handleSyllabusChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      const validationError = validateSelectedFile(selected);
      if (validationError) {
        setError(validationError);
        setSyllabusFile(null);
        e.target.value = "";
        return;
      }
      setSyllabusFile(selected);
      setError(null);
    }
  };

  const handleClearSyllabus = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setSyllabusFile(null);
    const input = document.getElementById("syllabus-upload") as HTMLInputElement;
    if (input) input.value = "";
  };

  const handleCheckCompliance = async () => {
    if (!file) {
      setError("Please choose a question paper file first.");
      return;
    }

    setIsLoading(true);
    setProgress(5);
    setCurrentStepIndex(0);
    setElapsedSeconds(0);
    setError(null);
    setReport(null);
    setPdfDownloadError(null);
    setPdfDownloadSuccess(null);

    const startTime = Date.now();
    const timerInterval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      setElapsedSeconds(elapsed);

      setProgress((prev) => {
        if (prev < 18) return Math.min(18, prev + 2.5);
        if (prev < 36) return Math.min(36, prev + 1.8);
        if (prev < 52) return Math.min(52, prev + 1.5);
        if (prev < 68) return Math.min(68, prev + 1.2);
        if (prev < 84) return Math.min(84, prev + 1.0);
        if (prev < 95) return Math.min(95, prev + 0.4);
        return prev;
      });
    }, 100);

    const formData = new FormData();
    formData.append("file", file);
    if (syllabusFile) {
      formData.append("syllabus_file", syllabusFile);
    }
    formData.append("exam_type", activeTab);
    formData.append("pattern_name", selectedPatternId);
    if (expectedRegulationYear.trim()) {
      formData.append("expected_regulation_year", expectedRegulationYear.trim());
    }

    try {
      const response = await fetch("/api/v1/scrutiny/check-format", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned error status ${response.status}`);
      }

      const data = await response.json();
      clearInterval(timerInterval);
      setProgress(100);
      setCurrentStepIndex(SCRUTINY_STEPS.length - 1);

      // Brief transition so user sees 100% completion
      setTimeout(() => {
        setReport(data);
        setActiveExtractedTab("qp");
        setIsLoading(false);
      }, 500);
    } catch (err: any) {
      clearInterval(timerInterval);
      setError(err.message || "Failed to process question paper with scrutiny backend.");
      setIsLoading(false);
      setProgress(0);
    }
  };

  const handleCopyText = async (textToCopy: string) => {
    if (!textToCopy) return;
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const handleDownloadPdfReport = async () => {
    if (!report || isDownloadingPdf) return;
    setIsDownloadingPdf(true);
    setPdfDownloadError(null);
    setPdfDownloadSuccess(null);

    try {
      let response: Response;

      // 1. Primary: GET /api/v1/reports/{report_id}/download
      if (report.report_id) {
        response = await fetch(`/api/v1/reports/${encodeURIComponent(report.report_id)}/download`, {
          method: "GET",
          headers: {
            Accept: "application/pdf",
          },
        });

        // 2. Fallback: If report not in store (or session reloaded), POST full report model
        if (response.status === 404) {
          response = await fetch("/api/v1/reports/download-pdf", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Accept: "application/pdf",
            },
            body: JSON.stringify(report),
          });
        }
      } else {
        response = await fetch("/api/v1/reports/download-pdf", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/pdf",
          },
          body: JSON.stringify(report),
        });
      }

      if (!response.ok) {
        let errorMsg = `PDF generation failed (${response.status})`;
        try {
          const errData = await response.json();
          if (errData?.detail) {
            errorMsg = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch {
          // ignore json parse error
        }
        throw new Error(errorMsg);
      }

      // Extract filename from Content-Disposition header if available
      let filename = `ScruCheck_AI_Scrutiny_Report_${new Date().toISOString().slice(0, 10)}.pdf`;
      const disposition = response.headers.get("content-disposition");
      if (disposition && disposition.includes("filename=")) {
        const match = disposition.match(/filename=["']?([^"';]+)["']?/);
        if (match && match[1]) {
          filename = match[1].trim();
        }
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);

      setPdfDownloadSuccess(`Scrutiny report "${filename}" downloaded successfully.`);
      setTimeout(() => {
        setPdfDownloadSuccess(null);
      }, 6000);
    } catch (err: any) {
      console.error("PDF Report download error:", err);
      setPdfDownloadError(err?.message || "Failed to download PDF report. Please try again.");
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const activePatterns = PATTERNS_DATA[activeTab] || [];
  const qpExtractedText = report?.extracted_text || "";
  const syllabusExtractedText = report?.syllabus_extracted_text || "";

  const displayedText = activeExtractedTab === "syllabus" ? syllabusExtractedText : qpExtractedText;
  const textLineCount = displayedText ? displayedText.split("\n").length : 0;
  const textCharCount = displayedText.length;

  const isFormatCompliant = Boolean(
    report?.pattern_compliance?.pattern_name_match &&
    report?.pattern_compliance?.marks_match &&
    report?.pattern_compliance?.duration_match &&
    report?.pattern_compliance?.sections_match
  );

  const isUniversity = report?.selected_category?.toUpperCase() === "UNIVERSITY";

  const formatCriteria = report ? [
    {
      id: "exam_pattern_name",
      num: "1.1",
      label: "Exam / Pattern Name",
      description: isUniversity
        ? `Pattern structure verification vs selected (${report.selected_pattern_name})`
        : `Exam pattern declared in question paper vs selected (${report.selected_category})`,
      passed: Boolean(report.pattern_compliance?.pattern_name_match),
      value: isUniversity
        ? (report.pattern_compliance?.pattern_name_match
            ? `${report.selected_pattern_name} (Structure Verified)`
            : `${report.selected_pattern_name} (Structure Mismatch)`)
        : (report.pattern_compliance?.pattern_name_in_paper || "Missing / Not Declared"),
      note: isUniversity
        ? (report.pattern_compliance?.pattern_name_match
            ? `Question paper structure matches selected pattern '${report.selected_pattern_name}'`
            : (report.header_checks?.exam_pattern_name?.message || "Pattern structure does not match selected pattern"))
        : (report.pattern_compliance?.pattern_name_match
            ? `Declared pattern matches selected ${report.selected_category}`
            : (report.pattern_compliance?.has_pattern_name
                ? `Pattern mismatch: declares '${report.pattern_compliance.pattern_name_in_paper}', expected '${report.selected_category}'`
                : "Missing exam pattern name (e.g. CAT-1, CAT-2, CAT-3)")),
    },
    {
      id: "section_headers",
      num: "1.2",
      label: "Section Headers & Mark Structure",
      description: "Unit-wise section headings and question mark breakdown",
      passed: Boolean(report.pattern_compliance?.sections_match),
      value: report.header_checks?.section_headers?.extracted_value || report.pattern_compliance.found_sections?.join(", ") || "—",
      note: report.header_checks?.section_headers?.message,
    },
    {
      id: "exam_date",
      num: "1.3",
      label: isUniversity ? "Month & Year of Examination" : "Exam Date",
      description: isUniversity
        ? "Month and Year of university examinations (e.g. April/May 2026)"
        : "Scheduled examination date",
      passed: Boolean(report.header_checks?.exam_date?.found),
      value: report.header_checks?.exam_date?.extracted_value || "—",
      note: report.header_checks?.exam_date?.message,
    },
  ] : [];

  const examDetailsCriteria = report ? [
    {
      num: "2.1",
      label: "Regulations",
      description: "Standard regulation declaration: e.g. [Regulations 2023] or (Regulations 2021)",
      passed: Boolean(report.exam_details?.items?.regulations?.found ?? report.regulation?.is_accepted),
      value: report.exam_details?.items?.regulations?.extracted_value || report.regulation?.regulation_code || "Missing / Not Declared",
      note: report.exam_details?.items?.regulations?.note || report.regulation?.message || "Missing regulation code like [Regulations 2023]",
    },
    {
      num: "2.2",
      label: "Programme",
      description: "Academic programme / degree (e.g. B.E., B.Tech, M.E., M.Tech)",
      passed: Boolean(report.exam_details?.items?.programme?.found ?? report.header_checks?.degree_branch?.found),
      value: report.exam_details?.items?.programme?.extracted_value || report.extracted_metadata?.programme || "Missing / Not Declared",
      note: report.exam_details?.items?.programme?.note || (report.exam_details?.items?.programme?.found ? "Programme identified" : "Academic programme is missing"),
    },
    {
      num: "2.3",
      label: "Branch",
      description: "Academic branch / department (e.g. Computer Science and Engineering, CSE)",
      passed: Boolean(report.exam_details?.items?.branch?.found),
      value: report.exam_details?.items?.branch?.extracted_value || report.extracted_metadata?.branch || "Missing / Not Declared",
      note: report.exam_details?.items?.branch?.note || (report.exam_details?.items?.branch?.found ? "Branch identified" : "Branch is missing"),
    },
    {
      num: "2.4",
      label: "Semester",
      description: "Semester designation in roman or numeric format (e.g. Semester V, 5)",
      passed: Boolean(report.exam_details?.items?.semester?.found ?? report.header_checks?.semester?.found),
      value: report.exam_details?.items?.semester?.extracted_value || report.header_checks?.semester?.extracted_value || "Missing / Not Declared",
      note: report.exam_details?.items?.semester?.note || report.header_checks?.semester?.message || "Semester number is missing",
    },
    {
      num: "2.5",
      label: "Subject Code",
      description: "Standard alphanumeric course / subject code (e.g. CS3351, GE3151)",
      passed: Boolean(report.exam_details?.items?.subject_code?.found ?? report.header_checks?.course_code?.found),
      value: report.exam_details?.items?.subject_code?.extracted_value || report.header_checks?.course_code?.extracted_value || "Missing / Not Declared",
      note: report.exam_details?.items?.subject_code?.note || report.header_checks?.course_code?.message || "Subject code is missing",
    },
    {
      num: "2.6",
      label: "Subject Name",
      description: "Course title / subject name declared clearly in header",
      passed: Boolean(report.exam_details?.items?.subject_name?.found ?? report.header_checks?.course_title?.found),
      value: report.exam_details?.items?.subject_name?.extracted_value || report.header_checks?.course_title?.extracted_value || "Missing / Not Declared",
      note: report.exam_details?.items?.subject_name?.note || report.header_checks?.course_title?.message || "Subject name is missing",
    },
    {
      num: "2.7",
      label: "Duration",
      description: `Examination time duration vs expected (${report.pattern_compliance?.expected_duration_minutes ?? "None"}m)`,
      passed: Boolean(report.exam_details?.items?.duration?.found ?? report.pattern_compliance?.duration_match),
      value: report.exam_details?.items?.duration?.extracted_value || (report.pattern_compliance?.found_duration_minutes ? `${report.pattern_compliance.found_duration_minutes} Minutes` : "Missing / Not Declared"),
      note: report.exam_details?.items?.duration?.note || (report.pattern_compliance?.duration_match ? "Matches expected duration" : "Duration mismatch or missing"),
    },
    {
      num: "2.8",
      label: "Maximum Marks",
      description: `Maximum marks declaration vs expected (${report.pattern_compliance?.expected_total_marks ?? "None"} Marks)`,
      passed: Boolean(report.exam_details?.items?.maximum_marks?.found ?? report.pattern_compliance?.marks_match),
      value: report.exam_details?.items?.maximum_marks?.extracted_value || (report.pattern_compliance?.found_total_marks ? `${report.pattern_compliance.found_total_marks} Marks` : "Missing / Not Declared"),
      note: report.exam_details?.items?.maximum_marks?.note || (report.pattern_compliance?.marks_match ? "Matches expected maximum marks" : "Marks mismatch or missing"),
    },
  ] : [];

  return (
    <div className="app-shell min-h-screen bg-canvas text-ink py-6 sm:py-10 px-4 sm:px-6 lg:px-8 font-sans selection:bg-brand selection:text-btn-brand">
      <div className="max-w-6xl mx-auto space-y-5">
        {/* Top Header Card */}
        <header className="hero-panel rounded-2xl border border-line bg-surface p-4 sm:px-6 sm:py-5 flex items-center justify-between gap-4">
          <div className="brand-identity">
            <div>
              <h1 className="brand-wordmark text-xl sm:text-2xl font-bold text-ink leading-tight">
                Scru-Check-AI
              </h1>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setTheme((prev) => (prev === "dark" ? "light" : "dark"))}
            aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
            className="theme-toggle flex items-center space-x-2 px-3.5 py-2 rounded-lg border border-line text-xs font-semibold text-ink bg-surface hover:bg-surface-subtle transition-all cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
          >
            {isDark ? (
              <>
                <Moon className="w-3.5 h-3.5 text-brand" />
                <span>Dark mode</span>
              </>
            ) : (
              <>
                <Sun className="w-3.5 h-3.5 text-accent-ink" />
                <span>Light mode</span>
              </>
            )}
          </button>
        </header>

        {/* Exam Pattern Card */}
        <section className="workspace-card rounded-[28px] border border-line bg-surface p-6 shadow-sm space-y-4">
          <div>
            <h2 className="text-xl font-bold text-ink tracking-tight">Exam Pattern</h2>
          </div>

          {/* Tab Capsule Segmented Control */}
          <div className="bg-track p-1.5 rounded-2xl flex items-center gap-1.5 mt-3 border border-line-subtle">
            {TABS.map((tab) => {
              const isActive = activeTab === tab;
              return (
                <button
                  type="button"
                  key={tab}
                  onClick={() => handleTabChange(tab)}
                  className={`flex-1 py-2 px-3 text-center text-xs sm:text-sm font-semibold rounded-xl transition-all duration-200 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
                    isActive
                      ? "bg-brand text-btn-brand shadow-sm font-bold"
                      : "text-ink-muted hover:text-ink hover:bg-surface/50 font-medium"
                  }`}
                >
                  {tab}
                </button>
              );
            })}
          </div>
        </section>

        {/* Pattern Option Cards (2-Column Grid) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {activePatterns.map((pattern) => {
            const isSelected = selectedPatternId === pattern.id;
            const isAlternate = pattern.id.includes("Alternate");

            // Derive Part A and Part B distribution representation
            const partALabel = isAlternate ? "6×2=12" : (pattern.sections.includes("Part C") ? "10×2=20" : "5×2=10");
            const partBLabel = isAlternate ? "1×13=13" : (pattern.sections.includes("Part C") ? "5×13=65" : "1×15=15");
            const partAWidth = isAlternate ? "30%" : (pattern.sections.includes("Part C") ? "20%" : "35%");
            const partBWidth = isAlternate ? "70%" : (pattern.sections.includes("Part C") ? "80%" : "65%");

            return (
              <div
                key={pattern.id}
                role="button"
                tabIndex={0}
                aria-pressed={isSelected}
                onClick={() => setSelectedPatternId(pattern.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setSelectedPatternId(pattern.id);
                  }
                }}
                className={`rounded-2xl p-6 bg-surface shadow-sm relative transition-all duration-200 cursor-pointer flex flex-col justify-between focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
                  isSelected
                    ? "border-2 border-brand ring-1 ring-brand-line"
                    : "border border-line hover:border-brand-line"
                }`}
              >
                <div>
                  {/* Top row: Badge & Subtitle */}
                  <div className="flex items-center justify-between">
                    <span
                      className={`px-3 py-0.5 rounded-full text-[11px] font-semibold tracking-wide ${
                        isSelected
                          ? "bg-brand text-btn-brand"
                          : "bg-track text-ink-muted"
                      }`}
                    >
                      {isSelected ? "Selected" : "Alternate"}
                    </span>
                    <span className="text-xs text-ink-faint font-mono font-medium">
                      {pattern.subtitle}
                    </span>
                  </div>

                  {/* Pattern Name */}
                  <h3 className="text-base font-bold text-ink mt-3">
                    {pattern.name}
                  </h3>

                  {/* Large Total Marks Display */}
                  <div className="flex items-baseline space-x-1.5 mt-2">
                    <span className="text-4xl font-extrabold text-ink tracking-tight">
                      {pattern.total_marks}
                    </span>
                    <span className="text-sm text-ink-faint font-medium">marks</span>
                  </div>
                </div>

                {/* Progress / Distribution Bar & Legend */}
                <div className="mt-5 space-y-2">
                  <div className="h-2.5 w-full rounded-full flex overflow-hidden bg-surface-muted">
                    <div
                      className={`h-full transition-all duration-300 ${
                        isSelected ? "bg-brand" : "bg-[#5fa89b]"
                      }`}
                      style={{ width: partAWidth }}
                    />
                    <div
                      className={`h-full transition-all duration-300 ${
                        isSelected ? "bg-accent" : "bg-[#e5ad60]"
                      }`}
                      style={{ width: partBWidth }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-xs pt-1">
                    <span>
                      <strong className="text-ink font-bold">Part A</strong>{" "}
                      <span className="text-ink-faint font-mono">{partALabel}</span>
                    </span>
                    <span>
                      <strong className="text-ink font-bold">Part B</strong>{" "}
                      <span className="text-ink-faint font-mono">{partBLabel}</span>
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Upload & Configuration (3-Column Grid) */}
        <div className="upload-grid grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Column 1: Question Paper Upload */}
          <div className="rounded-2xl p-5 bg-surface border border-line shadow-sm flex flex-col justify-between">
            <h3 className="text-base font-bold text-ink mb-3">Question Paper</h3>
            <div
              onClick={() => document.getElementById("file-upload")?.click()}
              className="border-2 border-dashed border-brand-line rounded-2xl p-5 flex flex-col items-center justify-center text-center bg-surface hover:bg-surface-subtle transition-colors cursor-pointer group min-h-[155px]"
            >
              <input
                type="file"
                id="file-upload"
                accept=".pdf,.docx"
                onChange={handleFileChange}
                className="hidden"
              />
              <Upload className="w-6 h-6 text-brand-ink mb-2 stroke-[2.2] group-hover:scale-110 transition-transform" />
              {file ? (
                <div className="space-y-1 mb-2 max-w-full px-2">
                  <div className="flex items-center justify-center space-x-1.5 text-xs font-semibold text-brand-ink truncate">
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-brand-ink" />
                    <span className="truncate">{file.name}</span>
                  </div>
                  <span className="text-[10px] text-ink-faint block font-mono">
                    {(file.size / 1024).toFixed(0)} KB • Selected
                  </span>
                </div>
              ) : (
                <span className="text-xs text-ink-faint mb-3 font-medium">Drop file here</span>
              )}
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    document.getElementById("file-upload")?.click();
                  }}
                  className="px-5 py-2 rounded-xl bg-brand hover:bg-brand-hover text-btn-brand text-xs font-semibold shadow-sm transition-all cursor-pointer active:scale-95"
                >
                  {file ? "Change" : "Upload"}
                </button>
                {file && (
                  <button
                    type="button"
                    onClick={handleClearFile}
                    className="p-1.5 rounded-xl border border-line text-ink-faint hover:text-danger-ink hover:bg-surface-subtle transition-colors"
                    title="Remove question paper"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Column 2: Syllabus Upload */}
          <div className="rounded-2xl p-5 bg-surface border border-line shadow-sm flex flex-col justify-between">
            <h3 className="text-base font-bold text-ink mb-3">Syllabus</h3>
            <div
              onClick={() => document.getElementById("syllabus-upload")?.click()}
              className="border-2 border-dashed border-accent-line rounded-2xl p-5 flex flex-col items-center justify-center text-center bg-surface hover:bg-surface-subtle transition-colors cursor-pointer group min-h-[155px]"
            >
              <input
                type="file"
                id="syllabus-upload"
                accept=".pdf,.docx"
                onChange={handleSyllabusChange}
                className="hidden"
              />
              <BookOpen className="w-6 h-6 text-accent-ink mb-2 stroke-[2.2] group-hover:scale-110 transition-transform" />
              {syllabusFile ? (
                <div className="space-y-1 mb-2 max-w-full px-2">
                  <div className="flex items-center justify-center space-x-1.5 text-xs font-semibold text-accent-ink truncate">
                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-accent-ink" />
                    <span className="truncate">{syllabusFile.name}</span>
                  </div>
                  <span className="text-[10px] text-ink-faint block font-mono">
                    {(syllabusFile.size / 1024).toFixed(0)} KB • Attached
                  </span>
                </div>
              ) : (
                <span className="text-xs text-ink-faint mb-3 font-medium">PDF or DOCX</span>
              )}
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    document.getElementById("syllabus-upload")?.click();
                  }}
                  className="px-5 py-2 rounded-xl bg-accent hover:bg-accent-hover text-btn-accent text-xs font-semibold shadow-sm transition-all cursor-pointer active:scale-95"
                >
                  {syllabusFile ? "Change" : "Upload"}
                </button>
                {syllabusFile && (
                  <button
                    type="button"
                    onClick={handleClearSyllabus}
                    className="p-1.5 rounded-xl border border-line text-ink-faint hover:text-danger-ink hover:bg-surface-subtle transition-colors"
                    title="Remove syllabus"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Column 3: Regulation Check */}
          <div className="rounded-2xl p-5 bg-surface border border-line shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="text-base font-bold text-ink">Regulation Check</h3>
              <p className="text-xs text-ink-faint mt-0.5 mb-4 font-medium">
                Enforce year: Regulations {expectedRegulationYear || "2023"}
              </p>
            </div>
            <div className="space-y-2.5">
              <button
                type="button"
                onClick={() => setExpectedRegulationYear("")}
                className={`w-full py-2.5 rounded-xl font-semibold text-xs shadow-sm transition-all cursor-pointer ${
                  !expectedRegulationYear
                    ? "bg-brand text-btn-brand shadow-sm"
                    : "border border-line text-ink bg-surface hover:bg-surface-subtle"
                }`}
              >
                Auto
              </button>
              <div className="flex gap-2.5">
                <button
                  type="button"
                  onClick={() => setExpectedRegulationYear("2023")}
                  className={`flex-1 py-2 rounded-xl font-semibold text-xs transition-all cursor-pointer ${
                    expectedRegulationYear === "2023"
                      ? "bg-brand text-btn-brand shadow-sm"
                      : "border border-line text-ink bg-surface hover:bg-surface-subtle"
                  }`}
                >
                  2023
                </button>
                <button
                  type="button"
                  onClick={() => setExpectedRegulationYear("2021")}
                  className={`flex-1 py-2 rounded-xl font-semibold text-xs transition-all cursor-pointer ${
                    expectedRegulationYear === "2021"
                      ? "bg-brand text-btn-brand shadow-sm"
                      : "border border-line text-ink bg-surface hover:bg-surface-subtle"
                  }`}
                >
                  2021
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Primary scrutiny action */}
        <div className="flex justify-center py-2 sm:py-3">
          <button
            type="button"
            onClick={handleCheckCompliance}
            disabled={isLoading || !file}
            className="px-7 py-3.5 rounded-xl bg-brand hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed text-btn-brand font-extrabold text-xs sm:text-sm tracking-wide shadow-sm transition-all whitespace-nowrap cursor-pointer active:scale-98 flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <>
                <span className="w-4 h-4 border-2 border-slate-900/30 border-t-slate-900 rounded-full animate-spin" />
                <span>Evaluating Scrutiny Criteria ({Math.round(progress)}%)...</span>
              </>
            ) : (
              <span>Check Question Paper</span>
            )}
          </button>
        </div>

          {/* Real-time Execution Tracker Card with Clean Theme */}
          {isLoading && (
            <div className="rounded-2xl border border-line bg-surface p-6 shadow-md space-y-5 animate-in fade-in duration-300 text-ink">
              {/* Top Header: Title, Live Number & Elapsed Time */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-line-subtle pb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-brand text-btn-brand flex items-center justify-center font-bold shadow-sm shrink-0">
                    <Activity className="w-5 h-5 text-btn-brand" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="text-base sm:text-lg font-bold text-ink tracking-tight">
                        Executing Institutional Scrutiny
                      </h3>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-brand-surface border border-brand-line text-brand-ink font-bold animate-pulse">
                        LIVE ENGINE
                      </span>
                    </div>
                    <p className="text-xs text-ink-faint">
                      {SCRUTINY_STEPS[currentStepIndex]?.name || "Evaluating criteria..."}
                    </p>
                  </div>
                </div>

                {/* Progress Numbers */}
                <div className="flex items-baseline space-x-3 shrink-0">
                  <div className="text-right">
                    <span className="text-2xl sm:text-3xl font-extrabold font-mono text-brand-ink tracking-tight">
                      {Math.round(progress)}%
                    </span>
                    <span className="block text-[11px] font-mono text-ink-faint">
                      Step {currentStepIndex + 1} of {SCRUTINY_STEPS.length}
                    </span>
                  </div>
                  <div className="px-2.5 py-1 rounded-lg bg-surface-muted border border-line text-[11px] font-mono text-ink-muted flex items-center space-x-1.5 self-center">
                    <Clock className="w-3.5 h-3.5 text-ink-faint" />
                    <span>{elapsedSeconds.toFixed(1)}s</span>
                  </div>
                </div>
              </div>

              {/* Primary Loading Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-ink-faint text-[11px]">
                    {SCRUTINY_STEPS[currentStepIndex]?.description}
                  </span>
                  <span className="text-brand-ink font-bold">{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-surface-muted rounded-full h-3 overflow-hidden border border-line p-0.5 relative">
                  <div
                    className="bg-brand h-full rounded-full transition-all duration-200 ease-out shadow-sm"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Live Step-by-Step Execution Tracker Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-2">
                {SCRUTINY_STEPS.map((step, idx) => {
                  const isDone = progress === 100 || idx < currentStepIndex;
                  const isCurrent = progress < 100 && idx === currentStepIndex;

                  return (
                    <div
                      key={step.id}
                      className={`p-3 rounded-xl border transition-all text-xs flex items-start space-x-3 duration-200 ${
                        isDone
                          ? "bg-brand-surface border-brand-line text-brand-ink"
                          : isCurrent
                          ? "bg-accent-surface border-2 border-accent text-ink shadow-sm"
                          : "bg-surface-subtle border-line-subtle text-ink-faint"
                      }`}
                    >
                      <div className="shrink-0 mt-0.5">
                        {isDone ? (
                          <CheckCircle2 className="w-4 h-4 text-brand-ink" />
                        ) : isCurrent ? (
                          <span className="w-4 h-4 border-2 border-accent/30 border-t-accent rounded-full animate-spin block" />
                        ) : (
                          <span className="w-4 h-4 rounded-full border border-line block text-[10px] text-ink-faint text-center leading-3.5 font-mono">
                            {idx + 1}
                          </span>
                        )}
                      </div>
                      <div className="space-y-0.5 min-w-0">
                        <div className="flex items-center space-x-2">
                          <span
                            className={`font-mono font-bold truncate ${
                              isCurrent ? "text-ink" : isDone ? "text-brand-ink" : "text-ink-faint"
                            }`}
                          >
                            {idx + 1}. {step.name}
                          </span>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-surface-muted text-ink-muted border border-line shrink-0">
                            {step.criterion}
                          </span>
                        </div>
                        <p className="text-[11px] line-clamp-1 text-ink-faint">
                          {step.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Extracted Content Bar when report is ready */}
          {report && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-2 p-3.5 rounded-2xl border border-line bg-surface shadow-sm text-ink">
              <div className="flex items-center space-x-2.5 truncate">
                <FileText className="w-4 h-4 text-brand-ink shrink-0" />
                <span className="text-xs text-ink-muted font-medium truncate">
                  QP: <span className="text-ink font-mono font-bold">{qpExtractedText.length.toLocaleString()} chars</span>
                  {report.syllabus_extracted_text && (
                    <span className="ml-2 text-ink-faint">
                      • Syllabus: <span className="text-ink font-mono font-bold">{report.syllabus_extracted_text.length.toLocaleString()} chars</span>
                    </span>
                  )}
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setActiveExtractedTab("qp");
                  setShowExtractedModal(true);
                }}
                className="w-full sm:w-auto px-4 py-2 rounded-xl bg-surface hover:bg-surface-subtle border border-line text-ink text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all shadow-sm cursor-pointer focus-visible:ring-2 focus-visible:ring-brand"
              >
                <Eye className="w-3.5 h-3.5 text-brand-ink" />
                <span>View Extracted Text</span>
              </button>
            </div>
          )}

          {error && (
            <div className="p-3.5 rounded-2xl bg-danger-surface border border-danger-line text-danger-ink text-xs flex items-center space-x-2 shadow-sm">
              <XCircle className="w-4 h-4 shrink-0 text-danger" />
              <span className="font-medium">{error}</span>
            </div>
          )}

        {/* Scrutiny Results Panel */}
        {report && (
          <div className="mt-6 rounded-2xl border border-line bg-surface p-6 space-y-6 shadow-sm text-ink">
            {/* Overall Scrutiny Banner */}
            <div
              className={`p-5 rounded-2xl border-2 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all duration-300 shadow-sm ${
                report.is_approved
                  ? "bg-brand-surface border-brand text-ink"
                  : "bg-danger-surface border-danger text-ink"
              }`}
            >
              <div className="flex items-center space-x-3.5">
                {report.is_approved ? (
                  <CheckCircle2 className="w-7 h-7 text-brand-ink shrink-0" />
                ) : (
                  <XCircle className="w-7 h-7 text-danger shrink-0" />
                )}
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-extrabold text-sm sm:text-base tracking-wide text-ink">
                      {report.is_approved ? "QUESTION PAPER SCRUTINY APPROVED" : "SCRUTINY BLOCKED"}
                    </span>
                    <span
                      className={`text-[10px] px-2.5 py-0.5 rounded-full font-black uppercase font-mono shadow-sm ${
                        report.is_approved
                          ? "bg-brand text-btn-brand"
                          : "bg-danger text-white"
                      }`}
                    >
                      {report.approval_status}
                    </span>
                  </div>
                  <p className="text-xs text-ink-faint mt-0.5 font-medium flex items-center flex-wrap gap-2">
                    <span>Pattern: <span className="text-ink font-semibold">{report.selected_pattern_name}</span></span>
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-4 shrink-0">
                <button
                  type="button"
                  onClick={handleDownloadPdfReport}
                  disabled={isDownloadingPdf}
                  className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold font-mono tracking-wide uppercase transition-all duration-200 bg-brand hover:bg-brand-hover text-btn-brand shadow-sm cursor-pointer active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed border border-brand focus-visible:ring-2 focus-visible:ring-brand"
                  title="Download complete academic scrutiny report as PDF"
                >
                  {isDownloadingPdf ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-btn-brand/20 border-t-btn-brand rounded-full animate-spin inline-block" />
                      <span>Generating PDF...</span>
                    </>
                  ) : (
                    <>
                      <FileDown className="w-4 h-4 text-btn-brand" />
                      <span>Download PDF Report</span>
                    </>
                  )}
                </button>

                <div className="text-right border-l border-line pl-4">
                  <span className="text-[10px] text-ink-faint uppercase font-semibold block">Score</span>
                  <span className={`text-2xl font-black ${report.is_approved ? "text-brand-ink" : "text-danger-ink"}`}>
                    {report.compliance_score}%
                  </span>
                </div>
              </div>
            </div>

            {/* PDF Download Notifications */}
            {pdfDownloadSuccess && (
              <div className="p-3.5 rounded-xl bg-brand-surface border border-brand-line text-brand-ink flex items-center justify-between text-xs font-mono shadow-sm transition-all animate-in fade-in slide-in-from-top-1">
                <div className="flex items-center space-x-2.5">
                  <CheckCircle2 className="w-4 h-4 text-brand-ink shrink-0" />
                  <span className="font-semibold">{pdfDownloadSuccess}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setPdfDownloadSuccess(null)}
                  className="text-ink-faint hover:text-brand-ink p-1 rounded transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {pdfDownloadError && (
              <div className="p-3.5 rounded-xl bg-danger-surface border border-danger-line text-danger-ink flex items-center justify-between text-xs font-mono shadow-sm transition-all animate-in fade-in slide-in-from-top-1">
                <div className="flex items-center space-x-2.5">
                  <AlertTriangle className="w-4 h-4 text-danger shrink-0" />
                  <span className="font-semibold">{pdfDownloadError}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setPdfDownloadError(null)}
                  className="text-ink-faint hover:text-danger-ink p-1 rounded transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* Blocking Reasons */}
            {!report.is_approved && report.blocking_reasons.length > 0 && (
              <div className="p-4 rounded-xl bg-danger-surface border border-danger-line space-y-2 text-danger-ink shadow-sm">
                <div className="flex items-center space-x-2 font-bold text-xs">
                  <span>Strict Scrutiny Blocking Reasons ({report.blocking_reasons.length})</span>
                </div>
                <ul className="list-disc list-inside text-xs text-danger-ink space-y-1 font-mono">
                  {report.blocking_reasons.map((r: string, idx: number) => (
                    <li key={idx} className="leading-relaxed">{r}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* 1) Format Compliance Section */}
            <div className="space-y-4 pt-1">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-line">
                <div className="flex items-center space-x-2.5">
                  <span className="px-2.5 py-0.5 rounded-lg bg-track border border-brand-line text-brand-ink font-mono font-bold text-xs">
                    1
                  </span>
                  <div>
                    <h2 className="text-sm sm:text-base font-bold text-ink tracking-wide uppercase">
                      Format Compliance
                    </h2>
                  </div>
                </div>
                <span
                  className={`text-[11px] px-3 py-1 rounded-full font-black uppercase font-mono self-start sm:self-auto shadow-sm transition-all duration-300 ${
                    isFormatCompliant
                      ? "bg-brand text-btn-brand"
                      : "bg-accent text-btn-accent"
                  }`}
                >
                  {isFormatCompliant ? "COMPLIANT" : "NON-COMPLIANT"}
                </span>
              </div>

              {/* Pattern Matching Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 rounded-xl border border-line bg-surface-subtle">
                  <span className="text-ink-faint block text-[11px]">Exam Pattern</span>
                  <span className="text-ink font-bold text-xs block mt-0.5 truncate font-mono">
                    {isUniversity
                      ? report.selected_pattern_name
                      : (report.pattern_compliance.pattern_name_in_paper || "None")}
                  </span>
                  <span
                    className={`text-[10px] font-semibold mt-1 block truncate ${
                      report.pattern_compliance.pattern_name_match ? "text-brand-ink font-bold" : "text-accent-ink"
                    }`}
                  >
                    {report.pattern_compliance.pattern_name_match
                      ? `✓ Matches (${isUniversity ? report.selected_pattern_name : report.pattern_compliance.selected_category})`
                      : (isUniversity
                          ? "✗ Structure Mismatch"
                          : (report.pattern_compliance.has_pattern_name ? "✗ Mismatch" : "✗ Missing"))}
                  </span>
                </div>

                <div className="p-3 rounded-xl border border-line bg-surface-subtle">
                  <span className="text-ink-faint block text-[11px]">Maximum Marks</span>
                  <span className="text-ink font-bold text-sm block mt-0.5 font-mono">
                    {report.pattern_compliance.found_total_marks ?? "None"} / {report.pattern_compliance.expected_total_marks}
                  </span>
                  <span
                    className={`text-[10px] font-semibold mt-1 block ${
                      report.pattern_compliance.marks_match ? "text-brand-ink font-bold" : "text-accent-ink"
                    }`}
                  >
                    {report.pattern_compliance.marks_match ? "✓ Matches" : "✗ Mismatch"}
                  </span>
                </div>

                <div className="p-3 rounded-xl border border-line bg-surface-subtle">
                  <span className="text-ink-faint block text-[11px]">Duration</span>
                  <span className="text-ink font-bold text-sm block mt-0.5 font-mono">
                    {report.pattern_compliance.found_duration_minutes ?? "None"} / {report.pattern_compliance.expected_duration_minutes}m
                  </span>
                  <span
                    className={`text-[10px] font-semibold mt-1 block ${
                      report.pattern_compliance.duration_match ? "text-brand-ink font-bold" : "text-accent-ink"
                    }`}
                  >
                    {report.pattern_compliance.duration_match ? "✓ Matches" : "✗ Mismatch"}
                  </span>
                </div>

                <div
                  className="p-3 rounded-xl border border-line bg-surface-subtle"
                  title={report.pattern_compliance.found_sections?.join(", ") || ""}
                >
                  <span className="text-ink-faint block text-[11px]">Section Headers</span>
                  <span className="text-ink font-bold text-xs block mt-0.5 truncate font-mono">
                    {report.pattern_compliance.found_sections?.join(", ") || "None"}
                  </span>
                  <span
                    className={`text-[10px] font-semibold mt-1 block ${
                      report.pattern_compliance.sections_match ? "text-brand-ink font-bold" : "text-accent-ink"
                    }`}
                  >
                    {report.pattern_compliance.sections_match ? "✓ Matches" : "✗ Incomplete"}
                  </span>
                </div>
              </div>

              {/* Format Criteria Displayed One by One */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-ink-muted uppercase tracking-wider">
                    Format Criteria Checklist ({formatCriteria.length} items)
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowExtractedModal(true)}
                    className="text-xs text-brand-ink hover:underline underline-offset-4 flex items-center space-x-1 font-medium cursor-pointer"
                  >
                    <span>Inspect raw text</span>
                  </button>
                </div>

                <div className="border border-line rounded-xl overflow-hidden divide-y divide-line-subtle bg-surface shadow-sm">
                  {formatCriteria.map((c) => (
                    <div
                      key={c.id}
                      className="p-3 sm:px-4 sm:py-3 grid grid-cols-1 gap-2 sm:grid-cols-[minmax(0,1fr)_180px_minmax(0,1.35fr)] sm:items-center sm:gap-4 hover:bg-surface-subtle transition-colors"
                    >
                      <div className="min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="text-[11px] font-mono text-ink-faint font-bold">{c.num}</span>
                          <span className="text-xs font-semibold text-ink">{c.label}</span>
                        </div>
                      </div>

                      <div className="flex items-center sm:justify-center">
                        {c.passed ? (
                          <span className="text-xs text-brand-ink font-bold inline-flex items-center">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-brand-ink shrink-0" />
                            Found
                          </span>
                        ) : (
                          <span className="text-xs text-ink-faint font-medium inline-flex items-center">
                            <XCircle className="w-3.5 h-3.5 mr-1.5 text-ink-faint shrink-0" />
                            Missing
                          </span>
                        )}
                      </div>

                      <div className="min-w-0 text-left">
                        <div className="font-mono text-xs text-ink truncate font-medium">
                          {c.value}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 2) Exam Details Section */}
            <div className="space-y-4 pt-2 border-t border-line">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-line">
                <div className="flex items-center space-x-2.5">
                  <span className="px-2.5 py-0.5 rounded-lg bg-track border border-brand-line text-brand-ink font-mono font-bold text-xs">
                    2
                  </span>
                  <div>
                    <h2 className="text-sm sm:text-base font-bold text-ink tracking-wide uppercase">
                      Exam Details
                    </h2>
                  </div>
                </div>
                <span
                  className={`text-[11px] px-2.5 py-1 rounded-full font-bold uppercase font-mono self-start sm:self-auto shadow-sm ${
                    report.exam_details?.is_approved
                      ? "bg-brand text-btn-brand"
                      : "bg-accent text-btn-accent"
                  }`}
                >
                  {report.exam_details?.status || "BLOCKED"}
                </span>
              </div>

              {/* Mandatory Examination Details Summary Card */}
              <div className="p-4 rounded-xl border border-line bg-surface-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-surface border border-line flex items-center justify-center text-brand-ink shrink-0 shadow-sm">
                    <ClipboardList className="w-5 h-5 text-brand-ink" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-ink-muted font-bold uppercase tracking-wider">
                        Mandatory Examination Details
                      </span>
                      <span
                        className={`text-[11px] px-2.5 py-0.5 rounded-md font-mono font-bold uppercase ${
                          report.exam_details?.is_approved
                            ? "bg-brand text-btn-brand"
                            : "bg-accent text-btn-accent"
                        }`}
                      >
                        {report.exam_details?.is_approved ? "COMPLETE" : "INCOMPLETE"}
                      </span>
                    </div>
                    <p className="text-sm font-bold text-ink font-mono mt-0.5">
                      {examDetailsCriteria.filter((c) => c.passed).length} / {examDetailsCriteria.length} Details Clearly Given
                    </p>
                  </div>
                </div>

                {!report.exam_details?.is_approved && (
                  <div className="text-xs text-ink-faint font-mono sm:text-right max-w-sm">
                    Missing: {report.exam_details?.missing_details?.join(", ") || "Mandatory examination details missing"}
                  </div>
                )}
              </div>

              {/* Exam Details Criteria Displayed One by One */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-ink-muted uppercase tracking-wider">
                  Exam Details Checklist ({examDetailsCriteria.length} items)
                </span>

                <div className="border border-line rounded-xl overflow-hidden divide-y divide-line-subtle bg-surface shadow-sm">
                  {examDetailsCriteria.map((c) => (
                    <div
                      key={c.num}
                      className="p-3 sm:px-4 sm:py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-surface-subtle transition-colors"
                    >
                      <div className="space-y-0.5 sm:w-1/3">
                        <div className="flex items-center space-x-2">
                          <span className="text-[11px] font-mono text-ink-faint font-bold">{c.num}</span>
                          <span className="text-xs font-semibold text-ink">{c.label}</span>
                        </div>
                      </div>

                      <div className="sm:w-1/4 flex items-center">
                        {c.passed ? (
                          <span className="text-xs text-brand-ink font-bold inline-flex items-center">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-brand-ink shrink-0" />
                            Given
                          </span>
                        ) : (
                          <span className="text-xs text-ink-faint font-medium inline-flex items-center">
                            <XCircle className="w-3.5 h-3.5 mr-1.5 text-ink-faint shrink-0" />
                            Missing
                          </span>
                        )}
                      </div>

                      <div className="sm:w-5/12 text-left">
                        <div className="font-mono text-xs text-ink truncate font-medium">
                          {c.value}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 3) Syllabus Alignment & Unit Validation Section (Criterion 3 - Strict Zero Score) */}
            <div className="space-y-5 pt-3 border-t border-line">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-line">
                <div className="flex items-center space-x-2.5">
                  <span className="px-2.5 py-0.5 rounded-lg bg-track border border-brand-line text-brand-ink font-mono font-bold text-xs">
                    3
                  </span>
                  <div>
                    <h2 className="text-sm sm:text-base font-bold text-ink tracking-wide uppercase">
                      Syllabus Alignment & Unit Validation
                    </h2>
                  </div>
                </div>

                {report.syllabus_alignment ? (
                  <span
                    className={`text-[11px] px-3 py-1 rounded-full font-black uppercase font-mono self-start sm:self-auto shadow-sm transition-all duration-300 ${
                      report.syllabus_alignment.overall_status === "ALIGNED" || report.syllabus_alignment.overall_status === "PASS"
                        ? "bg-brand text-btn-brand"
                        : report.syllabus_alignment.overall_status === "MISMATCH" || report.syllabus_alignment.overall_status === "FLAG"
                        ? "bg-accent text-btn-accent"
                        : "bg-track text-brand-ink border border-brand-line"
                    }`}
                  >
                    {report.syllabus_alignment.overall_status}
                  </span>
                ) : (
                  <span className="text-[11px] px-2.5 py-1 rounded-full font-semibold font-mono bg-surface-muted text-ink-faint border border-line">
                    Syllabus Not Attached
                  </span>
                )}
              </div>

              {!report.syllabus_alignment ? (
                <div className="p-4 rounded-xl border border-line bg-surface-subtle flex items-center justify-between gap-3 text-xs text-ink-muted">
                  <div className="flex items-center space-x-2.5">
                    <BookOpen className="w-5 h-5 text-accent-ink shrink-0" />
                    <div>
                      <p className="font-semibold text-ink">No Syllabus Uploaded for Criterion 3 Validation</p>
                      <p className="text-[11px] text-ink-faint mt-0.5">
                        Upload a syllabus document (PDF / DOCX) in the upload bar above and re-check to perform automated question-to-syllabus semantic alignment.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Categorical Status & Question Count Cards (Counts Only, No Scores) */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Total Items</span>
                      <span className="text-ink font-bold text-base block mt-0.5 font-mono">
                        {report.syllabus_alignment.total_questions}
                      </span>
                      <span className="text-[10px] text-ink-faint block">Assessable Qs</span>
                    </div>

                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Aligned</span>
                      <span className="text-brand-ink font-bold text-base block mt-0.5 font-mono">
                        {report.syllabus_alignment.aligned_count}
                      </span>
                      <span className="text-[10px] text-brand-ink block font-semibold">In Scope</span>
                    </div>

                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Mismatch</span>
                      <span className={`text-base font-bold block mt-0.5 font-mono ${report.syllabus_alignment.mismatch_count > 0 ? "text-accent-ink underline font-extrabold" : "text-ink-faint"}`}>
                        {report.syllabus_alignment.mismatch_count}
                      </span>
                      <span className="text-[10px] text-ink-faint block">Scope Violation</span>
                    </div>

                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Ambiguous</span>
                      <span className="text-ink font-bold text-base block mt-0.5 font-mono">
                        {report.syllabus_alignment.ambiguous_count}
                      </span>
                      <span className="text-[10px] text-ink-faint block">Borderline</span>
                    </div>

                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Unmapped</span>
                      <span className="text-ink font-bold text-base block mt-0.5 font-mono">
                        {report.syllabus_alignment.unmapped_count}
                      </span>
                      <span className="text-[10px] text-ink-faint block">Outside Syl.</span>
                    </div>

                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Review Req.</span>
                      <span className={`text-base font-bold block mt-0.5 font-mono ${report.syllabus_alignment.review_required_count > 0 ? "text-accent-ink font-extrabold" : "text-ink-faint"}`}>
                        {report.syllabus_alignment.review_required_count}
                      </span>
                      <span className="text-[10px] text-ink-faint block">Faculty Review</span>
                    </div>
                  </div>

                  {/* Human Scrutiny Review Panel */}
                  {report.syllabus_alignment.requires_human_review && (
                    <div className="p-3.5 rounded-xl bg-accent-surface border border-accent-line space-y-2">
                      <div className="flex items-center space-x-2 text-accent-ink font-bold text-xs">
                        <AlertTriangle className="w-3.5 h-3.5 text-accent-ink" />
                        <span>Human Scrutiny Review Triggers</span>
                      </div>
                      <ul className="list-disc list-inside text-xs text-accent-ink space-y-1 font-mono">
                        {report.syllabus_alignment.review_reasons?.map((reason: string, idx: number) => (
                          <li key={idx}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* 3 Recharts Bar Charts */}
                  <div className="space-y-2.5">

                    <div className="syllabus-insight-grid grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Chart A: Prescribed Units */}
                      <div className="syllabus-unit-card p-5 rounded-2xl space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-ink uppercase tracking-[0.12em]">
                            Prescribed Units
                          </span>
                          <span className="syllabus-unit-tag">Units 1–5</span>
                        </div>
                        <div className="h-44 w-full pt-1">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={report.syllabus_alignment.chart_prescribed_units || []} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
                              <XAxis dataKey="unit_label" stroke={chartTheme.axisText} fontSize={10} tickLine={false} />
                              <YAxis stroke={chartTheme.axisText} fontSize={10} allowDecimals={false} tickLine={false} />
                              <Tooltip
                                contentStyle={{ backgroundColor: chartTheme.tooltipBg, borderColor: chartTheme.tooltipBorder, color: chartTheme.tooltipText, borderRadius: "8px", fontSize: "11px", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                              />
                              <Bar dataKey="question_count" name="Items" fill={isDark ? "#FFA116" : "#991B1B"} radius={[5, 5, 0, 0]} />
                              <Bar dataKey="question_group_count" name="Distinct Groups" fill={isDark ? "#0095FF" : "#EAB308"} radius={[5, 5, 0, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      {/* Syllabus Coverage Card */}
                      {(() => {
                        const prescribedUnits = report.syllabus_alignment.chart_prescribed_units || [];
                        const totalCoverageQuestions = prescribedUnits.reduce(
                          (sum: number, u: any) => sum + (u.question_count || 0),
                          0
                        ) || (report.syllabus_alignment.results?.length || 0);

                        const coverageUnitsData = (prescribedUnits.length > 0
                          ? prescribedUnits
                          : [
                              { unit_label: "Unit 1", question_count: 0 },
                              { unit_label: "Unit 2", question_count: 0 },
                              { unit_label: "Unit 3", question_count: 0 },
                              { unit_label: "Unit 4", question_count: 0 },
                              { unit_label: "Unit 5", question_count: 0 },
                            ]
                        ).map((u: any) => {
                          const count = u.question_count || 0;
                          const pct = totalCoverageQuestions > 0 ? Math.round((count / totalCoverageQuestions) * 100) : 0;
                          return {
                            ...u,
                            question_count: count,
                            percentage: pct,
                          };
                        });

                        return (
                          <div className="syllabus-coverage-card p-5 rounded-2xl space-y-4 md:col-span-2">
                            <div className="flex items-center justify-between gap-3">
                              <div className="flex items-center space-x-3">
                                <div className="syllabus-coverage-icon">
                                  <BarChart3 className="w-4 h-4" />
                                </div>
                                <span className="text-base font-bold text-ink tracking-tight">
                                  Syllabus Coverage
                                </span>
                              </div>
                              <span className="syllabus-total-badge">
                                {totalCoverageQuestions} questions
                              </span>
                            </div>

                            {/* Horizontal Bar Chart */}
                            <div className="h-44 w-full pt-1">
                              <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                  layout="vertical"
                                  data={coverageUnitsData}
                                  margin={{ top: 4, right: 20, left: 6, bottom: 4 }}
                                >
                                  <XAxis
                                    type="number"
                                    stroke={chartTheme.axisText}
                                    fontSize={10}
                                    tickLine={false}
                                    axisLine={{ stroke: chartTheme.grid }}
                                    allowDecimals={false}
                                  />
                                  <YAxis
                                    type="category"
                                    dataKey="unit_label"
                                    stroke={chartTheme.axisText}
                                    fontSize={11}
                                    tickLine={false}
                                    axisLine={false}
                                    width={55}
                                  />
                                  <Tooltip
                                    contentStyle={{
                                      backgroundColor: chartTheme.tooltipBg,
                                      borderColor: chartTheme.tooltipBorder,
                                      borderRadius: "8px",
                                      fontSize: "11px",
                                      color: chartTheme.tooltipText,
                                      boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                                    }}
                                    formatter={(value: any) => [`${value} questions`, "Coverage"]}
                                  />
                                  <Bar
                                    dataKey="question_count"
                                    name="Questions"
                                    fill={isDark ? "#FFA116" : "#991B1B"}
                                    radius={[0, 7, 7, 0]}
                                    barSize={16}
                                  />
                                </BarChart>
                              </ResponsiveContainer>
                            </div>

                            {/* Coverage Distribution Progress Bars */}
                            <div className="space-y-3 pt-3 border-t border-line">
                              <div className="flex items-center justify-between text-xs text-ink-faint">
                                <span className="font-semibold text-ink-muted uppercase tracking-wider text-[10px]">Coverage Distribution</span>
                                <span className="font-mono text-ink-faint">By unit</span>
                              </div>

                              <div className="space-y-2 pt-0.5">
                                {coverageUnitsData.map((u: any) => (
                                  <div key={u.unit_label} className="syllabus-coverage-row flex items-center space-x-3 text-xs">
                                    <span className="w-14 text-ink-muted font-semibold shrink-0">{u.unit_label}</span>
                                    <div className="flex-1 h-1.5 bg-surface-muted rounded-full overflow-hidden">
                                      <div
                                        className="h-full rounded-full transition-all duration-500"
                                        style={{
                                          width: `${Math.min(100, Math.max(u.percentage > 0 ? 3 : 0, u.percentage))}%`,
                                          backgroundColor: isDark ? "#FFA116" : "#991B1B",
                                        }}
                                      />
                                    </div>
                                    <span className="w-16 text-right font-mono font-medium text-ink shrink-0">
                                      {u.question_count} ({u.percentage}%)
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  </div>

                  {/* Question-to-Syllabus Mapping Table */}
                  <div className="space-y-3 pt-1">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <Layers className="w-4 h-4 text-brand-ink shrink-0" />
                        <span className="text-xs font-bold text-ink uppercase tracking-wider">
                          Question-to-Syllabus Mapping Matrix
                        </span>
                      </div>

                      {/* Filters Bar */}
                      <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono">
                        {/* Unit Filter */}
                        <div className="flex items-center space-x-1 bg-surface-muted border border-line rounded-lg px-2 py-1">
                          <span className="text-ink-faint text-[10px]">Unit:</span>
                          <select
                            value={filterUnit}
                            onChange={(e) => setFilterUnit(e.target.value)}
                            className="bg-transparent text-ink font-bold outline-none cursor-pointer text-[11px]"
                          >
                            <option value="ALL" className="bg-surface text-ink">All</option>
                            <option value="1" className="bg-surface text-ink">Unit 1</option>
                            <option value="2" className="bg-surface text-ink">Unit 2</option>
                            <option value="3" className="bg-surface text-ink">Unit 3</option>
                            <option value="4" className="bg-surface text-ink">Unit 4</option>
                            <option value="5" className="bg-surface text-ink">Unit 5</option>
                          </select>
                        </div>

                        {/* Section Filter */}
                        <div className="flex items-center space-x-1 bg-surface-muted border border-line rounded-lg px-2 py-1">
                          <span className="text-ink-faint text-[10px]">Part:</span>
                          <select
                            value={filterSection}
                            onChange={(e) => setFilterSection(e.target.value)}
                            className="bg-transparent text-ink font-bold outline-none cursor-pointer text-[11px]"
                          >
                            <option value="ALL" className="bg-surface text-ink">All Parts</option>
                            <option value="PART A" className="bg-surface text-ink">Part A</option>
                            <option value="PART B" className="bg-surface text-ink">Part B</option>
                            <option value="PART C" className="bg-surface text-ink">Part C</option>
                          </select>
                        </div>

                        {/* Status Filter */}
                        <div className="flex items-center space-x-1 bg-surface-muted border border-line rounded-lg px-2 py-1">
                          <span className="text-ink-faint text-[10px]">Status:</span>
                          <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="bg-transparent text-ink font-bold outline-none cursor-pointer text-[11px]"
                          >
                            <option value="ALL" className="bg-surface text-ink">All</option>
                            <option value="ALIGNED" className="bg-surface text-ink">ALIGNED</option>
                            <option value="MISMATCH" className="bg-surface text-ink">MISMATCH</option>
                            <option value="AMBIGUOUS" className="bg-surface text-ink">AMBIGUOUS</option>
                            <option value="UNMAPPED" className="bg-surface text-ink">UNMAPPED</option>
                            <option value="REVIEW_REQUIRED" className="bg-surface text-ink">REVIEW</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Mapping Table */}
                    <div className="border border-line rounded-xl overflow-x-auto bg-surface shadow-sm">
                      <table className="w-full table-fixed text-left border-collapse text-xs">
                        <colgroup>
                          <col className="w-[116px]" />
                          <col className="w-[210px]" />
                          <col className="w-[92px]" />
                          <col className="w-[92px]" />
                          <col className="w-[210px]" />
                          <col className="w-[92px]" />
                          <col className="w-[250px]" />
                        </colgroup>
                        <thead>
                          <tr className="border-b border-line bg-surface-muted text-ink-muted font-mono text-[10px] uppercase">
                            <th className="py-2.5 px-3">Q#</th>
                            <th className="py-2.5 px-3 min-w-[200px]">Question Statement</th>
                            <th className="py-2.5 px-2.5 text-center">Prescribed</th>
                            <th className="py-2.5 px-2.5 text-center">Matched</th>
                            <th className="py-2.5 px-3">Matched Syllabus Topic</th>
                            <th className="py-2.5 px-2.5 text-center">Status</th>
                            <th className="py-2.5 px-3 min-w-[180px]">Scrutinizer Explanation</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-line-subtle">
                          {filteredResults.length === 0 ? (
                            <tr>
                              <td colSpan={7} className="py-8 text-center text-ink-faint font-mono text-xs">
                                No questions matched the selected filters.
                              </td>
                            </tr>
                          ) : (
                            filteredResults.map((item: any) => (
                              <tr key={item.question_id} className="h-20 hover:bg-surface-subtle transition-colors">
                                <td className="px-3 align-middle font-mono">
                                  <div className="flex flex-col items-start gap-1">
                                    <span className="font-bold text-ink">{item.question_id}</span>
                                    <div className="flex items-center gap-1 whitespace-nowrap">
                                      {item.section && (
                                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-track border border-brand-line text-brand-ink font-semibold">
                                          {item.section}
                                        </span>
                                      )}
                                      {item.marks != null && (
                                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-danger-surface text-danger-ink border border-danger-line font-bold">
                                          {item.marks}M
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </td>
                                <td className="px-3 align-middle text-ink-muted font-medium">
                                  <p className="truncate" title={item.question_text}>
                                    {item.question_text}
                                  </p>
                                </td>
                                <td className="px-2.5 align-middle text-center font-mono">
                                  {item.marks === 15 || item.section?.toUpperCase().includes("C") || item.question_number === "16" ? (
                                    <span className="font-bold text-ink-muted text-[11px] px-1.5 py-0.5 rounded bg-surface-muted border border-line" title="15-mark questions are permitted from any unit in the syllabus">
                                      Any (1-5)
                                    </span>
                                  ) : item.required_unit ? (
                                    <span className="font-bold text-ink">Unit {item.required_unit}</span>
                                  ) : (
                                    <span className="text-ink-faint text-[11px]">—</span>
                                  )}
                                </td>
                                <td className="px-2.5 align-middle text-center font-mono">
                                  {item.matched_unit ? (
                                    <span className="font-bold text-brand-ink">Unit {item.matched_unit}</span>
                                  ) : (
                                    <span className="text-ink-faint text-[11px]">None</span>
                                  )}
                                </td>
                                <td className="px-3 align-middle text-ink-muted font-medium">
                                  <span className="truncate block max-w-[180px]" title={item.matched_topic || "None"}>
                                    {item.matched_topic || "—"}
                                  </span>
                                </td>
                                <td className="px-2.5 align-middle text-center font-mono">
                                  <span
                                    className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase shadow-sm ${
                                      item.status === "ALIGNED"
                                        ? "bg-brand text-btn-brand"
                                        : item.status === "MISMATCH"
                                        ? "bg-accent text-btn-accent"
                                        : item.status === "AMBIGUOUS"
                                        ? "bg-track text-brand-ink border border-brand-line"
                                        : item.status === "UNMAPPED"
                                        ? "bg-danger-surface text-danger-ink border border-danger-line"
                                        : "bg-track text-brand-ink border border-brand-line"
                                    }`}
                                  >
                                    {item.status}
                                  </span>
                                </td>
                                <td className="px-3 align-middle text-left">
                                  <p className="truncate text-[11px] text-ink-muted" title={item.reason}>
                                    {item.reason}
                                  </p>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 4) Mark and Time Distribution Section (Criterion 4 - Strict Zero Score) */}
            <div className="space-y-5 pt-3 border-t border-line">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-line">
                <div className="flex items-center space-x-2.5">
                  <span className="px-2.5 py-0.5 rounded-lg bg-track border border-brand-line text-brand-ink font-mono font-bold text-xs">
                    4
                  </span>
                  <div>
                    <h2 className="text-sm sm:text-base font-bold text-ink tracking-wide uppercase">
                      Mark and Time Distribution
                    </h2>
                  </div>
                </div>

                {report.mark_distribution ? (
                  <span
                    className={`text-[11px] px-3 py-1 rounded-full font-black uppercase font-mono self-start sm:self-auto shadow-sm transition-all duration-300 ${
                      report.mark_distribution.overall_status === "PASS"
                        ? "bg-brand text-btn-brand"
                        : report.mark_distribution.overall_status === "FLAG"
                        ? "bg-accent text-btn-accent"
                        : "bg-track text-brand-ink border border-brand-line"
                    }`}
                  >
                    {report.mark_distribution.overall_status}
                  </span>
                ) : (
                  <span className="text-[11px] px-2.5 py-1 rounded-full font-semibold font-mono bg-surface-muted text-ink-faint border border-line">
                    Not Evaluated
                  </span>
                )}
              </div>

              {!report.mark_distribution ? (
                <div className="p-4 rounded-xl border border-line bg-surface-subtle flex items-center justify-between gap-3 text-xs text-ink-muted">
                  <div className="flex items-center space-x-2.5">
                    <AlertTriangle className="w-5 h-5 text-accent-ink shrink-0" />
                    <div>
                      <p className="font-semibold text-ink">Mark Distribution Scrutiny Not Available</p>
                      <p className="text-[11px] text-ink-faint mt-0.5">
                        Please upload a question paper document to analyze question complexity and mark allocations.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Categorical Metric Cards (Counts Only, Zero Scores) */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Total Evaluated</span>
                      <span className="text-ink font-bold text-base block mt-0.5 font-mono">
                        {report.mark_distribution.total_questions_evaluated}
                      </span>
                      <span className="text-[10px] text-ink-faint block">Questions</span>
                    </div>

                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Compliant</span>
                      <span className="text-brand-ink font-bold text-base block mt-0.5 font-mono">
                        {report.mark_distribution.pass_count}
                      </span>
                      <span className="text-[10px] text-brand-ink block font-semibold">PASS</span>
                    </div>

                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Flagged</span>
                      <span className={`text-base font-bold block mt-0.5 font-mono ${report.mark_distribution.flag_count > 0 ? "text-accent-ink underline font-extrabold" : "text-ink-faint"}`}>
                        {report.mark_distribution.flag_count}
                      </span>
                      <span className="text-[10px] text-ink-faint block">Violations</span>
                    </div>

                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Rule 1: Part A</span>
                      <span className={`text-base font-bold block mt-0.5 font-mono ${(report.mark_distribution.rule_part_a_subdivision_flags || report.mark_distribution.part_a_subdivision_flags) > 0 ? "text-accent-ink underline font-extrabold" : "text-ink-faint"}`}>
                        {report.mark_distribution.rule_part_a_subdivision_flags || report.mark_distribution.part_a_subdivision_flags || 0}
                      </span>
                      <span className="text-[10px] text-ink-faint block">No Sub-divisions</span>
                    </div>

                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Rule 2: Part B/C</span>
                      <span className={`text-base font-bold block mt-0.5 font-mono ${report.mark_distribution.rule_3_subdivision_flags > 0 ? "text-accent-ink underline font-extrabold" : "text-ink-faint"}`}>
                        {report.mark_distribution.rule_3_subdivision_flags || 0}
                      </span>
                      <span className="text-[10px] text-ink-faint block">Max 2 Sub-divisions</span>
                    </div>

                    <div className="p-2.5 rounded-xl border border-line bg-surface-subtle">
                      <span className="text-ink-faint block text-[10px] uppercase font-semibold">Rule 3: Part B/C</span>
                      <span className={`text-base font-bold block mt-0.5 font-mono ${(report.mark_distribution.rule_subdivision_mark_flags || report.mark_distribution.subdivision_mark_flags) > 0 ? "text-accent-ink underline font-extrabold" : "text-ink-faint"}`}>
                        {report.mark_distribution.rule_subdivision_mark_flags || report.mark_distribution.subdivision_mark_flags || 0}
                      </span>
                      <span className="text-[10px] text-ink-faint block">Sub-division Marks</span>
                    </div>
                  </div>

                  {/* Human Scrutiny Review Panel */}
                  {report.mark_distribution.requires_human_review && (
                    <div className="p-3.5 rounded-xl bg-accent-surface border border-accent-line space-y-2">
                      <div className="flex items-center space-x-2 text-accent-ink font-bold text-xs">
                        <AlertTriangle className="w-3.5 h-3.5 text-accent-ink" />
                        <span>Human Scrutiny Review Triggers (Criterion 4)</span>
                      </div>
                      <ul className="list-disc list-inside text-xs text-accent-ink space-y-1 font-mono">
                        {report.mark_distribution.review_reasons?.map((reason: string, idx: number) => (
                          <li key={idx}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Question-level Evaluation Matrix Table */}
                  <div className="space-y-3 pt-1">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <Layers className="w-4 h-4 text-brand-ink shrink-0" />
                        <span className="text-xs font-bold text-ink uppercase tracking-wider">
                          Mark Distribution Evaluation Matrix ({filteredC4Evaluations.length} of {report.mark_distribution.evaluations?.length || 0})
                        </span>
                      </div>

                      {/* Filters */}
                      <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono">
                        {/* Section Filter */}
                        <div className="flex items-center space-x-1 bg-surface-muted border border-line rounded-lg px-2 py-1">
                          <span className="text-ink-faint text-[10px]">Section:</span>
                          <select
                            value={c4FilterSection}
                            onChange={(e) => setC4FilterSection(e.target.value)}
                            className="bg-transparent text-ink font-bold outline-none cursor-pointer text-[11px]"
                          >
                            <option value="ALL" className="bg-surface text-ink">All</option>
                            <option value="PART A" className="bg-surface text-ink">Part A</option>
                            <option value="PART B" className="bg-surface text-ink">Part B</option>
                            <option value="PART C" className="bg-surface text-ink">Part C</option>
                          </select>
                        </div>

                        {/* Status Filter */}
                        <div className="flex items-center space-x-1 bg-surface-muted border border-line rounded-lg px-2 py-1">
                          <span className="text-ink-faint text-[10px]">Status:</span>
                          <select
                            value={c4FilterStatus}
                            onChange={(e) => setC4FilterStatus(e.target.value)}
                            className="bg-transparent text-ink font-bold outline-none cursor-pointer text-[11px]"
                          >
                            <option value="ALL" className="bg-surface text-ink">All</option>
                            <option value="PASS" className="bg-surface text-ink">PASS</option>
                            <option value="FLAG" className="bg-surface text-ink">FLAG</option>
                            <option value="REVIEW_REQUIRED" className="bg-surface text-ink">REVIEW</option>
                          </select>
                        </div>

                        {/* Rule Filter */}
                        <div className="flex items-center space-x-1 bg-surface-muted border border-line rounded-lg px-2 py-1">
                          <span className="text-ink-faint text-[10px]">Rule:</span>
                          <select
                            value={c4FilterRule}
                            onChange={(e) => setC4FilterRule(e.target.value)}
                            className="bg-transparent text-ink font-bold outline-none cursor-pointer text-[11px]"
                          >
                            <option value="ALL" className="bg-surface text-ink">All Rules</option>
                            <option value="RULE_PART_A_NO_SUBDIVISIONS" className="bg-surface text-ink">Rule 1: Part A No Sub-divisions</option>
                            <option value="RULE_3_SUBDIVISION_COUNT" className="bg-surface text-ink">Rule 2: Part B/C Max 2 Sub-divisions</option>
                            <option value="RULE_SUBDIVISION_MARKS_ALLOCATION" className="bg-surface text-ink">Rule 3: Part B/C Sub-division Marks Allocation</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Table */}
                    <div className="border border-line rounded-xl overflow-x-auto bg-surface shadow-sm">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-line bg-surface-muted text-ink-muted font-mono text-[10px] uppercase">
                            <th className="py-2.5 px-3">Q#</th>
                            <th className="py-2.5 px-2.5 text-center">Section</th>
                            <th className="py-2.5 px-2.5 text-center">Marks</th>
                            <th className="py-2.5 px-3 text-center">Sub-divisions</th>
                            <th className="py-2.5 px-2.5 text-center">Status</th>
                            <th className="py-2.5 px-3 min-w-[240px]">Scrutiny Finding / Justification</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-line-subtle">
                          {filteredC4Evaluations.length === 0 ? (
                            <tr>
                              <td colSpan={7} className="py-8 text-center text-ink-faint font-mono text-xs">
                                No questions matched the selected filters.
                              </td>
                            </tr>
                          ) : (
                            filteredC4Evaluations.map((item: any) => (
                              <tr key={item.question_id} className="hover:bg-surface-subtle transition-colors">
                                <td className="py-3 px-3 font-mono font-bold text-ink">
                                  {item.question_id}
                                </td>
                                <td className="py-3 px-2.5 text-center font-mono text-ink-muted">
                                  {item.section || "—"}
                                </td>
                                <td className="py-3 px-2.5 text-center font-mono">
                                  {item.assigned_marks != null ? (
                                    <span className="text-[11px] px-2 py-0.5 rounded bg-surface-muted border border-line text-ink font-bold">
                                      {item.assigned_marks}M
                                    </span>
                                  ) : (
                                    <span className="text-ink-faint">—</span>
                                  )}
                                </td>
                                <td className="py-3 px-3 text-center font-mono">
                                  {item.subdivision_count != null ? (
                                    <div className="flex flex-col items-center">
                                      <span className={`text-[11px] font-bold ${item.subdivision_count > 2 ? "text-accent-ink underline" : "text-ink-muted"}`}>
                                        {item.subdivision_count} sub{item.subdivision_count !== 1 ? "s" : ""}
                                      </span>
                                      {item.subdivision_labels && item.subdivision_labels.length > 0 && (
                                        <span className="text-[9px] text-ink-faint block max-w-[120px] truncate" title={item.subdivision_labels.join(", ")}>
                                          [{item.subdivision_labels.join(", ")}]
                                        </span>
                                      )}
                                    </div>
                                  ) : (
                                    <span className="text-ink-faint">—</span>
                                  )}
                                </td>
                                <td className="py-3 px-2.5 text-center font-mono">
                                  <span
                                    className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase shadow-sm ${
                                      item.status === "PASS"
                                        ? "bg-brand text-btn-brand"
                                        : item.status === "FLAG"
                                        ? "bg-accent text-btn-accent"
                                        : "bg-track text-brand-ink border border-brand-line"
                                    }`}
                                  >
                                    {item.status}
                                  </span>
                                </td>
                                <td className="py-3 px-3 text-left">
                                  <p className="text-[11px] text-ink-muted leading-relaxed" title={item.reason}>
                                    {item.reason}
                                  </p>
                                  {item.rule_triggered && (
                                    <span className="text-[9px] text-ink-faint font-mono block mt-1 uppercase">
                                      Trigger: {item.rule_triggered}
                                    </span>
                                  )}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* 5) Bloom's Taxonomy Section (Criterion 5 - Strict Zero Score) */}
            {report.blooms_taxonomy && (
              <div className="rounded-2xl border border-line bg-surface p-6 shadow-sm space-y-6 text-ink">
                {/* Section Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-line">
                  <div className="flex items-center space-x-2.5">
                    <span className="px-2.5 py-0.5 rounded-lg bg-track border border-brand-line text-brand-ink font-mono font-bold text-xs">
                      5
                    </span>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h2 className="text-sm sm:text-base font-bold text-ink tracking-wide uppercase">
                          Bloom&apos;s Taxonomy
                        </h2>
                      </div>
                    </div>
                  </div>

                  {/* Overall Status Badge */}
                  <div className="shrink-0 flex items-center">
                    <span
                      className={`text-xs font-mono font-black px-4 py-1.5 rounded-full flex items-center space-x-1.5 shadow-sm uppercase transition-all duration-300 ${
                        report.blooms_taxonomy.overall_status === "PASS"
                          ? "bg-brand text-btn-brand"
                          : report.blooms_taxonomy.overall_status === "FLAG"
                          ? "bg-accent text-btn-accent"
                          : "bg-track text-brand-ink border border-brand-line"
                      }`}
                    >
                      {report.blooms_taxonomy.overall_status === "PASS" ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5 text-btn-brand" />
                          <span>COMPLIANT — BT APPROVED</span>
                        </>
                      ) : report.blooms_taxonomy.overall_status === "FLAG" ? (
                        <span>BT SCRUTINY FLAGGED</span>
                      ) : (
                        <span>HUMAN REVIEW REQUIRED</span>
                      )}
                    </span>
                  </div>
                </div>

                {/* 4 Metric Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {/* 1. Declared BT Level */}
                  <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1.5">
                    <span className="text-[11px] font-mono text-ink-faint uppercase tracking-wider block">
                      1. Declared BT Level
                    </span>
                    <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                      {report.blooms_taxonomy.rule_bt_mentioned_count} / {report.blooms_taxonomy.total_questions} Mentioned
                    </p>
                  </div>

                  {/* 2. Either/Or Parity */}
                  <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1.5">
                    <span className="text-[11px] font-mono text-ink-faint uppercase tracking-wider block">
                      2. Choice Option Parity
                    </span>
                    <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                      {report.blooms_taxonomy.choice_pairs_parity.length - report.blooms_taxonomy.rule_or_parity_flag_count} / {report.blooms_taxonomy.choice_pairs_parity.length} Parity Compliant
                    </p>
                  </div>
                </div>

                {/* Pie Chart & UG Target Breakdown Section */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 p-5 rounded-xl border border-line bg-surface-subtle">
                  {/* Left: Recharts Pie Chart (5 cols) */}
                  <div className="lg:col-span-5 flex flex-col items-center justify-center border-b lg:border-b-0 lg:border-r border-line pb-6 lg:pb-0 lg:pr-6">
                    <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink-muted mb-2">
                      Bloom&apos;s Taxonomy Weightage (Pie Chart)
                    </h3>
                    <div className="w-full h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={report.blooms_taxonomy.distribution_pie_data}
                            dataKey="marks_percentage"
                            nameKey="display_name"
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            innerRadius={45}
                            paddingAngle={3}
                            label={(entry: any) => `${(entry.name || "").replace("Category ", "Cat ")}: ${entry.marks_percentage ?? entry.value}%`}
                          >
                            {report.blooms_taxonomy.distribution_pie_data.map((entry: any, index: number) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={chartTheme.pieColors[index % chartTheme.pieColors.length]}
                                stroke={chartTheme.tooltipBg}
                                strokeWidth={2}
                              />
                            ))}
                          </Pie>
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const data = payload[0].payload;
                                return (
                                  <div className="bg-surface border border-line text-ink p-2.5 rounded-lg text-xs shadow-xl space-y-1">
                                    <p className="font-bold font-mono">{data.display_name} — {data.tier}</p>
                                    <p className="text-ink-muted">Marks: <span className="font-mono font-bold text-ink">{data.marks}M</span> ({data.marks_percentage}%)</p>
                                    <p className="text-ink-muted">UG Target: <span className="font-mono text-brand-ink font-bold">{data.target}</span></p>
                                    <p className="text-ink-faint">Questions: {data.question_count}</p>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="flex items-center justify-center space-x-4 mt-2 text-[11px] font-mono font-bold">
                      <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full inline-block shadow-sm" style={{ backgroundColor: chartTheme.pieColors[0] }}></span><span className="text-ink-muted">Cat A (Base)</span></span>
                      <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full inline-block shadow-sm" style={{ backgroundColor: chartTheme.pieColors[1] }}></span><span className="text-ink-muted">Cat B (Medium)</span></span>
                      <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full inline-block shadow-sm" style={{ backgroundColor: chartTheme.pieColors[2] }}></span><span className="text-ink-muted">Cat C (Highest)</span></span>
                    </div>
                  </div>

                  {/* Right: 3 Category Target Cards (7 cols) */}
                  <div className="lg:col-span-7 space-y-3 flex flex-col justify-center">
                    <div className="flex items-center justify-between pb-1">
                      <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink-muted">
                        UG Level Distribution Targets
                      </h3>
                      <span className="text-[11px] font-mono text-ink-faint">Target Guidelines</span>
                    </div>

                    {report.blooms_taxonomy.distribution_slices.map((slice: any, idx: number) => (
                      <div
                        key={`slice-${idx}`}
                        className="p-3.5 rounded-xl border border-line bg-surface flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-sm"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-ink font-mono">{slice.display_name}</span>
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-muted text-ink-muted border border-line">
                              {slice.description}
                            </span>
                          </div>
                          <div className="text-[11px] text-ink-faint">
                            Levels: <span className="text-ink font-mono font-semibold">{slice.levels_present.join(", ") || "None"}</span> • {slice.question_count} question(s)
                          </div>
                          <div className="text-[11px] text-ink-faint">
                            {slice.comment}
                          </div>
                        </div>

                        <div className="text-left sm:text-right shrink-0">
                          <div className="flex items-baseline sm:justify-end space-x-1.5">
                            <span className="text-base font-bold font-mono text-brand-ink">{slice.marks_percentage}%</span>
                            <span className="text-xs text-ink-faint font-mono">({slice.total_marks}M)</span>
                          </div>
                          <div className="text-[11px] font-mono text-ink-faint">
                            Target: <span className="text-ink font-semibold">{slice.target_percentage_str}</span>
                          </div>
                          <span
                            className={`inline-block text-[10px] font-mono font-bold mt-1 px-2.5 py-0.5 rounded-full shadow-sm ${
                              slice.status === "PASS"
                                ? "bg-brand text-btn-brand"
                                : "bg-accent text-btn-accent"
                            }`}
                          >
                            {slice.status === "PASS" ? "TARGET MET" : "OUT OF RANGE"}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Either / Or Option Knowledge Parity Table */}
                {report.blooms_taxonomy.choice_pairs_parity.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <h3 className="text-xs sm:text-sm font-bold text-ink tracking-tight">
                          &apos;Either&apos; and &apos;Or&apos; Knowledge Level Parity Audit
                        </h3>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-ink-faint font-mono">Filter:</span>
                        <select
                          value={btParityFilter}
                          onChange={(e) => setBtParityFilter(e.target.value)}
                          className="bg-surface-muted border border-line text-ink text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-brand font-mono"
                        >
                          <option value="ALL" className="bg-surface text-ink">All Pairs ({report.blooms_taxonomy.choice_pairs_parity.length})</option>
                          <option value="FLAG" className="bg-surface text-ink">Disparities Flagged ({report.blooms_taxonomy.rule_or_parity_flag_count})</option>
                          <option value="PASS" className="bg-surface text-ink">Parity Compliant</option>
                        </select>
                      </div>
                    </div>

                    <div className="overflow-x-auto rounded-xl border border-line bg-surface shadow-sm">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="border-b border-line bg-surface-muted font-mono text-ink-muted uppercase text-[10px]">
                            <th className="py-2.5 px-3">Choice Group</th>
                            <th className="py-2.5 px-3">Option A (Either)</th>
                            <th className="py-2.5 px-3">Option B (Or)</th>
                            <th className="py-2.5 px-3">Parity Status</th>
                            <th className="py-2.5 px-3">Scrutiny Finding</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-line-subtle">
                          {filteredBtParity.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="py-4 text-center text-ink-faint font-mono">
                                No choice pairs match the selected filter.
                              </td>
                            </tr>
                          ) : (
                            filteredBtParity.map((pair: any, pIdx: number) => (
                              <tr key={`parity-${pIdx}`} className="hover:bg-surface-subtle transition-colors">
                                <td className="py-2.5 px-3 font-mono font-bold text-ink whitespace-nowrap">
                                  {pair.choice_group}
                                  <span className="text-[10px] text-ink-faint font-normal block">{pair.section}</span>
                                </td>
                                <td className="py-2.5 px-3 font-mono whitespace-nowrap">
                                  <span className="text-ink font-semibold">{pair.option_a_id}</span>
                                  <span className="text-ink-faint block text-[11px]">{pair.option_a_bt} ({pair.option_a_category})</span>
                                </td>
                                <td className="py-2.5 px-3 font-mono whitespace-nowrap">
                                  <span className="text-ink font-semibold">{pair.option_b_id}</span>
                                  <span className="text-ink-faint block text-[11px]">{pair.option_b_bt} ({pair.option_b_category})</span>
                                </td>
                                <td className="py-2.5 px-3 whitespace-nowrap">
                                  <span
                                    className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full inline-block shadow-sm ${
                                      pair.status === "PASS"
                                        ? "bg-brand text-btn-brand"
                                        : "bg-accent text-btn-accent"
                                    }`}
                                  >
                                    {pair.status}
                                  </span>
                                </td>
                                <td className="py-2.5 px-3 text-ink-muted">
                                  {pair.reason}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Question-by-Question Bloom's Taxonomy Table */}
                <div className="space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h3 className="text-xs sm:text-sm font-bold text-ink tracking-tight">
                        Question-Level Bloom&apos;s Taxonomy Verification
                      </h3>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-ink-faint font-mono">Filter:</span>
                      <select
                        value={btQuestionFilter}
                        onChange={(e) => setBtQuestionFilter(e.target.value)}
                        className="bg-surface-muted border border-line text-ink text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-brand font-mono"
                      >
                        <option value="ALL" className="bg-surface text-ink">All Questions ({report.blooms_taxonomy.questions.length})</option>
                        <option value="MISSING_BT" className="bg-surface text-ink">Missing Declared BT ({report.blooms_taxonomy.rule_bt_missing_count})</option>
                        <option value="MISMATCH_BT" className="bg-surface text-ink">Mismatched BT ({report.blooms_taxonomy.rule_bt_mismatch_count})</option>
                        <option value="WH_FLAG" className="bg-surface text-ink">Wh-Questions Flagged ({report.blooms_taxonomy.rule_wh_avoidance_flag_count})</option>
                        <option value="CATEGORY_A" className="bg-surface text-ink">Category A (Remember / Understand)</option>
                        <option value="CATEGORY_B" className="bg-surface text-ink">Category B (Apply / Analyze)</option>
                        <option value="CATEGORY_C" className="bg-surface text-ink">Category C (Evaluate / Create)</option>
                        <option value="FLAG" className="bg-surface text-ink">Overall Flagged</option>
                        <option value="PASS" className="bg-surface text-ink">Overall Passed</option>
                      </select>
                    </div>
                  </div>

                  <div className="overflow-x-auto rounded-xl border border-line bg-surface shadow-sm">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-line bg-surface-muted font-mono text-ink-muted uppercase text-[10px]">
                          <th className="py-2.5 px-3">Q ID</th>
                          <th className="py-2.5 px-3">Marks</th>
                          <th className="py-2.5 px-3">Question Statement</th>
                          <th className="py-2.5 px-3">Declared BT</th>
                          <th className="py-2.5 px-3">Evaluated BT</th>
                          <th className="py-2.5 px-3">Action Verb</th>
                          <th className="py-2.5 px-3">Wh-Check</th>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3 min-w-[200px]">Scrutiny Finding</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-line-subtle">
                        {filteredBtQuestions.length === 0 ? (
                          <tr>
                            <td colSpan={9} className="py-4 text-center text-ink-faint font-mono">
                              No questions match the selected filter.
                            </td>
                          </tr>
                        ) : (
                          filteredBtQuestions.map((q: any, qIdx: number) => (
                            <tr key={`bt-q-${qIdx}`} className="hover:bg-surface-subtle transition-colors">
                              <td className="py-2.5 px-3 font-mono font-bold text-ink whitespace-nowrap">
                                {q.question_id}
                                <span className="text-[10px] text-ink-faint font-normal block">{q.section}</span>
                              </td>
                              <td className="py-2.5 px-3 font-mono text-ink-muted whitespace-nowrap">
                                {q.marks}M
                              </td>
                              <td className="py-2.5 px-3 max-w-xs text-ink-muted">
                                <p className="line-clamp-2" title={q.text}>{q.text}</p>
                              </td>
                              <td className="py-2.5 px-3 font-mono whitespace-nowrap">
                                {q.declared_bt ? (
                                  <span className="px-2 py-0.5 rounded bg-surface-muted border border-line text-ink font-bold">
                                    {q.declared_bt}
                                  </span>
                                ) : (
                                  <span className="text-[11px] font-mono text-ink-faint italic">
                                    Missing
                                  </span>
                                )}
                              </td>
                              <td className="py-2.5 px-3 font-mono whitespace-nowrap">
                                <span className="font-bold text-brand-ink">{q.evaluated_bt}</span>
                                <span className="text-[10px] text-ink-faint block">{q.bt_level_name}</span>
                              </td>
                              <td className="py-2.5 px-3 font-mono text-ink-muted whitespace-nowrap">
                                {q.matched_action_verb ? (
                                  <span className="capitalize">{q.matched_action_verb}</span>
                                ) : (
                                  <span className="text-ink-faint">—</span>
                                )}
                              </td>
                              <td className="py-2.5 px-3 whitespace-nowrap font-mono text-[11px]">
                                {q.has_wh_question ? (
                                  <span className="text-accent-ink font-bold">&apos;{q.wh_word_found}&apos;</span>
                                ) : (
                                  <span className="text-ink-faint">✓ None</span>
                                )}
                              </td>
                              <td className="py-2.5 px-3 whitespace-nowrap">
                                <span
                                  className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full inline-block shadow-sm ${
                                    q.overall_status === "PASS"
                                      ? "bg-brand text-btn-brand"
                                      : "bg-accent text-btn-accent"
                                  }`}
                                >
                                  {q.overall_status}
                                </span>
                              </td>
                              <td className="py-2.5 px-3 text-[11px] text-ink-faint">
                                {q.reasons && q.reasons.length > 0 ? (
                                  <ul className="list-disc pl-3 space-y-0.5">
                                    {q.reasons.map((r: string, rIdx: number) => (
                                      <li key={`r-${rIdx}`} className="text-ink-muted">{r}</li>
                                    ))}
                                  </ul>
                                ) : (
                                  <span className="text-ink-faint">All checks passed.</span>
                                )}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* 6) Grammar, Spelling and Sentence Formation Section (Criterion 6 - Strict Zero Score) */}
        {report.grammar_check && (
          <div className="rounded-2xl border border-line bg-surface p-6 shadow-sm space-y-6 text-ink">
            {/* Section Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-line">
              <div className="flex items-center space-x-2.5">
                <span className="px-2.5 py-0.5 rounded-lg bg-track border border-brand-line text-brand-ink font-mono font-bold text-xs">
                  6
                </span>
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-base sm:text-lg font-bold text-ink tracking-tight">
                      Grammar, Spelling & Sentence Formation
                    </h2>
                  </div>
                </div>
              </div>

              {/* Overall Status Badge */}
              <div className="shrink-0 flex items-center">
                <span
                  className={`text-xs font-mono font-black px-4 py-1.5 rounded-full flex items-center space-x-1.5 shadow-sm uppercase transition-all duration-300 ${
                    report.grammar_check.overall_status === "PASS"
                      ? "bg-brand text-btn-brand"
                      : report.grammar_check.overall_status === "FLAG"
                      ? "bg-accent text-btn-accent"
                      : "bg-track text-brand-ink border border-brand-line"
                  }`}
                >
                  {report.grammar_check.overall_status === "PASS" ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-btn-brand" />
                      <span>COMPLIANT — LINGUISTICALLY SOUND</span>
                    </>
                  ) : report.grammar_check.overall_status === "FLAG" ? (
                    <span>LINGUISTIC ISSUES FLAGGED</span>
                  ) : (
                    <span>HUMAN REVIEW REQUIRED</span>
                  )}
                </span>
              </div>
            </div>

            {/* 4 Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* 1. Overall Status */}
              <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1.5">
                <span className="text-[11px] font-mono text-ink-faint uppercase tracking-wider block">
                  1. Overall Linguistic Status
                </span>
                <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                  {report.grammar_check.overall_status}
                </p>
              </div>

              {/* 2. Questions Examined */}
              <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1.5">
                <span className="text-[11px] font-mono text-ink-faint uppercase tracking-wider block">
                  2. Questions Examined
                </span>
                <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                  {report.grammar_check.total_questions_examined} Questions
                </p>
              </div>

              {/* 3. Questions Flagged */}
              <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1.5">
                <span className="text-[11px] font-mono text-ink-faint uppercase tracking-wider block">
                  3. Questions Flagged
                </span>
                <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                  {report.grammar_check.questions_with_issues_count} Flagged
                </p>
              </div>

            </div>

            {/* Error Breakdown By Category Chips */}
            <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold uppercase tracking-wider text-ink-muted">
                  Filters
                </span>
              </div>
              <div className="flex flex-wrap gap-2 pt-1">
                {[
                  { key: "SPELLING", label: "Spelling" },
                  { key: "GRAMMAR", label: "Grammar" },
                  { key: "SENTENCE_STRUCTURE", label: "Sentence Structure" },
                  { key: "PUNCTUATION", label: "Punctuation" },
                  { key: "CLARITY", label: "Clarity" },
                  { key: "AMBIGUITY", label: "Ambiguity" },
                  { key: "INCOMPLETE_SENTENCE", label: "Incomplete Sentence" },
                ].map(({ key, label }) => {
                  const count = (report.grammar_check.issues_by_category || {})[key] || 0;
                  const isSelected = grammarCategoryFilter === key;
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() =>
                        setGrammarCategoryFilter(isSelected ? "ALL" : key)
                      }
                      className={`text-[11px] font-mono px-3 py-1.5 rounded-lg border transition-all flex items-center space-x-1.5 cursor-pointer focus-visible:ring-2 focus-visible:ring-brand ${
                        isSelected
                          ? "bg-brand text-btn-brand border-brand font-bold shadow-sm"
                          : count > 0
                          ? "bg-surface border-line text-ink hover:border-brand"
                          : "bg-surface-muted border-transparent text-ink-faint hover:text-ink-muted"
                      }`}
                    >
                      <span>{label}:</span>
                      <span
                        className={`font-bold ${
                          isSelected
                            ? "text-btn-brand"
                            : count > 0
                            ? "text-brand-ink"
                            : "text-ink-faint"
                        }`}
                      >
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Question-Level Grammar Scrutiny Audit */}
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-xs sm:text-sm font-bold text-ink tracking-tight">
                    Question-by-Question Linguistic & Grammatical Audit
                  </h3>
                </div>

                {/* Filters */}
                <div className="flex flex-wrap items-center gap-2">
                  {/* Status Filter */}
                  <select
                    value={grammarStatusFilter}
                    onChange={(e) => setGrammarStatusFilter(e.target.value)}
                    className="bg-surface-muted border border-line text-ink text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-brand font-mono"
                  >
                    <option value="ALL" className="bg-surface text-ink">All Statuses ({report.grammar_check.questions.length})</option>
                    <option value="FLAG" className="bg-surface text-ink">Flagged ({report.grammar_check.questions_with_issues_count})</option>
                    <option value="REVIEW_REQUIRED" className="bg-surface text-ink">Review Required</option>
                    <option value="PASS" className="bg-surface text-ink">Pass ({report.grammar_check.clean_questions_count})</option>
                  </select>

                  {/* Section Filter */}
                  <select
                    value={grammarSectionFilter}
                    onChange={(e) => setGrammarSectionFilter(e.target.value)}
                    className="bg-surface-muted border border-line text-ink text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-brand font-mono"
                  >
                    <option value="ALL" className="bg-surface text-ink">All Sections</option>
                    <option value="Part A" className="bg-surface text-ink">Part A</option>
                    <option value="Part B" className="bg-surface text-ink">Part B</option>
                    <option value="Part C" className="bg-surface text-ink">Part C</option>
                  </select>

                  {/* Category Filter */}
                  <select
                    value={grammarCategoryFilter}
                    onChange={(e) => setGrammarCategoryFilter(e.target.value)}
                    className="bg-surface-muted border border-line text-ink text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-brand font-mono"
                  >
                    <option value="ALL" className="bg-surface text-ink">All Categories</option>
                    <option value="SPELLING" className="bg-surface text-ink">Spelling</option>
                    <option value="GRAMMAR" className="bg-surface text-ink">Grammar</option>
                    <option value="SENTENCE_STRUCTURE" className="bg-surface text-ink">Sentence Structure</option>
                    <option value="PUNCTUATION" className="bg-surface text-ink">Punctuation</option>
                    <option value="CLARITY" className="bg-surface text-ink">Clarity</option>
                    <option value="AMBIGUITY" className="bg-surface text-ink">Ambiguity</option>
                    <option value="INCOMPLETE_SENTENCE" className="bg-surface text-ink">Incomplete Sentence</option>
                  </select>
                </div>
              </div>

              {/* Questions List */}
              <div className="space-y-3">
                {filteredGrammarQuestions.length === 0 ? (
                  <div className="p-8 text-center rounded-xl border border-line bg-surface-subtle text-ink-faint font-mono text-xs">
                    No questions match the selected grammar and linguistic filters.
                  </div>
                ) : (
                  filteredGrammarQuestions.map((q: any, qIdx: number) => {
                    const hasIssues = q.issues && q.issues.length > 0;
                    return (
                      <div
                        key={`grammar-q-${qIdx}`}
                        className={`rounded-xl border p-4 space-y-3 transition-colors ${
                          q.status === "FLAG"
                            ? "border-accent-line bg-accent-surface"
                            : q.status === "REVIEW_REQUIRED"
                            ? "border-line bg-surface-subtle"
                            : "border border-line bg-surface shadow-sm"
                        }`}
                      >
                        {/* Header bar of Question Card */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-line pb-2.5">
                          <div className="flex items-center space-x-2.5">
                            <span className="font-mono font-bold text-ink text-xs px-2.5 py-1 rounded bg-surface-muted border border-line">
                              {q.question_id || `Q${q.question_number}`}
                            </span>
                            <span className="text-[11px] font-mono text-ink-faint">
                              {q.section || "General"}
                            </span>
                            {q.marks !== undefined && (
                              <span className="text-[11px] font-mono text-ink-faint">
                                • {q.marks} Mark{q.marks > 1 ? "s" : ""}
                              </span>
                            )}
                            {q.requires_human_review && (
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-accent-surface text-accent-ink border border-accent-line">
                                Faculty Review Recommended
                              </span>
                            )}
                          </div>

                          <div className="flex items-center space-x-2">
                            <span
                              className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded-full uppercase shadow-sm ${
                                q.status === "PASS"
                                  ? "bg-brand text-btn-brand"
                                  : q.status === "FLAG"
                                  ? "bg-accent text-btn-accent font-extrabold"
                                  : "bg-track text-brand-ink border border-brand-line"
                              }`}
                            >
                              {q.status === "PASS"
                                ? "PASS — CLEAN"
                                : q.status === "FLAG"
                                ? "FLAGGED"
                                : "REVIEW REQUIRED"}
                            </span>
                          </div>
                        </div>

                        {/* Original Question Statement */}
                        <div className="space-y-1">
                          <span className="text-[10px] font-mono uppercase tracking-wider text-ink-faint font-semibold block">
                            Original Question Statement:
                          </span>
                          <div className="p-3 rounded-lg bg-surface-subtle border border-line text-ink-muted text-xs font-serif leading-relaxed">
                            {q.original_text}
                          </div>
                        </div>

                        {/* Itemized Issues */}
                        {hasIssues ? (
                          <div className="space-y-2 pt-1">
                            <span className="text-[10px] font-mono uppercase tracking-wider text-ink-faint font-semibold block">
                              Identified Linguistic Issues ({q.issues.length}):
                            </span>
                            <div className="space-y-2">
                              {q.issues.map((issue: any, issIdx: number) => (
                                <div
                                  key={`issue-${issIdx}`}
                                  className="p-3 rounded-lg border border-line bg-surface text-xs space-y-1.5 shadow-sm"
                                >
                                  <div className="flex flex-wrap items-center justify-between gap-2">
                                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-muted text-ink border border-line font-semibold">
                                      {issue.category}
                                    </span>
                                    <div className="text-[11px] font-mono text-ink-faint">
                                      Problematic:{" "}
                                      <span className="text-danger-ink line-through decoration-danger-ink font-semibold">
                                        &ldquo;{issue.problematic_text}&rdquo;
                                      </span>
                                    </div>
                                  </div>
                                  <div className="text-ink-muted text-[11px] leading-relaxed">
                                    <span className="text-ink-faint font-mono">Explanation: </span>
                                    {issue.explanation}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-2 text-xs text-brand-ink font-mono py-1">
                            <CheckCircle2 className="w-3.5 h-3.5 text-brand-ink" />
                            <span>No grammatical, spelling, or structural issues detected.</span>
                          </div>
                        )}

                        {/* Suggested Full Revised Statement */}
                        {q.suggested_full_text && hasIssues && (
                          <div className="space-y-1.5 pt-1 border-t border-line">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono uppercase tracking-wider text-ink-muted font-semibold">
                                Suggested Revision (For Faculty Approval):
                              </span>
                            </div>
                            <div className="p-3 rounded-lg bg-brand-surface border border-brand-line text-ink text-xs font-serif leading-relaxed">
                              {q.suggested_full_text}
                            </div>
                          </div>
                        )}

                        {/* Technical Preservation Notes */}
                        {q.notes && q.notes.length > 0 && (
                          <div className="text-[11px] font-mono text-ink-faint pt-1">
                            Technical preservation: {q.notes.join("; ")}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        )}

        {/* 7) SI Units, Mathematical Symbols & Index Figures Section (Criterion 7 - Strict Zero Score) */}
        {report.notation_check && (
          <div className="rounded-2xl border border-line bg-surface p-6 shadow-sm space-y-6 text-ink">
            {/* Section Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-line">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-track border border-brand-line text-brand-ink flex items-center justify-center font-bold shadow-sm shrink-0">
                  <Calculator className="w-5 h-5 text-brand-ink" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-base sm:text-lg font-bold text-ink tracking-tight">
                      7. SI Units, Mathematical Symbols & Index Figures
                    </h2>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-surface-muted border border-line text-ink-muted font-semibold">
                      Criterion 7
                    </span>
                  </div>
                  <p className="text-xs text-ink-faint">
                    Verifies SI unit adoption, symbol correctness, capitalization, number-unit spacing, mathematical clarity, and delineation of subscripts/superscripts
                  </p>
                </div>
              </div>

              {/* Overall Status Badge */}
              <div className="shrink-0 flex items-center">
                <span
                  className={`text-xs font-mono font-black px-4 py-1.5 rounded-full flex items-center space-x-1.5 shadow-sm uppercase transition-all duration-300 ${
                    report.notation_check.overall_status === "PASS"
                      ? "bg-brand text-btn-brand"
                      : report.notation_check.overall_status === "FLAG"
                      ? "bg-accent text-btn-accent"
                      : "bg-track text-brand-ink border border-brand-line"
                  }`}
                >
                  {report.notation_check.overall_status === "PASS" ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-btn-brand" />
                      <span>COMPLIANT — NOTATION APPROVED</span>
                    </>
                  ) : report.notation_check.overall_status === "FLAG" ? (
                    <>
                      <AlertTriangle className="w-3.5 h-3.5 text-btn-accent" />
                      <span>NOTATION ISSUES FLAGGED</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-3.5 h-3.5 text-brand-ink" />
                      <span>HUMAN REVIEW REQUIRED</span>
                    </>
                  )}
                </span>
              </div>
            </div>

            {/* 4 Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* 1. Overall Status */}
              <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1.5">
                <span className="text-[11px] font-mono text-ink-faint uppercase tracking-wider block">
                  1. Overall Notation Status
                </span>
                <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                  {report.notation_check.overall_status}
                </p>
                <div className="text-[11px] text-ink-faint">
                  {report.notation_check.overall_status === "PASS"
                    ? "Conforms to institutional SI & math standards"
                    : report.notation_check.overall_status === "FLAG"
                    ? "Definite unit or symbol issues detected"
                    : "Visual layout or ambiguous notation requires review"}
                </div>
              </div>

              {/* 2. Questions Examined */}
              <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1.5">
                <span className="text-[11px] font-mono text-ink-faint uppercase tracking-wider block">
                  2. Questions Examined
                </span>
                <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                  {report.notation_check.total_questions_examined} Questions
                </p>
                <div className="text-[11px] text-ink-faint">
                  {report.notation_check.clean_questions_count} compliant questions (clean)
                </div>
              </div>

              {/* 3. Questions Flagged */}
              <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1.5">
                <span className="text-[11px] font-mono text-ink-faint uppercase tracking-wider block">
                  3. Questions Flagged
                </span>
                <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                  {report.notation_check.questions_with_issues_count} Flagged
                </p>
                <div className="text-[11px] text-ink-faint">
                  {report.notation_check.questions_with_issues_count === 0 ? (
                    <span className="text-brand-ink font-bold">✓ No notation errors detected</span>
                  ) : (
                    <span className="text-accent-ink font-mono font-bold">
                      ⚠️ {report.notation_check.questions_with_issues_count} question(s) need review
                    </span>
                  )}
                </div>
              </div>

              {/* 4. Total Issues Found */}
              <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1.5">
                <span className="text-[11px] font-mono text-ink-faint uppercase tracking-wider block">
                  4. Total Issues Found
                </span>
                <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                  {(Object.values(report.notation_check.issues_by_category || {}) as number[]).reduce(
                    (a: number, b: number) => a + Number(b || 0),
                    0
                  )}{" "}
                  Issues
                </p>
                <div className="text-[11px] text-ink-faint truncate">
                  Across SI units, symbols, indices & clarity
                </div>
              </div>
            </div>

            {/* Error Breakdown By Category Chips */}
            <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold uppercase tracking-wider text-ink-muted">
                  Notation Categories & Institutional Rules
                </span>
                <span className="text-[11px] font-mono text-ink-faint">
                  Click category to filter
                </span>
              </div>
              <div className="flex flex-wrap gap-2 pt-1">
                {[
                  { key: "SI_UNIT", label: "SI Units & Spacing" },
                  { key: "MATHEMATICAL_SYMBOL", label: "Mathematical Symbols" },
                  { key: "INDEX_NOTATION", label: "Subscripts & Indices" },
                  { key: "CLARITY_AND_AMBIGUITY", label: "Clarity & Ambiguity" },
                ].map(({ key, label }) => {
                  const count = (report.notation_check.issues_by_category || {})[key] || 0;
                  const isSelected = notationCategoryFilter === key;
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() =>
                        setNotationCategoryFilter(isSelected ? "ALL" : key)
                      }
                      className={`text-[11px] font-mono px-3 py-1.5 rounded-lg border transition-all flex items-center space-x-1.5 cursor-pointer focus-visible:ring-2 focus-visible:ring-brand ${
                        isSelected
                          ? "bg-brand text-btn-brand border-brand font-bold shadow-sm"
                          : count > 0
                          ? "bg-surface border-line text-ink hover:border-brand"
                          : "bg-surface-muted border-transparent text-ink-faint hover:text-ink-muted"
                      }`}
                    >
                      <span>{label}:</span>
                      <span
                        className={`font-bold ${
                          isSelected
                            ? "text-btn-brand"
                            : count > 0
                            ? "text-brand-ink"
                            : "text-ink-faint"
                        }`}
                      >
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>
              <div className="text-[11px] text-ink-faint pt-1">
                Rajalakshmi Institute of Technology guideline: Dimensionless quantities (Mach, Reynolds, strain) and mathematical constants are preserved.
              </div>
            </div>

            {/* Question-Level Notation Audit */}
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-xs sm:text-sm font-bold text-ink tracking-tight">
                    Question-by-Question Unit & Notation Audit
                  </h3>
                  <p className="text-xs text-ink-muted">
                    Detailed verification of SI unit symbols, capitalization, spacing, operators, indices, and document layout formatting
                  </p>
                </div>

                {/* Filters */}
                <div className="flex flex-wrap items-center gap-2">
                  {/* Status Filter */}
                  <select
                    value={notationStatusFilter}
                    onChange={(e) => setNotationStatusFilter(e.target.value)}
                    className="bg-surface-muted border border-line text-ink text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-brand font-mono"
                  >
                    <option value="ALL">All Statuses ({report.notation_check.questions.length})</option>
                    <option value="FLAG">Flagged ({report.notation_check.questions_with_issues_count})</option>
                    <option value="REVIEW_REQUIRED">Review Required</option>
                    <option value="PASS">Pass ({report.notation_check.clean_questions_count})</option>
                  </select>

                  {/* Section Filter */}
                  <select
                    value={notationSectionFilter}
                    onChange={(e) => setNotationSectionFilter(e.target.value)}
                    className="bg-surface-muted border border-line text-ink text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-brand font-mono"
                  >
                    <option value="ALL">All Sections</option>
                    <option value="Part A">Part A</option>
                    <option value="Part B">Part B</option>
                    <option value="Part C">Part C</option>
                  </select>

                  {/* Category Filter */}
                  <select
                    value={notationCategoryFilter}
                    onChange={(e) => setNotationCategoryFilter(e.target.value)}
                    className="bg-surface-muted border border-line text-ink text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-brand font-mono"
                  >
                    <option value="ALL">All Categories</option>
                    <option value="SI_UNIT">SI Units & Spacing</option>
                    <option value="MATHEMATICAL_SYMBOL">Mathematical Symbols</option>
                    <option value="INDEX_NOTATION">Index Notation</option>
                    <option value="CLARITY_AND_AMBIGUITY">Clarity & Ambiguity</option>
                  </select>
                </div>
              </div>

              {/* Questions List */}
              <div className="space-y-3">
                {filteredNotationQuestions.length === 0 ? (
                  <div className="p-8 text-center rounded-xl border border-line bg-surface-subtle text-ink-faint font-mono text-xs">
                    No questions match the selected notation filters.
                  </div>
                ) : (
                  filteredNotationQuestions.map((q: any, qIdx: number) => {
                    const hasIssues = q.issues && q.issues.length > 0;
                    return (
                      <div
                        key={`notation-q-${qIdx}`}
                        className={`rounded-xl border p-4 space-y-3 transition-colors ${
                          q.status === "FLAG"
                            ? "border-accent-line bg-accent-surface"
                            : q.status === "REVIEW_REQUIRED"
                            ? "border-line bg-surface-subtle"
                            : "border-line bg-surface shadow-sm"
                        }`}
                      >
                        {/* Header bar of Question Card */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-line pb-2.5">
                          <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
                            <span className="font-mono font-bold text-ink text-xs px-2.5 py-1 rounded bg-surface-muted border border-line">
                              {q.question_id || `Q${q.question_number}`}
                            </span>
                            <span className="text-[11px] font-mono text-ink-muted">
                              {q.section || "General"}
                            </span>
                            {q.marks !== undefined && (
                              <span className="text-[11px] font-mono text-ink-muted">
                                • {q.marks} Mark{q.marks > 1 ? "s" : ""}
                              </span>
                            )}
                            {q.formatting_verified ? (
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-brand-surface text-brand-ink border border-brand-line font-semibold">
                                ✓ Layout Verified
                              </span>
                            ) : (
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-surface-muted text-ink-muted border border-line">
                                Unverified Visual Layout
                              </span>
                            )}
                            {q.requires_human_review && (
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-accent-surface text-accent-ink border border-accent-line">
                                Faculty Review Recommended
                              </span>
                            )}
                          </div>

                          <div className="flex items-center space-x-2">
                            <span
                              className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded-full uppercase shadow-sm ${
                                q.status === "PASS"
                                  ? "bg-brand text-btn-brand"
                                  : q.status === "FLAG"
                                  ? "bg-accent text-btn-accent font-extrabold"
                                  : "bg-brand-surface text-brand-ink border border-brand-line"
                              }`}
                            >
                              {q.status === "PASS"
                                ? "PASS — COMPLIANT"
                                : q.status === "FLAG"
                                ? "FLAGGED"
                                : "REVIEW REQUIRED"}
                            </span>
                          </div>
                        </div>

                        {/* Original Question Statement */}
                        <div className="space-y-1">
                          <span className="text-[10px] font-mono uppercase tracking-wider text-ink-muted font-semibold block">
                            Original Question Statement:
                          </span>
                          <div className="p-3 rounded-lg bg-surface-subtle border border-line text-ink text-xs font-serif leading-relaxed">
                            {q.original_text}
                          </div>
                        </div>

                        {/* Itemized Issues */}
                        {hasIssues ? (
                          <div className="space-y-2 pt-1">
                            <span className="text-[10px] font-mono uppercase tracking-wider text-ink-muted font-semibold block">
                              Identified Notation & Unit Issues ({q.issues.length}):
                            </span>
                            <div className="space-y-2">
                              {q.issues.map((issue: any, issIdx: number) => (
                                <div
                                  key={`iss-${issIdx}`}
                                  className="p-3 rounded-lg border border-line bg-surface text-xs space-y-1.5 shadow-sm"
                                >
                                  <div className="flex flex-wrap items-center justify-between gap-2">
                                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-muted text-ink border border-line font-semibold">
                                      {issue.category}
                                    </span>
                                    <div className="text-[11px] font-mono text-ink-muted">
                                      Problematic:{" "}
                                      <span className="text-danger-ink line-through decoration-danger-ink font-semibold">
                                        &ldquo;{issue.problematic_text}&rdquo;
                                      </span>
                                    </div>
                                  </div>
                                  <div className="text-ink-muted text-[11px] leading-relaxed">
                                    <span className="text-ink-faint font-mono">Explanation: </span>
                                    {issue.explanation}
                                  </div>
                                  {issue.suggested_correction && (
                                    <div className="text-ink text-[11px] pt-0.5">
                                      <span className="text-ink-faint font-mono">Suggested Fix: </span>
                                      <span className="font-mono bg-brand-surface text-brand-ink px-1.5 py-0.5 rounded border border-brand-line font-bold">
                                        {issue.suggested_correction}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-2 text-xs text-brand-ink font-mono py-1">
                            <CheckCircle2 className="w-3.5 h-3.5 text-brand-ink" />
                            <span>SI units, mathematical symbols, and index figures correctly delineated.</span>
                          </div>
                        )}

                        {/* Suggested Full Revised Statement */}
                        {q.suggested_full_text && hasIssues && (
                          <div className="space-y-1.5 pt-1 border-t border-line">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono uppercase tracking-wider text-ink font-semibold">
                                Suggested Revision (For Faculty Approval):
                              </span>
                              <span className="text-[10px] font-mono text-ink-faint">
                                Non-destructive recommendation
                              </span>
                            </div>
                            <div className="p-3 rounded-lg bg-brand-surface border border-brand-line text-ink text-xs font-serif leading-relaxed">
                              {q.suggested_full_text}
                            </div>
                          </div>
                        )}

                        {/* Technical Preservation Notes */}
                        {q.notes && q.notes.length > 0 && (
                          <div className="text-[11px] font-mono text-ink-faint pt-1">
                            {q.notes.join("; ")}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        )}

        {/* 6) Repetition Risk Analysis Section (Criterion 9 - Strict Zero Score) */}
              {report.repetition_risk && (
                <div className="rounded-2xl border border-line bg-surface p-6 shadow-sm space-y-6 text-ink">
                  {/* Section Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-line">
                    <div className="flex items-center space-x-2.5">
                      <span className="px-2.5 py-0.5 rounded-lg bg-track border border-brand-line text-brand-ink font-mono font-bold text-xs">
                        7
                      </span>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h2 className="text-base sm:text-lg font-bold text-ink tracking-tight">
                            Repetition Risk Analysis
                          </h2>
                        </div>
                      </div>
                    </div>

                    {/* Overall Status Badge */}
                    <div className="shrink-0 flex items-center">
                      <span
                        className={`text-xs font-mono font-black px-4 py-1.5 rounded-full flex items-center space-x-1.5 shadow-sm uppercase transition-all duration-300 ${
                          report.repetition_risk.overall_status === "PASS"
                            ? "bg-brand text-btn-brand"
                            : report.repetition_risk.overall_status === "FLAG"
                            ? "bg-accent text-btn-accent font-extrabold"
                            : "bg-brand-surface text-brand-ink border border-brand-line"
                        }`}
                      >
                        {report.repetition_risk.overall_status === "PASS" ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>COMPLIANT — ZERO REPETITIONS</span>
                          </>
                        ) : report.repetition_risk.overall_status === "FLAG" ? (
                          <>
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>REPETITION RISK FLAGGED</span>
                          </>
                        ) : <span>HUMAN REVIEW REQUIRED</span>}
                      </span>
                    </div>
                  </div>

                  {/* 3 Metric Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1">
                      <span className="text-[11px] font-mono text-ink-muted uppercase tracking-wider block">Overall Status</span>
                      <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                        {report.repetition_risk.overall_status}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1">
                      <span className="text-[11px] font-mono text-ink-muted uppercase tracking-wider block">Questions Evaluated</span>
                      <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                        {report.repetition_risk.total_questions_evaluated}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl border border-line bg-surface-subtle space-y-1">
                      <span className="text-[11px] font-mono text-ink-muted uppercase tracking-wider block">Duplicate / Repetition Flags</span>
                      <p className="text-lg sm:text-xl font-bold font-mono text-ink tracking-tight">
                        {report.repetition_risk.internal_duplicates_count}
                      </p>
                    </div>
                  </div>

                  {/* Filter Controls */}
                  <div className="p-4 rounded-xl border border-line bg-surface-muted space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                      {/* Filter by Status */}
                      <div className="flex items-center space-x-2">
                        <Filter className="w-3.5 h-3.5 text-ink-muted shrink-0" />
                        <span className="text-ink-muted text-[11px] font-semibold uppercase">Status:</span>
                        <div className="flex items-center space-x-1">
                          {["ALL", "FLAG", "REVIEW_REQUIRED", "PASS"].map((st) => (
                            <button
                              type="button"
                              key={st}
                              onClick={() => setC9FilterStatus(st)}
                              className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-bold transition-all ${
                                c9FilterStatus === st
                                  ? "bg-brand text-btn-brand shadow-sm"
                                  : "bg-surface text-ink-muted border border-line hover:bg-surface-subtle hover:text-ink"
                              }`}
                            >
                              {st === "ALL" ? "All" : st}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Filter by Scope */}
                      <div className="flex items-center space-x-2">
                        <span className="text-ink-muted text-[11px] font-semibold uppercase">Scope:</span>
                        <div className="flex items-center space-x-1">
                          {[
                            { id: "ALL", label: "All" },
                            { id: "INTERNAL", label: "Repeated" },
                            { id: "UNIQUE", label: "Unique" },
                          ].map((sc) => (
                            <button
                              type="button"
                              key={sc.id}
                              onClick={() => setC9FilterScope(sc.id)}
                              className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-bold transition-all ${
                                c9FilterScope === sc.id
                                  ? "bg-brand text-btn-brand shadow-sm"
                                  : "bg-surface text-ink-muted border border-line hover:bg-surface-subtle hover:text-ink"
                              }`}
                            >
                              {sc.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Repetition Matrix Table */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between px-1">
                      <span className="text-xs font-semibold text-ink font-mono">
                        Question Repetition Scrutiny Matrix ({filteredC9Evaluations.length} items)
                      </span>
                    </div>

                    <div className="rounded-xl border border-line bg-surface overflow-x-auto shadow-sm">
                      <table className="w-full min-w-[760px] table-fixed text-xs text-left border-collapse">
                        <colgroup>
                          <col className="w-[92px]" />
                          <col className="w-[92px]" />
                          <col className="w-[76px]" />
                          <col className="w-[142px]" />
                          <col className="w-[148px]" />
                          <col />
                        </colgroup>
                        <thead>
                          <tr className="border-b border-line bg-surface-muted font-mono text-ink-muted uppercase text-[10px]">
                            <th className="py-2.5 px-3">Question</th>
                            <th className="py-2.5 px-2.5 text-center">Section</th>
                            <th className="py-2.5 px-2.5 text-center">Marks</th>
                            <th className="py-2.5 px-3 text-center">Classification</th>
                            <th className="py-2.5 px-2.5 text-center">Status</th>
                            <th className="py-2.5 px-3">Analysis & Matched Content</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-line-subtle">
                          {filteredC9Evaluations.length === 0 ? (
                            <tr>
                              <td colSpan={6} className="py-8 text-center text-ink-faint font-mono text-xs">
                                No questions matching the selected repetition filter.
                              </td>
                            </tr>
                          ) : (
                            filteredC9Evaluations.map((item: any) => {
                              const isExpanded = c9ExpandedMatchId === item.question_id;
                              const hasMatches = Boolean(item.matches && item.matches.length > 0);

                              return (
                                <React.Fragment key={item.question_id}>
                                  <tr className="hover:bg-surface-subtle transition-colors">
                                    <td className="py-3 px-3 font-mono font-bold text-ink">
                                      {item.question_id}
                                    </td>
                                    <td className="py-3 px-2.5 text-center font-mono text-ink-muted whitespace-nowrap">
                                      {item.section || "—"}
                                    </td>
                                    <td className="py-3 px-2.5 text-center font-mono">
                                      {item.assigned_marks !== null && item.assigned_marks !== undefined ? (
                                        <span className="px-2 py-0.5 rounded bg-surface-muted border border-line text-ink font-bold">
                                          {item.assigned_marks}M
                                        </span>
                                      ) : (
                                        <span className="text-ink-faint">—</span>
                                      )}
                                    </td>

                                    <td className="py-3 px-3 text-center font-mono">
                                      <span
                                        className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                                          item.similarity_category === "DUPLICATE"
                                            ? "bg-danger-surface text-danger-ink border border-danger-line"
                                            : item.similarity_category === "SUBSTANTIALLY_SIMILAR"
                                            ? "bg-accent-surface text-accent-ink border border-accent-line"
                                            : item.similarity_category === "MODERATE_SIMILARITY"
                                            ? "bg-accent-surface text-accent-ink border border-dashed border-accent-line"
                                            : "text-ink-muted bg-surface-muted border border-line"
                                        }`}
                                      >
                                        {item.similarity_category === "SUBSTANTIALLY_SIMILAR"
                                          ? "Substantial"
                                          : item.similarity_category === "MODERATE_SIMILARITY"
                                          ? "Moderate"
                                          : item.similarity_category}
                                      </span>
                                    </td>
                                    <td className="py-3 px-2.5 text-center font-mono">
                                      <span
                                        className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                                          item.status === "PASS"
                                            ? "bg-brand-surface text-brand-ink border border-brand-line"
                                            : item.status === "FLAG"
                                            ? "bg-accent-surface text-accent-ink border border-accent-line"
                                            : "bg-surface-muted text-ink-muted border border-line"
                                        }`}
                                      >
                                        {item.status}
                                      </span>
                                    </td>
                                    <td className="py-3 px-3 text-left">
                                      <p className="text-[11px] text-ink leading-relaxed">
                                        {item.repetition_type === "NONE" ? "Unique question Statement" : item.reason}
                                      </p>
                                      {hasMatches && (
                                        <button
                                          type="button"
                                          onClick={() => setC9ExpandedMatchId(isExpanded ? null : item.question_id)}
                                          className="mt-1 text-[10px] font-mono text-brand-ink hover:underline flex items-center space-x-1 font-semibold"
                                        >
                                          <GitCompare className="w-3 h-3 inline" />
                                          <span>{isExpanded ? "Hide Comparison" : `View Comparison (${item.matches.length})`}</span>
                                        </button>
                                      )}
                                    </td>
                                  </tr>

                                  {/* Expandable Comparison Drawer */}
                                  {isExpanded && hasMatches && (
                                    <tr className="bg-surface-subtle border-b border-line">
                                      <td colSpan={6} className="p-4 space-y-3">
                                        <div className="space-y-2">
                                          <span className="text-[10px] font-mono font-bold text-ink-muted uppercase tracking-wider block">
                                            Side-by-Side Question Comparison
                                          </span>
                                          {item.matches.map((m: any, mIdx: number) => (
                                            <div
                                              key={mIdx}
                                              className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3 rounded-lg border border-line bg-surface text-xs shadow-sm"
                                            >
                                              <div className="space-y-1 border-r border-line pr-2">
                                                <div className="flex items-center space-x-2">
                                                  <span className="font-mono font-bold text-brand-ink">Current Paper ({m.source_question_id})</span>
                                                </div>
                                                <p className="text-ink font-mono text-[11px] leading-relaxed">
                                                  {m.source_text_snippet}
                                                </p>
                                              </div>

                                              <div className="space-y-1 pl-1">
                                                <div className="flex items-center space-x-2">
                                                  <span className="font-mono font-bold text-accent-ink">
                                                    {m.target_paper_label} ({m.target_question_id})
                                                  </span>
                                                  <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-surface-muted text-ink-muted border border-line">
                                                    {m.repetition_type}
                                                  </span>
                                                </div>
                                                <p className="text-ink font-mono text-[11px] leading-relaxed">
                                                  {m.target_text_snippet}
                                                </p>
                                              </div>
                                            </div>
                                          ))}
                                        </div>
                                      </td>
                                    </tr>
                                  )}
                                </React.Fragment>
                              );
                            })
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Extracted Text Modal Dialog with Tabs for Question Paper & Syllabus */}
        {showExtractedModal && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 animate-fadeIn">
            <div className="w-full max-w-3xl bg-surface border border-line rounded-2xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
              {/* Modal Header */}
              <div className="p-4 sm:p-5 border-b border-line flex items-center justify-between bg-surface">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-lg bg-track text-brand-ink flex items-center justify-center">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-sm sm:text-base font-bold text-ink">
                      {activeExtractedTab === "syllabus"
                        ? "Extracted Syllabus Text"
                        : "Extracted Question Paper Text"}
                    </h2>
                    <p className="text-xs text-ink-muted font-mono">
                      {textCharCount.toLocaleString()} characters • {textLineCount} lines
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => handleCopyText(displayedText)}
                    className="px-3 py-1.5 rounded-lg bg-brand text-btn-brand hover:bg-brand-hover text-xs font-bold flex items-center space-x-1.5 transition-all shadow-sm focus-visible:ring-2 focus-visible:ring-brand"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy Text</span>
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={() => setShowExtractedModal(false)}
                    className="p-1.5 rounded-lg text-ink-muted hover:text-ink hover:bg-surface-subtle transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Document Switcher Tabs if syllabus exists */}
              {report?.syllabus_extracted_text && (
                <div className="px-5 pt-2 pb-0 bg-surface-subtle flex items-center space-x-4 border-b border-line">
                  <button
                    type="button"
                    onClick={() => setActiveExtractedTab("qp")}
                    className={`py-2 px-1 text-xs font-bold border-b-2 transition-all ${
                      activeExtractedTab === "qp"
                        ? "border-brand text-brand-ink"
                        : "border-transparent text-ink-faint hover:text-ink"
                    }`}
                  >
                    Question Paper
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveExtractedTab("syllabus")}
                    className={`py-2 px-1 text-xs font-bold border-b-2 transition-all ${
                      activeExtractedTab === "syllabus"
                        ? "border-brand text-brand-ink"
                        : "border-transparent text-ink-faint hover:text-ink"
                    }`}
                  >
                    Syllabus ({report.syllabus_filename || "Document"})
                  </button>
                </div>
              )}

              {/* Modal Content - Raw Extracted Text */}
              <div className="p-4 sm:p-6 overflow-y-auto flex-1 bg-surface-subtle">
                {displayedText ? (
                  <pre className="font-mono text-xs text-ink whitespace-pre-wrap leading-relaxed select-text font-normal">
                    {displayedText}
                  </pre>
                ) : (
                  <div className="text-center py-12 text-ink-faint text-xs font-mono">
                    No text extracted for this selection.
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="p-3.5 border-t border-line bg-surface-muted flex items-center justify-between text-xs text-ink-muted">
                <span>Unified extraction via PyMuPDF / python-docx</span>
                <button
                  type="button"
                  onClick={() => setShowExtractedModal(false)}
                  className="px-4 py-1.5 rounded-lg bg-surface border border-line hover:bg-surface-subtle text-ink text-xs font-medium transition-colors shadow-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
