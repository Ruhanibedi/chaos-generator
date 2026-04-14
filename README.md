# chaos-generator

Chaos Engineering Platform
A platform that intentionally breaks a running Kubernetes application on AWS
and measures how fast it recovers — generating a resilience score.
Tech Stack

Terraform — Infrastructure as code (AWS provisioning)
AWS EKS — Managed Kubernetes cluster on AWS Mumbai region
Kubernetes — Orchestrates 3 replicas of the target app with liveness probes
Docker — Containerizes the target application
Ansible — Chaos injection engine (kills pods, measures recovery time)
Python Flask — Target app + live dashboard

Project Structure
chaos-platform/
├── terraform/
│   └── main.tf               # AWS infrastructure definition
├── k8s/
│   ├── deployment.yaml       # Kubernetes app deployment + service
│   └── dashboard.yaml        # Dashboard deployment + RBAC
├── ansible/
│   └── chaos_pod_kill.yml    # Chaos experiment playbook
└── app/
    ├── app.py                # Target Flask application
    ├── dashboard.py          # Live chaos dashboard
    ├── Dockerfile            # Container definition
    └── requirements.txt      # Python dependencies
How to Run
1. Provision Infrastructure
bash# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create EKS cluster
eksctl create cluster \
  --name chaos-platform \
  --region ap-south-1 \
  --nodegroup-name worker-nodes \
  --node-type t3.micro \
  --nodes 2 \
  --managed
2. Deploy Target Application
bashkubectl apply -f k8s/deployment.yaml
kubectl get pods
3. Deploy Dashboard
bashkubectl create configmap dashboard-code --from-file=dashboard.py=app/dashboard.py
kubectl apply -f k8s/dashboard.yaml
kubectl get svc chaos-dashboard-svc  # Get public URL
4. Run Chaos Experiment
bashpip install ansible
ansible-playbook ansible/chaos_pod_kill.yml
What It Does

Deploys a target app with 3 Kubernetes pod replicas
Ansible playbook identifies a running pod and kills it deliberately
Kubernetes detects the failure and schedules a replacement pod
Platform measures recovery time and calculates resilience score
Live dashboard shows pod status, recovery time, and score in real time

Resilience Score Formula
Score = 100 - (recovery_time_seconds * 2)

Recovery in 20s = Score of 60/100
Recovery in 10s = Score of 80/100
Recovery in 5s  = Score of 90/100

Remaining Work (50% → 100%)

 CPU stress experiment (stress-ng)
 Network latency experiment (tc netem)
 AWS CloudWatch metrics integration
 Historical resilience score tracking
 Multi-experiment comparison dashboard
