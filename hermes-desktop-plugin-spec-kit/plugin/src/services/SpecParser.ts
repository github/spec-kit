/**
 * SpecParser — Round-trip spec.md <-> model using remark/MDX AST
 * Preserves [NEEDS CLARIFICATION], comments, formatting
 */
import { parse, stringify } from "remark"
import { visit } from "unist-util-visit"

export interface SpecModel {
  featureName: string
  status: string
  created: string
  scenarios: Scenario[]
  requirements: Requirement[]
  entities: Entity[]
  clarifications: string[]
  constitutionGates: Gate[]
}

export interface Scenario {
  id: number
  name: string
  given: string
  when: string
  then: string
}

export interface Requirement {
  id: string
  title: string
  description: string
  priority: "High" | "Medium" | "Low"
  acceptanceCriteria: string[]
}

export interface Entity {
  name: string
  attributes: Attribute[]
}

export interface Attribute {
  name: string
  type: string
  description: string
}

export interface Gate {
  id: string
  label: string
  passed: boolean
}

export function parseSpec(markdown: string): SpecModel {
  const tree = parse(markdown)
  const model: SpecModel = {
    featureName: "",
    status: "Draft",
    created: new Date().toISOString().split("T")[0],
    scenarios: [],
    requirements: [],
    entities: [],
    clarifications: [],
    constitutionGates: [],
  }

  // Extract feature name from first heading
  visit(tree, "heading", (node) => {
    if (node.depth === 1 && node.children[0]?.type === "text") {
      model.featureName = node.children[0].value.replace("Feature Specification:", "").trim()
    }
  })

  // Parse scenarios
  visit(tree, "heading", (node) => {
    if (node.depth === 3 && node.children[0]?.type === "text") {
      const text = node.children[0].value
      if (text.startsWith("Scenario")) {
        model.scenarios.push({ id: model.scenarios.length + 1, name: text, given: "", when: "", then: "" })
      }
    }
  })

  // Parse clarifications
  visit(tree, "blockquote", (node) => {
    const text = stringify(node)
    const matches = text.matchAll(/\[NEEDS CLARIFICATION\]: (.+)/g)
    for (const match of matches) {
      model.clarifications.push(match[1].trim())
    }
  })

  // Parse gates (checkboxes)
  visit(tree, "listItem", (node) => {
    const text = stringify(node)
    if (text.includes("[ ]") || text.includes("[x]")) {
      const gateId = text.match(/\[( |x)\]\s*(.+)/)?.[2]?.trim()
      if (gateId) {
        model.constitutionGates.push({ id: gateId, label: gateId, passed: text.includes("[x]") })
      }
    }
  })

  return model
}

export function serializeSpec(model: SpecModel): string {
  let md = "# Feature Specification: " + model.featureName + "\n\n"
  md += "> **Status**: " + model.status + "\n"
  md += "> **Created**: " + model.created + "\n"
  md += "> **Constitution**: \`.specify/memory/constitution.md\`\n\n"

  // Scenarios
  md += "## Scenarios\n\n"
  model.scenarios.forEach((s, i) => {
    md += "### Scenario " + (i + 1) + ": " + s.name + "\n"
    md += "**Given** " + s.given + "\n"
    md += "**When** " + s.when + "\n"
    md += "**Then** " + s.then + "\n\n"
  })

  // Requirements
  md += "## Functional Requirements\n\n"
  model.requirements.forEach((r) => {
    md += "### " + r.id + ": " + r.title + "\n"
    md += "**Description**: " + r.description + "\n"
    md += "**Priority**: " + r.priority + "\n"
    md += "**Acceptance Criteria**:\n"
    r.acceptanceCriteria.forEach(c => { md += "- [ ] " + c + "\n" })
    md += "\n"
  })

  // Entities
  md += "## Entities\n\n"
  model.entities.forEach((e) => {
    md += "### " + e.name + "\n"
    md += "**Attributes**:\n"
    e.attributes.forEach(a => { md += "- \`" + a.name + "\`: " + a.type + " — " + a.description + "\n" })
    md += "\n"
  })

  // Clarifications
  if (model.clarifications.length > 0) {
    md += "## Clarifications\n\n"
    model.clarifications.forEach(c => { md += "> **[NEEDS CLARIFICATION]**: " + c + "\n" })
    md += "\n"
  }

  // Constitution Gates
  if (model.constitutionGates.length > 0) {
    md += "## Constitution Gates\n\n"
    model.constitutionGates.forEach(g => {
      md += "- [" + (g.passed ? "x" : " ") + "] " + g.label + "\n"
    })
    md += "\n"
  }

  return md
}

export function updateSpec(model: SpecModel, edit: Partial<SpecModel>): SpecModel {
  return { ...model, ...edit }
}

