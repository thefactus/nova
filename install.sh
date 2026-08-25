#!/bin/sh

set -eu
umask 077

NOVA_INSTALL_VERSION=0.1.6
NOVA_RELEASE_BASE_URL=${NOVA_RELEASE_BASE_URL:-https://github.com/thefactus/nova/releases/download}

fail() {
  printf 'Nova installer: %s\n' "$1" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

calculate_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
    return
  fi

  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
    return
  fi

  fail "required command not found: sha256sum or shasum"
}

for command_name in curl git tar awk mktemp sed chmod; do
  require_command "$command_name"
done

if [ "$#" -gt 1 ]; then
  fail "usage: install.sh [destination]"
fi

if [ "$#" -eq 1 ]; then
  destination=$1
else
  [ -n "${HOME:-}" ] || fail "HOME is not set; pass a destination explicitly"
  destination=$HOME/nova
fi

[ ! -e "$destination" ] || fail "destination already exists: $destination"

version=$NOVA_INSTALL_VERSION
archive_name=nova-v$version.tar.gz
checksum_name=$archive_name.sha256
release_url=$NOVA_RELEASE_BASE_URL/v$version
temporary_directory=$(mktemp -d "${TMPDIR:-/tmp}/nova-install.XXXXXX")

cleanup() {
  rm -rf "$temporary_directory"
}

trap cleanup EXIT HUP INT TERM

archive_path=$temporary_directory/$archive_name
checksum_path=$temporary_directory/$checksum_name

printf 'Downloading Nova %s...\n' "$version"
curl --fail --location --silent --show-error \
  "$release_url/$archive_name" \
  --output "$archive_path"
curl --fail --location --silent --show-error \
  "$release_url/$checksum_name" \
  --output "$checksum_path"

expected_checksum=$(awk 'NR == 1 { print $1 }' "$checksum_path")
case "$expected_checksum" in
  ''|*[!0-9a-fA-F]*) fail "invalid release checksum" ;;
esac
[ "${#expected_checksum}" -eq 64 ] || fail "invalid release checksum"

actual_checksum=$(calculate_sha256 "$archive_path")
[ "$actual_checksum" = "$expected_checksum" ] || fail "release checksum does not match"

archive_root=nova-v$version
archive_listing=$temporary_directory/archive-listing.txt
tar -tzf "$archive_path" > "$archive_listing"

while IFS= read -r archive_entry; do
  case "$archive_entry" in
    "$archive_root"|"$archive_root/"|"$archive_root/"*) ;;
    *) fail "release contains an unexpected path: $archive_entry" ;;
  esac

  case "$archive_entry" in
    /*|../*|*/../*|*/..|*/.git|*/.git/*)
      fail "release contains an unsafe path: $archive_entry"
      ;;
  esac
done < "$archive_listing"

tar -xzf "$archive_path" -C "$temporary_directory"
extracted_directory=$temporary_directory/$archive_root
[ -d "$extracted_directory" ] || fail "release root is missing"
[ "$(sed -n '1p' "$extracted_directory/VERSION")" = "$version" ] || \
  fail "release version does not match the installer"
chmod 700 "$extracted_directory"

destination_parent=$(dirname "$destination")
mkdir -p "$destination_parent"

git -C "$extracted_directory" init -q -b main
git -C "$extracted_directory" add --all

if git -C "$extracted_directory" config user.name >/dev/null 2>&1 && \
   git -C "$extracted_directory" config user.email >/dev/null 2>&1; then
  git -C "$extracted_directory" commit -q -m "Start my Nova"
else
  GIT_AUTHOR_NAME=Nova \
  GIT_AUTHOR_EMAIL=nova@localhost \
  GIT_COMMITTER_NAME=Nova \
  GIT_COMMITTER_EMAIL=nova@localhost \
    git -C "$extracted_directory" commit -q -m "Start my Nova"
fi

[ ! -e "$destination" ] || fail "destination already exists: $destination"
mv "$extracted_directory" "$destination"

quoted_destination=$(printf '%s' "$destination" | sed "s/'/'\\\\''/g")

printf '\nNova %s is ready at %s\n' "$version" "$destination"
printf '\nNext:\n'
printf "  cd '%s'\n" "$quoted_destination"
printf '\nStart your coding agent from that directory.\n'
