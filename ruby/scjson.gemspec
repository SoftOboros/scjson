Gem::Specification.new do |spec|
  spec.name        = 'scjson'
  spec.version     = '0.1.4'
  spec.summary     = 'SCXML <-> scjson converter and validator'
  spec.authors     = ['Softoboros Technology Inc.']
  spec.email       = ['info@softoboros.com']
  spec.license     = 'BSD-1-Clause'
  spec.files       = Dir['lib/**/*.rb']
  spec.executables = ['scjson']
  spec.require_paths = ['lib']
  spec.add_runtime_dependency 'nokogiri'
end
