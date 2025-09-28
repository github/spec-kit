# Create plan for specific prompt

## Variables

RESEARCH_NOTES: $ARGUMENTS

## Execute

Analyze $RESEARCH_NOTES to understand the feature requirements, use cases, and researched knowledge.

For large features, create multiple plan files - each implementing a self-contained, testable component.
Within each plan, do not include any assumptions or speculations. Include only specific instructions and code snippets of what exactly needs to be implemented.

Each plan must include:
- Relevant resources (code snippets, links, research notes from $RESEARCH_NOTES)
- Specific implementation instructions without assumptions
- Exact code to be implemented

Before adding to the plan, verify functionality doesn't already exist in the codebase.

File organization:
1. Check existing specs for highest prefix number, increment by 10
2. Create folder: `./specs/XXX-<feature-name>/`
3. Name plans: `XXX-<feature-name>-<part-number>.md`
4. Part numbers indicate implementation order
