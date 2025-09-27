#!/usr/bin/env bash
set -euo pipefail

# create-github-release.sh
# Create a GitHub release with all template zip files
# Usage: create-github-release.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"

# Remove 'v' prefix from version for release title
VERSION_NO_V=${VERSION#v}

files=( )
for f in \
  .genreleases/spec-kit-template-*-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-*-ps-"$VERSION".zip; do
  [[ -f "$f" ]] && files+=("$f")
done

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No template artifacts found in .genreleases for $VERSION" >&2
  exit 1
fi

gh release create "$VERSION" \
  "${files[@]}" \
  --title "Spec Kit Templates - $VERSION_NO_V" \
  --notes-file release_notes.md