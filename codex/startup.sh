apt update && apt install -y nano maven gradle lua5.4 luarocks dotnet-sdk-8.0
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

cd java && mvn clean install -DskipTests -B && cd ..
cd rust && cargo clean && cargo fetch && cargo build --locked && cd ..
cd swift && swift package resolve && swift build && cd ..
cd go && go mod verify && go mod download && go build -mod=readonly && cd ..
cd csharp/ScjsonCli && dotnet restore && dotnet build --no-restore && cd ../..
cd csharp/Scjson.Tests && dotnet restore && cd ../..



