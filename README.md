# 🐍🐘 Multi-Tier Python API + PostgreSQL `StatefulSet` on Kubernetes

A production-grade multi-tier microservice architecture deploying a **Python (Flask)** backend API connected over an internal Kubernetes **`ClusterIP` Service** to a stateful **PostgreSQL 16 Database (`StatefulSet`)** backed by persistent storage (**`PersistentVolumeClaim`**).

---

## 🏗️ Architecture & Kubernetes Resources (`k8s.yaml`)

```text
[ Browser / Client (http://localhost:8000) ]
                     │
                     ▼
      ┌──────────────────────────────┐
      │   Service: python-svc        │  (type: LoadBalancer | Port 8000 ➔ 5000)
      └──────────────┬───────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Pod: python-1  │     │  Pod: python-2  │  (Deployment: python-deploy | Replicas: 2)
│  Flask + psycopg2│     │  Flask + psycopg2│  (Reads DB credentials via secretRef: db-secret)
└────────┬────────┘     └────────┬────────┘
         └───────────┬───────────┘
                     │ Internal DNS: postgres-svc:5432
                     ▼
      ┌──────────────────────────────┐
      │   Service: postgres-svc      │  (type: ClusterIP — Isolated Internal Network Only!)
      └──────────────┬───────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │   Pod: postgres-0            │  (StatefulSet: postgres | Sticky Identity)
      │   Image: postgres:16-alpine  │  (VolumeMount: /var/lib/postgresql/data)
      └──────────────┬───────────────┘
                     │
                     ▼
      ┌──────────────────────────────┐
      │   PVC: postgres-pvc (1Gi)    │  (ReadWriteOnce — Survives Pod Deletion & Restarts!)
      └──────────────────────────────┘
```

---

## ✨ Key Engineering Highlights

1. **Stateful Database Orchestration (`kind: StatefulSet`):**
   - Unlike stateless `Deployment` workloads, PostgreSQL is deployed as a **`StatefulSet`** (`postgres-0`) with a dedicated `serviceName: postgres-svc` for deterministic network identity and ordered lifecycle management.
2. **Database Persistence Across Pod Failures (`kind: PersistentVolumeClaim`):**
   - Mounted a `1Gi` `ReadWriteOnce` **`PersistentVolumeClaim` (`postgres-pvc`)** to `/var/lib/postgresql/data`.
   - Verified zero data loss by querying rows directly via `psql`, deleting the `postgres-0` Pod (`kubectl delete pod postgres-0`), and confirming historical rows persisted after automatic `StatefulSet` self-healing.
3. **Network Isolation (`ClusterIP` vs. `LoadBalancer`):**
   - **Database Tier (`postgres-svc`):** Configured as an internal-only **`ClusterIP`** on port `5432` (`EXTERNAL-IP: <none>`), ensuring the database cannot be reached from outside the Kubernetes cluster.
   - **Application Tier (`python-svc`):** Exposed via **`LoadBalancer`** (`8000 -> 5000`) load-balancing across 2 stateless Python Flask replicas.
4. **Decoupled Credentials (`kind: Secret`):**
   - Database credentials (`POSTGRES_PASSWORD`) are stored in a Kubernetes `Secret` (`db-secret`) and injected into both the PostgreSQL `StatefulSet` and Python `Deployment` via `envFrom.secretRef`.

---

## 🚀 Quickstart & Verification Commands

### 1. Build & Push the Python Image
```bash
docker build -t fluffythepenguin/python-postgres-app:v1 .
docker push fluffythepenguin/python-postgres-app:v1
```

### 2. Deploy the Full Stack to Kubernetes
```bash
kubectl apply -f k8s.yaml
kubectl get po,svc,pvc,endpoints
```

### 3. Test Database Writes & Persistence Across Pod Deletion
```bash
# 1. Insert rows via the Python API
curl http://localhost:8000

# 2. Inspect raw SQL rows directly inside the PostgreSQL StatefulSet Pod
kubectl exec -it postgres-0 -- psql -U postgres -c "SELECT * FROM visits;"

# 3. Simulate a database crash by deleting postgres-0
kubectl delete pod postgres-0

# 4. Verify StatefulSet recreates postgres-0 and PVC retains all existing rows
curl http://localhost:8000
```
