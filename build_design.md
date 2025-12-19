We want to set up healthy, best-practice, portable linux builds of this project.

That means

✓ Have an old-ish build environment docker container: docker/build_env.dockerfile
> Be able to run package builds in that container, across all supported python versions
  from our makefile. e.g. via a `make release`.
- Not break existing local builds e.g. `make package`.
- Ensure local (non-dockerized) builds put artifacts in a directory that's not
  dist/, so that we don't acidentally push non-release packages.


Stretch:

- Have fast builds

Note: For now, we're not targeting any dockerized testing infra, just builds.
