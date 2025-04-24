#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.2"
    exit 1
fi

NEW_VERSION=$1
CURRENT_VERSION=$(poetry version -s)

# Function to compare versions
version_gt() {
    test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1";
}

if ! version_gt "$NEW_VERSION" "$CURRENT_VERSION"; then
    echo "Error: New version ($NEW_VERSION) must be greater than current version ($CURRENT_VERSION)"
    exit 1
fi

# Update version in pyproject.toml
poetry version $NEW_VERSION

# Create and push tag
git add pyproject.toml
git commit -m "Bump version to $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
git push origin main
git push origin "v$NEW_VERSION"
