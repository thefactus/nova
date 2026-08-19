#!/bin/sh

case "${1:-}" in
  session-start)
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"Nova operating check:\n- Read memories/USER.md and memories/MEMORY.md before substantive work.\n- Review skill names and descriptions under skills/. Load a complete SKILL.md only when it clearly matches the task.\n- Use second_brain/ only when deeper project history or decisions are needed.\n- Keep durable knowledge in canonical Nova files."}}'
    ;;
  prompt-submit)
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"Nova skill-routing check:\n1. Review skills/ for clearly relevant procedures before substantive work.\n2. Load each relevant SKILL.md completely.\n3. If no skill applies, proceed normally. Do not force a weak match.\n4. After non-trivial work, classify durable learning as none, memory, project knowledge, skill improvement, or new-skill proposal."}}'
    ;;
esac
