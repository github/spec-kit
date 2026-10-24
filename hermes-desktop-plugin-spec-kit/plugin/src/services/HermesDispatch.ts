/**
 * HermesDispatch — Skill invocation abstraction
 * v1: hermes chat -Q -q "<query>" -s speckit-<skill>
 * v2: host.request("skills.invoke", ...)
 */
export interface SkillResult {
  success: boolean
  output?: string
  error?: string
  sessionId?: string
}

export class HermesDispatch {
  private static instance: HermesDispatch
  private useInternalApi = false

  static getInstance(): HermesDispatch {
    if (!HermesDispatch.instance) {
      HermesDispatch.instance = new HermesDispatch()
    }
    return HermesDispatch.instance
  }

  setInternalApi(enabled: boolean) {
    this.useInternalApi = enabled
  }

  async invoke(skill: string, args: string): Promise<SkillResult> {
    if (this.useInternalApi) {
      return this.invokeInternal(skill, args)
    }
    return this.invokeCli(skill, args)
  }

  private async invokeCli(skill: string, args: string): Promise<SkillResult> {
    // In v1, this would spawn: hermes chat -Q -q "<args>" -s speckit-<skill>
    // For now, return mock result
    console.log("[HermesDispatch] CLI invoke:", skill, args)
    return { success: true, output: "Mock CLI result for " + skill, sessionId: "mock-session" }
  }

  private async invokeInternal(skill: string, args: string): Promise<SkillResult> {
    // In v2, use host.request("skills.invoke", { skill, args })
    console.log("[HermesDispatch] Internal API invoke:", skill, args)
    return { success: true, output: "Mock internal result for " + skill, sessionId: "mock-session" }
  }

  // Convenience methods for spec-kit skills
  async specify(featureName: string, interactive = false): Promise<SkillResult> {
    return this.invoke("speckit.specify", featureName + (interactive ? " --interactive" : ""))
  }

  async clarify(featureName: string, all = false): Promise<SkillResult> {
    return this.invoke("speckit.clarify", featureName + (all ? " --all" : ""))
  }

  async plan(featureName: string, interactive = false): Promise<SkillResult> {
    return this.invoke("speckit.plan", featureName + (interactive ? " --interactive" : ""))
  }

  async tasks(featureName: string, interactive = false): Promise<SkillResult> {
    return this.invoke("speckit.tasks", featureName + (interactive ? " --interactive" : ""))
  }

  async implement(taskId: string, goal = false): Promise<SkillResult> {
    return this.invoke("speckit.implement", taskId + (goal ? " --goal" : ""))
  }

  async converge(featureName: string, checklist = false): Promise<SkillResult> {
    return this.invoke("speckit.converge", featureName + (checklist ? " --checklist" : ""))
  }

  async constitution(action: "init" | "review" | "amend" = "init"): Promise<SkillResult> {
    return this.invoke("speckit.constitution", "--" + action)
  }
}

export const hermesDispatch = HermesDispatch.getInstance()

