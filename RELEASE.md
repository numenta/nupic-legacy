# Release Process

1. Send announcement that a release is underway to the committer's lounge on
discourse.numenta.org and ask reviewers not to merge PRs in NuPIC until you're
done with the release.
2. Create a PR that includes:
    - Release notes added to CHANGELOG.md
    - Change to the VERSION file so it matches the intended release version
3. Wait for the PR to be approved and merged, and the Bamboo build to complete
successfully
4. Create a "release" in Bamboo with a version matching the intended release
version
5. Deploy the release in Bamboo. This will:
    - Validate that the Bamboo release number matches the wheel version
    - Check that release notes are present for the version to be released
    - Push the wheel to PyPI
    - If successful, push a version tag to the repo
6. Send announcement to the committer's lounge on discourse.numenta.org that the release is complete.
