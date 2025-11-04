# A makefile for building bounce_desktop library, python package, and vendored weston.
#
# Commands:
#   make build: Builds the whole project and installs it under build/
#   make build_weston: Builds vendored weston and installs it under build/
#   make test: Runs the project's unit tests
#   make package: Builds the project's python package, runs its tests, and stores the
#                 built package under dist/ if all tests pass.
#   make upload: Run the project's unit and packaging tests and then uploads
#                the package to pypi.
#
#
# Note: We use a makefile for all of our builds, since:
# 1. We only support running this project in a locally installed configuration, so
#    we don't want users running "meson compile ..."
# 2. It gives us a convenient place to unify and document the build, package, test,
#    and upload commands our project uses.

BUILD_DIR := ${CURDIR}/build
build: build_weston
	meson setup build/ --prefix=${BUILD_DIR}
	meson install -C build/

WESTON_BUILD_DIR := ${CURDIR}/build/weston-fork
# We install to a temporary prefix and then copy over to our final
# desired prefix to materialize symlinks that are unsupported by python
# packaging.
TMP_WESTON_PREFIX := ${CURDIR}/build/bounce_desktop/_vendored/tmp_weston
WESTON_PREFIX := ${CURDIR}/build/bounce_desktop/_vendored/weston
build_weston:
	mkdir -p ${TMP_WESTON_PREFIX}

	cd subprojects/weston-fork; \
	meson setup ${WESTON_BUILD_DIR} --reconfigure --buildtype=release \
		--prefix=${TMP_WESTON_PREFIX} \
		-Dwerror=false \
		-Dbackend-vnc=true \
		-Drenderer-gl=true \
		-Dbackend-headless=true \
		-Dbackend-default=headless \
		-Drenderer-vulkan=false \
		-Dbackend-drm=false \
		-Dbackend-wayland=false \
		-Dbackend-x11=false \
		-Dbackend-rdp=false \
		-Dremoting=false \
		-Dpipewire=false

	meson compile -C ${WESTON_BUILD_DIR}
	meson install -C ${WESTON_BUILD_DIR}

	mkdir -p ${WESTON_PREFIX}
	cp -rL ${TMP_WESTON_PREFIX}/. ${WESTON_PREFIX}/
	rm -rf ${TMP_WESTON_PREFIX}

test: build
	meson test -C build/ --print-errorlogs --max-lines 2000

package: build test
	mkdir -p dist/ && mkdir -p packaging/dist
	poetry build --output packaging/dist
	./packaging/test_package.sh
	rm -rf dist/* && cp packaging/dist/* dist/

upload: package
	twine upload dist/*
