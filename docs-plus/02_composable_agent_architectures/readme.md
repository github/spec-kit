# The Main Reusable Abstraction are Subagent

**[Detailed Technical Whitepaper on Coposable Agents](composable_agents_paper.md)**

We will discuss how Anthropic’s *Skills* concept, *subagents*, and the *Model Context Protocol (MCP)* fit together.

In a **Claude Code / Gemini CLI / OpenAI Agents SDK**–style ecosystem,
the **main reusable abstraction** is going to become the **“subagent”** — and each subagent will have:

* its **own system prompt** (defining persona, scope, domain boundaries),
* a **bundle of skills** (Docker, Kubernetes, Dapr, A2A, etc.),
* and **registered MCP connections** (e.g., Docker MCP, K8s MCP, GitHub MCP).

That combination makes subagents both **self-contained units of capability** and **composable modules** for agentic architectures.

These subagents — equipped with composable *skills* and connected via *MCP* — will become the **main abstraction and unit of reuse** across all serious AI operating systems and CLIs.

Here’s how the layering shakes out:

---

### 🧩 Layered Design Pattern Emerging

| Layer                                   | Role                                   | Example in your DevOps Agent                          |
| --------------------------------------- | -------------------------------------- | ----------------------------------------------------- |
| **Base Agent (LLM runtime)**            | Reasoning and control loop             | Gemini, Claude, or OpenAI Agent SDK                   |
| **Subagent (Domain specialization)**    | Handles a domain with clear boundaries | DevOps Agent                                          |
| **Skills (Composable functions)**       | Adds pluggable powers                  | Docker skill, Kubernetes skill, Dapr skill, A2A skill |
| **MCP Servers (External tool bridges)** | Real-world system connections          | Docker MCP, K8s MCP, GitHub MCP                       |
| **Protocol Interface (A2A)**            | Communication between orgs / agents    | DIDComm, A2A JSON-LD, or Dapr pub/sub                 |

---

### ⚙️ Example: DevOps Subagent

**System Prompt (persona):**

> “You are a DevOps automation subagent. You manage container lifecycles, Kubernetes deployments, and agent mesh networking using Dapr and A2A protocols.”

**Attached Skills:**

* 🐳 `DockerSkill` → Build, run, tag, and push images.
* ☸️ `KubernetesSkill` → Apply manifests, watch pods, scale deployments.
* 🧠 `DaprSkill` → Wrap stateful agents as Dapr Actors for resilience.
* 🌐 `A2ASkill` → Expose agents for secure agent-to-agent calls.

**Connected MCP Servers:**

* `docker.mcp.local`
* `kubernetes.mcp.cluster.local`
* `github.mcp.company.net`

Then, your **main orchestrator** (say, `InfraCoordinatorAgent`) can just “spin up” the DevOps subagent when a task hits that skill boundary — e.g., “Deploy the forecasting agent to staging.”

---

### 🧠 Why This Model Is So Powerful

1. **Composable Units of Competence:**
   Each subagent is like a microservice for cognition — plug it in, version it, reuse it.

2. **Skill-based Extensibility:**
   Skills act like dynamic libraries that can be installed or swapped without retraining or fine-tuning.

3. **Cross-Agent Reuse:**
   A `DaprSkill` written once can power multiple agents (DevOps, DataOps, FinOps, etc.).

4. **MCP Integration = Real Autonomy:**
   MCP lets the skill connect to actual tools (Docker, GitHub, K8s) safely and reproducibly.

5. **A2A = Federated Agent Networks:**
   The A2A skill you mentioned makes these subagents interoperable across organizations — the foundation for a *“network of agentic services.”*

---

### 🚀 Vision: The “Skill + Subagent” Ecosystem

Imagine your org has a **Skill Registry** and a **Subagent Hub**:

```
/skills
  ├─ DockerSkill/
  ├─ KubernetesSkill/
  ├─ DaprSkill/
  └─ A2ASkill/

/subagents
  ├─ DevOpsAgent/
  ├─ FinanceAgent/
  ├─ DataAgent/
  └─ SecurityAgent/
```

Each subagent has:

* `system_prompt.yaml`
* `skills.yaml`
* `mcp_connections.yaml`

Then, AI CLIs like **Claude Code**, **Gemini CLI**, or **OpenAI Agents SDK shells**
can dynamically load and run these as local or remote extensions.

---

Here’s the **Markdown whitepaper** version, with your clarification incorporated — it now explicitly applies both to *extending AI CLIs with subagents* **and** *building multi-agent systems in any domain.*

---

## **Composable Agent Architectures: Integrating Skills, Subagents, and MCP for Multi-Agent Systems and AI CLIs**


## **Abstract**

This whitepaper introduces a modular architecture for developing intelligent, extensible, and interoperable agent systems. It formalizes the relationship between **Skills**, **Subagents**, and the **Model Context Protocol (MCP)** as core abstractions for both extending **AI Command-Line Interfaces (AI CLIs)** and building **multi-agent systems (MAS)** across domains.

A case study—the **DevOps Subagent**—demonstrates how composable capabilities (Skills) and real-world integrations (MCP servers) can be orchestrated to automate DevOps workflows and interconnect with other organizational agents via the A2A (Agent-to-Agent) protocol.

The same principles generalize to finance, data science, robotics, education, and beyond, forming the foundation of a new generation of **Agentic Cloud ecosystems.**

---

## **1. Introduction**

LLMs have evolved from language models into **autonomous agentic systems** capable of complex reasoning, memory, and collaboration. Frameworks such as **Claude Code**, **Gemini CLI**, and **OpenAI Agents SDK** now allow agents to be structured, orchestrated, and extended through declarative manifests, modular tools, and standardized protocols.

However, as these systems grow, developers face the same challenges that once defined distributed software engineering:

* Reuse across domains and organizations
* Secure interoperability
* Scalable deployment
* Modular capability composition

This paper introduces three key abstractions to address these challenges:

1. **Skills** — portable modules of functional capability.
2. **Subagents** — specialized cognitive components composed of skills.
3. **MCP Servers** — structured bridges between agents and real-world systems.

Together, these enable *composable*, *extensible*, and *federated* AI systems—both within a single CLI environment and across multi-agent ecosystems.

---

## **2. The Agentic Stack**

| Layer                   | Description                                     | Example                           |
| ----------------------- | ----------------------------------------------- | --------------------------------- |
| **LLM Runtime**         | Core reasoning loop                             | Gemini, Claude, OpenAI Agents SDK |
| **Subagent**            | Domain persona equipped with context and skills | DevOpsAgent                       |
| **Skills**              | Modular and reusable capabilities               | DockerSkill, DaprSkill, A2ASkill  |
| **MCP Servers**         | Tool and environment connectors                 | Docker MCP, K8s MCP, GitHub MCP   |
| **Protocols**           | Agent communication layer                       | A2A, DIDComm, WebSocket           |
| **Observability Layer** | Logging, tracing, policy                        | Jaeger, OpenTelemetry, AgentOps   |

This architecture mirrors the composability of **microservices**, but at the **cognitive level**, where agents and subagents act as autonomous yet cooperative processes.

---

## **3. Core Abstractions**

### **3.1 Skills: Reusable Cognitive Capabilities**

A **Skill** defines a bounded function that an agent can call, encapsulating logic, configuration, and security policy.

A skill module contains:

* `skill.yaml`: metadata and permissions
* Implementation code (Python, JS, etc.)
* Optional dependency manifests

**Example: KubernetesSkill**

```yaml
name: "KubernetesSkill"
description: "Manage Kubernetes deployments via MCP"
commands:
  - apply_manifest
  - get_pod_logs
dependencies:
  - mcp: "kubernetes_mcp.yaml"
permissions:
  - kube_apply
  - kube_read
```

Skills can be installed dynamically, versioned, and shared across subagents and organizations.

---

### **3.2 Subagents: Modular Cognitive Units**

A **Subagent** is a reusable, contextually specialized AI component that combines:

* A **system prompt** defining its purpose and reasoning constraints
* A set of **skills** defining what it can do
* A set of **MCP connections** defining what it can access

Subagents can:

* Run standalone (CLI command mode)
* Operate under a parent agent (as a subtask executor)
* Interact with external agents via A2A protocols

**Example use case:**
A *DevOps Subagent* handles deployment workflows while a *DataAgent* handles analytics, both coordinated by a *Meta-Agent* for enterprise automation.

---

### **3.3 Model Context Protocol (MCP): Bridging AI and Infrastructure**

The **Model Context Protocol (MCP)** standardizes how agents access external systems—analogous to “drivers” for the agent world.

Each MCP connection defines:

* Endpoint, transport, and credentials
* Supported capabilities (CRUD, deploy, monitor)
* Access boundaries and audit rules

**Example:**

```yaml
name: "kubernetes"
protocol: "mcp"
endpoint: "kubernetes.mcp.cluster.local"
auth:
  type: "serviceaccount"
  token_path: "/var/run/secrets/kubernetes.io/serviceaccount/token"
capabilities:
  - deploy
  - scale
  - status
```

This allows secure, typed, and reproducible execution of real-world actions by AI agents.

---

## **4. Case Study: The DevOps Subagent**

The **DevOps Subagent** embodies this architecture.

### **Core Skills**

| Skill               | Function                                   |
| ------------------- | ------------------------------------------ |
| **DockerSkill**     | Build, run, and publish containers         |
| **KubernetesSkill** | Deploy and scale workloads                 |
| **DaprSkill**       | Wrap stateful agents as Dapr Actors        |
| **A2ASkill**        | Enable cross-organization agent federation |

### **Capabilities**

* Convert stateful OpenAI Agents SDK agents into Dapr Actors
* Deploy them in stateless containers for scalability
* Expose them via A2A gateways for external access

This transforms an internal DevOps agent into a **federated AI service node** on an A2A network.

---

## **5. Applying This Model Beyond DevOps**

The same design pattern applies in *any domain*:

| Domain         | Example Subagents               | Typical Skills                     |
| -------------- | ------------------------------- | ---------------------------------- |
| **Finance**    | AccountingAgent, AuditAgent     | XeroSkill, PowerBISkill            |
| **Education**  | CoteacherAgent, TutorAgent      | CurriculumSkill, AssessmentSkill   |
| **Healthcare** | DiagnosisAgent, SchedulingAgent | EHRSkill, HIPAACompliantAPISkill   |
| **Robotics**   | NavigationAgent, VisionAgent    | ROS2Skill, MotionPlanningSkill     |
| **AI CLIs**    | DevOpsAgent, ResearchAgent      | DockerSkill, GitHubSkill, A2ASkill |

Thus, this framework becomes a **universal pattern** for extending AI CLIs (like Gemini CLI or Claude Code) and for composing distributed multi-agent ecosystems.

---

## **6. A2A Protocol: Federated Agent Collaboration**

The **A2A (Agent-to-Agent) Protocol** defines how agents communicate securely and semantically across organizations.

**Features:**

* Message envelopes with identity and intent
* Optional DID-based or JWT authentication
* Capability negotiation via `/capabilities` endpoint
* Dapr-based routing for high reliability

**Example Envelope:**

```json
{
  "type": "A2A_MESSAGE",
  "protocol": "a2a/v1",
  "sender": "did:org1:agent123",
  "recipient": "did:org2:forecast-agent",
  "intent": "forecast_project",
  "payload": { "project_id": "PX-1003" },
  "signature": "0xE7B3A..."
}
```

The A2A skill enables cross-agent workflows—like one company’s *FinanceAgent* securely calling another company’s *AuditAgent*.

---

## **7. Extending AI CLIs with Subagents**

In CLI ecosystems like **Claude Code**, **Gemini CLI**, or **Codex**, subagents become **command-level extensions**.

For example:

```
$ ai devops deploy --agent project_forecaster.yaml
```

Under the hood:

1. The CLI activates the **DevOps Subagent**.
2. It loads skills (Docker, K8s, Dapr).
3. It calls the **Deploy-to-Dapr Skill** to containerize the agent.
4. The **A2A Skill** exposes it to other agents.

Subagents thus form a reusable command surface, bridging AI reasoning with developer tooling.

---

## **8. Benefits of the Skills + Subagents Model**

| Benefit              | Description                                           |
| -------------------- | ----------------------------------------------------- |
| **Modularity**       | Agents are built from reusable skill modules.         |
| **Reusability**      | Skills and subagents can be versioned like libraries. |
| **Security**         | MCP enforces strict boundary access.                  |
| **Interoperability** | A2A allows multi-organization collaboration.          |
| **Scalability**      | Dapr Actors allow stateful logic on stateless infra.  |
| **Extensibility**    | Works in CLIs, web agents, and cloud-native services. |

---

## **9. Roadmap for Implementation**

1. **Define Subagent Manifests:** YAML descriptors for system prompts and skills.
2. **Standardize Skill Metadata:** Shared schema across frameworks.
3. **Integrate MCP Connectors:** Secure, typed external APIs.
4. **Enable A2A Networking:** Agent-to-agent protocol layer.
5. **Develop Agent Mesh Monitoring:** Logs, traces, governance, and billing.

---

## **10. Conclusion**

By unifying **Skills**, **Subagents**, and **MCP**, we unlock a new software paradigm where AI agents function as **composable cognitive microservices**.

This pattern applies equally to:

* Extending **AI CLIs** with specialized agentic commands
* Building **multi-agent systems** in domains from DevOps to education

The result is a scalable, interoperable **Agentic Cloud**, where agents evolve from isolated tools into **federated digital organizations** capable of collaboration, reasoning, and shared growth.

---






