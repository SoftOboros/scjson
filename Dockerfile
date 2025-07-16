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
    git \
    nano \
    python3 \
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
    && rm -rf /var/lib/apt/lists/*

# Install Node.js from official tarball
RUN curl -fsSL https://nodejs.org/dist/v22.2.0/node-v22.2.0-linux-x64.tar.xz -o node.tar.xz \
    && tar -xJf node.tar.xz -C /usr/local --strip-components=1 \
    && rm node.tar.xz

# Install Swift using Swiftly
RUN curl -fsSL https://github.com/swift-server/swiftly/releases/download/1.0.1/swiftly-linux-amd64 -o /usr/local/bin/swiftly \
    && chmod +x /usr/local/bin/swiftly \
    && swiftly install 6.1.2

WORKDIR /opt/scjson
COPY . .

# Replicate repository setup
RUN git submodule update --init \
    && cd js && npm ci && cd .. \
    && cd py && pip install -r requirements.txt && cd .. \
    && cd lua && luarocks install luaexpat --deps-mode=one && \
       luarocks install dkjson --deps-mode=one && \
       luarocks install busted --deps-mode=one && cd .. \
    && cd ruby && gem install bundler && bundle install && cd .. \
    && mkdir -p /root/.m2 \
    && [ -f /root/.m2/settings.xml ] || (cat > /root/.m2/settings.xml <<'EOS'
<settings>
  <proxies>
    <proxy>
      <id>internal-proxy</id>
      <active>true</active>
      <protocol>http</protocol>
      <host>proxy</host>
      <port>8080</port>
      <nonProxyHosts>localhost|127.0.0.1</nonProxyHosts>
    </proxy>
    <proxy>
      <id>internal-proxy-https</id>
      <active>true</active>
      <protocol>https</protocol>
      <host>proxy</host>
      <port>8080</port>
      <nonProxyHosts>localhost|127.0.0.1</nonProxyHosts>
    </proxy>
  </proxies>
</settings>
EOS
) \
    && cd java && mvn clean install -DskipTests -B && cd .. \
    && cd rust && cargo clean && cargo fetch && cargo build --locked && cd .. \
    && cd swift && swift package resolve && swift build && cd .. \
    && cd go && go mod verify && go mod download && go build -mod=readonly && cd .. \
    && cd csharp/ScjsonCli && dotnet restore && dotnet build --no-restore && cd ../.. \
    && cd csharp/Scjson.Tests && dotnet restore && cd ../..

CMD ["bash"]
