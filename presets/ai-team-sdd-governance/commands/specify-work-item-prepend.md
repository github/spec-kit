## AI Team work item

Treat `coding_issue_url` as the primary coding issue when present. Accept
`also_resolves_issue_urls` only when the linked issues describe different
symptoms of the same root-cause change. Confidential features may instead use
the allowed `handoff_requirement_url`.

Ensure the generated `spec.md` contains a concise **Work Items** section with
the primary issue or handoff requirement and any also-resolved coding issues.
Do not copy private demand into the public specification. Every linked issue
must later map to separate reproduction or acceptance evidence.
