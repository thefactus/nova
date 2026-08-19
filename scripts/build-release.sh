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
