# Global Directives

## Output
- Zero emojis anywhere: chat, code, comments, commit messages, docs, UI strings, logs.
- Never add gratituous text (including unnecessary punctuation, headers and footers) or eyebrow elements to UI, ever. They're annoying and ugly.

## Project Plan
- Before project planning, implementation, training, evaluation, or reporting, read [the agreed project plan](tutorial/project-plan.html) and follow its scope, experiment controls, stages, and success criteria.
- Keep early-check decisions open until supported by the planned checks. Do not treat suggested budgets or expert-data amounts as settled settings.
- Later explicit user instructions take precedence. When the user changes an agreed project decision, update the HTML plan to keep it current.
- Use saved results and executed checks as evidence of progress. Checkbox state is browser-local and is not shared proof of completed work.

## Anti-loop
- Same fix fails 2x → STOP. List attempts, re-diagnose root cause, switch strategy or ask.
- Never rerun identical failing command. Before any retry: 1-line hypothesis why prior attempt failed.

## Anti-guess
- Unsure of API/signature/flag/config key → verify in source, types, or docs. Never invent.
- Ambiguity that changes outcome → state chosen interpretation in 1 line, then proceed.

## Root cause only
- Forbidden "fixes": error suppression (empty catch, ignore flags), type escapes (`any`, casts), skipping/deleting failing tests, hardcoding outputs to satisfy checks, lint-disable comments. Symptom patch ≠ fix.

## Proof
- Claim "done"/"fixed" ONLY with executed verification (test/build/run) + output shown. Otherwise label "unverified".

## Secrets
- Never commit secrets, .env, credentials, tokens. Scan diff before every commit.

## Compaction
- When compacting, preserve: modified-file list, approaches already tried and failed, active test commands.
