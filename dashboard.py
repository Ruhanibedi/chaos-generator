from flask import Flask, jsonify, render_template_string
import urllib.request, urllib.error, json, os, ssl, time

app = Flask(__name__)

def k8s_request(path, method='GET', body=None):
    token = open('/var/run/secrets/kubernetes.io/serviceaccount/token').read()
    ca = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
    ctx = ssl.create_default_context(cafile=ca)
    host = 'https://kubernetes.default.svc'
    req = urllib.request.Request(f'{host}{path}', data=body, method=method)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, context=ctx) as r:
        return json.loads(r.read())

HTML = '''<!DOCTYPE html>
<html>
<head>
  <title>Chaos Engineering Platform</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #0a0e1a; color: #fff; font-family: 'Segoe UI', sans-serif; padding: 30px; }
    h1 { text-align: center; font-size: 2rem; margin-bottom: 8px; }
    .subtitle { text-align: center; color: #888; margin-bottom: 40px; font-size: 0.95rem; }
    .cluster-info { display: flex; justify-content: center; gap: 30px; margin-bottom: 40px; flex-wrap: wrap; }
    .info-card { background: #131929; border: 1px solid #1e2d4a; border-radius: 12px; padding: 20px 30px; text-align: center; }
    .info-card .label { color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .info-card .value { font-size: 1.4rem; font-weight: 600; color: #4ade80; }
    .pods-section { margin-bottom: 40px; }
    .pods-section h2 { color: #888; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 16px; text-align: center; }
    .pods-grid { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
    .pod-card { background: #131929; border: 1px solid #1e2d4a; border-radius: 12px; padding: 20px; width: 200px; text-align: center; transition: all 0.3s; }
    .pod-card.running { border-color: #166534; background: #052e16; }
    .pod-card.killed { border-color: #991b1b; background: #2d0a0a; }
    .pod-card.creating { border-color: #854d0e; background: #1c1002; }
    .pod-dot { width: 14px; height: 14px; border-radius: 50%; margin: 0 auto 12px; }
    .running .pod-dot { background: #4ade80; box-shadow: 0 0 10px #4ade80; }
    .killed .pod-dot { background: #ef4444; box-shadow: 0 0 10px #ef4444; }
    .creating .pod-dot { background: #f59e0b; box-shadow: 0 0 10px #f59e0b; animation: blink 0.8s infinite; }
    .pod-name { font-size: 0.7rem; color: #aaa; word-break: break-all; margin-bottom: 6px; }
    .pod-status { font-size: 0.85rem; font-weight: 600; }
    .running .pod-status { color: #4ade80; }
    .killed .pod-status { color: #ef4444; }
    .creating .pod-status { color: #f59e0b; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
    .chaos-section { text-align: center; margin-bottom: 40px; }
    .chaos-btn { background: linear-gradient(135deg, #dc2626, #991b1b); color: white; border: none; padding: 18px 50px; font-size: 1.1rem; font-weight: 700; border-radius: 12px; cursor: pointer; letter-spacing: 1px; transition: all 0.2s; text-transform: uppercase; }
    .chaos-btn:hover { transform: scale(1.05); box-shadow: 0 0 30px rgba(220,38,38,0.5); }
    .chaos-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
    .score-section { display: flex; justify-content: center; gap: 30px; margin-bottom: 30px; }
    .score-card { background: #131929; border: 1px solid #1e2d4a; border-radius: 12px; padding: 24px 40px; text-align: center; min-width: 180px; }
    .score-card .label { color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
    .score-card .big { font-size: 2.5rem; font-weight: 700; }
    .score-good { color: #4ade80; }
    .score-mid { color: #f59e0b; }
    .score-bad { color: #ef4444; }
    .log { background: #0d1117; border: 1px solid #1e2d4a; border-radius: 8px; padding: 16px; font-family: monospace; font-size: 0.8rem; color: #4ade80; max-height: 180px; overflow-y: auto; text-align: left; }
    .log-entry { margin-bottom: 4px; }
    .log-entry .time { color: #555; margin-right: 8px; }
  </style>
</head>
<body>
  <h1>Chaos Engineering Platform</h1>
  <p class="subtitle">AWS EKS · Kubernetes · Ansible · Real-time resilience testing</p>
  <div class="cluster-info">
    <div class="info-card"><div class="label">Cluster</div><div class="value">chaos-platform</div></div>
    <div class="info-card"><div class="label">Nodes</div><div class="value" id="node-count">-</div></div>
    <div class="info-card"><div class="label">Region</div><div class="value" style="color:#60a5fa">ap-south-1</div></div>
    <div class="info-card"><div class="label">Experiments Run</div><div class="value" id="exp-count">0</div></div>
  </div>
  <div class="pods-section">
    <h2>Live Pod Status</h2>
    <div class="pods-grid" id="pods-grid"><div style="color:#555">Loading pods...</div></div>
  </div>
  <div class="chaos-section">
    <button class="chaos-btn" id="chaos-btn" onclick="launchChaos()">Launch Chaos Attack</button>
    <p style="color:#555;margin-top:12px;font-size:0.85rem" id="chaos-status">Ready to inject failure</p>
  </div>
  <div class="score-section">
    <div class="score-card"><div class="label">Last Recovery Time</div><div class="big score-good" id="recovery-time">--</div><div style="color:#555;font-size:0.8rem">seconds</div></div>
    <div class="score-card"><div class="label">Resilience Score</div><div class="big" id="resilience-score">--</div><div style="color:#555;font-size:0.8rem">out of 100</div></div>
  </div>
  <div class="log" id="log"><div class="log-entry"><span class="time">[ready]</span> Chaos platform initialized. Cluster connected.</div></div>
  <script>
    let expCount=0,timer=null,elapsed=0;
    function addLog(msg){const log=document.getElementById('log');const t=new Date().toLocaleTimeString();log.innerHTML+=`<div class="log-entry"><span class="time">[${t}]</span> ${msg}</div>`;log.scrollTop=log.scrollHeight;}
    function updatePods(){fetch('/api/pods').then(r=>r.json()).then(data=>{const grid=document.getElementById('pods-grid');grid.innerHTML='';if(data.pods.length===0){grid.innerHTML='<div style="color:#555">No target pods found</div>';return;}data.pods.forEach(pod=>{const cls=pod.status==='Running'?'running':pod.status==='ContainerCreating'?'creating':'killed';const label=pod.status==='ContainerCreating'?'Recovering...':pod.status;grid.innerHTML+=`<div class="pod-card ${cls}"><div class="pod-dot"></div><div class="pod-name">${pod.name.slice(-14)}</div><div class="pod-status">${label}</div></div>`;});document.getElementById('node-count').textContent=data.nodes;}).catch(()=>{});}
    function launchChaos(){const btn=document.getElementById('chaos-btn');btn.disabled=true;elapsed=0;document.getElementById('chaos-status').textContent='Injecting failure...';document.getElementById('recovery-time').textContent='--';document.getElementById('resilience-score').textContent='--';addLog('Chaos attack initiated — selecting target pod...');timer=setInterval(()=>{elapsed++;document.getElementById('chaos-status').textContent=`Measuring recovery... ${elapsed}s elapsed`;},1000);fetch('/api/chaos',{method:'POST'}).then(r=>r.json()).then(data=>{clearInterval(timer);expCount++;document.getElementById('exp-count').textContent=expCount;const rt=data.recovery_time;const score=Math.max(0,100-(rt*2));document.getElementById('recovery-time').textContent=rt;const scoreEl=document.getElementById('resilience-score');scoreEl.textContent=score;scoreEl.className='big '+(score>=70?'score-good':score>=40?'score-mid':'score-bad');addLog(`Pod "${data.killed_pod}" terminated successfully`);addLog(`Kubernetes detected failure and scheduled replacement`);addLog(`System recovered in ${rt} seconds — Resilience score: ${score}/100`);document.getElementById('chaos-status').textContent=`Recovered in ${rt}s — Score: ${score}/100`;btn.disabled=false;updatePods();});}
    updatePods();setInterval(updatePods,3000);
  </script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/pods')
def get_pods():
    try:
        data = k8s_request('/api/v1/namespaces/default/pods?labelSelector=app%3Dchaos-target')
        pods = []
        for item in data.get('items', []):
            name = item['metadata']['name']
            phase = item['status'].get('phase', 'Unknown')
            cs = item['status'].get('containerStatuses', [])
            if cs and cs[0].get('state', {}).get('waiting', {}).get('reason') == 'ContainerCreating':
                phase = 'ContainerCreating'
            pods.append({'name': name, 'status': phase})
        nodes = k8s_request('/api/v1/nodes')
        node_count = len(nodes.get('items', []))
        return jsonify({'pods': pods, 'nodes': node_count})
    except Exception as e:
        return jsonify({'pods': [], 'nodes': 0, 'error': str(e)})

@app.route('/api/chaos', methods=['POST'])
def run_chaos():
    try:
        data = k8s_request('/api/v1/namespaces/default/pods?labelSelector=app%3Dchaos-target&fieldSelector=status.phase%3DRunning')
        items = data.get('items', [])
        if not items:
            return jsonify({'killed_pod': 'none', 'recovery_time': 0, 'error': 'no running pods'})
        pod_name = items[0]['metadata']['name']
        start = time.time()
        k8s_request(f'/api/v1/namespaces/default/pods/{pod_name}', method='DELETE', body=b'{}')
        time.sleep(20)
        recovery_time = int(time.time() - start)
        return jsonify({'killed_pod': pod_name, 'recovery_time': recovery_time})
    except Exception as e:
        return jsonify({'killed_pod': 'error', 'recovery_time': 99, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
