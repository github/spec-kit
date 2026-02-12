---
description: Create or update the project design system defining visual design, component patterns, and UX guidelines.
handoffs: 
  - label: Create Feature Spec
    agent: speckit.specify
    prompt: Create a spec following our design system. I want to build...
  - label: Update Constitution
    agent: speckit.constitution
    prompt: Update constitution to align with design principles
  - label: Create Implementation Plan
    agent: speckit.plan
    prompt: Create a plan that follows the design system guidelines
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

You are creating or updating the project design system at `/memory/design-system.md`. This file serves as the single source of truth for visual design, component patterns, and UX guidelines. Your job is to (a) collect design requirements, (b) fill the template with concrete design decisions, and (c) ensure consistency with the project constitution.

Follow this execution flow:

1. **Check if design system exists**:
   - Load `/memory/design-system.md` if it exists
   - If exists: identify what the user wants to update/add
   - If not exists: prepare to create from scratch
   - Load `/memory/constitution.md` to ensure alignment with project principles

2. **Determine the scope of work**:
   - **For new design system**: Collect comprehensive design requirements
   - **For updates**: Identify specific sections to modify (colors, typography, components, etc.)
   - Parse user input to understand:
     - Visual identity requirements (colors, fonts, spacing)
     - Component library approach (custom, third-party, hybrid)
     - UX priorities (accessibility, responsiveness, performance)
     - Technology choices (CSS framework, component library, icon set)

3. **Information collection strategy**:

   **If creating new design system (file doesn't exist)**:
   
   Ask the user targeted questions ONLY if the user input doesn't provide enough information:
   
   a. **Visual Foundation** (only ask if not specified):
      - Primary color palette and intent
      - Typography choices (font families, scale)
      - Spacing/layout system (grid, spacing scale)
      - Icon system preference
   
   b. **Component Approach** (only ask if not specified):
      - Using existing library (shadcn/ui, Material UI, etc.) or custom?
      - Component customization level
      - State management approach for UI
   
   c. **UX Standards** (only ask if not specified):
      - Accessibility target (WCAG AA, AAA)
      - Responsive approach (mobile-first, desktop-first)
      - Animation philosophy (minimal, moderate, rich)
   
   d. **Technology Stack** (only ask if not specified):
      - CSS approach (Tailwind, CSS-in-JS, SCSS, etc.)
      - Component library choice
      - Icon library preference
   
   **IMPORTANT**: Make informed guesses based on common patterns if user doesn't specify everything. Only mark items as [NEEDS CLARIFICATION] if they significantly impact design direction and have no reasonable default.

   **If updating existing design system**:
   - Load current design system
   - Identify the specific changes requested
   - Validate changes don't conflict with existing specs/plans
   - Propose version bump (MAJOR/MINOR/PATCH)

4. **Generate design system content**:
   
   Use the template at `/templates/design-system-template.md` and fill with collected information.
   
   **Mandatory sections**:
   - Visual Foundation (colors, typography, spacing, icons)
   - Component Library (core components, patterns, states)
   - UX Guidelines (accessibility, responsiveness, interactions)
   - Implementation Notes (tech stack, file structure, naming)
   - Governance (versioning, change management)
   
   **Optional enhancements**:
   - Generate mermaid diagrams for:
     - Color palette visualization
     - Component hierarchy (graph)
     - Responsive breakpoint flows
     - Typography scale
   - Include code examples for:
     - Color usage patterns
     - Component composition examples
     - Responsive patterns
   
5. **Validate and ensure consistency**:
   
   **Quality checklist**:
   - [ ] All mandatory sections completed
   - [ ] Visual foundation clearly defined (colors, typography, spacing)
   - [ ] Component patterns documented with examples
   - [ ] Accessibility standards specified (WCAG level, keyboard nav)
   - [ ] Responsive strategy defined (breakpoints, approach)
   - [ ] Technology choices specified and justified
   - [ ] Aligns with constitution principles
   - [ ] Version number follows semantic versioning
   - [ ] No placeholder tokens remaining (except intentionally deferred items)
   
   **Constitution alignment**:
   - Compare design principles with constitution
   - Ensure no conflicts (e.g., constitution requires simplicity, design doesn't add unnecessary complexity)
   - If conflicts found, flag them and suggest resolution
   
   **Impact assessment** (if updating):
   - Check existing specs in `specs/*/spec.md` for design references
   - Check existing plans in `specs/*/plan.md` for component usage
   - Identify specs/plans that may be affected by design changes
   - Generate list of potentially impacted artifacts

6. **Write the design system file**:
   - Write to `/memory/design-system.md`
   - Include sync impact report as HTML comment at the top (for updates)
   - Ensure proper markdown formatting
   - Include version information and dates

7. **Generate visual documentation** (when applicable):
   
   Create mermaid diagrams to visualize:
   
   **Color Palette Example**:
   ```mermaid
   graph LR
       subgraph primary [Primary Colors]
           P1[Primary: #3B82F6]
           P2[Primary Dark: #2563EB]
           P3[Primary Light: #60A5FA]
       end
       subgraph semantic [Semantic Colors]
           S1[Success: #10B981]
           S2[Warning: #F59E0B]
           S3[Error: #EF4444]
       end
   ```
   
   **Component Hierarchy Example**:
   ```mermaid
   graph TD
       Base[Base Components] --> Button[Button]
       Base --> Input[Input]
       Base --> Card[Card]
       
       Button --> PrimaryButton[Primary Button]
       Button --> SecondaryButton[Secondary Button]
       
       Card --> ContentCard[Content Card]
       Card --> FeatureCard[Feature Card]
       
       Patterns[Composite Patterns] --> Form[Form Pattern]
       Form --> Input
       Form --> Button
   ```

8. **Output summary to user**:
   
   Provide a clear summary with:
   - Design system file location: `/memory/design-system.md`
   - Version information (new version if update)
   - Key design decisions documented
   - Technology choices confirmed
   - Next steps:
     - Review the generated design system
     - Use `/speckit.specify` to create specs that follow the design system
     - Use `/speckit.plan` to create implementation plans aligned with design
   - If updates made: List of specs/plans that may need review
   - Suggested commit message (if applicable)

## Key Guidelines

### For AI Generation

When creating/updating the design system:

1. **Be specific and concrete**: Replace all placeholders with actual values
   - ❌ Bad: "Use a modern color palette"
   - ✅ Good: "Primary: #3B82F6 (blue), Secondary: #8B5CF6 (purple)"

2. **Provide context and rationale**: Explain design decisions
   - Why these colors? (brand alignment, accessibility, psychology)
   - Why this component library? (ecosystem, flexibility, learning curve)
   - Why this spacing system? (consistency, flexibility, development speed)

3. **Include practical examples**: Show, don't just tell
   - Color usage: "Primary for CTAs, Secondary for highlights, Muted for disabled states"
   - Component composition: "Cards contain Heading + Content + optional Button"
   - Responsive patterns: "Stack vertically on mobile, 2-column grid on tablet, 3-column on desktop"

4. **Document accessibility**: Be explicit about a11y standards
   - Color contrast ratios (AA: 4.5:1 for text, AAA: 7:1)
   - Keyboard navigation patterns
   - Screen reader considerations
   - Focus indicators

5. **Define component states clearly**:
   - Default, Hover, Active, Focus, Disabled, Loading, Error
   - Visual changes for each state
   - Animation/transition timing if applicable

6. **Technology choices must be actionable**:
   - Specify exact libraries/versions when possible
   - Include installation/setup notes if relevant
   - Reference documentation URLs

### Versioning Rules

Design system versions follow semantic versioning:

- **MAJOR (X.0.0)**: Breaking changes
  - Changing component library (Material UI → shadcn/ui)
  - Complete color palette overhaul
  - Typography system replacement
  - Changes requiring component rewrites

- **MINOR (0.X.0)**: Additive changes
  - New components added to library
  - New color variations (dark mode palette)
  - Extended spacing scale
  - New animation patterns
  - Additional accessibility features

- **PATCH (0.0.X)**: Non-breaking refinements
  - Color value adjustments (shade tweaks)
  - Documentation improvements
  - Example additions
  - Clarifications to guidelines
  - Fixed typos or formatting

### When to Ask for Clarification

Only use [NEEDS CLARIFICATION: ...] markers for:

1. **Critical brand decisions** with no context:
   - Color palette when no brand guidelines exist
   - Typography when no brand fonts specified

2. **Significant technical tradeoffs**:
   - Component library choice when multiple viable options
   - CSS approach with different architectural implications

3. **Accessibility requirements** when legally sensitive:
   - Specific WCAG conformance level for regulated industries
   - Required accessibility features for specific user groups

**Do NOT ask about**:
- Common spacing scales (use 4px/8px base)
- Standard responsive breakpoints (use Tailwind defaults or common standards)
- Basic accessibility (always target WCAG AA minimum)
- Icon libraries (suggest popular choices like Lucide, Heroicons)

### Integration with Other Commands

- **`/speckit.constitution`**: Design system must align with constitution principles
- **`/speckit.specify`**: Specs should reference design system components
- **`/speckit.plan`**: Plans should validate against design system guidelines
- **`/speckit.tasks`**: Tasks should include design system compliance checks
- **`/speckit.implement`**: Implementation must follow design system patterns

### Common Patterns to Include

When documenting, always include:

1. **Color Usage Patterns**:
   ```
   - Primary: Call-to-action buttons, links, focused states
   - Secondary: Less prominent actions, secondary information
   - Accent: Highlights, badges, special callouts
   - Success/Warning/Error: Feedback messages, form validation
   - Muted: Disabled states, placeholder text, secondary content
   - Background: Page backgrounds, card surfaces, dividers
   ```

2. **Typography Scale** (example using Tailwind):
   ```
   - xs: 0.75rem (12px) - Captions, helper text
   - sm: 0.875rem (14px) - Secondary text
   - base: 1rem (16px) - Body text
   - lg: 1.125rem (18px) - Lead paragraphs
   - xl: 1.25rem (20px) - Subheadings
   - 2xl: 1.5rem (24px) - Headings
   - 3xl: 1.875rem (30px) - Page titles
   ```

3. **Spacing Scale** (example using 4px base):
   ```
   - 1: 0.25rem (4px) - Tight spacing
   - 2: 0.5rem (8px) - Compact spacing
   - 4: 1rem (16px) - Default spacing
   - 6: 1.5rem (24px) - Comfortable spacing
   - 8: 2rem (32px) - Loose spacing
   - 12: 3rem (48px) - Section spacing
   - 16: 4rem (64px) - Major section spacing
   ```

4. **Responsive Breakpoints** (example using Tailwind):
   ```
   - sm: 640px - Tablet portrait
   - md: 768px - Tablet landscape
   - lg: 1024px - Desktop
   - xl: 1280px - Large desktop
   - 2xl: 1536px - Extra large desktop
   ```

## Formatting & Style Requirements

- Use Markdown headings exactly as in template
- Keep sections organized and scannable
- Use bullet points for lists of guidelines
- Use code blocks for technical examples
- Include mermaid diagrams for visual concepts
- Maintain consistent terminology throughout
- Keep line length reasonable (<100 chars ideally)
- No trailing whitespace
- Single blank line between sections

## Error Handling

If critical information is missing and cannot be reasonably inferred:
1. Document what's missing with [NEEDS CLARIFICATION: specific question]
2. Provide 2-3 reasonable options with tradeoffs
3. Set a sensible default if user doesn't respond
4. Include rationale for the default choice

If conflicts with constitution are found:
1. Clearly identify the conflict
2. Explain why it's a problem
3. Suggest 2-3 resolution paths
4. Wait for user decision before proceeding
