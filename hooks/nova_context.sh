#!/bin/sh

skill_write_policy() {
  write_approval=false

  if [ -f config.yaml ]; then
    configured_line=$(
      awk '
        /^[[:space:]]*skills:[[:space:]]*($|#)/ { in_skills = 1; next }
        in_skills && /^[^[:space:]#]/ { in_skills = 0 }
        in_skills && /^[[:space:]]+write_approval:[[:space:]]*/ {
          print
          exit
        }
      ' config.yaml
    )

    if [ -n "$configured_line" ]; then
      configured_value=$(
        printf '%s\n' "$configured_line" | awk '
          {
            sub(/^[[:space:]]+write_approval:[[:space:]]*/, "")
            sub(/[[:space:]#].*$/, "")
            print
          }
        '
      )
      normalized_value=$(printf '%s' "$configured_value" | tr '[:upper:]' '[:lower:]')

      case "$normalized_value" in
        true|yes|on) write_approval=true ;;
        false|no|off) write_approval=false ;;
        *) write_approval=true ;;
      esac
    fi
  fi

  if [ "$write_approval" = true ]; then
    printf '%s' 'skills.write_approval=true; stage canonical skill writes for owner review'
  else
    printf '%s' 'skills.write_approval=false; apply justified canonical skill creations and updates autonomously'
  fi
}

case "${1:-}" in
  session-start)
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"Nova operating check:\n- Read memories/USER.md and memories/MEMORY.md before substantive work.\n- Review skill names and descriptions under skills/. Load a complete SKILL.md only when it clearly matches the task.\n- Read config.yaml before creating or modifying skills.\n- Use second_brain/ only when deeper project history or decisions are needed.\n- Keep durable knowledge in canonical Nova files."}}'
    ;;
  prompt-submit)
    active_policy=$(skill_write_policy)
    printf '%s%s%s\n' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"Nova skill-routing check:\n1. Review skills/ for clearly relevant procedures before substantive work.\n2. Load each relevant SKILL.md completely.\n3. If no skill applies, proceed normally. Do not force a weak match.\n4. After non-trivial work, classify durable learning. Active skill policy: ' "$active_policy" '."}}'
    ;;
esac
