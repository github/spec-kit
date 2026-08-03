---
description: "Override of the myext extension's myextcmd command"
---

<!-- Preset override for speckit.myext.myextcmd -->

You are following a customized version of the myext extension's myextcmd command.

When executing this command:

1. Read the user's input from $ARGUMENTS
2. Follow the standard myextcmd workflow
3. Additionally, apply the following customizations from this preset:
   - Add compliance checks before proceeding
   - Include audit trail entries in the output

> CUSTOMIZE: Replace the instructions above with your own.
> This file overrides the command that the "myext" extension provides.
> When this preset is installed, all agents (Claude, Gemini, Copilot, etc.)
> will use this version instead of the extension's original.
