/**
 * ConstitutionWizard — Guided 5-step decision tree for project constitution
 */
import { host, PANES_AREA, Button, Input, Textarea, Badge, ScrollArea, EmptyState, GlyphSpinner, Codicon, icons } from "@hermes/plugin-sdk"
import { useState, useEffect } from "react"
import { jsx, jsxs, Fragment } from "react/jsx-runtime"

const ID = "spec-kit-hermes"
const PANE_ID = ID + ":constitution-wizard"

const STEPS = [
  { id: 1, label: "Purpose", icon: "target" },
  { id: 2, label: "Principles", icon: "list-ordered" },
  { id: 3, label: "Architecture", icon: "layout" },
  { id: 4, label: "Governance", icon: "gavel" },
  { id: 5, label: "Ratify", icon: "shield-check" },
]

function ConstitutionWizard() {
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState({ purpose: "", principles: [], architecture: [], governance: {} })
  const [saving, setSaving] = useState(false)

  const isFirstStep = currentStep === 1
  const isLastStep = currentStep === STEPS.length

  const handleNext = () => setCurrentStep(c => Math.min(c + 1, STEPS.length))
  const handlePrev = () => setCurrentStep(c => Math.max(c - 1, 1))
  const handleSubmit = async () => {
    setSaving(true)
    await new Promise(r => setTimeout(r, 500))
    host.notify({ kind: "success", message: "Constitution ratified" })
    setSaving(false)
  }

  return jsx("div", { className: "flex h-full flex-col", "data-pane-id": PANE_ID, children: [
    jsx("div", { className: "p-3 border-b border-(--ui-stroke-secondary)", children: [
      jsx("h2", { className: "font-medium", children: "Constitution Wizard" }),
      jsx("div", { className: "flex gap-1 mt-2", children: STEPS.map(s => jsx("div", { key: s.id, className: "flex-1 text-center text-xs text-(--ui-text-tertiary)", children: s.label })) })
    ]}),
    jsx("div", { className: "flex-1 p-4", children: jsx("div", { className: "max-w-2xl mx-auto", children: [
      jsx("h3", { className: "text-lg font-medium mb-4", children: "Step " + currentStep + ": " + STEPS[currentStep-1].label }),
      jsx("p", { className: "text-sm text-(--ui-text-tertiary) mb-4", children: "Constitution Wizard - Step " + currentStep + " implementation pending" }),
    ]})}),
    jsx("div", { className: "p-3 border-t border-(--ui-stroke-secondary)", children: jsx("div", { className: "flex justify-between", children: [
      jsx(Button, { variant: "secondary", onClick: () => setCurrentStep(c => Math.max(c-1, 1)), disabled: isFirstStep, children: "Back" }),
      isLastStep ? jsx(Button, { variant: "primary", onClick: handleSubmit, disabled: saving, children: saving ? "Saving..." : "Ratify" }) : jsx(Button, { variant: "primary", onClick: () => setCurrentStep(c => Math.min(c+1, STEPS.length)), children: "Next" })
    ]})})
  ]})
}

export default { id: "constitution-wizard", area: PANES_AREA, title: "Constitution Wizard", data: { placement: "right", width: "500px" }, render: () => jsx(ConstitutionWizard, {}) }

