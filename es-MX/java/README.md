<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Paquete Java scjson

Este directorio contiene la implementación de Java de **scjson** usando Maven. Proporciona una interfaz de línea de comandos para convertir entre documentos `.scxml` y `.scjson` y validarlos contra el esquema compartido.

## Compilación

```bash
cd java && mvn package -DskipTests
```

## Uso por Línea de Comandos

```bash
java -jar target/scjson.jar json path/to/machine.scxml
java -jar target/scjson.jar xml path/to/machine.scjson
java -jar target/scjson.jar validate path/to/dir -r
java -jar target/scjson.jar run path/to/machine.scxml -e events.json -o trace.json
```

### Configuración del Proxy Java

La implementación de Java utiliza Maven. Si su entorno requiere un proxy HTTP/HTTPS, cree `~/.m2/settings.xml` con la configuración del proxy antes de compilar:

```xml
<settings>
  <proxies>
    <proxy>
      <id>internal-proxy</id>
      <active>true</active>
      <protocol>http</protocol>
      <host>proxy</host>
      <port>8080</port>
      <nonProxyHosts>localhost|127.0.0.1</nonProxyHosts>s
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
```

Compile el módulo con:

```bash
cd java && mvn clean install -DskipTests -B && cd ..
```

#### Ejecutando documentos SCXML
Puede ejecutar una máquina de estados usando la CLI:
```bash
java -jar target/scjson.jar run examples/example.scxml -e examples/events.json -o trace.json
```
Esto usa `ScxmlRunner` internamente y requiere la librería Apache Commons SCXML. Asegúrese de que Maven pueda descargar las dependencias o las tenga almacenadas en caché localmente.

Todo el código fuente en este directorio se publica bajo la licencia BSD 1-Clause. Consulte `LICENSE` y `LEGAL.md` para más detalles.
