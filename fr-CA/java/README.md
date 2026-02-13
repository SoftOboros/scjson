<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Paquet Java scjson

Ce répertoire contient l'implémentation Java de **scjson** utilisant Maven. Il fournit une interface en ligne de commande pour convertir des documents `.scxml` en `.scjson` et vice-versa, et pour les valider par rapport au schéma partagé.

## Compilation

```bash
cd java && mvn package -DskipTests
```

## Utilisation en ligne de commande

```bash
java -jar target/scjson.jar json path/to/machine.scxml
java -jar target/scjson.jar xml path/to/machine.scjson
java -jar target/scjson.jar validate path/to/dir -r
java -jar target/scjson.jar run path/to/machine.scxml -e events.json -o trace.json
```

### Configuration du proxy Java

L'implémentation Java utilise Maven. Si votre environnement requiert un proxy HTTP/HTTPS,
créez le fichier `~/.m2/settings.xml` avec les paramètres de proxy avant la compilation :

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

Compilez le module avec :

```bash
cd java && mvn clean install -DskipTests -B && cd ..
```

#### Exécution de documents SCXML
Vous pouvez exécuter une machine à états en utilisant l'interface en ligne de commande :
```bash
java -jar target/scjson.jar run examples/example.scxml -e examples/events.json -o trace.json
```
Ceci utilise `ScxmlRunner` en arrière-plan et requiert la bibliothèque Apache Commons SCXML. Assurez-vous que Maven peut télécharger les dépendances ou les a mises en cache localement.

Tout le code source de ce répertoire est publié sous la licence BSD 1-Clause. Voir `LICENSE` et `LEGAL.md` pour plus de détails.
