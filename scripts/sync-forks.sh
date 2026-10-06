#!/usr/bin/env bash
set -euo pipefail

# Imports and syncs the third-party skills under skills/forks/ from their
# upstream repos, as listed in skills/forks/upstreams.tsv.
#
#   scripts/sync-forks.sh            sync every entry
#   scripts/sync-forks.sh <name>...  sync only the named entries
#
# An entry with no synced commit yet ("-") is imported fresh with
# `git read-tree`. Otherwise the upstream diff between the recorded synced
# commit and the new upstream head is applied with `git apply --3way`, so local
# edits survive and genuine clashes surface as ordinary conflict markers. The
# manifest's synced column is then advanced. Nothing is committed: review the
# staged result, resolve any conflicts, and commit it yourself.
#
# This deliberately avoids `git subtree split`: re-splitting a large upstream
# history once per skill takes minutes per skill on Windows.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
FORKS="skills/forks"
MANIFEST="$FORKS/upstreams.tsv"

cd "$REPO"

if [ -n "$(git status --porcelain)" ]; then
  echo "error: working tree is not clean. Commit or stash first." >&2
  exit 1
fi

wanted=("$@")
is_wanted() {
  [ ${#wanted[@]} -eq 0 ] && return 0
  local w
  for w in "${wanted[@]}"; do [ "$w" = "$1" ] && return 0; done
  return 1
}

fetched=" "
conflicts=()
updated=()
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

while IFS= read -r line || [ -n "$line" ]; do
  line="${line%$'\r'}"
  case "$line" in
    ''|'#'*) printf '%s\n' "$line" >>"$tmp"; continue ;;
  esac

  read -r name remote url ref path synced <<<"$line"
  if ! is_wanted "$name"; then
    printf '%s\n' "$line" >>"$tmp"
    continue
  fi

  if ! git remote get-url "$remote" >/dev/null 2>&1; then
    git remote add "$remote" "$url"
  fi
  case "$fetched" in
    *" $remote "*) ;;
    *) git fetch --quiet "$remote"; fetched="$fetched$remote " ;;
  esac

  head="$(git rev-parse "$remote/$ref")"
  dest="$FORKS/$name"

  if [ "$path" = "." ]; then
    tree="$head^{tree}"
    relative=()
  else
    tree="$head:$path"
    relative=("--relative=$path")
  fi

  if [ "$synced" = "-" ]; then
    if [ -e "$dest" ]; then
      echo "error: $dest exists but $name has no synced commit in $MANIFEST." >&2
      exit 1
    fi
    git read-tree --prefix="$dest/" -u "$tree"
    echo "imported $name at ${head:0:12}"
    updated+=("$name")
  elif [ "$synced" = "$head" ]; then
    echo "up to date $name"
  else
    git diff --binary -M "${relative[@]}" "$synced" "$head" -- "${path%/}" >"$tmp.patch"
    if [ ! -s "$tmp.patch" ]; then
      echo "no upstream changes to $name (${synced:0:12}..${head:0:12})"
    elif git apply --3way -p1 --directory="$dest" "$tmp.patch"; then
      echo "synced $name ${synced:0:12}..${head:0:12}"
    else
      echo "CONFLICT syncing $name ${synced:0:12}..${head:0:12}" >&2
      conflicts+=("$name")
    fi
    rm -f "$tmp.patch"
    updated+=("$name")
  fi

  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$name" "$remote" "$url" "$ref" "$path" "$head" >>"$tmp"
done <"$MANIFEST"

cp "$tmp" "$MANIFEST"
git add "$MANIFEST"

if [ ${#updated[@]} -gt 0 ]; then
  echo
  echo "Re-check skills/forks/README.md and the local divergences it lists before committing."
  echo "If a skill was added or renamed, re-run scripts/link-skills.sh."
fi
if [ ${#conflicts[@]} -gt 0 ]; then
  echo
  echo "Resolve conflicts in: ${conflicts[*]} (see git status), then commit." >&2
  exit 1
fi
