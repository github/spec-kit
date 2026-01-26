# [PROJECT_NAME] Design System

<!-- Example: TaskFlow Design System, PhotoVault Design System, etc. -->

## Visual Foundation

### Color Palette

**Primary Colors**

[PRIMARY_COLOR_SCHEME]
<!-- Example:
- Primary: #3B82F6 (blue-500) - Main brand color for CTAs, links, focused states
- Primary Dark: #2563EB (blue-600) - Hover states, emphasized elements
- Primary Light: #60A5FA (blue-400) - Backgrounds, subtle highlights
- Primary Subtle: #DBEAFE (blue-100) - Very subtle backgrounds, hover surfaces
-->

**Secondary Colors**

[SECONDARY_COLOR_SCHEME]
<!-- Example:
- Secondary: #8B5CF6 (purple-500) - Secondary actions, accents
- Secondary Dark: #7C3AED (purple-600) - Hover states
- Secondary Light: #A78BFA (purple-400) - Highlights
-->

**Semantic Colors**

[SEMANTIC_COLOR_SCHEME]
<!-- Example:
- Success: #10B981 (green-500) - Success messages, positive states, completion
- Warning: #F59E0B (amber-500) - Warning messages, caution states
- Error: #EF4444 (red-500) - Error messages, destructive actions, validation errors
- Info: #3B82F6 (blue-500) - Informational messages, tips, helpers
-->

**Neutral Colors**

[NEUTRAL_COLOR_SCHEME]
<!-- Example:
- Background: #FFFFFF (white) - Page backgrounds, card surfaces
- Background Alt: #F9FAFB (gray-50) - Alternate backgrounds, subtle surfaces
- Border: #E5E7EB (gray-200) - Borders, dividers, separators
- Muted: #6B7280 (gray-500) - Secondary text, disabled states, placeholders
- Text: #111827 (gray-900) - Primary text, headings, content
- Text Secondary: #4B5563 (gray-600) - Secondary text, captions, metadata
-->

**Accessibility Notes**

[COLOR_ACCESSIBILITY_NOTES]
<!-- Example:
- All color combinations meet WCAG AA standards (4.5:1 contrast ratio for text)
- Primary text on white background: 8.2:1 ratio (exceeds AA, meets AAA)
- Error color ensures readability for colorblind users (tested with simulators)
- Never rely on color alone for information (always include icons/text labels)
-->

### Typography

**Font Families**

[FONT_FAMILIES]
<!-- Example:
- Primary Font: Inter (body text, UI elements)
  - Fallback: system-ui, -apple-system, "Segoe UI", sans-serif
  - Usage: All body text, form inputs, buttons, navigation
  
- Heading Font: Inter (same as body for consistency)
  - Weights: 600 (semibold) for h1-h3, 500 (medium) for h4-h6
  - Usage: All headings, section titles, card headers
  
- Monospace Font: "JetBrains Mono", "Fira Code", Consolas, monospace
  - Usage: Code blocks, inline code, technical content
-->

**Type Scale**

[TYPE_SCALE]
<!-- Example (using Tailwind naming):
- xs: 0.75rem (12px) / line-height: 1rem (16px)
  Usage: Captions, fine print, helper text, badges
  
- sm: 0.875rem (14px) / line-height: 1.25rem (20px)
  Usage: Secondary text, form labels, metadata, timestamps
  
- base: 1rem (16px) / line-height: 1.5rem (24px)
  Usage: Body text, default paragraph text, descriptions
  
- lg: 1.125rem (18px) / line-height: 1.75rem (28px)
  Usage: Lead paragraphs, emphasized text, large UI elements
  
- xl: 1.25rem (20px) / line-height: 1.75rem (28px)
  Usage: Subheadings (h4), card titles, section headers
  
- 2xl: 1.5rem (24px) / line-height: 2rem (32px)
  Usage: Section headings (h3), modal titles, prominent text
  
- 3xl: 1.875rem (30px) / line-height: 2.25rem (36px)
  Usage: Page headings (h2), feature titles
  
- 4xl: 2.25rem (36px) / line-height: 2.5rem (40px)
  Usage: Hero headings (h1), landing page titles
-->

**Font Weights**

[FONT_WEIGHTS]
<!-- Example:
- Regular (400): Body text, paragraphs, descriptions
- Medium (500): Emphasized text, labels, secondary headings (h4-h6)
- Semibold (600): Primary headings (h1-h3), buttons, strong emphasis
- Bold (700): Very strong emphasis (use sparingly)
-->

### Spacing & Layout

**Spacing Scale**

[SPACING_SCALE]
<!-- Example (4px base system):
- 0.5: 0.125rem (2px) - Extremely tight spacing, borders
- 1: 0.25rem (4px) - Tight spacing, icon padding
- 2: 0.5rem (8px) - Compact spacing, small gaps
- 3: 0.75rem (12px) - Comfortable small spacing
- 4: 1rem (16px) - Default spacing, standard gaps
- 6: 1.5rem (24px) - Comfortable spacing, card padding
- 8: 2rem (32px) - Loose spacing, section spacing
- 12: 3rem (48px) - Section separation, major spacing
- 16: 4rem (64px) - Large section separation
- 20: 5rem (80px) - Hero spacing, major separations
- 24: 6rem (96px) - Very large spacing (rare)
-->

**Grid System**

[GRID_SYSTEM]
<!-- Example:
- Container Max Width: 1280px (xl breakpoint)
- Gutter Width: 1rem (16px) on mobile, 1.5rem (24px) on desktop
- Column System: 12-column grid
- Gap Standard: 1rem (16px) for most layouts, 1.5rem (24px) for spacious layouts

Layout Patterns:
- Single column: Mobile default, narrow content
- 2 columns: Tablet and up, forms, feature lists
- 3 columns: Desktop and up, card grids, feature showcases
- 4 columns: Large desktop, dense content grids
-->

**Responsive Breakpoints**

[RESPONSIVE_BREAKPOINTS]
<!-- Example (mobile-first approach):
- xs: 0px - Mobile portrait (default, no media query needed)
- sm: 640px - Mobile landscape, small tablet
  @media (min-width: 640px)
  
- md: 768px - Tablet portrait
  @media (min-width: 768px)
  
- lg: 1024px - Tablet landscape, small desktop
  @media (min-width: 1024px)
  
- xl: 1280px - Desktop
  @media (min-width: 1280px)
  
- 2xl: 1536px - Large desktop
  @media (min-width: 1536px)
-->

### Iconography

**Icon System**

[ICON_SYSTEM]
<!-- Example:
- Library: Lucide React (https://lucide.dev)
- Style: Outline/stroke icons, consistent 2px stroke width
- Default Size: 20px (1.25rem) for UI elements
- Sizes Available:
  - sm: 16px (1rem) - Inline with text, small buttons
  - base: 20px (1.25rem) - Standard buttons, navigation
  - lg: 24px (1.5rem) - Feature icons, emphasis
  - xl: 32px (2rem) - Hero sections, large features
  
Icon Usage:
- Always include aria-label for standalone icons
- Use icons with text labels for clarity
- Maintain consistent sizing within component groups
- Ensure icons have adequate touch targets (min 44x44px)
-->

**Icon Colors**

[ICON_COLOR_GUIDELINES]
<!-- Example:
- Default: currentColor (inherits from parent text color)
- Primary Actions: Primary color
- Success/Warning/Error: Corresponding semantic colors
- Disabled: Muted color (gray-400)
- On Dark Backgrounds: White or very light gray
-->

## Component Library

### Core Components

[CORE_COMPONENTS]
<!-- Example:

**Button**
- Variants: Primary, Secondary, Outline, Ghost, Destructive
- Sizes: sm, base, lg
- States: Default, Hover, Active, Focus, Disabled, Loading
- Features: Icon support (leading/trailing), full-width option

**Input**
- Types: Text, Email, Password, Number, Search, Textarea
- States: Default, Focus, Error, Disabled, Read-only
- Features: Label, helper text, error message, leading/trailing icons

**Card**
- Structure: Optional header, content area, optional footer
- Variants: Default, bordered, elevated, interactive (hoverable)
- Padding: Comfortable (p-6) by default

**Badge**
- Variants: Default, Primary, Secondary, Success, Warning, Error, Outline
- Sizes: sm, base
- Use: Status indicators, tags, counts, labels

**Modal/Dialog**
- Sizes: sm, base, lg, xl, full
- Features: Overlay, close button, header, content, footer (actions)
- Behavior: Focus trap, ESC to close, click outside to close (optional)

**Dropdown Menu**
- Trigger: Button, link, or custom trigger
- Features: Keyboard navigation, groups, separators, icons, shortcuts
- Positioning: Auto-position to stay in viewport

**Toast/Notification**
- Variants: Success, Error, Warning, Info
- Duration: Auto-dismiss (configurable), manual dismiss option
- Position: Top-right (default), customizable

**Tooltip**
- Trigger: Hover, focus
- Positioning: Auto-position based on available space
- Content: Text only (keep brief), no interactive elements

**Tabs**
- Variants: Line (underline), Enclosed (boxed)
- Features: Keyboard navigation (arrow keys), active state indicator
- Responsive: Scrollable on mobile if needed

**Table**
- Features: Sortable columns, selectable rows, pagination
- Responsive: Horizontal scroll on mobile, stacked layout option
- States: Hover row highlight, selected row, loading state

**Form**
- Layout: Vertical (default), horizontal (inline labels), grid (multi-column)
- Validation: Real-time, on blur, on submit
- Error Handling: Field-level errors, form-level errors, summary
-->

### Patterns & Compositions

[COMPOSITION_PATTERNS]
<!-- Example:

**Form Pattern**
Components: Label + Input + Helper Text + Error Message
Layout: Vertical stacking (default), horizontal inline (compact)
Spacing: 1rem between fields, 0.5rem between label and input
Example:
```
<Form>
  <FormField>
    <Label>Email</Label>
    <Input type="email" />
    <HelperText>We'll never share your email</HelperText>
  </FormField>
  <FormField>
    <Label>Password</Label>
    <Input type="password" />
    {error && <ErrorText>Password is required</ErrorText>}
  </FormField>
  <Button type="submit">Sign In</Button>
</Form>
```

**Card Grid Pattern**
Components: Container + Cards
Layout: 1 column (mobile), 2 columns (tablet), 3+ columns (desktop)
Spacing: 1rem gap on mobile, 1.5rem gap on desktop
Example: Feature showcases, product listings, blog posts

**Navigation Pattern**
Components: Nav Container + Logo + Nav Links + User Menu
Layout: Horizontal bar (desktop), hamburger menu (mobile)
Behavior: Sticky on scroll (optional), highlight active page

**Hero Section Pattern**
Components: Container + Heading + Description + CTA Buttons + Optional Image
Layout: Centered text (default), split layout (text + image)
Spacing: Large spacing (8-12 units), breathing room

**Data Table Pattern**
Components: Table + Header Row + Data Rows + Pagination + Optional Filters
Features: Sortable columns, row selection, row actions
Responsive: Horizontal scroll or stacked cards on mobile
-->

### Component States

[COMPONENT_STATE_DEFINITIONS]
<!-- Example:

**Interactive Element States:**

1. **Default (Rest)**
   - Initial appearance when page loads
   - No user interaction
   - Example: Button with primary background, normal text

2. **Hover**
   - Mouse cursor over element
   - Visual change: Darken background, show underline, scale up slightly
   - Timing: Instant (0ms) or very quick (100ms)
   - Example: Button background darkens from blue-500 to blue-600

3. **Active (Pressed)**
   - Mouse button down or touch held
   - Visual change: Slightly darker than hover, sometimes scale down
   - Example: Button background darkens to blue-700, scale(0.98)

4. **Focus**
   - Element selected via keyboard (Tab key)
   - Visual indicator: Outline ring, usually primary color
   - Accessibility: Must be clearly visible, 2px minimum width
   - Example: 2px blue-500 ring with 2px offset

5. **Disabled**
   - Element cannot be interacted with
   - Visual change: Reduced opacity (0.5-0.6), muted colors, no pointer
   - Cursor: not-allowed
   - Example: Gray background, gray text, opacity 0.6

6. **Loading**
   - Asynchronous action in progress
   - Visual indicator: Spinner icon, disabled interaction
   - Example: Button shows spinner, text changes to "Loading...", disabled

7. **Error**
   - Invalid state or failed validation
   - Visual change: Red border, red text, error icon
   - Example: Input with red-500 border, error message below

8. **Success**
   - Valid state or successful completion
   - Visual change: Green border or checkmark icon
   - Example: Input with green-500 border, success message
-->

## UX Guidelines

### Accessibility

**WCAG Compliance Level**: [WCAG_LEVEL]
<!-- Example: WCAG 2.1 Level AA (or AAA for higher requirements) -->

[ACCESSIBILITY_STANDARDS]
<!-- Example:

**Color Contrast:**
- Text: Minimum 4.5:1 ratio for normal text (AA), 7:1 for AAA
- Large Text (18pt+): Minimum 3:1 ratio (AA), 4.5:1 for AAA
- UI Components: Minimum 3:1 ratio for interactive elements
- Tool: Use WebAIM Contrast Checker to validate

**Keyboard Navigation:**
- All interactive elements must be keyboard accessible
- Tab order follows visual/logical order
- Focus indicators clearly visible (2px ring minimum)
- Shortcuts: Enter/Space to activate, Arrow keys for lists/menus, ESC to close
- No keyboard traps (user can navigate away from any element)

**Screen Readers:**
- Semantic HTML (use proper heading hierarchy h1-h6)
- ARIA labels for icon-only buttons and controls
- ARIA live regions for dynamic content updates (toasts, loading states)
- Alt text for images (empty alt="" for decorative images)
- Form labels properly associated with inputs

**Focus Management:**
- Modals trap focus (can't tab outside)
- Closing modal returns focus to trigger element
- Skip links for main content navigation
- Auto-focus on first field in forms (when appropriate)

**Motion & Animations:**
- Respect prefers-reduced-motion user preference
- Provide option to disable animations
- No auto-playing videos or carousels without controls
- Animations serve purpose (not just decorative)

**Touch Targets:**
- Minimum size: 44x44px (iOS) or 48x48px (Android)
- Adequate spacing between interactive elements (8px minimum)
- Responsive touch feedback (visual state change)
-->

### Responsiveness

**Mobile-First Approach**: [RESPONSIVE_STRATEGY]
<!-- Example: Yes, design for mobile first, progressively enhance for larger screens -->

[RESPONSIVE_DESIGN_GUIDELINES]
<!-- Example:

**Breakpoint Strategy:**
- Start with mobile design (320px min width)
- Add complexity/features as screen size increases
- Use fluid typography (clamp or responsive units)
- Test on actual devices, not just browser resize

**Layout Adaptations:**

Mobile (< 640px):
- Single column layouts
- Stack elements vertically
- Full-width components
- Hamburger navigation
- Reduced spacing (1rem standard)
- Touch-optimized buttons (44px min height)

Tablet (640px - 1024px):
- 2-column layouts for content
- Side-by-side forms
- Visible navigation (collapsed optional)
- Moderate spacing (1.5rem)
- Hybrid touch/mouse optimization

Desktop (1024px+):
- Multi-column layouts (3-4 columns)
- Horizontal navigation
- Hover states and tooltips
- Generous spacing (2rem)
- Mouse-optimized interactions

**Images & Media:**
- Use srcset for responsive images
- Lazy loading for below-fold images
- Serve WebP with fallbacks
- Max width: 100% to prevent overflow
- Aspect ratio boxes to prevent layout shift

**Typography Scaling:**
- Use clamp() for fluid typography (if supported)
- Smaller base size on mobile (14-16px)
- Larger base size on desktop (16-18px)
- Scale headings appropriately for screen size

**Performance Considerations:**
- Defer non-critical CSS
- Minimize JavaScript on mobile
- Use system fonts when possible for speed
- Optimize for 3G connections (test on slow network)
-->

### Interactions & Animations

**Animation Philosophy**: [ANIMATION_APPROACH]
<!-- Example: Purposeful, subtle animations that enhance UX without distraction -->

[ANIMATION_PRINCIPLES]
<!-- Example:

**Timing & Easing:**
- Fast transitions: 100-200ms (hover states, focus changes)
- Medium transitions: 200-300ms (dropdowns, tooltips, fades)
- Slow transitions: 300-500ms (modals, page transitions, slides)
- Easing: ease-out for exits, ease-in for entrances, ease-in-out for movements
- Spring animations: Use for natural, physical movement (dragging, swiping)

**Animation Types:**

1. **Micro-interactions** (Fast, < 200ms)
   - Button hover state changes
   - Focus ring appearance
   - Icon color changes
   - Ripple effects on click

2. **Transitions** (Medium, 200-300ms)
   - Fade in/out (opacity changes)
   - Slide in/out (transform: translateY)
   - Dropdown/collapse (height animation + fade)
   - Tooltip appearance

3. **Page Transitions** (Slow, 300-500ms)
   - Route changes (fade + slide)
   - Modal open/close (scale + fade)
   - Drawer slide in/out
   - Full-screen overlays

**Animation Purposes:**
- **Feedback**: Confirm user actions (button press, form submit)
- **Direction**: Guide attention (tooltip pointing, highlight)
- **Relationship**: Show connection (expanding accordion)
- **Context**: Show where elements come from/go to (modal origin)
- **Progression**: Show loading state (spinner, skeleton)

**What NOT to Animate:**
- Don't animate everything (causes fatigue)
- Avoid animations > 500ms (feels sluggish)
- No animations during page load (performance)
- No continuous animations (battery drain)
- Skip animations if prefers-reduced-motion

**CSS Animation Example:**
```css
/* Button hover */
.button {
  transition: background-color 150ms ease-out, transform 100ms ease-out;
}
.button:hover {
  background-color: var(--color-primary-dark);
  transform: translateY(-1px);
}

/* Modal entrance */
.modal {
  animation: modalEnter 300ms ease-out;
}
@keyframes modalEnter {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
```
-->

### Feedback & Messaging

[FEEDBACK_GUIDELINES]
<!-- Example:

**User Feedback Types:**

1. **Success Messages**
   - When: Action completed successfully
   - Style: Green background, checkmark icon, brief text
   - Duration: 3-5 seconds auto-dismiss
   - Placement: Top-right corner (toast) or inline (form success)
   - Example: "Profile updated successfully"

2. **Error Messages**
   - When: Action failed or validation error
   - Style: Red background, error icon, clear explanation
   - Duration: User must dismiss (don't auto-dismiss errors)
   - Placement: Inline near error source (field) or top of form
   - Example: "Email is required" or "Failed to save changes. Please try again."

3. **Warning Messages**
   - When: Caution needed or potential issue
   - Style: Yellow/amber background, warning icon
   - Duration: User should dismiss or 7-10 seconds
   - Example: "Unsaved changes will be lost if you leave this page"

4. **Informational Messages**
   - When: General info, tips, help
   - Style: Blue background, info icon
   - Duration: 5-7 seconds or user dismiss
   - Example: "Tip: Use Ctrl+K to open quick search"

5. **Loading States**
   - When: Asynchronous operation in progress
   - Style: Spinner + optional text, disable interaction
   - Types:
     - Inline: Spinner in button, small spinner inline with content
     - Overlay: Full-screen or section spinner with backdrop
     - Skeleton: Placeholder content (better UX than blank screen)
   - Example: "Saving..." with spinner icon

6. **Empty States**
   - When: No content to display
   - Style: Icon + heading + description + optional CTA
   - Purpose: Guide user to take action or explain why empty
   - Example: "No posts yet. Create your first post to get started."

7. **Confirmation Dialogs**
   - When: Destructive or important action needs confirmation
   - Style: Modal with clear question, two actions (confirm/cancel)
   - Buttons: Destructive action (red), cancel (gray)
   - Example: "Are you sure you want to delete this item? This cannot be undone."

**Tone & Voice:**
- Friendly and conversational (but professional)
- Clear and concise (no jargon)
- Helpful and actionable (tell user what to do next)
- Consistent terminology across the app
- Avoid technical error messages (translate for users)

**Message Placement:**
- Errors: Near the source of the problem
- Success: Top-right corner or near action
- Global: Top center or top-right
- Contextual: Inline with related content
-->

## Implementation Notes

### Technology Stack

[TECH_STACK_UI]
<!-- Example:

**CSS Framework:**
- Primary: Tailwind CSS v3.4+
- Approach: Utility-first, component composition
- Customization: Extended theme in tailwind.config.js
- Why: Rapid development, consistency, tree-shaking for small bundle size

**Component Library:**
- Primary: shadcn/ui (headless Radix UI + Tailwind)
- Approach: Copy components into project, full customization
- Why: Full control, no black box, accessibility built-in, TypeScript support

**Icon Library:**
- Primary: Lucide React (v0.263.1+)
- Style: Outline icons, consistent stroke width
- Why: Modern, well-maintained, tree-shakeable, large icon set

**Animation Library:**
- Primary: Tailwind CSS built-in transitions
- Optional: Framer Motion for complex animations
- Why: Simple for most cases, powerful when needed

**Form Handling:**
- Primary: React Hook Form (v7.x)
- Validation: Zod (v3.x) for schema validation
- Why: Performance, minimal re-renders, TypeScript integration

**State Management:**
- UI State: React useState, useContext
- Server State: TanStack Query (React Query v5)
- Why: Separation of concerns, cache management, optimistic updates
-->

### File Structure

[FILE_ORGANIZATION]
<!-- Example:

**Component Organization:**
```
src/
├── components/
│   ├── ui/                  # Base UI components (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── forms/               # Form-specific components
│   │   ├── LoginForm.tsx
│   │   ├── ProfileForm.tsx
│   │   └── ...
│   ├── layout/              # Layout components
│   │   ├── Navbar.tsx
│   │   ├── Footer.tsx
│   │   ├── Sidebar.tsx
│   │   └── ...
│   └── features/            # Feature-specific components
│       ├── dashboard/
│       ├── profile/
│       └── ...
├── lib/
│   ├── utils.ts            # Utility functions (cn, formatters, etc.)
│   └── constants.ts        # Design tokens, config
├── styles/
│   ├── globals.css         # Global styles, Tailwind imports
│   └── animations.css      # Custom animation keyframes
└── hooks/                  # Custom React hooks
    ├── useToast.ts
    ├── useMediaQuery.ts
    └── ...
```

**Naming Conventions:**
- Components: PascalCase (Button.tsx, UserProfile.tsx)
- Hooks: camelCase with "use" prefix (useAuth.ts, useLocalStorage.ts)
- Utils: camelCase (formatDate.ts, validateEmail.ts)
- Constants: UPPER_SNAKE_CASE (API_BASE_URL, MAX_FILE_SIZE)
- CSS classes: kebab-case (btn-primary, card-header) or Tailwind utilities
-->

### Naming Conventions

[NAMING_RULES]
<!-- Example:

**Component Naming:**
- Descriptive and specific: UserProfileCard not GenericCard
- Avoid abbreviations: Button not Btn, Navigation not Nav (unless very common)
- Compound names: SearchInput, SettingsModal, PricingCard

**CSS Class Naming:**
- Use Tailwind utilities as primary approach
- Custom classes: BEM-like naming (block__element--modifier)
- Example: card__header, button--primary, input--error
- Avoid over-specific names: .user-settings-form-submit-button (too long)

**Variable Naming:**
- Boolean variables: isLoading, hasError, canEdit (is/has/can prefix)
- Handlers: handleClick, handleSubmit, onInputChange (handle/on prefix)
- State: user, users, isOpen, selectedId (descriptive noun)
- Constants: API_BASE_URL, MAX_UPLOAD_SIZE (all caps with underscores)

**File Naming:**
- Components: Match component name (Button.tsx for Button component)
- Utilities: Descriptive function name (formatDate.ts, validateEmail.ts)
- Pages: Descriptive route name (Dashboard.tsx, Profile.tsx, [id].tsx)
- Types: .types.ts or .d.ts suffix (user.types.ts, api.d.ts)

**Consistency Rules:**
- Pick one convention and stick to it across entire project
- Document exceptions and reasons
- Use linter/formatter to enforce consistency (ESLint, Prettier)
-->

### Design Tokens

[DESIGN_TOKENS]
<!-- Example (if using CSS variables or config file):

**CSS Variables (in globals.css):**
```css
:root {
  /* Colors */
  --color-primary: #3B82F6;
  --color-primary-dark: #2563EB;
  --color-primary-light: #60A5FA;
  
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  
  /* Spacing (based on 4px) */
  --spacing-1: 0.25rem;
  --spacing-2: 0.5rem;
  --spacing-4: 1rem;
  --spacing-6: 1.5rem;
  --spacing-8: 2rem;
  
  /* Typography */
  --font-primary: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}
```

**Or Tailwind Config:**
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3B82F6',
          dark: '#2563EB',
          light: '#60A5FA',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
};
```
-->

## Governance

[GOVERNANCE_RULES]
<!-- Example:

**Change Management:**

1. **Proposing Changes**
   - Document the reason for change (user feedback, accessibility, consistency)
   - Show examples/mockups of proposed change
   - Assess impact on existing components/features
   - Get approval from design lead or team vote

2. **Breaking Changes (MAJOR version bump)**
   - Require team consensus
   - Must include migration guide
   - Deprecate old API before removing (if possible)
   - Announce at least one sprint in advance
   - Examples: Changing component library, major color overhaul

3. **Additive Changes (MINOR version bump)**
   - Document new component/pattern in design system
   - Ensure accessibility tested
   - Add to component showcase/storybook
   - Examples: New component, new color variant, new animation

4. **Refinements (PATCH version bump)**
   - Can be made quickly, low impact
   - Document in changelog
   - Examples: Color shade adjustment, spacing tweak, doc improvement

**Documentation Updates:**
- Update this file for any design system changes
- Update component documentation (Storybook, inline comments)
- Update related specs/plans if affected
- Announce changes in team channel/meeting

**Review Process:**
- All new components reviewed for accessibility
- Design changes previewed before implementation
- Regular design system audits (quarterly)
- User testing for major changes

**Compliance Checks:**
- Automated linting for design token usage
- Visual regression testing (Percy, Chromatic)
- Accessibility audits (aXe, Lighthouse)
- Performance budgets (bundle size, paint times)

**Evolution Strategy:**
- Keep design system as living document
- Regular design system showcases/reviews
- Encourage feedback from developers and users
- Iterate based on real-world usage
- Don't be afraid to deprecate what doesn't work
-->

## Version History

**Current Version**: [DESIGN_SYSTEM_VERSION]
**Created**: [CREATION_DATE]
**Last Updated**: [LAST_UPDATED_DATE]

[VERSION_CHANGELOG]
<!-- Example:

## Changelog

### Version 2.1.0 (2024-01-26)
- Added dark mode color palette
- New data table component patterns
- Extended spacing scale for larger layouts
- Improved accessibility guidelines with more examples

### Version 2.0.0 (2024-01-15)
- BREAKING: Migrated from Material UI to shadcn/ui
- BREAKING: Updated color palette for better contrast
- Redesigned button component variants
- New typography scale based on fluid sizing
- Added comprehensive animation guidelines

### Version 1.2.0 (2024-01-01)
- Added tooltip component
- Extended icon library with custom icons
- New form validation patterns
- Improved mobile responsive guidelines

### Version 1.1.0 (2023-12-15)
- Added secondary color palette
- New card component variants
- Badge component and guidelines
- Accessibility audit fixes

### Version 1.0.0 (2023-12-01)
- Initial design system release
- Core components defined
- Color palette established
- Typography scale defined
- Basic responsive guidelines
-->

---

**Maintained by**: [TEAM_OR_PERSON]
**Questions or suggestions?**: [CONTACT_METHOD]
