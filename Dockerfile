# Agent Name: environment-dockerfile
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install base languages and build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    nano \
    python3 \
    python3-venv \
    python3-pip \
    ruby-full \
    maven \
    gradle \
    lua5.4 \
    luarocks \
    dotnet-sdk-8.0 \
    openjdk-21-jdk \
    golang-go \
    rustc \
    cargo \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js from official tarball
RUN wget https://download.swift.org/swift-6.1.2-release/ubuntu2204/swift-6.1.2-RELEASE/swift-6.1.2-RELEASE-ubuntu22.04.tar.gz \
    && tar -xzf swift-6.1.2-RELEASE-ubuntu22.04.tar.gz \
    && mv swift-6.1.2-RELEASE-ubuntu22.04 /opt/swift

ENV PATH="/opt/swift/usr/bin:$PATH"

WORKDIR /opt/scjson

# Upgrade node
ENV NODE_VERSION=22.2.0
RUN wget https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.xz \
    && tar -xJf node-v$NODE_VERSION-linux-x64.tar.xz -C /usr/local --strip-components=1 \
    && rm node-v$NODE_VERSION-linux-x64.tar.xz

# Upgrade Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain nightly
ENV PATH="/root/.cargo/bin:$PATH"

# copy repo to container
COPY . .

# Replicate repository setup
RUN git submodule update --init 

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN cd py && pip install -r requirements.txt && cd .. \
    && cd js && npm ci && cd .. \
    && cd lua \
        && luarocks install luaexpat --deps-mode=one \
        && luarocks install dkjson --deps-mode=one \
        && luarocks install busted --deps-mode=one \
        && cd .. \
    && cd ruby && gem install bundler && bundle install && cd ..

# build compiled items.
RUN cd java && mvn clean install -DskipTests -B && cd .. \
    && cd rust && cargo clean && cargo fetch && cargo build -Znext-lockfile-bump --locked && cd .. \
    && cd swift && swift package resolve && swift build && cd .. \
    && cd go && go mod verify && go mod download && go build -mod=readonly && cd .. \
    && cd csharp/ScjsonCli && dotnet restore && dotnet build --no-restore && cd ../.. \
    && cd csharp/Scjson.Tests && dotnet restore && cd ../..

# Setup proxy settings.xml separately
COPY ./java/proxy-settings.xml /root/.m2/settings.xml

CMD ["bash"]
