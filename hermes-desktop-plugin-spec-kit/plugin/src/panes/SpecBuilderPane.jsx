/**
 * SpecBuilderPane — Interactive spec.md editor for Hermes Desktop
 * Features: FRs, scenarios, entities, [NEEDS CLARIFICATION] markers, constitution gate validation
 */
import {
  host,
  atom,
  useValue,
  useQuery,
  useMutation,
  queryClient,
  Button,
  Input,
  Textarea,
  Badge,
  ScrollArea,
  EmptyState,
  ErrorState,
  GlyphSpinner,
  Skeleton,
  SearchField,
  SegmentedControl,
  Separator,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Popover,
  PopoverTrigger,
  PopoverContent,
  Codicon,
  icons,
  cn,
  relativeTime,
  PANES_AREA,
} from '@hermes/plugin-sdk'
import { useState, useEffect, useMemo, useRef } from 'react'
import { jsx, jsxs, Fragment } from 'react/jsx-runtime'

const ID = 'spec-kit-hermes'
const PANE_ID = `${ID}:spec-builder`

// Tabs for spec sections
const TABS = [
  { id: 'scenarios', label: 'Scenarios', icon: 'book-open' },
  { id: 'requirements', label: 'Requirements', icon: 'list-ordered' },
  { id: 'entities', label: 'Entities', icon: 'database' },
  { id: 'clarifications', label: 'Clarifications', icon: 'help-circle' },
  { id: 'gates', label: 'Constitution Gates', icon: 'shield-check' },
]

function SpecBuilderPane() {
  const [activeTab, setActiveTab] = useState('scenarios')
  const [specContent, setSpecContent] = useState('')
  const [clarifications, setClarifications] = useState([])
  const [maxClarifications] = useState(3)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  // Load spec from .specify/
  useEffect(() => {
    loadSpec()
  }, [])

  const loadSpec = async () => {
    try {
      // In v1, read from file system via host.request or ctx.rest
      // For now, initialize empty
      setSpecContent(getDefaultSpec())
    } catch (err) {
      setError(err.message)
    }
  }

  const getDefaultSpec = () => \`# Feature Specification: New Feature

> **Status**: Draft
> **Created**: \${new Date().toISOString().split('T')[0]}
> **Constitution**: \`.specify/memory/constitution.md\`

## Scenarios

### Scenario 1: Happy Path
**Given** a user wants to do something
**When** they perform the action
**Then** the expected outcome occurs

---

## Functional Requirements

### FR-1: Core Functionality
**Description**: The main feature behavior
**Priority**: High
**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2

---

## Entities

### EntityName
**Attributes**:
- \`id\`: string — Unique identifier
- \`name\`: string — Display name
- \`created_at\`: datetime — Creation timestamp

---

## Edge Cases

1. **Empty State**: Handle when no data exists
2. **Error State**: Graceful error handling

---

## Clarifications

> **[NEEDS CLARIFICATION]**: What should happen in edge case X?
> **[NEEDS CLARIFICATION]**: Which API endpoint to use?
> **[NEEDS CLARIFICATION]**: What are the validation rules?

---

## Constitution Gates

- [ ] Purpose Alignment
- [ ] Principle Compliance
- [ ] Architecture Fit
- [ ] Governance Review
\`

  const handleSave = async () => {
    setSaving(true)
    try {
      // Write to .specify/specs/<feature>/spec.md
      // In v1: use host.request('fs.write', ...) or ctx.rest
      await new Promise(r => setTimeout(r, 500)) // Simulate
      host.notify({ kind: 'success', message: 'Spec saved' })
    } catch (err) {
      setError(err.message)
      host.notifyError(err, 'Failed to save spec')
    } finally {
      setSaving(false)
    }
  }

  const handleClarificationAdd = () => {
    if (clarifications.length >= maxClarifications) {
      host.notify({ kind: 'warning', message: \`Maximum \${maxClarifications} clarifications allowed\` })
      return
    }
    const newClarification = \`[NEEDS CLARIFICATION]: \${new Date().toISOString()}\`
    setClarifications([...clarifications, newClarification])
  }

  const handleClarificationRemove = (index) => {
    setClarifications(clarifications.filter((_, i) => i !== index))
  }

  const renderTab = (tabId) => {
    switch (tabId) {
      case 'scenarios':
        return (
          <ScrollArea className="h-full p-4">
            <Textarea
              value={specContent}
              onChange={(e) => setSpecContent(e.target.value)}
              placeholder="Write scenarios in Given/When/Then format..."
              className="h-full font-mono text-sm"
              rows={20}
            />
          </ScrollArea>
        )
      case 'requirements':
        return (
          <ScrollArea className="h-full p-4">
            <Textarea
              value={specContent}
              onChange={(e) => setSpecContent(e.target.value)}
              placeholder="Write functional requirements..."
              className="h-full font-mono text-sm"
              rows={20}
            />
          </ScrollArea>
        )
      case 'entities':
        return (
          <ScrollArea className="h-full p-4">
            <Textarea
              value={specContent}
              onChange={(e) => setSpecContent(e.target.value)}
              placeholder="Define entities and attributes..."
              className="h-full font-mono text-sm"
              rows={20}
            />
          </ScrollArea>
        )
      case 'clarifications':
        return (
          <div className="flex flex-col h-full p-4 gap-3">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">Clarification Markers (max {maxClarifications})</h3>
              <Badge variant="outline" className="text-xs">
                {clarifications.length}/{maxClarifications}
              </Badge>
            </div>
            <ScrollArea className="flex-1">
              {clarifications.map((c, i) => (
                <div key={i} className="flex items-start gap-2 p-2 bg-(--ui-bg-quaternary) rounded">
                  <span className="font-mono text-xs text-(--ui-text-tertiary)">[NEEDS CLARIFICATION]</span>
                  <Input
                    value={c}
                    onChange={(e) => {
                      const newClarifications = [...clarifications]
                      newClarifications[i] = e.target.value
                      setClarifications(newClarifications)
                    }}
                    className="flex-1 text-sm"
                    placeholder="Enter clarification question..."
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleClarificationRemove(i)}
                    disabled={clarifications.length <= 1}
                  >
                    <Codicon icon={icons.x} className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </ScrollArea>
            {clarifications.length < maxClarifications && (
              <Button variant="secondary" size="sm" onClick={handleClarificationAdd} className="w-full">
                <Codicon icon={icons.plus} className="h-4 w-4 mr-1" />
                Add Clarification
              </Button>
            )}
          </div>
        )
      case 'gates':
        return (
          <ScrollArea className="h-full p-4 space-y-4">
            <h3 className="font-medium">Constitution Gate Validation</h3>
            <div className="space-y-3">
              {[
                { id: 'purpose', label: 'Purpose Alignment', desc: 'Feature aligns with declared project purpose' },
                { id: 'principles', label: 'Principle Compliance', desc: 'No violation of core principles' },
                { id: 
