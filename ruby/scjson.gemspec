Gem::Specification.new do |spec|
  spec.name        = 'scjson'
  spec.version     = '0.3.4'
  spec.summary     = 'SCXML/SCML execution, SCXML <-> scjson converter and validator'
  spec.description = 'scjson: SCXML ↔ JSON converter, validator, and execution trace interface. Provides CLI tools for conversion, validation, and emitting deterministic traces compatible with SCION semantics.'
  spec.authors     = ['Softoboros Technology Inc.']
  spec.email       = ['info@softoboros.com']
  spec.license     = 'BSD-1-Clause'
  spec.homepage    = 'https://github.com/SoftOboros/scjson'
  spec.metadata    = {
    'source_code_uri' => 'https://github.com/SoftOboros/scjson',
    'documentation_uri' => 'https://github.com/SoftOboros/scjson/tree/main/docs',
    'changelog_uri' => 'https://github.com/SoftOboros/scjson/releases',
    'homepage_uri' => 'https://github.com/SoftOboros/scjson',
    'keywords' => 'scxml,statecharts,state-machine,scjson,scml,execution'
  }
  spec.files       = Dir['lib/**/*.rb', 'README.md', 'LICENSE', 'LEGAL.md']
  spec.executables = ['scjson']
  spec.require_paths = ['lib']
  spec.add_runtime_dependency 'nokogiri'
end
