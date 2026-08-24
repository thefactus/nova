#!/bin/sh

skill_index_path=.runtime/skill-index.md
learning_state_directory=.runtime/learning
learning_lock_directory=$learning_state_directory/lock
turn_count_path=$learning_state_directory/turn-count
action_count_path=$learning_state_directory/action-count
review_due_path=$learning_state_directory/review-due
update_state_directory=.runtime/update-check
update_checked_at_path=$update_state_directory/checked-at
update_latest_version_path=$update_state_directory/latest-version
nova_release_api_url=${NOVA_RELEASE_API_URL:-https://api.github.com/repos/thefactus/nova/releases/latest}

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

update_config_value() {
  requested_key=$1

  [ -f config.yaml ] || return 0

  awk -v requested_key="$requested_key" '
    /^[[:space:]]*updates:[[:space:]]*($|#)/ {
      in_updates = 1
      next
    }
    in_updates && /^[^[:space:]#]/ {
      in_updates = 0
    }
    in_updates {
      pattern = "^[[:space:]]{2}" requested_key ":[[:space:]]*"
      if ($0 ~ pattern) {
        value = $0
        sub(pattern, "", value)
        sub(/[[:space:]#].*$/, "", value)
        print value
        exit
      }
    }
  ' config.yaml
}

load_update_config() {
  update_check_on_startup=true
  update_check_interval_hours=24

  configured_check=$(update_config_value check_on_startup)
  normalized_check=$(printf '%s' "$configured_check" | tr '[:upper:]' '[:lower:]')

  case "$normalized_check" in
    '') ;;
    true|yes|on) update_check_on_startup=true ;;
    false|no|off) update_check_on_startup=false ;;
    *) update_check_on_startup=false ;;
  esac

  configured_interval=$(update_config_value check_interval_hours)
  case "$configured_interval" in
    '') ;;
    *[!0-9]*|0) ;;
    *) update_check_interval_hours=$configured_interval ;;
  esac
}

valid_semver() {
  printf '%s\n' "$1" | awk '
    BEGIN { valid = 0 }
    /^[0-9]+\.[0-9]+\.[0-9]+$/ { valid = 1 }
    END { exit valid ? 0 : 1 }
  '
}

newer_semver() {
  candidate_version=$1
  current_version=$2

  awk -v candidate="$candidate_version" -v current="$current_version" 'BEGIN {
    split(candidate, candidate_parts, ".")
    split(current, current_parts, ".")
    for (part_index = 1; part_index <= 3; part_index += 1) {
      if ((candidate_parts[part_index] + 0) > (current_parts[part_index] + 0)) exit 0
      if ((candidate_parts[part_index] + 0) < (current_parts[part_index] + 0)) exit 1
    }
    exit 1
  }'
}

fetch_latest_release_version() {
  command -v curl >/dev/null 2>&1 || return 1

  release_response=$(
    curl -fsSL --connect-timeout 1 --max-time 2 "$nova_release_api_url" 2>/dev/null
  ) || return 1

  latest_release_version=$(
    printf '%s\n' "$release_response" | sed -n \
      's/.*"tag_name":[[:space:]]*"v\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)".*/\1/p' |
      sed -n '1p'
  )

  valid_semver "$latest_release_version" || return 1
  printf '%s' "$latest_release_version"
}

refresh_update_cache_when_due() {
  current_timestamp=$(date +%s 2>/dev/null) || return 1
  cache_is_fresh=false
  checked_at=

  if [ -f "$update_checked_at_path" ]; then
    IFS= read -r checked_at < "$update_checked_at_path"
  fi

  case "$checked_at" in
    ''|*[!0-9]*) ;;
    *)
      cache_age=$((current_timestamp - checked_at))
      cache_interval=$((update_check_interval_hours * 3600))
      if [ "$cache_age" -ge 0 ] && [ "$cache_age" -lt "$cache_interval" ]; then
        cache_is_fresh=true
      fi
      ;;
  esac

  [ "$cache_is_fresh" = false ] || return 0
  mkdir -p "$update_state_directory" || return 1

  temporary_checked_at=$update_checked_at_path.$$.tmp
  printf '%s\n' "$current_timestamp" > "$temporary_checked_at" || return 1
  mv "$temporary_checked_at" "$update_checked_at_path" || return 1

  if fetched_version=$(fetch_latest_release_version); then
    temporary_latest_version=$update_latest_version_path.$$.tmp
    printf '%s\n' "$fetched_version" > "$temporary_latest_version" || return 1
    mv "$temporary_latest_version" "$update_latest_version_path" || return 1
  else
    rm -f "$update_latest_version_path"
  fi
}

check_for_nova_update() {
  installed_update_version=
  available_update_version=
  load_update_config
  [ "$update_check_on_startup" = true ] || return 1
  [ -f VERSION ] || return 1

  IFS= read -r installed_update_version < VERSION
  valid_semver "$installed_update_version" || return 1
  refresh_update_cache_when_due || return 1
  [ -f "$update_latest_version_path" ] || return 1
  IFS= read -r available_update_version < "$update_latest_version_path"
  valid_semver "$available_update_version" || return 1
  newer_semver "$available_update_version" "$installed_update_version"
}

periodic_review_value() {
  requested_key=$1

  [ -f config.yaml ] || return 0

  awk -v requested_key="$requested_key" '
    /^[[:space:]]*learning:[[:space:]]*($|#)/ {
      in_learning = 1
      in_periodic_review = 0
      next
    }
    in_learning && /^[^[:space:]#]/ {
      in_learning = 0
      in_periodic_review = 0
    }
    in_learning && /^[[:space:]]{2}periodic_review:[[:space:]]*($|#)/ {
      in_periodic_review = 1
      next
    }
    in_periodic_review && /^[[:space:]]{2}[^[:space:]#]/ {
      in_periodic_review = 0
    }
    in_periodic_review {
      pattern = "^[[:space:]]{4}" requested_key ":[[:space:]]*"
      if ($0 ~ pattern) {
        value = $0
        sub(pattern, "", value)
        sub(/[[:space:]#].*$/, "", value)
        print value
        exit
      }
    }
  ' config.yaml
}

load_periodic_review_config() {
  periodic_review_enabled=true
  periodic_turn_interval=10
  periodic_action_interval=15

  configured_enabled=$(periodic_review_value enabled)
  normalized_enabled=$(printf '%s' "$configured_enabled" | tr '[:upper:]' '[:lower:]')

  case "$normalized_enabled" in
    '') ;;
    true|yes|on) periodic_review_enabled=true ;;
    false|no|off) periodic_review_enabled=false ;;
    *) periodic_review_enabled=false ;;
  esac

  configured_turn_interval=$(periodic_review_value turn_interval)
  case "$configured_turn_interval" in
    '') ;;
    *[!0-9]*|0) ;;
    *) periodic_turn_interval=$configured_turn_interval ;;
  esac

  configured_action_interval=$(periodic_review_value action_interval)
  case "$configured_action_interval" in
    '') ;;
    *[!0-9]*|0) ;;
    *) periodic_action_interval=$configured_action_interval ;;
  esac
}

read_counter() {
  counter_path=$1
  counter_value=0

  if [ -f "$counter_path" ]; then
    IFS= read -r counter_value < "$counter_path"
  fi

  case "$counter_value" in
    ''|*[!0-9]*) counter_value=0 ;;
  esac

  printf '%s' "$counter_value"
}

write_counter() {
  counter_path=$1
  counter_value=$2
  temporary_counter=$counter_path.$$.tmp

  printf '%s\n' "$counter_value" > "$temporary_counter" || return 1
  mv "$temporary_counter" "$counter_path"
}

release_learning_lock() {
  lock_owner=
  if [ -f "$learning_lock_directory/owner" ]; then
    IFS= read -r lock_owner < "$learning_lock_directory/owner"
  fi

  if [ "$lock_owner" = "$$" ]; then
    rm -f "$learning_lock_directory/owner"
    rmdir "$learning_lock_directory" 2>/dev/null || true
  fi
}

acquire_learning_lock() {
  mkdir -p "$learning_state_directory" || return 1
  lock_attempts=0

  while ! mkdir "$learning_lock_directory" 2>/dev/null; do
    if [ -f "$learning_lock_directory/owner" ]; then
      IFS= read -r lock_owner < "$learning_lock_directory/owner"
      case "$lock_owner" in
        ''|*[!0-9]*) ;;
        *)
          if ! kill -0 "$lock_owner" 2>/dev/null; then
            rm -f "$learning_lock_directory/owner"
            rmdir "$learning_lock_directory" 2>/dev/null || true
            continue
          fi
          ;;
      esac
    fi

    lock_attempts=$((lock_attempts + 1))
    [ "$lock_attempts" -lt 40 ] || return 1
    sleep 0.05
  done

  printf '%s\n' "$$" > "$learning_lock_directory/owner" || {
    rmdir "$learning_lock_directory" 2>/dev/null || true
    return 1
  }

  trap release_learning_lock EXIT
  trap 'exit 1' HUP INT TERM
}

record_periodic_turn() {
  periodic_review_due=false
  load_periodic_review_config
  [ "$periodic_review_enabled" = true ] || return 0
  acquire_learning_lock || return 0

  current_turn_count=$(read_counter "$turn_count_path")
  write_counter "$turn_count_path" "$((current_turn_count + 1))" || true

  if [ -f "$review_due_path" ]; then
    periodic_review_due=true
    rm -f "$review_due_path"
  fi

  release_learning_lock
  trap - EXIT HUP INT TERM
}

record_periodic_action() {
  load_periodic_review_config
  [ "$periodic_review_enabled" = true ] || return 0
  acquire_learning_lock || return 0

  current_action_count=$(read_counter "$action_count_path")
  write_counter "$action_count_path" "$((current_action_count + 1))" || true

  release_learning_lock
  trap - EXIT HUP INT TERM
}

mark_periodic_review_when_due() {
  load_periodic_review_config
  [ "$periodic_review_enabled" = true ] || return 0
  acquire_learning_lock || return 0

  current_turn_count=$(read_counter "$turn_count_path")
  current_action_count=$(read_counter "$action_count_path")

  if [ "$current_turn_count" -ge "$periodic_turn_interval" ] || \
     [ "$current_action_count" -ge "$periodic_action_interval" ]; then
    : > "$review_due_path"
    write_counter "$turn_count_path" 0 || true
    write_counter "$action_count_path" 0 || true
  fi

  release_learning_lock
  trap - EXIT HUP INT TERM
}

case "${1:-}" in
  session-start)
    build_skill_index
    if check_for_nova_update; then
      update_context='\n\nNova update available: '"$installed_update_version"' -> '"$available_update_version"'.\nTell the owner once in your first response that their current Nova is '"$installed_update_version"', version '"$available_update_version"' is available, and they can ask you to update it. Do not update automatically.'
    else
      update_context=
    fi
    printf '%s%s%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"Nova operating check:\n- Read memories/USER.md and memories/MEMORY.md before substantive work.\n- Use .runtime/skill-index.md to find applicable Nova skills, then load only their canonical SKILL.md files.\n- Nova skills are additive; global, project, plugin, and built-in skills may remain available.\n- Read config.yaml before creating or modifying skills.\n- Use second_brain/ only when deeper project history or decisions are needed.\n- Keep durable knowledge in canonical Nova files.' "$update_context" '"}}'
    ;;
  prompt-submit)
    record_periodic_turn
    active_policy=$(skill_write_policy)
    if [ "$periodic_review_due" = true ]; then
      periodic_review_context='\n6. Periodic learning review is due. During this turn, inspect recent completed work for durable corrections, missing skill steps, or an uncovered repeated workflow. Apply the smallest justified Nova-owned change under the active policy; if there is no durable learning, make no change.'
    else
      periodic_review_context=
    fi
    printf '%s%s%s%s%s\n' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"Nova skill-routing check:\n1. Use .runtime/skill-index.md to identify relevant Nova skills.\n2. Load each relevant SKILL.md completely.\n3. After non-trivial work, actively review corrections, missing steps, and repeated workflows for durable skill learning. Do not stop at classification.\n4. If no skill applies or no durable learning exists, proceed normally. Active skill policy: ' "$active_policy" '.\n5. After non-trivial work that changes canonical Nova files, create a focused local commit for attributable task changes after verification. Leave unrelated changes untouched; never publish without explicit authorization.' "$periodic_review_context" '"}}'
    ;;
  post-tool-use)
    record_periodic_action
    ;;
  stop)
    mark_periodic_review_when_due
    ;;
esac
