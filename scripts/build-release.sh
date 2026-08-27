#!/bin/sh

set -eu

script_directory=$(
  CDPATH=
  cd "$(dirname "$0")"
  pwd
)
repository_root=$(dirname "$script_directory")
version=$(sed -n '1p' "$repository_root/VERSION")
installer_version=$(sed -n 's/^NOVA_INSTALL_VERSION=//p' "$repository_root/install.sh")

[ "$version" = "$installer_version" ] || {
  printf 'VERSION and install.sh do not match\n' >&2
  exit 1
}

[ -z "$(git -C "$repository_root" status --porcelain --untracked-files=normal)" ] || {
  printf 'repository must be clean before building release assets\n' >&2
  exit 1
}

output_directory=$repository_root/dist
archive_name=nova-v$version.tar.gz
archive_path=$output_directory/$archive_name
checksum_path=$archive_path.sha256
installer_path=$output_directory/install.sh

mkdir -p "$output_directory"
rm -f "$archive_path" "$checksum_path" "$installer_path"

git -C "$repository_root" archive \
  --format=tar.gz \
  --prefix="nova-v$version/" \
  --output="$archive_path" \
  HEAD

archive_listing=$output_directory/.archive-listing.$$
cleanup() {
  rm -f "$archive_listing"
}
trap cleanup EXIT HUP INT TERM

tar -tzf "$archive_path" > "$archive_listing"

for required_path in \
  "nova-v$version/AGENTS.md" \
  "nova-v$version/bin/nova-safety" \
  "nova-v$version/config.yaml" \
  "nova-v$version/.githooks/pre-commit" \
  "nova-v$version/.githooks/pre-push" \
  "nova-v$version/hooks/nova_context.sh" \
  "nova-v$version/skills/update-nova/SKILL.md"
do
  grep -Fx "$required_path" "$archive_listing" >/dev/null || {
    printf 'release archive is missing %s\n' "$required_path" >&2
    exit 1
  }
done

if grep -Fx "nova-v$version/.nova-public-source" "$archive_listing" >/dev/null; then
  printf 'release archive contains the public-source marker\n' >&2
  exit 1
fi

for excluded_path in .github scripts tests; do
  if grep -F "nova-v$version/$excluded_path/" "$archive_listing" >/dev/null; then
    printf 'release archive contains development path: %s\n' "$excluded_path" >&2
    exit 1
  fi
done

if command -v sha256sum >/dev/null 2>&1; then
  checksum=$(sha256sum "$archive_path" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
  checksum=$(shasum -a 256 "$archive_path" | awk '{print $1}')
else
  printf 'sha256sum or shasum is required\n' >&2
  exit 1
fi

printf '%s  %s\n' "$checksum" "$archive_name" > "$checksum_path"
cp "$repository_root/install.sh" "$installer_path"

printf 'Release assets created in %s\n' "$output_directory"
printf '%s\n%s\n%s\n' "$installer_path" "$archive_path" "$checksum_path"
