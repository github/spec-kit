# Designer Portfolio Suite Constitution

## Core Principles

### Clean, Modular, and Intuitive UI/UX
Centered on designers' needs with an interface that reduces cognitive load and maximizes creative workflow efficiency.

### Component-Based, Token-Driven Architecture
Using shadcn/ui tokens for all styling, theming, and branding to ensure consistency and maintainability.

### Open-Source Extensibility and Transparency
For user-driven innovation, allowing the community to contribute and extend functionality.

### Real-Time Preview and WYSIWYG Editing
Minimal cognitive load for users with immediate visual feedback on all changes.

### Seamless Data Mapping
Dynamic portfolio outputs through seamless mapping of project data and brand assets.

## Functional Requirements

### Multi-Resume Manager
Create, store, edit, and select from multiple resumes—each mappable to unique project sets, portfolios, and job applications.

### Airtable-like CMS
Manage projects, case studies, testimonials, clients, and assets via a spreadsheet/database interface. Support tags, media attachments, custom fields, and relationships.

### Designer-Focused Portfolio Site Builder
- **Core**: Live, component-based website canvas and drag-and-drop editor.
- **All elements/components** are styled using grouped brand tokens (colors, typography, radius, etc.) that can be edited globally or overwritten locally.
- **Components and layout blocks** are entirely prop/token-driven, supporting modular construction and instant style updates.
- **Global design tokens** (brand palette, font stack, spacing, etc.) are visible in an organized sidebar and assignable to any part of the canvas or component tree.
- **Users can edit, duplicate, and remix** components and re-apply token sets across site sections.
- **Live preview updates** as tokens or props change; undo/redo for every step.
- **Asset/media manager**: Upload, group, and assign assets (logos, images, palettes, icons, documents) to projects, CMS entries, or site elements.
- **Outreach tools**: Create job application and networking drafts mapped to specific resumes, projects, and roles.

## UI/UX Organization

### Dashboard
Central hub for quick access to resume manager, CMS, portfolio builder, and assets.

### Left Sidebar
Accordion/tabs for navigation between core modules (Tokens/Themes, CMS, Asset Library, Components, Pages/Site).

### Central Canvas
Drag-and-drop, modular preview area. Updates in real-time with token/editor changes. Component tree shown for selection/context.

### Token Editor
Sidebar shows grouped shadcn tokens, with inline token editing, drag-to-apply, and global/local switch.

### Component Review
UI to browse/search/clone/remix all created site components. New component can be built from existing or from asset+token templates.

### Asset Organizer
Group/assign assets by type (logo, imagery, document, palette) and tag for comprehensive project management.

### Workflow Diagram Section
Built-in visual designer for mapping project-to-portfolio flows, CMS-website connections, and resume-job-application processes.

## Must-Have Features

- All portfolio site output is strictly component-based and token-driven: global brand tokens propagate instantly to every site element and can be overridden per component or block.
- True drag-and-drop block canvas with live preview and undo/redo.
- CMS with project/asset linking and batch import/export.
- Editable, grouped theme tokens (shadcn registry) with live effect preview.
- Comprehensive asset manager: inline cropping, grouping, tagging, versioning.
- Modular component browser/creator with remix capability.
- Dynamic workflow visualization tools, including flow diagrams for onboarding and project mapping.
- Intuitive onboarding, guided tours, contextual help, and persistent tooltips.
- Accessibility: keyboard navigation, ARIA support, and responsive layout.

## Governance

Open to public contribution—feedback/PR templates provided. Core roadmap set by community voting with transparent backlog.

**Version**: 1.0 | **Ratified**: 2025-09-10 | **Last Amended**: 2025-09-10
