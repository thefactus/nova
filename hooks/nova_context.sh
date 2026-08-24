#!/bin/sh

skill_index_path=.runtime/skill-index.md

build_skill_index() {
  mkdir -p .runtime || return 0
  temporary_index=.runtime/skill-index.$$.tmp

  {
    printf '%s\n\n' '# Nova skill index'

    for skill_file in skills/*/SKILL.md; do
      [ -f "$skill_file" ] || continue

      skill_name=$(
        awk '
          /^---[[:space:]]*$/ { boundary += 1; next }
          boundary == 1 && /^name:[[:space:]]*/ {
            value = $0
            sub(/^name:[[:space:]]*/, "", value)
            if (value ~ /^".*"$/ || value ~ /^'\''.*'\''$/) {
              value = substr(value, 2, length(value) - 2)
            }
            print value
            exit
          }
          boundary > 1 { exit }
        ' "$skill_file"
      )
      skill_description=$(
        awk '
          /^---[[:space:]]*$/ { boundary += 1; next }
          boundary == 1 && /^description:[[:space:]]*/ {
            value = $0
            sub(/^description:[[:space:]]*/, "", value)
            if (value ~ /^".*"$/ || value ~ /^'\''.*'\''$/) {
              value = substr(value, 2, length(value) - 2)
            }
            print value
            exit
          }
          boundary > 1 { exit }
        ' "$skill_file"
      )

      if [ -n "$skill_name" ] && [ -n "$skill_description" ]; then
        printf -- '- `%s`: %s (`%s`)\n' \
          "$skill_name" "$skill_description" "$skill_file"
      fi
    done
  } > "$temporary_index" || {
    rm -f "$temporary_index"
    return 0
  }

  mv "$temporary_index" "$skill_index_path"
}

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
    printf '%s' 'skills.write_approval=true; stage justified Nova skill updates and creations for owner review'
  else
    printf '%s' 'skills.write_approval=false; apply justified Nova skill updates and creations autonomously'
  fi
}

case "${1:-}" in
  session-start)
    build_skill_index
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"Nova operating check:\n- Read memories/USER.md and memories/MEMORY.md before substantive work.\n- Use .runtime/skill-index.md to find applicable Nova skills, then load only their canonical SKILL.md files.\n- Nova skills are additive; global, project, plugin, and built-in skills may remain available.\n- Read config.yaml before creating or modifying skills.\n- Use second_brain/ only when deeper project history or decisions are needed.\n- Keep durable knowledge in canonical Nova files."}}'
    ;;
  prompt-submit)
    active_policy=$(skill_write_policy)
    printf '%s%s%s\n' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"Nova skill-routing check:\n1. Use .runtime/skill-index.md to identify relevant Nova skills.\n2. Load each relevant SKILL.md completely.\n3. After non-trivial work, actively review corrections, missing steps, and repeated workflows for durable skill learning. Do not stop at classification.\n4. If no skill applies or no durable learning exists, proceed normally. Active skill policy: ' "$active_policy" '."}}'
    ;;
esac
