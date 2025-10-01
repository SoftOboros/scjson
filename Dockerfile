# Agent Name: environment-dockerfile
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential      \
    ca-certificates      \
    cargo                \
    clang                \
    cmake                \
    curl                 \
    dotnet-sdk-8.0       \
    git                  \
    openssh-client       \
    libclang-dev         \
    libfreetype6-dev     \
    libgtk-3-dev         \
    librlottie-dev       \
    libsdl2-dev          \
    libssl-dev           \
    libx11-dev           \
    libxext-dev          \
    libxrender1          \
    llvm-dev             \
    lua5.4               \
    luarocks             \
    gcc-arm-none-eabi    \
    gnupg                \
    golang-go            \
    gradle               \
    binutils-arm-none-eabi \
    zstd                 \
    maven                \
    mold                 \
    nano                 \
    ninja-build          \
    openjdk-21-jdk       \
    pkg-config           \
    python3              \
    python3-pip          \
    python3-venv         \
    ruby-full            \
    sccache              \
    unzip                \
    vim                  \
    wget                 \
    xvfb                 \
    && rm -rf /var/lib/apt/lists/*

# Ensure Java tooling is fully configured
ENV JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"
ENV PATH="$JAVA_HOME/bin:$PATH"

RUN mkdir -p /etc/ssl/certs/java && \
    if [ ! -f /etc/ssl/certs/java/cacerts ]; then \
      keytool -genkeypair \
        -alias temp \
        -keystore /etc/ssl/certs/java/cacerts \
        -storepass changeit \
        -keypass changeit \
        -dname "CN=temp" \
        -keyalg RSA \
        -keysize 2048 \
        -validity 1 \
        -noprompt || echo "⚠️ failed to create dummy keystore"; \
      keytool -delete -alias temp \
        -keystore /etc/ssl/certs/java/cacerts \
        -storepass changeit || echo "⚠️ failed to delete dummy entry"; \
    fi && \
    dpkg --configure -a || true

# Install Node.js from official tarball
RUN wget https://download.swift.org/swift-6.1.2-release/ubuntu2204/swift-6.1.2-RELEASE/swift-6.1.2-RELEASE-ubuntu22.04.tar.gz \
    && tar -xzf swift-6.1.2-RELEASE-ubuntu22.04.tar.gz \
    && mv swift-6.1.2-RELEASE-ubuntu22.04 /opt/swift

ENV PATH="/opt/swift/usr/bin:$PATH"

WORKDIR /opt/scjson

# Install Node.js (LTS) via NodeSource
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws
RUN npm install -g yarn @openai/codex makeitso-codex

# Upgrade Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain nightly
ENV PATH="/root/.cargo/bin:$PATH"

# If you run as a non-root user at runtime, make sure they can read/write as needed
ARG SOFTOBOROS_USER=softoboros
ARG GIT_USERNAME
ARG GIT_EMAIL
RUN useradd -m -s /bin/bash "$SOFTOBOROS_USER" || true 
RUN mkdir -p /home/debian/.ssh

## Switch to non-root for app setup and runtime before creating workdir
USER ${SOFTOBOROS_USER}

# Set working directory (created as the app user to ensure ownership)
WORKDIR /home/${SOFTOBOROS_USER}/scjson

# Ensure venv binaries are on PATH for subsequent steps
ENV GEM_HOME="/home/${SOFTOBOROS_USER}/.gem"
ENV PATH="/home/${SOFTOBOROS_USER}/.local/bin:/home/${SOFTOBOROS_USER}/.luarocks/bin:${GEM_HOME}/bin:/root/.cargo/bin:$PATH"

ENV CARGO_INCREMENTAL=0
ENV SCCACHE_S3_KEY_PREFIX=/scjson

# Comment this out to remove sccache, or remove on run.
ENV RUSTC_WRAPPER=/usr/bin/sccache

# Prepare user-owned folders and Python venv
RUN mkdir -p \
    /home/${SOFTOBOROS_USER}/.ssh \
    /home/${SOFTOBOROS_USER}/.codex \
    /home/${SOFTOBOROS_USER}/.npm \
    /home/${SOFTOBOROS_USER}/.local \
    /home/${SOFTOBOROS_USER}/.luarocks \
    /home/${SOFTOBOROS_USER}/.gem \
  && python3 -m venv /home/${SOFTOBOROS_USER}/.local

# copy repo to container
COPY --chown=${SOFTOBOROS_USER}:${SOFTOBOROS_USER} . .

# Replicate repository setup
RUN git submodule update --init --recursive

# install dependancies
RUN cd py && pip install -r requirements.txt && cd .. \
    && cd js && npm ci && cd .. \
    && cd lua \
        && luarocks --local install luaexpat --deps-mode=one \
        && luarocks --local install dkjson --deps-mode=one \
        && luarocks --local install busted --deps-mode=one \
        && cd .. \
    && cd ruby \
        && gem install --no-document bundler \
        && bundle config set --local path vendor/bundle \
        && bundle install \
        && cd ..

RUN luarocks --local path >> /home/${SOFTOBOROS_USER}/.bashrc

# Build Apache Commons SCXML 0.9 from source for comparison harness
#RUN bash -lc 'set -euo pipefail; \
#    cd /tmp && \
#    curl -Lf http://archive.apache.org/dist/commons/scxml/source/commons-scxml-0.9-src.tar.gz -o commons-scxml-0.9-src.tar.gz && \
#    tar -xzf commons-scxml-0.9-src.tar.gz && \
#    cd commons-scxml-0.9-src && \
#    cd /tmp && rm -rf commons-scxml-0.9-src commons-scxml-0.9-src.tar.gz'


## Install Apache Commons SCXML 0.9 binary into local Maven repository
#RUN bash -lc 'set -euo pipefail; \
#    mkdir -p /tmp/commons-scxml-0.9/lib && \
#    cd /tmp && \
#    curl -Lf http://archive.apache.org/dist/commons/scxml/source/commons-scxml-0.9-src.tar.gz -o commons-scxml-0.9-src.tar.gz && \
#    tar -xzf commons-scxml-0.9-src.tar.gz && \
#    find commons-scxml-0.9-src -name "*.jar" -exec cp {} /tmp/commons-scxml-0.9/lib/ \; && \
#    curl -Lf http://archive.apache.org/dist/commons/scxml/binaries/commons-scxml-0.9-bin.zip -o commons-scxml-0.9-bin.zip && \
#    unzip -q commons-scxml-0.9-bin.zip && \
#    mv commons-scxml-0.9/lib/*.jar /tmp/commons-scxml-0.9/lib/ && \
#    for jar in /tmp/commons-scxml-0.9/lib/*.jar; do \
#        base=$(basename "$jar" .jar); \
#        mvn org.apache.maven.plugins:maven-install-plugin:3.1.1:install-file \
#           -Dfile="$jar" \
#           -DgroupId=local.apache.commons \
#           -DartifactId="$base" \
#           -Dversion=0.9 \
#           -Dpackaging=jar; \
#    done && \
#    rm -rf commons-scxml-0.9-src commons-scxml-0.9-bin.zip /tmp/commons-scxml-0.9'
#
# build compiled items.
#RUN cd java && mvn clean install -DskipTests -B && cd .. \
RUN cd rust && cargo clean && cargo fetch && cargo build -Znext-lockfile-bump --locked && cd .. \
    && cd swift && swift package resolve && swift build && cd .. \
    && cd go && go mod verify && go mod download && go build -mod=readonly && cd .. \
    && cd csharp/ScjsonCli && dotnet restore && dotnet build --no-restore && cd ../.. \
    && cd csharp/Scjson.Tests && dotnet restore && cd ../..

# Setup proxy settings.xml separately
COPY ./java/proxy-settings.xml /${SOFTOBOROS_USER}/.m2/settings.xml

CMD ["bash"]
