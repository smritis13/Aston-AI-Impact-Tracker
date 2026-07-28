# Impact Case Study Report Generator

## Overview

The Impact Case Study Report Generator is a powerful tool for creating structured research impact case studies. It provides a comprehensive form interface for researchers to document and showcase the impact of their research work through a structured, peer-reviewed format.

## Features

### 1. **Dynamic Section Management**
- Pre-configured default sections (customizable):
  - **Underpinning Research** (500 words max): Key research insights and findings
  - **References to the Research** (200 words max): Key outputs and quality evidence
  - **Details of the Impact** (750 words max): Narrative with supporting evidence
  - **Sources to Corroborate the Impact** (300 words max): External corroboration sources
- Add custom sections with flexible word limits
- Remove sections as needed (minimum 1 section required)
- Auto-adjustable section numbering

### 2. **Intelligent Input Handling**
- **Prompt Input**: Main research topic or impact question
- **File Upload**: Upload DOCX files as context (optional, multiple files supported)
- **Theme Selection**: Categorize under existing themes or create new ones
- **Summary Generation**: Optional auto-generated summary section

### 3. **Advanced Options**
- Expandable advanced settings panel
- Configurable number of outcomes
- Search complexity levels

### 4. **Real-time Preview**
- Live preview panel showing generated content
- Progress tracking during report generation
- Loading states with spinners

## User Interface

### Main Layout
- **Left Column (70%)**: Form inputs and configuration
- **Right Column (30%)**: Real-time preview (sticky on desktop)

### Form Sections
1. **Prompt Section**: Text area for research topic
2. **File Upload**: DOCX file upload button with filename display
3. **Theme Selector**: Dropdown for theme selection
4. **Sections Configuration**: 
   - Dynamic section cards
   - Title, description, and word count fields
   - Add/Remove section buttons
5. **Summary Checkbox**: Include auto-generated summary
6. **Advanced Options**: Expandable for additional settings
7. **Submit Button**: Generate Impact Case Study Report

## Technical Implementation

### Frontend Routes
- **Route**: `/impact-case-study`
- **Component**: `ImpactCaseStudyPage.tsx`
- **Navigation**: Sidebar menu → "Impact Case Studies" → "Research"

### API Integration
- **Endpoint**: `POST /content/reports/generate`
- **Payload Structure**:
  ```json
  {
    "query": "prompt text",
    "report_type": "impact_case_study",
    "theme_id": null,
    "sections_config": [...],
    "include_summary": true,
    "files": [...]
  }
  ```

### State Management
- React hooks for form state management
- `useToast` for notifications
- `useTheme` for theme data
- `ContentHttpService` for API calls

### Styling
- Bootstrap framework for responsive design
- Custom CSS files:
  - `ImpactCaseStudyPage.css`: Layout and preview styling
  - `ImpactCaseStudyForm.css`: Form styling and responsiveness
- Mobile-first responsive design

## Component Structure

```
ImpactCaseStudyPage.tsx (Main Page)
├── MainLayout (Layout wrapper)
├── BreadcrumbWidget (Navigation)
├── ImpactCaseStudyForm (Form Component)
│   ├── Prompt Input
│   ├── File Upload
│   ├── SelectTheme
│   ├── Sections Configuration
│   │   └── Section Cards (Dynamic)
│   ├── Advanced Options
│   └── Submit Button
└── Preview Panel
    └── Generated Report Display
```

## File Organization

```
frontend/src/features/feature_data/
├── pages/
│   ├── ImpactCaseStudyPage.tsx
│   └── ImpactCaseStudyPage.css
├── components/
│   ├── ImpactCaseStudyForm.tsx
│   └── ImpactCaseStudyForm.css
└── constants/
    └── impactCaseStudyConstants.ts
```

## Constants & Configuration

Located in `impactCaseStudyConstants.ts`:

### Default Sections
```typescript
DEFAULT_IMPACT_SECTIONS: ImpactSection[]
```

### Templates
Multiple impact templates available:
- Academic Impact
- Industry Impact
- Policy Impact
- Social Impact

### Configuration
- Max file size: 10MB
- Allowed file types: DOCX
- Word count warning thresholds: 50%, 75%, 100%

## Usage Guide

### For End Users

1. **Navigate to Impact Case Study Generator**
   - Click "Impact Case Studies" in the sidebar
   - Select "Research"

2. **Fill in the Prompt**
   - Enter your research topic or impact question
   - This is required to proceed

3. **Optional: Upload Supporting Documents**
   - Click "Upload DOCX files as context"
   - Select one or more DOCX files
   - Files are passed to the LLM for context

4. **Select a Theme**
   - Choose an existing theme to categorize your case study
   - Leave blank to create a new theme automatically

5. **Configure Sections**
   - Modify section titles if needed
   - Adjust word limits based on your needs
   - Add additional sections with "Add Section"
   - Remove sections with "Remove Section" (keep at least 1)

6. **Enable/Disable Summary**
   - Check "Include Summary section at the end" if desired
   - Summary will be auto-generated by the LLM

7. **Expand Advanced Options** (Optional)
   - Adjust number of outcomes
   - Configure search parameters

8. **Generate Report**
   - Click "Generate Impact Case Study Report"
   - Monitor progress in the preview panel
   - Wait for report generation to complete

### For Developers

#### Adding Custom Sections Template

1. Update `impactCaseStudyConstants.ts`:
```typescript
export const IMPACT_CASE_STUDY_TEMPLATES = {
  customTemplate: {
    name: "Custom Template",
    sections: [
      {
        id: "1",
        title: "Custom Section",
        description: "Description",
        maxWords: 500,
      },
      // ... more sections
    ],
  },
};
```

2. Update `ImpactCaseStudyForm.tsx` to include template selector

#### Extending Form Functionality

1. Add new fields to `ImpactCaseStudyFormData` interface
2. Create corresponding form controls in `ImpactCaseStudyForm.tsx`
3. Update API payload in `handleSubmit` method
4. Add corresponding CSS styles

## Responsive Behavior

### Desktop (≥1200px)
- Two-column layout (form + sticky preview)
- Preview panel fixed to viewport
- Full form width

### Tablet (≥768px, <1200px)
- Stacked columns (form above preview)
- Preview takes full width
- Reduced font sizes

### Mobile (<768px)
- Single column layout
- Full-width form
- Preview below form
- Simplified typography

## Performance Considerations

1. **File Upload Handling**: Validates file types before upload
2. **Real-time Updates**: Form state updates don't require re-fetching data
3. **Lazy Loading**: Preview panel only re-renders on content change
4. **Memory Management**: File references cleared after upload

## Error Handling

- **Empty Prompt**: Shows validation error
- **File Upload Errors**: Validates file type and size
- **API Errors**: Toast notifications with error message
- **Network Issues**: Graceful error recovery

## Future Enhancements

1. **History/Archive**: Display list of previously generated case studies
2. **Export Options**: PDF, Word, Markdown export
3. **Templates Selector**: UI for choosing different impact templates
4. **Word Count Tracking**: Real-time word count for each section
5. **Draft Saving**: Save incomplete drafts
6. **Collaboration**: Share and edit with team members
7. **Review Workflow**: Built-in review and approval process
8. **Analytics**: Track impact case study generation metrics

## Troubleshooting

### Report Generation Fails
- Check that the prompt is not empty
- Verify theme exists if theme_id is specified
- Check backend logs for error details

### File Upload Not Working
- Verify file is in DOCX format
- Check file size is under 10MB
- Ensure browser allows file uploads

### Preview Not Showing
- Wait for report generation to complete
- Check browser console for errors
- Verify Pusher connection is established

## Support & Documentation

For additional help:
- Check backend `StructuredReportGenerator` documentation
- Review API endpoint specifications in `content/views.py`
- Refer to existing report generation pages for patterns
