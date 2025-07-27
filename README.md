# 🌸 observable & scalable iris classifier api

[![build](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/adhithyasash1/observable-k8s-pipeline/actions)
[![deployment](https://img.shields.io/badge/deployment-live-blue)](http://34.55.215.228)
[![kubernetes](https://img.shields.io/badge/kubernetes-gke-success)](https://cloud.google.com/kubernetes-engine)
[![observability](https://img.shields.io/badge/observability-enabled-yellowgreen)](https://cloud.google.com/trace)

this project builds and scales a machine learning inference api using fastapi and kubernetes. it supports multiple concurrent requests and includes observability features using google cloud logging and tracing.

---

rest of the readme follows as before. if you want custom icons or to match your repo's actual CI/CD status badges, i can fetch those too.

---

## 🎯 objective

scale a basic iris classification api to handle concurrent load using kubernetes, and identify performance bottlenecks with open telemetry.

---

## 🧱 project structure

```
observable-k8s-pipeline/
├── app/                   → fastapi app + model
│   ├── main.py
│   └── model.joblib
├── k8s/                   → kubernetes manifests
│   ├── deployment.yaml
│   ├── hpa.yaml
│   └── service.yaml
├── Dockerfile             → multi-stage docker build
├── pyproject.toml         → dependencies (via poetry)
├── post.lua               → wrk load test script
├── wrk_results.txt        → benchmarking output
├── command_history.txt    → full terminal command log
```

---

## ⚙️ how it works

* **fastapi** serves a `/predict` endpoint using a pre-trained sklearn model
* requests are traced using **open telemetry** and **cloud trace**
* logs are structured in json and sent to **cloud logging**
* deployed on **gke** with autoscaling enabled using **hpa**
* load testing is done using `wrk` with 100 concurrent users

---

## ☁️ cloud setup steps

1. enabled apis: `cloud trace`, `cloud logging`, `artifact registry`, `gke`
2. created a gke cluster named `iris-scaling-cluster`
3. enabled workload identity to allow k8s service account to impersonate a gcp service account
4. created a gcp service account named `telemetry-access`
5. granted it:

   * `roles/logging.logWriter`
   * `roles/cloudtrace.agent`
   * `roles/iam.workloadIdentityUser`
6. annotated the k8s service account to use the gcp one:

   ```bash
   kubectl annotate serviceaccount telemetry-access \
     iam.gke.io/gcp-service-account=telemetry-access@$PROJECT_ID.iam.gserviceaccount.com
   ```

---

## 🐳 container build & deploy

* used poetry for dependency management
* built and pushed the image to artifact registry:

  ```bash
  docker build -t $IMAGE_PATH .
  docker push $IMAGE_PATH
  ```
* deployed with:

  ```bash
  kubectl apply -f k8s/deployment.yaml
  kubectl apply -f k8s/service.yaml
  kubectl apply -f k8s/hpa.yaml
  ```

---

## 📈 observability details

* spans created for every request and inference step
* latency captured and sent to cloud trace
* response headers include `x-process-time-ms`
* logs are formatted in json with trace ids

---

## 🧪 load test summary (`wrk`)

* tested with:

  ```
  wrk -t4 -c100 -d30s --latency -s post.lua http://<external-ip>/predict
  ```
* results:

  * avg latency: \~697ms
  * requests/sec: \~141
  * total requests: 4,244
* full results in `wrk_results.txt`

---

## 🔁 sample request

```bash
curl -X POST http://<external-ip>/predict \
  -H "content-type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

---

## 👤 author

R Sashi Adhithya /
(21F3000611) /
github: [@adhithyasash1](https://github.com/adhithyasash1)
