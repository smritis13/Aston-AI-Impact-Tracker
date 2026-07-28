// Impact Case Study default sections and constants

import { ImpactSection } from "../pages/ImpactCaseStudyPage";

export const DEFAULT_IMPACT_SECTIONS: ImpactSection[] = [
  {
    id: "1",
    title: "Underpinning Research",
    description:
      "Key research insights or findings that underpinned the impact, details of research undertaken, when, and by whom",
    maxWords: 500,
  },
  {
    id: "2",
    title: "References to the Research",
    description: "Key outputs from the research and evidence about the quality of the research",
    maxWords: 200,
  },
  {
    id: "3",
    title: "Details of the Impact",
    description:
      "Narrative with supporting evidence explaining how research underpinned impact and the nature and extent of the impact",
    maxWords: 750,
  },
  {
    id: "4",
    title: "Sources to Corroborate the Impact",
    description: "External sources that could provide corroboration of specific claims made in the case study",
    maxWords: 300,
  },
];

export const IMPACT_CASE_STUDY_TEMPLATES = {
  academic: {
    name: "Academic Impact",
    sections: DEFAULT_IMPACT_SECTIONS,
  },
  industry: {
    name: "Industry Impact",
    sections: DEFAULT_IMPACT_SECTIONS,
  },
  policy: {
    name: "Policy Impact",
    sections: DEFAULT_IMPACT_SECTIONS,
  },
  social: {
    name: "Social Impact",
    sections: DEFAULT_IMPACT_SECTIONS,
  },
};

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
export const ALLOWED_FILE_TYPES = [
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/pdf",
];

export const WORD_COUNT_WARNINGS = {
  LOW: 0.5, // 50% of max
  MEDIUM: 0.75, // 75% of max
  HIGH: 1.0, // 100% of max
};

export const IMPACT_CASE_STUDY_HELP_TEXT = {
  prompt: "Enter your main research topic or impact question that the case study should address.",
  theme: "Select an existing theme to categorize this impact case study, or leave empty to create a new theme.",
  fileUpload: "Upload relevant PDF or DOCX documents that provide context or evidence for your impact case study.",
  includeSummary: "A summary section will be auto-generated at the end if this is checked.",
  sections: "Configure the sections of your impact case study. Each section can have its own title and word limit.",
};
