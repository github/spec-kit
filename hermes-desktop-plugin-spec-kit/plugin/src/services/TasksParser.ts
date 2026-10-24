/**
 * TasksParser — Round-trip tasks.md <-> Kanban model
 * Parses [P] parallel groups, [US#] story labels, file paths
 */
import { parse, stringify } from "remark"
import { visit } from "unist-util-visit"

export interface Task {
  id: string
  title: string
  body: string
  status: "triage" | "todo" | "ready" | "running" | "review" | "convergence" | "done" | "blocked" | "archived"
  assignee: string
  parallelGroup?: string
  storyLabel?: string
  filePath?: string
  checkbox: boolean
}

export interface KanbanColumn {
  id: string
  label: string
  tasks: Task[]
}

export function parseTasks(markdown: string): Task[] {
  const tree = parse(markdown)
  const tasks: Task[] = []

  visit(tree, "listItem", (node) => {
    const text = stringify(node).trim()
    // Match: - [ ] Task title [P:group] [US#123]
    const match = text.match(/^- \[( |x)\] (.+?)(?: \[P:([^\]]+)\])?(?: \[US#(\d+)\])?$/)
    if (match) {
      tasks.push({
        id: "t-" + (tasks.length + 1).toString().padStart(4, "0"),
        title: match[2].trim(),
        body: "",
        status: match[1] === "x" ? "done" : "todo",
        assignee: "default",
        parallelGroup: match[3] || undefined,
        storyLabel: match[4] ? "US#" + match[4] : undefined,
        checkbox: match[1] === "x",
      })
    }
  })

  return tasks
}

export function serializeTasks(tasks: Task[]): string {
  let md = "# Task List\n\n"
  md += "> **Status**: Active\n"
  md += "> **Kanban Board**: \`hermes kanban list --assignee default\`\n\n"

  // Group by parallel group
  const groups = new Map<string, Task[]>()
  tasks.forEach(t => {
    const key = t.parallelGroup || "sequential"
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(t)
  })

  groups.forEach((groupTasks, groupName) => {
    if (groupName !== "sequential") {
      md += "### Parallel Group " + groupName + " [P:" + groupName + "]\n\n"
    }
    groupTasks.forEach(t => {
      md += "- [" + (t.checkbox ? "x" : " ") + "] " + t.title
      if (t.parallelGroup) md += " [P:" + t.parallelGroup + "]"
      if (t.storyLabel) md += " " + t.storyLabel
      md += "\n"
    })
    md += "\n"
  })

  return md
}

export function tasksToKanban(tasks: Task[]): Record<string, Task[]> {
  const columns: Record<string, Task[]> = {
    triage: [],
    todo: [],
    ready: [],
    running: [],
    review: [],
    convergence: [],
    done: [],
    blocked: [],
    archived: [],
  }
  tasks.forEach(t => {
    if (columns[t.status]) columns[t.status].push(t)
  })
  return columns
}

export function kanbanToTasks(columns: Record<string, Task[]>): Task[] {
  return Object.values(columns).flat()
}

