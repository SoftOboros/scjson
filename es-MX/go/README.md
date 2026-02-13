<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Paquete Go de scjson

Este directorio contiene la implementación en Go de **scjson**, un formato para representar máquinas de estado SCXML en JSON. La herramienta de línea de comandos puede convertir entre archivos `.scxml` y `.scjson` y validar documentos utilizando el esquema compartido.

## Instalación

```bash
go install github.com/softoboros/scjson/go @scripts/aws/update_web_latest.sh
```

También puedes construir desde este repositorio:

```bash
cd go && go build
```

## Uso de la línea de comandos

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

Todo el código fuente en este directorio se publica bajo la licencia BSD de 1 cláusula. Consulta [LICENSE](./LICENSE) y [LEGAL.md](./LEGAL.md) para más detalles.
