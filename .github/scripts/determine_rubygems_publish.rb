=begin
Agent Name: ci-determine-rubygems-publish

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

Ruby helper that inspects the gemspec and the RubyGems API to determine whether
CI should attempt to publish the gem.
=end

require 'json'
require 'net/http'
require 'pathname'

def main
  repo_root = Pathname(__FILE__).expand_path.parent.parent.parent
  gemspec_path = repo_root.join('ruby', 'scjson.gemspec')
  unless gemspec_path.exist?
    warn "gemspec not found at #{gemspec_path}"
    return 1
  end

  spec = Gem::Specification.load(gemspec_path.to_s)
  name = spec.name
  version = spec.version.to_s

  existing = []
  begin
    uri = URI("https://rubygems.org/api/v1/versions/#{name}.json")
    response = Net::HTTP.get(uri)
    existing = JSON.parse(response).map { |v| v['number'] }
  rescue StandardError
    existing = []
  end

  should_publish = existing.include?(version) ? 'false' : 'true'

  output_path = ENV['GITHUB_OUTPUT']
  if output_path && !output_path.empty?
    File.open(output_path, 'a') do |fh|
      fh.puts "name=#{name}"
      fh.puts "version=#{version}"
      fh.puts "should_publish=#{should_publish}"
    end
  end

  puts "RubyGems target #{name}@#{version}; existing versions: #{existing.inspect}"
  0
end

exit(main)
