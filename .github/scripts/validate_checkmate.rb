# Validate the real Compose model and Umbrel 1.7.x's string-only volume handling.
require 'yaml'
require 'json'
require 'open3'
require 'tmpdir'
require 'shellwords'

root = File.expand_path('../..', __dir__)
app = File.join(root, 'koningkoffie-checkmate')
compose = YAML.load_file(File.join(app, 'docker-compose.yml'))
manifest = YAML.load_file(File.join(app, 'umbrel-app.yml'))
compose.fetch('services').each do |name, service|
  (service['volumes'] || []).each do |volume|
    abort "#{name}: Umbrel 1.7.x requires string-form mounts" unless volume.is_a?(String)
    volume.gsub('/data/storage/downloads', '/home/Downloads').gsub('/data/storage', '/home')
  end
end
abort 'Unexpected app ID' unless manifest['id'] == 'koningkoffie-checkmate'
abort 'Capture key is not shown in Umbrel' unless manifest['deterministicPassword'] == true

env = {
  'APP_DATA_DIR' => '/tmp/checkmate-validation-data', 'APP_PROXY_PORT' => manifest.fetch('port').to_s,
  'APP_PASSWORD' => 'capture-validation-key', 'APP_KONINGKOFFIE_CHECKMATE_LOCAL_IP' => '192.168.1.50',
  'APP_KONINGKOFFIE_CHECKMATE_DOCKER_GID' => '998', 'APP_KONINGKOFFIE_CHECKMATE_MONGO_PASSWORD' => 'a' * 64,
  'APP_KONINGKOFFIE_CHECKMATE_JWT_SECRET' => 'b' * 64,
  'APP_KONINGKOFFIE_CHECKMATE_ENCRYPTION_KEY' => ['c' * 32].pack('m0')
}
Dir.mktmpdir('checkmate-compose-') do |tmp|
  proxy = File.join(tmp, 'proxy.yml')
  File.write(proxy, "services:\n  app_proxy:\n    image: getumbrel/app-proxy:validation-only\n")
  command = Shellwords.split(ENV.fetch('COMPOSE_COMMAND', 'docker compose')) +
    ['-p', 'koningkoffie-checkmate', '-f', File.join(app, 'docker-compose.yml'), '-f', proxy, 'config', '--format', 'json']
  output, errors, status = Open3.capture3(env, *command)
  abort errors unless status.success?
  services = JSON.parse(output).fetch('services')
  server, capture, db = services.values_at('server', 'capture', 'db')
  abort 'Socket group missing' unless server['group_add'] == ['998']
  socket = server.fetch('volumes').find { |v| v['target'] == '/var/run/docker.sock' }
  abort 'Socket mount changed' unless socket && socket['source'] == '/var/run/docker.sock' && socket['read_only']
  host = capture.fetch('volumes').find { |v| v['target'] == '/host/root' }
  abort 'Host mount changed' unless host && host['source'] == '/' && host['read_only'] && host.dig('bind', 'propagation') == 'rslave'
  abort 'Capture network changed' unless capture['network_mode'] == 'host'
  abort 'Capture authentication changed' unless capture.dig('environment', 'API_SECRET') == env['APP_PASSWORD']
  abort 'Database credentials mismatch' unless server.dig('environment', 'DB_CONNECTION_STRING').include?(db.dig('environment', 'MONGO_INITDB_ROOT_PASSWORD'))
  abort 'Database readiness dependency missing' unless server.dig('depends_on', 'db', 'condition') == 'service_healthy'
  abort 'Proxy authentication changed' unless services.dig('app_proxy', 'environment', 'PROXY_AUTH_ADD') == 'false'
  services.each do |name, service|
    next if name == 'app_proxy'
    abort "#{name}: image is not pinned" unless service.fetch('image').match?(/@sha256:[a-f0-9]{64}$/)
  end
  env.keys.grep(/SECRET|PASSWORD|KEY|LOCAL_IP|DOCKER_GID/).each do |key|
    _, _, failed = Open3.capture3(env.merge(key => ''), *command)
    abort "Missing #{key} did not prevent startup" if failed.success?
  end
end
abort 'Invalid exports.sh syntax' unless system('bash', '-n', File.join(app, 'exports.sh'))
puts 'Compose, required variables, and Umbrel installer compatibility passed.'
