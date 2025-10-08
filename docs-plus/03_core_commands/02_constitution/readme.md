# **Step 2: Create the Project Rulebook - The [Constitution](https://github.com/panaversity/spec-kit-plus/blob/main/spec-driven.md#the-constitutional-foundation-enforcing-architectural-discipline)!**

**Goal:** document the non-negotiable principles that every spec, plan, and task must honor.

## **Purpose: What is a Constitution?**

Imagine you and your computer helper are a team building a giant LEGO castle. Before you start, you need to agree on some rules so you don't mess things up.

*   What if you want all the towers to be **square**, but your helper starts building **round** ones?
*   What if you decide the roof must be **blue**, but your helper builds a **red** one?

That would be a mess!

The **Constitution** is your team's **Rulebook**. It lists the most important rules that both you and your computer helper **MUST** follow, no matter what. It makes sure you both build the project the exact same way, every single time.

## **Best Practices: What Rules Go in the Rulebook?**

Your rulebook shouldn't be a thousand pages long. It should only have the most important, "non-negotiable" rules. Think about these questions:

*   **How will we know it works?**
    *   *Good Rule:* "Every part we build must have a special check (a test) to make sure it's not broken."
    *   *Bad Rule:* "Try to make it good." (This is too vague!)

*   **What should it look like?**
    *   *Good Rule:* "We will always use bright, happy colors and the 'Comic Sans' font."
    *   *Good Rule:* "We will build it with these special 'NextJS' LEGO bricks."

*   **How will we keep it safe?**
    *   *Good Rule:* "We will never write down secret passwords inside our project."

*   **How will we work together?**
    *   *Good Rule:* "We will only build in small pieces at a time, not one giant chunk."

You write these rules down so your computer helper can read them and never forget them. It helps the AI build exactly what you want, in the style you want, and keeps your project strong and safe.

## Your Hands-On Plan

Setup a new project `sp init hello_spp` and follow along:

1.  **Ask your helper to write the first draft.**
    *   In your agent chat, running `/sp.constitution` is like asking your helper, "Can you start a new rulebook for us?"

2.  **Tell your helper what kind of project you're making.**
    *   When you run the prompt: `/sp.constitution Fill the constitution with the bare minimum requirements for a static web app based on the template. We use NextJS15...`, you're telling the AI, "Okay, the game we're playing is 'Website Building'. Let's write down the basic rules for that game, using these specific LEGO pieces."

3.  **Be the Boss: Check the Rules.**
    *   Your computer helper is smart, but you're the boss. Open the `constitution.md` file and read the rules it wrote. Do they make sense? Is anything missing? You can change, add, or remove any rule you want.

4.  **Save Your Rulebook.**
    *   "Committing the first version as v1.0" is like taking a picture of your finished rulebook and labeling it "Version 1." This way, your whole team knows which rules to follow, and you can always look back to see how the rules have changed over time.

### Inputs

- The generated `.specify/memory/constitution.md`
- Any existing engineering guardrails (testing policy, security requirements, coding standards)
- Stakeholder alignment on mandatory practices

### Actions

1. In your agent chat, run `/sp.constitution` to generate or update the baseline document.

2. Now we have to update the constitution.md file. You can use AI Agent Tool; Prompt:
```
/sp.constitution Fill the constitution with the bare minimum requirements for a static web app based on the template. We use NextJS15 React19, Tailwind CSS and ShadCN components. 
```

3. Open `.specify/memory/constitution.md` and review generated rules.
4. Commit the first version as `v1.0`.

### Deliverables

- Canonical constitution stored in Git and referenced by every downstream artifact

## Common Pitfalls

- Writing vague aspirations (“write clean code”) instead of enforceable rules
- Allowing the constitution to drift from reality—review it alongside major releases
- Leaving the file outside version control (loses traceability)

## References

- Spec Kit Plus repo: https://github.com/panaversity/spec-kit-plus
- PyPI package: https://pypi.org/project/specifyplus/
- Original GitHub Spec Kit repo: https://github.com/github/spec-kit
- Microsoft Dev Blog (Spec Kit intro): https://developer.microsoft.com/blog/spec-driven-development-spec-kit
- The ONLY guide you'll need for GitHub Spec Kit: https://www.youtube.com/watch?v=a9eR1xsfvHg