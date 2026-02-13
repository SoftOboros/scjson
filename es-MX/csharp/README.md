```markdown
<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Paquete scjson C#

Este directorio contiene la implementación .NET de **scjson**, que proporciona una herramienta de línea de comandos y una biblioteca para convertir entre archivos `.scxml` y `.scjson`.

## Instalación

```bash
dotnet build csharp/ScjsonCli
```

Después de la compilación, puede ejecutar la CLI con:

```bash
dotnet run --project csharp/ScjsonCli -- json path/to/machine.scxml
```

## Uso desde la línea de comandos

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

Todo el código fuente en este directorio se publica bajo la licencia BSD 1-Clause. Consulte [LICENSE](./LICENSE) y [LEGAL.md](./LEGAL.md) para obtener más detalles.
```
