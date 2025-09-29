# Module 08 – Evaluation-Driven Development (EDD)

> **The AI testing discipline: How to systematically test and optimize your AI prompts and models in agentic applications.**

## 🎯 **What EDD Actually Is**

**EDD is the AI-specific testing discipline that works alongside TDD:**

- **TDD**: Tests traditional code (functions, APIs, business logic)
- **EDD**: Tests AI components (prompts, models, agent behavior)

**EDD is NOT:**
- A replacement for TDD
- A single learning path
- A magic solution for all AI problems
- A replacement for good prompt engineering

## 🔄 **TDD vs EDD: Parallel Testing Disciplines**

### **TDD (Test-Driven Development)**
**For:** Traditional code and functions
**Tests:** Code logic, APIs, database operations, business logic
**Focus:** "Does my code work correctly?"

**Example:**
```python
def test_user_creation():
    user = create_user("john@example.com", "password123")
    assert user.email == "john@example.com"
    assert user.is_active == True
```

### **EDD (Evaluation-Driven Development)**
**For:** AI agents and LLM applications
**Tests:** Prompt quality, agent behavior, model performance, reasoning chains
**Focus:** "Does my AI agent work correctly?"

**Example:**
```python
def test_agent_response():
    response = agent.run("Help me book a flight")
    assert response.contains("flight")
    assert response.is_helpful()
    assert response.cost < 0.01
```

## 🤖 **For Agentic Applications, You Need Both**

**TDD for the "plumbing":**
- Database connections
- API integrations
- Business logic
- Error handling
- Authentication

**EDD for the "intelligence":**
- Agent prompts
- Reasoning chains
- Tool selection
- Conversation flow
- Model performance

## 🔄 **How EDD Fits in SDD Workflow**

**SDD → TDD → EDD → PHR**

**1. SDD Design**: Plan your AI agent's capabilities and user interactions
**2. TDD Implementation**: Build the traditional code that supports the agent
**3. EDD Implementation**: Build and test the AI components that make the agent intelligent
**4. PHR Learning**: Capture insights from both TDD and EDD

### **Why EDD Matters for Agentic Applications**

**Agentic applications are complex because:**
- Agents make multiple decisions in sequence
- Each decision depends on previous context
- Agent behavior is emergent and hard to predict
- Prompt quality directly determines agent performance

**EDD helps by:**
- Testing agent prompts systematically
- Comparing models for agent tasks
- Measuring agent performance with data
- Optimizing based on real results

## 🛠️ **How to Actually Do EDD**

### **The 5-Step Learning Path**

**Step 1: Basic Prompt Testing**
```bash
# Install DeepEval
pip install deepeval pytest pytest-asyncio

# Create your first test
./edd-setup.sh create-test basic

# Run tests
./edd-setup.sh run-evals
```

**Step 2: Agent Behavior Testing**
```bash
# Test reasoning and decision making
./edd-setup.sh create-test agent

# Run agent behavior tests
./edd-setup.sh run-evals
```

**Step 3: Tool Integration Testing**
```bash
# Test tool calling behavior
./edd-setup.sh create-test tool

# Run tool integration tests
./edd-setup.sh run-evals
```

**Step 4: Safety and Boundaries Testing**
```bash
# Test safety and security
./edd-setup.sh create-test safety

# Run safety tests
./edd-setup.sh run-evals
```

**Step 5: Model Comparison and Optimization**
```bash
# Compare different models
./edd-setup.sh compare-models

# Analyze results
./edd-setup.sh analyze

# Update prompts based on results
./edd-setup.sh update-prompts
```

### **Quick Start with Spec Kit**

**1. Initialize EDD for Your Project**
```bash
./edd-setup.sh init --project "ai-tutor" --feature "tutoring"
```

**2. Use EDD Command in Spec Workflow**
```bash
# In your spec workflow
/spec --feature tutoring
/plan --feature tutoring
/tasks --feature tutoring
/edd --feature tutoring  # New EDD step
/phr --feature tutoring
```

**3. Follow the Learning Path**
- Complete the 5 steps in order
- Practice with real projects
- Integrate with your SDD workflow

### **Example: Testing an AI Tutor Agent**

```yaml
# Basic agent evaluation
prompts:
  - |
    You are an AI tutor. Help the student learn {{topic}}.
    Student: {{student_input}}
    
    Ask one helpful question.

providers:
  - openai:gpt-4.1-mini
  - openai:gpt-4.1

tests:
  - vars:
      topic: "machine learning"
      student_input: "I want to learn ML"
    assert:
      - type: contains
        value: "?"
      - type: llm-rubric
        value: "Asks a helpful learning question"
```

## 📁 **Organizing EDD for Agentic Applications**

### **Simple Directory Structure**

```
your-agent-project/
├── prompts/                 # Your agent prompts
│   ├── system_prompts/     # Main agent instructions
│   ├── tool_prompts/       # Tool calling prompts
│   └── conversation/       # Multi-turn conversation prompts
├── evaluations/            # EDD test files
│   ├── basic_tests.yaml   # Core functionality tests
│   ├── tool_tests.yaml    # Tool usage tests
│   └── safety_tests.yaml  # Safety and boundary tests
└── results/               # Evaluation results and reports
```

### **What to Test in Each Area**

**Core Agent Behavior:**
- Does the agent understand user intent?
- Does it respond appropriately?
- Does it maintain conversation context?

**Tool Integration:**
- Does the agent choose the right tools?
- Does it use tools correctly?
- Does it handle tool errors gracefully?

**Safety and Boundaries:**
- Does the agent refuse harmful requests?
- Does it stay within its defined role?
- Does it handle edge cases safely?

## 🔄 **EDD in Your SDD Workflow**

### **When to Use EDD**

**Use EDD when you have:**
- AI prompts that users interact with
- Multiple AI models to choose from
- Important AI responses that must be reliable
- Time to invest in making AI work better

### **How to Get Started**

**1. Follow the Learning Path**
- Complete the 5 steps in order
- Use the provided examples and exercises
- Practice with your own projects

**2. Use the EDD Setup Script**
```bash
# Initialize EDD for your project
./edd-setup.sh init --project "your-project" --feature "your-feature"

# Create specific test types
./edd-setup.sh create-test basic
./edd-setup.sh create-test agent
./edd-setup.sh create-test tool
./edd-setup.sh create-test safety

# Run all evaluations
./edd-setup.sh run-evals

# Analyze results and optimize
./edd-setup.sh analyze
./edd-setup.sh update-prompts
```

**3. Integrate with Spec Kit**
- Use `/edd` command in your spec workflow
- Add eval requirements to your specs
- Document results in PHRs

**4. Scale to Production**
- Set up continuous monitoring
- Collect real user feedback
- Iterate based on data

### **The Key Principle**

**Test your AI prompts like you test your code.**

## 🎯 **Summary**

**EDD is the AI-specific testing discipline that works alongside TDD in agentic applications.**

**Key points:**
- TDD tests traditional code, EDD tests AI components
- Both are essential for reliable agentic applications
- Test your prompts like you test your code
- Compare different models for your use case
- Measure performance with real data
- Optimize based on results, not guesswork

**For agentic applications:**
- Use TDD for the "plumbing" (APIs, databases, business logic)
- Use EDD for the "intelligence" (prompts, models, agent behavior)
- Both disciplines work together in the SDD workflow

**The 5-step approach:**
1. **Basic Prompt Testing** - Test simple prompt responses
2. **Agent Behavior Testing** - Test reasoning and decision making
3. **Tool Integration Testing** - Test tool calling behavior
4. **Safety and Boundaries Testing** - Test safety and security
5. **Model Comparison and Optimization** - Compare models and optimize

**Integration with SDD:**
- Use `/edd` command in your spec workflow
- Add eval requirements to your specs
- Document results in PHRs
- Scale to production monitoring

**Remember: TDD and EDD are parallel testing disciplines - you need both for agentic applications.**