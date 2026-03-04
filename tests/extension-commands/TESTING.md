# Testing Extension Commands

This directory contains a mock project to verify that LLM agents correctly identify and suggest custom extension commands defined in `.specify/extensions.yml`.

## The Test

1. Open a chat with an LLM (like GitHub Copilot) in this project.
2. Ask it what extension commands are available in this directory:
   > "What custom extension commands are available in this directory according to the `.specify/extensions.yml` file? Can you list them?"
3. **Expected Behavior**:
   - The LLM should read `.specify/extensions.yml` and identify the two custom commands: `/ext.lint` and `/ext.deploy`.
   - It should list their descriptions and prompts.

4. Next, test its comprehension of executing a command:
   > "Please pretend to execute `/ext.lint`."
5. **Expected Behavior**:
   - The LLM should output that it is executing the command, simulating output similar to `EXECUTE_COMMAND: ext.lint`.
   - Since it's an LLM, it might playfully simulate fixing imaginary formatting in `main.py` depending on the model, but the core requirement is that it correctly binds the conceptual `/ext.lint` string to the `custom_lint` object in yaml.

## Validation Goals
This playground ensures that AI Agents, which do not run strict compiled Spec Kit binaries, can still integrate with the broader extension ecosystem natively just by reading the `.specify/` configuration maps.
