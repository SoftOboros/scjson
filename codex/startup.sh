#!/bin/bash
# Agent Name: startup-script
#
# Part of the scjson project.
# Developed by Softoboros Technology Inc.
# Licensed under the BSD 1-Clause License.

apt update && apt install -y nano maven lua5.4 luarocks dotnet-sdk-8.0

# Ensure Java 21 is present
apt install -y default-jre-headless

# Explicitly set JAVA_HOME (check if this is the real path)
export JAVA_HOME="/usr/lib/jvm/java-21-openjdk"
export PATH="$JAVA_HOME/bin:$PATH"

# Sanity check for keytool
if ! command -v keytool >/dev/null; then
  echo "❌ keytool not found; Java may not be set up correctly"
else
  echo "✅ keytool is available"
fi

# Ensure keystore directory exists
mkdir -p /etc/ssl/certs/java

# Create a blank keystore manually to satisfy the updater
if [ ! -f /etc/ssl/certs/java/cacerts ]; then
  keytool -genkey -alias temp -keystore /etc/ssl/certs/java/cacerts \
    -storepass changeit -keypass changeit -dname "CN=temp" \
    -keyalg RSA -keysize 2048 -validity 1 || echo "⚠️ failed to create dummy keystore"

  # Delete the temporary key to make it a blank keystore
  keytool -delete -alias temp -keystore /etc/ssl/certs/java/cacerts \
    -storepass changeit || echo "⚠️ failed to delete dummy entry"
fi

# Now retry
dpkg --configure -a

unset NPM_CONFIG_HTTP_PROXY
unset NPM_CONFIG_HTTPS_PROXY
git submodule update --init
cd js && npm ci && cd ..
cd py && pip install -r requirements.txt && cd ..
cd lua && luarocks install luaexpat --deps-mode=one && \
    luarocks install dkjson --deps-mode=one && \
    luarocks install busted --deps-mode=one && cd ..

mkdir -p ~/.m2
if [ ! -f ~/.m2/settings.xml ]; then
  cat > ~/.m2/settings.xml <<EOF
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
EOF
fi

cd java \
  && git clone https://github.com/apache/commons-scxml.git \
  && cd commons-scxml \
  && git fetch --tags \
  && git checkout tags/commons-scxml2-2.0-M1 -b scxml-2.0-M1 \
  && mvn clean install -DskipTests -Dmaven.compiler.source=8 -Dmaven.compiler.target=8 || echo "⚠️ Failed to compile commons-scxml 2.0-M1" \
  && cd .. \
  && mvn dependency:resolve -DincludeScope=test || echo "⚠️ Failed to prefetch test-scope deps" \
  && mvn clean test -DskipTests || echo "⚠️ Failed to compile test classes (main test compile)" \
  && mvn clean install -DskipTests -B -Dmaven.compiler.source=8 -Dmaven.compiler.target=8 || echo "⚠️ Failed main build" \
  && mvn org.apache.maven.plugins:maven-surefire-plugin:3.1.2:test \
  -Dtest=NONE -Dsurefire.skipAfterFailureCount=0 || echo "⚠️ Surefire pre-cache failed" \
  && mvn dependency:go-offline -DincludeScope=test \
  && mvn dependency:get -Dartifact=org.apache.maven.surefire:surefire-junit-platform:3.1.2 \
  || echo "⚠️ Failed to prefetch surefire-junit-platform" \
  && cd ..
cd rust \
    && cargo clean \
    && cargo fetch || echo "⚠️ rust fetch failed" \
    && cargo build --locked || echo "⚠️ rust compile failed" \
    && cd .. 
cd swift \
    && swift package resolve || echo "⚠️ swift resolve failed" \
    && swift build || echo "⚠️ swift build failed" \
    && cd ..
cd go \
    && go mod verify || echo "⚠️ go mod verify failed" \
    && go mod download || echo "⚠️ go mod download failed" \
    && go build -mod=readonly || echo "⚠️ go build -mod=readonly failed" \
    && cd ..
cd csharp/ScjsonCli \
    && dotnet restore || echo "⚠️ dotnet restore failed" \
    && dotnet build --no-restore || echo "⚠️ (Cli) dotnet build --no-restore failed" \
    && cd ../..
cd csharp/Scjson.Tests \
    && dotnet restore || echo "⚠️ (Tests) dotnet restore failed" \
    && cd ../..
