"""Disposable Linux/Docker test. Uses fake Docker API and test credentials only."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'koningkoffie-checkmate'


def run(*cmd, **kwargs):
    return subprocess.check_output(cmd, text=True, **kwargs)


def wait_for(check, description, seconds=180):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if check():
                return
        except (subprocess.CalledProcessError, OSError):
            pass
        time.sleep(2)
    raise RuntimeError('Timed out: ' + description)


with tempfile.TemporaryDirectory(prefix='checkmate-smoke-') as directory:
    work = Path(directory)
    work.chmod(0o755)
    project = 'checkmate-smoke-' + str(os.getpid())
    env = {**os.environ, 'APP_DATA_DIR': directory, 'APP_PROXY_PORT': '52345', 'APP_PASSWORD': 'test-capture-key',
           'APP_KONINGKOFFIE_CHECKMATE_LOCAL_IP': '127.0.0.1',
           'APP_KONINGKOFFIE_CHECKMATE_DOCKER_GID': '1000',
           'APP_KONINGKOFFIE_CHECKMATE_MONGO_PASSWORD': 'test-root-password',
           'APP_KONINGKOFFIE_CHECKMATE_DB_PASSWORD': 'test-app-password',
           'APP_KONINGKOFFIE_CHECKMATE_JWT_SECRET': 'test-jwt-secret',
           'APP_KONINGKOFFIE_CHECKMATE_ENCRYPTION_KEY': 'Y2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2M='}
    for file in APP.glob('*.template'):
        shutil.copyfile(file, work / file.stem)
    for name in ['db', 'configdb', 'metrics']:
        (work / 'data' / name).mkdir(parents=True, exist_ok=True)
    proxy = work / 'umbrel.yml'
    proxy.write_text('services:\n  app_proxy:\n    image: getumbrel/app-proxy:validation-only\n')
    rendered = json.loads(run('docker', 'compose', '-p', project, '-f', str(APP / 'docker-compose.yml'), '-f', str(proxy), 'config', '--format', 'json', env=env))
    services = rendered['services']
    del services['app_proxy']
    # Use isolated Compose DNS while leaving production configuration untouched.
    services['db_init']['entrypoint'] = ['mongosh', '--host', 'db', '--quiet', '/init-db.js']
    services['server']['environment']['DB_CONNECTION_STRING'] = services['server']['environment']['DB_CONNECTION_STRING'].replace('koningkoffie-checkmate_db_1', 'db')
    # Disposable database volumes are removed by Docker, regardless of MongoDB UID.
    services['db']['volumes'] = [
        {'type': 'volume', 'source': 'smoke-db', 'target': '/data/db'},
        {'type': 'volume', 'source': 'smoke-configdb', 'target': '/data/configdb'}]
    rendered['volumes'].update({'smoke-db': {}, 'smoke-configdb': {}})
    # The only API the proxy may touch is this fixture, never the runner daemon.
    fixture = work / 'fake-docker.cjs'
    fixture.write_text("""
const http=require('http'),fs=require('fs');
const id='a'.repeat(64);
http.createServer((req,res)=>{
 const p=req.url.split('?')[0].replace(/^\\/v[0-9]+\\.[0-9]+/, '');
 res.setHeader('Content-Type','application/json');
 if(p==='/_ping')return res.end('OK');
 if(p==='/containers/json')return res.end(JSON.stringify([{Id:id,Names:['/fixture'],Image:'fixture',State:'running',Status:'Up'}]));
 if(p.endsWith('/json'))return res.end(JSON.stringify({Id:id,Config:{Env:['SECRET=must-not-leak']},RestartCount:0,State:{StartedAt:new Date().toISOString(),Health:{Status:'healthy'}},NetworkSettings:{Ports:{}},Mounts:[]}));
 if(p.endsWith('/stats'))return res.end(JSON.stringify({cpu_stats:{cpu_usage:{total_usage:1},system_cpu_usage:2,online_cpus:1},precpu_stats:{cpu_usage:{total_usage:0},system_cpu_usage:1},memory_stats:{usage:1024,limit:4096,stats:{}}}));
 if(p.endsWith('/logs'))return res.end('2026-01-01T00:00:00.000000000Z fixture log\\n');
 res.writeHead(404);res.end();
}).listen(process.argv[2],()=>fs.chmodSync(process.argv[2],0o666));
""")
    fake = subprocess.Popen(['node', str(fixture), str(work / 'docker.sock')])
    wait_for(lambda: (work / 'docker.sock').exists(), 'fake Docker socket', 15)
    for mount in services['docker_proxy']['volumes']:
        if mount['target'] == '/upstream.sock':
            mount['source'] = str(work / 'docker.sock')
    services['docker_proxy']['group_add'] = []
    # Capture API smoke test uses an isolated network and disposable filesystem.
    # Physical hardware accuracy still requires the user's Umbrel.
    capture = services['capture']
    del capture['network_mode']
    capture['networks'] = {'default': None}
    capture['volumes'] = [{'type': 'bind', 'source': str(work / 'data/metrics'), 'target': '/host/root', 'read_only': True}]
    for key in ['HOST_PROC', 'HOST_SYS', 'HOST_ETC', 'HOST_DEV']:
        capture['environment'].pop(key, None)
    config = work / 'compose.json'
    config.write_text(json.dumps(rendered))
    command = ['docker', 'compose', '-p', project, '-f', str(config)]
    def compose(*args):
        return run(*command, *args, env=env)
    def mongo(js):
        return compose('exec', '-T', 'db', 'mongosh', '--quiet', '--eval', js)
    def node(js):
        return compose('exec', '-T', 'server', 'node', '-e', js)
    try:
        compose('up', '-d', 'db')
        wait_for(lambda: 'healthy' == run('docker', 'inspect', '--format', '{{.State.Health.Status}}', compose('ps', '-q', 'db').strip()).strip(), 'MongoDB startup')
        # Simulate an existing installation containing user data before migration.
        mongo("db.getSiblingDB('admin').auth('checkmate',process.env.MONGO_INITDB_ROOT_PASSWORD); db.getSiblingDB('uptime_db').migration_probe.insertOne({preserved:true})")
        compose('up', '-d')
        wait_for(lambda: 'healthy' == run('docker', 'inspect', '--format', '{{.State.Health.Status}}', compose('ps', '-q', 'server').strip()).strip(), 'Checkmate readiness')
        mongo("const a=db.getSiblingDB('uptime_db'); if(a.auth('checkmate_app','test-app-password').ok!==1)quit(1); if(!a.migration_probe.findOne({preserved:true}))quit(2); a.migration_probe.insertOne({appWrite:true}); if(a.runCommand({serverStatus:1}).ok!==1)quit(4); let denied=false; try { db.getSiblingDB('admin').getUsers(); }catch(e){denied=e.code===13;} if(!denied)quit(3);")
        compose('run', '--rm', 'db_init')
        node("""
const http=require('http'),assert=require('assert');
const req=(method,path)=>new Promise((resolve,reject)=>{const q=http.request({socketPath:'/var/run/docker.sock',method,path},r=>{let b='';r.on('data',c=>b+=c);r.on('end',()=>resolve({status:r.statusCode,body:b}));});q.on('error',reject);q.end();});
(async()=>{
 assert.equal((await req('GET','/_ping')).status,200);
 assert.equal((await req('POST','/containers/create')).status,403);
 assert.equal((await req('GET','/containers/'+'a'.repeat(64)+'/archive?path=/etc/passwd')).status,403);
 const inspection=await req('GET','/containers/'+'a'.repeat(64)+'/json');assert.equal(inspection.status,200);assert(!inspection.body.includes('must-not-leak'));
 // Exercise the same Docker client library used by Checkmate.
 const Docker=require('dockerode');const docker=new Docker({socketPath:'/var/run/docker.sock'});
 await docker.ping();const containers=await docker.listContainers({all:true});assert.equal(containers.length,1);
 const c=docker.getContainer(containers[0].Id);await c.inspect();await c.stats({stream:false});await c.logs({follow:false,stdout:true,stderr:true,timestamps:true,tail:100});
 const no=await fetch('http://capture:59232/api/v1/metrics');assert.equal(no.status,401);
 const yes=await fetch('http://capture:59232/api/v1/metrics',{headers:{Authorization:'Bearer test-capture-key'}});assert([200,207].includes(yes.status));
 const data=await yes.json();assert(data.data.cpu);assert(data.data.memory);assert(Array.isArray(data.data.net));
 console.log('Runtime smoke passed: migration preserves data, restricted DB user, filtered Docker client, and Capture authentication/metrics.');
})().catch(e=>{console.error(e.message);process.exit(1)});
""")
        print('Runtime smoke passed, including existing-data migration and repeat initialization.')
    except Exception:
        print(compose('logs', '--tail', '60'))
        raise
    finally:
        try:
            compose('down', '-v', '--remove-orphans')
        finally:
            fake.terminate()
            fake.wait(timeout=10)
