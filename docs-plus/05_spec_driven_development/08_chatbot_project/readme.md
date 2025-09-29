# Step 8: Capstone – SDD Chatbot Project

**Part1: Spec 1, Branch 1, PR 1** - OpenAI Agents SDK + FastAPI + Chainlit Implementation

**Goal:** demonstrate end-to-end mastery by shipping a working chatbot experience using the full SDD workflow.

## Inputs

- Completed Steps 1–6 artifacts (constitution, spec, plan, tasks)
- A scoped chatbot objective (e.g., `/chat/wait` endpoint + `chat/streaming` SSE streaming)
- Evaluation harness or contract tests from earlier steps

## Actions

Re-run the SDD loop for the capstone feature set:
### 1. **Update constitution.**
	```prompt
		/constitution Create principles focused on code quality, testing standards, user experience consistency, and performance requirements. Include governance for how these principles should guide technical decisions and implementation choices.
		Core Guidelines:
		- Code quality with strong typing and linting
		- Async-first design for FastAPI endpoints
		- Clear separation between UI (Chainlit), Agent logic (OpenAI Agents SDK FrameWork), and API layer
		- Security: never expose API keys in responses
		- Extensibility: new endpoints or agent capabilities can be added with minimal changes
		- Streaming must be stable, resilient to disconnects, and retry-friendly
		- Test-First (NON-NEGOTIABLE)
	```
	
### 2. **Draft Spec** - At the specification stage in Spec-Driven Development (SDD), you should not bring in SDK or framework details yet (like “Agents SDK” or “FastAPI” or “Chainlit”).

Why?
- The Constitution already captures your architectural/technical principles (async, separation of layers, testing, security).
- The Spec is meant to describe the functional behavior of the system — what the chatbot should do, not how it’s implemented.
- The Plan step (after the Spec) is where the “how” and the technical stack choices (Agents SDK, Gemini CLI, FastAPI, Chainlit, etc.) get mapped to the functional requirements.

So right now → just focus on the chatbot working behavior
```prompt
	Develop a scoped chatbot service called "ChatWait".  
	It should expose two modes of interaction:

	1. **/chat/wait endpoint**  
	- Client sends a user message and receives a full response once it is completely generated.  
	- Used for synchronous request/response style interactions.  

	2. **/chat/streaming endpoint**  
	- Supports server-sent events (SSE).  
	- Client begins receiving tokens incrementally as they are generated.  
	- Must handle retries and reconnections gracefully so that if the connection drops, the user can resume without losing context.  

	**Functional Expectations**:  
	- The chatbot should respond conversationally, supporting multi-turn dialog.  
	- It must provide clear error messages if endpoints are misused.  
	- The system should be extensible so that future features (like conversation history, user sessions, or integrations) can be layered in without breaking existing functionality.  
	- Performance should be acceptable for real-time use: streaming latency must feel natural.  
	- User experience must be consistent across both wait and streaming modes.  

	**Constraints for this initial specification**:  
	- No authentication or user management.  
	- No persistence of chat history (stateless per request).  
	- Focus on proving stable synchronous and streaming interaction paths.  

	The output specification should include user stories and functional requirements to capture these behaviors clearly.  
```
	
### 3. **Clarify Spec**: Use this to de-risk and sharpen the specification.

```prompt
	/clarify Review the ChatWait specification for ambiguity, missing details, or hidden risks.  
	Focus especially on:  
	- Streaming resilience: how to handle disconnects, retries, and partial responses.  
	- Error handling: what kind of error payloads should be returned from each endpoint?  
	- Extensibility: are future features (history, sessions, integrations) blocked by current design choices?  
	- Performance: what thresholds should we consider for "natural latency" in streaming?  
	- UX consistency: does synchronous vs. streaming behavior differ in unexpected ways?  

	Propose clarifications or questions that should be answered before moving forward.  
```

It's important to use the interaction as an opportunity to clarify and ask questions around the specification - do not treat its first attempt as final.

### 4. **Generate a plan: You can now be specific about the tech stack and other technical requirements. 

Initial Plan:

```
/plan Create a detailed implementation plan for the ChatWait chatbot service based on the specification.  
This plan should now introduce the technical stack and map each functional requirement to concrete implementation details.

Tech Stack & Requirements:
- **UI Layer**: Chainlit for chat interface and demoing synchronous + streaming interactions.
- **Agent Logic**: OpenAI Agents SDK for conversation orchestration.  
  - v1: Stateless interactions (no session persistence).  
  - Note: SDK supports session memory (e.g., SQLiteSession). Future versions may enable this.  
- **LLM**: Gemini, configured and managed via Gemini CLI integration, using the OpenAI-compatible API.  
- **API Layer**: FastAPI providing two endpoints:
  - `/chat/wait` (sync request/response).
  - `/chat/streaming` (SSE streaming, retry-friendly).
- **Runtime**: Python 3.12+ with async-first design.
- **Project Management**: UV for environment, dependency, and script handling.
- **Testing**: Pytest with test-first enforcement. Include unit tests for API routes, integration tests for streaming stability, and resilience tests for disconnect/reconnect handling.

Plan Expectations:
1. **Architecture Breakdown**: Show clear separation between UI, agent logic, and API layer.
2. **Data Flow**: Describe how a message moves from UI → API → Agent → LLM → response.
3. **Streaming Strategy**: How SSE will be implemented, including reconnect and partial output handling.
4. **Extensibility Considerations**: Document how features like session memory can be enabled in later iterations without breaking current design.
5. **Testing Gates**: How constitution’s “test-first” principle will be enforced at each stage.
6. **Deployment Readiness**: Any setup needed for local development and CI/CD hooks for quality gates.

Deliverable:
- A detailed implementation plan document in `plans/001-chatwait/plan.md`.
- The plan should be concrete enough to guide `/tasks` next.
```


Followup to refine the bad assumtions
```prompt
Your data model can be well aligned with Chat Completions API Schema.@data-model.md 

Rather than reimplementing the response and fields we can use most that are offered by openAI Agents SDK Framework:
@https://openai.github.io/openai-agents-python/ 

Some things like reconnecting to a stream are not offered by agents sdk. Understand the core frame work again first

https://openai.github.io/openai-agents-python/agents/
@https://openai.github.io/openai-agents-python/running_agents/ 
@https://openai.github.io/openai-agents-python/sessions/ 
@https://openai.github.io/openai-agents-python/results/ 
@https://openai.github.io/openai-agents-python/streaming/ 
```

Some more refinements:

```prompt
@research.md Here some assumptions are incorrect like here's how to use Gemini with Agents SDK:

<python>
import os
from dotenv import load_dotenv, find_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool

_: bool = load_dotenv(find_dotenv())

# ONLY FOR TRACING
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

# 1. Which LLM Service?
external_client: AsyncOpenAI = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 2. Which LLM Model?
llm_model: OpenAIChatCompletionsModel = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=external_client
)

@function_tool
def get_weather(city: str) -> str:
    """A simple function to get the weather for a user."""
    return f"The weather for {city} is sunny."


base_agent: Agent = Agent(
    name="WeatherAgent",
    instructions="You are a helpful assistant.",
    model=llm_model,
    tools=[get_weather]
)

new_agent: Agent = Agent(
    name="WeatherAgent",
    instructions="You are a helpful assistant.",
    model=llm_model,
    tools=[get_weather]
)

res = Runner.run_sync(base_agent, "What's the weather in Karachi?")
print(res)

# Now check the trace in 
</python>


<streaming>
    output = Runner.run_streamed(
        starting_agent=math_agent, 
        input="search for the best math tutor in my area",
        context=user_context
        )
    async for event in output.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)
</streaming>
```

```prompt
I want you to go through the implementation plan and implementation details, looking for areas that could
benefit from additional research as OpenAI Agents SDK is python first agentic framework relatively new. I want you to update the research document with additional details that we are going to be using and spawn parallel research tasks to clarify any details using research from the web. @data-model.md @research.md @plan.md 
```

### 5. /tasks

```prompt
/tasks Break the ChatWait plan into precise, test-first development tasks.  
Focus on building only what’s needed for the scoped MVP: `/chat/wait` and `/chat/streaming` endpoints, with a minimal Chainlit UI for demoing both modes.  
Each task must be small, testable, and directly linked to a requirement in the spec.  

Task Breakdown:

1. **Project Bootstrap**
   - Init UV project with Python 3.12  
   - Add deps: fastapi, uvicorn, agents-sdk, pytest, chainlit, ruff, mypy  
   - Add CI script for linting + tests

2. **Agent Integration**
   - Configure Gemini as llm with Agents SDK
   - Implement `ChatAgent`
   - Unit test: calling agent with “hello” returns proper Agents SDK response @https://openai.github.io/openai-agents-python/results/ 

3. **/chat/wait Endpoint**
   - Implement FastAPI route: POST `/chat/wait` → runs agent synchronously  using await Runner.run(starting_agent, input: str | [{}])
   - Return JSON payload aligned with Agents SDK schema  
   - Tests:  
     - Given input “hello”, response includes non-empty `content`  
     - Malformed request returns `400` with error JSON

4. **/chat/streaming Endpoint**
   - Implement SSE FastAPI route: POST `/chat/streaming` → token stream from agent  
   - Ensure connection can be retried/resumed  
   - Tests:  
     - Response yields multiple token events  
     - Drop/reconnect sim is handled without crash

5. **Minimal Chainlit UI**
   - Add UI with two modes: wait + streaming  
   - Smoke test: manual check that messages appear for both modes  

6. **Error & Resilience**
   - Define error schema (`{error: {code, message}}`)  
   - Unit tests for invalid payloads, unsupported endpoints, and forced disconnects  

7. **Docs & Extensibility Notes**
   - Update README with run + test instructions  
   - Add note on where session/history could be inserted in v2  

Deliverable:
- `tasks` containing  concrete, ordered tasks
- Each task linked to corresponding spec item, with tests listed alongside implementation
```

### 6. **Analyze Spec**: Use this to validate alignment with the constitution and catch contradictions.
```prompt
/analyze Validate the ChatWait specification against the constitution principles.  
	Check explicitly for:  
	- Async-first design compliance in both endpoints.  
	- Clear separation between UI, agent logic, and API layer.  
	- Test-first enforceability: are specs testable as written?  
	- Security: confirm that no secrets or keys could be exposed in responses.  
	- Extensibility: verify that new endpoints or features can be added without breaking existing behavior.  

	Highlight inconsistencies, potential violations, or unclear areas.  
```

```prompt
Now I want you to go and audit the implementation plan and the implementation detail files. Read through it with an eye on determining whether or not there is a sequence of tasks that you need to be doing that are obvious from reading this. Because I don't know if there's enough here. For example, when I look at the core implementation, it would be useful to reference the appropriate places in the implementation details where it can find the information as it walks through each step in the core implementation or in the refinement.
```

So I got a few must do points - this can save a lot of time after implementation. Gave another prompt for summary

```prompt
Can you summarize the missing parts so we can get right context to update them.
```

LLM RESPONSE="""
Based on my analysis of the ChatWait implementation plan, here are the **critical gaps** that need to be addressed for successful implementation:

1. **SDK Integration Setup Sequence**
**Missing Tasks:**
- Environment variable validation (API keys, endpoints)
- AsyncOpenAI client initialization with proper error handling
- OpenAIChatCompletionsModel configuration and testing
- Agent creation with validation
- SDK connection testing

**Current Gap:** T015-T017 are too vague - "Configure Gemini LLM" and "Implement ChatAgent" don't provide step-by-step implementation details.

2. **Streaming Implementation Sequence** 
**Missing Tasks:**
- FastAPI SSE endpoint structure setup
- SDK streaming event processing (`ResponseTextDeltaEvent` handling)
- Response formatting with token counting
- Connection lifecycle management (connect/disconnect/cleanup)
- Error event streaming to clients

**Current Gap:** T019 assumes developers know how to bridge SDK streaming to FastAPI SSE without explicit guidance.

3. **Application Bootstrap Sequence**
**Missing Tasks:**
- FastAPI application factory setup
- Middleware configuration (CORS, logging, validation)
- Dependency injection container setup
- Health check endpoint implementation
- Application startup/shutdown lifecycle

**Current Gap:** No explicit tasks for core FastAPI application setup.

🔧 **MEDIUM PRIORITY MISSING DETAILS**
...
 📋 **SPECIFIC IMPLEMENTATION DETAILS MISSING**
...

🎯 **IMPACT ASSESSMENT**

**Without these additions:**
- ✅ 60% of tasks are well-defined and actionable
- ❌ 40% require "figuring it out" - major implementation sequences missing
- ❌ SDK integration would fail without proper setup sequence
- ❌ Streaming would not work without event processing details
- ❌ Production deployment would be impossible without middleware setup

"""


This is follow up prompt:

```prompt
1. T015-T017 are too vague - "Configure Gemini LLM" and "Implement ChatAgent" don't provide step-by-step implementation details.

Here is relevant guide:

"""
# Setup Project and Install dependencies:
# uv init 
# uv add openai-agents
# Create .env file and add the following variables:
# GEMINI_API_KEY=your_gemini_api_key
# Create main.py file and add the following code:
#  0. Importing the necessary libraries
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI

import os
from dotenv import load_dotenv, find_dotenv

# 0.1. Loading the environment variables
load_dotenv(find_dotenv())

# 1. Which LLM Provider to use? -> Google Chat Completions API Service
external_client: AsyncOpenAI = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 2. Which LLM Model to use?
llm_model: OpenAIChatCompletionsModel = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=external_client
)

# 3. Creating the Agent
agent: Agent = Agent(name="Assistant", model=llm_model)

# 4. Running the Agent
result = Runner.run_sync(starting_agent=agent, input="Welcome and motivate me to learn Agentic AI")

print("AGENT RESPONSE: " , result.final_output)
"""

2. We can just create a function that yields and connect to FastAPI streamer - here's a sample referece that we can refactor to keep it simple and effective

"""
    @router.post("/stream")
    async def stream_agent(request: AgentRequest):
        """
        Stream agent responses with events and automatic session support.
        
        Automatically uses session memory if:
        - ENABLE_SESSIONS=true in environment  
        - session_id is provided in request
        """
        async def generate_stream() -> AsyncGenerator[str, None]:
            try:
                # Automatically create session if enabled and session_id provided
                session = create_session_if_enabled(request.session_id)
                if session:
                    logger.info(f"Using session memory for streaming: {request.session_id}")
                
                stream_result = Runner.run_streamed(
                    starting_agent=agent,
                    input=request.input,
                    context=request.context,
                    session=session
                )
                
                async for event in stream_result.stream_events():
                    # Process each event type with proper serialization
                    formatted_event = _format_stream_event(event, logger)
                    if formatted_event:
                        yield f"data: {json.dumps(formatted_event)}\n\n"
                
                # Send completion event
                completion_event = {
                    "type": "stream_complete",
                    "final_output": stream_result.final_output,
                    "current_turn": stream_result.current_turn,
                    "usage": _extract_usage_info(stream_result) if hasattr(stream_result, 'usage') else None,
                    "session_id": request.session_id
                }
                yield f"data: {json.dumps(completion_event)}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                error_event = {
                    "type": "error", 
                    "message": str(e),
                    "timestamp": str(logger.info.__self__.makeRecord("", 0, "", 0, "", (), None).created),
                    "session_id": request.session_id if hasattr(request, 'session_id') else None
                }
                yield f"data: {json.dumps(error_event)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
"""



Chainlit can connect and call these endpoints at start of session we can generate id and use it
```

### 7. Execute tasks sequentially: lean on `/implement` for automated execution or drive the SDD loop manually (RED → GREEN → REFACTOR → EXPLAIN).

We can just ask it to implement - here we will expirement by giving agent escalation options to reach out to use when implementing

Here’s the refined /implement prompt with built-in escalation options:

```prompt
/implement Begin the @001-develop-a-scoped/  implementation, following the validated tasks and constitution.  
Work in small, test-first increments. Complete one task at a time, and commit before moving to the next.  

### Core Rules
- **Test-First**: write a test for each requirement before writing implementation code.  
- **Async-First**: all FastAPI routes and SDK calls must be async unless the SDK forces sync.  
- **Separation of Concerns**: keep UI (Chainlit), API (FastAPI), and Agent Logic (Agents SDK + Gemini) in distinct modules.  
- **Security**: never expose API keys in logs or responses. Use `.env` for secrets.  
- **Extensibility**: design endpoints so that new features (sessions, history, integrations) can be added without breaking current APIs.  

### Implementation Flow
1. Bootstrap project with UV + FastAPI + Agents SDK + Chainlit.  
2. Implement Gemini integration via `AsyncOpenAI` + `OpenAIChatCompletionsModel`.  
3. Implement `ChatAgent` wrapper.  
4. Add `/chat/wait` endpoint with synchronous run.  
5. Add `/chat/streaming` endpoint with SSE + reconnect logic.  
6. Connect Chainlit frontend with both endpoints.  
7. Add error handling schema + resilience tests.  
8. Finalize docs and extensibility notes.  

### Escalation Rules
If ambiguity or conflict arises:  
1. **Unclear SDK behavior** → pause and ask how to proceed (e.g., session memory, streaming gaps).  
2. **Conflict with Constitution** (e.g., sync helpers vs async requirement) → propose alternatives and wait for approval.  
3. **Missing spec detail** → ask for clarification (e.g., exact error schema, streaming reconnection strategy).  
4. **Test-first unclear** → propose a test contract before coding.  
5. **Major milestone** (agent integration, streaming endpoint, Chainlit UI) → checkpoint with summary + wait for go-ahead.  

### Expected Output
- Progressive implementation of `src/` code + `tests/`.  
- Each commit message maps directly to the completed task (e.g., `feat: add /chat/wait endpoint`).  
- Ask clarifying questions instead of making assumptions.  
- Deliver runnable, tested artifacts that conform to the constitution.  
```

Test and Iterate - so it stopped after each core implementation for review. I ran the code and reported bugs with enough context for solution - I was not trusting with it to figure out the solution on its own without my knowledge and this worked better.

### 8. Prepare a final PR or release note summarizing outcomes, metrics, and follow-up work.

## Deliverables

- Working chatbot implementation in your repo
- Updated spec, plan, tasks marked as “Completed” with references to commits/PRs
- Lessons learned feeding into continuous practices (see Steps 8–10)

## Quality Gates ✅

- CI pipeline (lint, tests, evaluations) passes without manual intervention
- PR reviewers confirm traceability to spec sections and constitution rules
- Post-release checklist completed (monitoring, rollback plan, known issues)

## Common Pitfalls

- Attempting too large a scope for the capstone; start with a single endpoint and iterate
- Skipping evaluation harnesses—chatbots need behavior tests, not just unit tests
- Neglecting to document learnings and follow-up tasks after the project wraps

## References

- Spec Kit repo: https://github.com/github/spec-kit
- Microsoft Dev Blog: https://developer.microsoft.com/blog/spec-driven-development-spec-kit
