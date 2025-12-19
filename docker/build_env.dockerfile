FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

#############################################################################
# Install build tools and C++20 toolchain
#############################################################################
RUN apt-get update && apt-get install -y \
    # Build toolchain
    build-essential \
    pkg-config \
    ninja-build \
    git \
    # Python bindings and Meson install
    python3 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    curl \
    python-is-python3 \
    # HTTPS git clones
    ca-certificates \
    # Add add-apt-repository
    software-properties-common \
    # Clean up installed data
    && rm -rf /var/lib/apt/lists/*

# Install GCC 13 for full C++20 support
RUN add-apt-repository -y ppa:ubuntu-toolchain-r/test && \
    apt-get update && \
    apt-get install -y gcc-13 g++-13 && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100 && \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 100 && \
    update-alternatives --install /usr/bin/cc cc /usr/bin/gcc-13 100 && \
    update-alternatives --install /usr/bin/c++ c++ /usr/bin/g++-13 100 && \
    rm -rf /var/lib/apt/lists/*

# Install newer meson via pip (Ubuntu 22.04's meson 0.61.2 is too old for Weston)
RUN pip3 install 'meson>=0.63.0'

#############################################################################
# Install Ubuntu 22.04 system dependencies
#############################################################################
RUN apt-get update && apt-get install -y \
    # Wayland ecosystem (will be supplemented by vendored Wayland)
    libwayland-dev \
    wayland-protocols \
    libwayland-bin \
    libxml2-dev \
    hwdata \
    # Xwayland
    libx11-xcb-dev \
    libxcb-composite0-dev \
    libxcb-cursor-dev \
    # Graphics and rendering
    libpixman-1-dev \
    libdrm-dev \
    libgbm-dev \
    libegl1-mesa-dev \
    libgles2-mesa-dev \
    libcairo2-dev \
    libpng-dev \
    liblcms2-dev \
    # VNC dependencies
    libaml-dev \
    libpam0g-dev \
    # Input and display
    libxkbcommon-dev \
    libinput-dev \
    libevdev-dev \
    libudev-dev \
    # Bounce desktop dependencies
    libvncserver-dev \
    libgvnc-1.0-dev \
    libsdl2-dev \
    # Used by reaper tests
    psmisc \
    # Testing frameworks
    libgtest-dev \
    libgmock-dev

# Install Python versions (including -dev and -venv packages for compiling and virtualenvs)
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y \
    python3.10 python3.10-dev python3.10-venv \
    python3.11 python3.11-dev python3.11-venv \
    python3.12 python3.12-dev python3.12-venv \
    python3.13 python3.13-dev python3.13-venv \
    python3.14 python3.14-dev python3.14-venv

# To test deleting packages and seeing if the container still runs, uncomment this line:
# RUN apt purge -y <packages> && apt autoremove -y

#############################################################################
# Build Wayland 1.23.93 from source (Weston requires >= 1.22.0, protocols needs >= 1.23.0)
#############################################################################
RUN git clone https://gitlab.freedesktop.org/wayland/wayland.git /tmp/wayland && \
    cd /tmp/wayland && \
    git checkout 1.23.93 && \
    meson setup build --prefix=/usr/local --buildtype=release -Ddocumentation=false && \
    ninja -C build && \
    ninja -C build install && \
    cd / && \
    rm -rf /tmp/wayland

# Build wayland-protocols from source (Ubuntu 22.04 has 1.25, but Weston needs >= 1.41)
RUN git clone https://gitlab.freedesktop.org/wayland/wayland-protocols.git /tmp/wayland-protocols && \
    cd /tmp/wayland-protocols && \
    git checkout 1.41 && \
    meson setup build --prefix=/usr/local --buildtype=release && \
    ninja -C build && \
    ninja -C build install && \
    cd / && \
    rm -rf /tmp/wayland-protocols

# Question: Do we need to set paths manually?
# Update library paths to use vendored Wayland
# ENV PKG_CONFIG_PATH=/usr/local/lib/x86_64-linux-gnu/pkgconfig:/usr/local/lib/pkgconfig:${PKG_CONFIG_PATH}
# ENV LD_LIBRARY_PATH=/usr/local/lib/x86_64-linux-gnu:/usr/local/lib:${LD_LIBRARY_PATH}

# Update ldconfig cache
RUN ldconfig

COPY ./ /workspace/
