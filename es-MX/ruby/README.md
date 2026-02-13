<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Gema de Ruby scjson

Este directorio contiene la implementación de Ruby de **scjson**. La gema proporciona una herramienta de línea de comandos y funciones de biblioteca para convertir entre archivos `.scxml` y `.scjson`.

## Instalación

```bash
gem install scjson
```

También puedes instalar desde una copia local:

```bash
cd ruby && gem build scjson.gemspec && gem install scjson-*.gem
```

## Uso desde la línea de comandos

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

## Uso como biblioteca

```ruby
require 'scjson'

document = Scjson::Types::ScxmlProps.new
json = document.to_json
round_trip = Scjson::Types::ScxmlProps.from_json(json)
```

Todo el código fuente en este directorio se publica bajo la licencia BSD de 1 cláusula. Consulte [LICENSE](./LICENSE) y [LEGAL.md](./LEGAL.md) para obtener más detalles.
