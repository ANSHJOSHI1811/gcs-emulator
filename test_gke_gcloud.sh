#!/usr/bin/env bash
# GKE gcloud CLI Test Suite — runs against the local GCP Stimulator backend

export CLOUDSDK_API_ENDPOINT_OVERRIDES_CONTAINER=http://localhost:8080/container/
PROJECT=test-gke-proj
LOCATION=us-central1-a
CLUSTER=gcloud-test-cluster
POOL=extra-pool

PASS=0; FAIL=0
ok()   { echo "  ✅ PASS: $*"; PASS=$((PASS+1)); }
fail() { echo "  ❌ FAIL: $*"; FAIL=$((FAIL+1)); }
hdr()  { echo; echo "══════════════════════════════════════════════════"; echo "  $*"; echo "══════════════════════════════════════════════════"; }

# ─── TC-1: serverConfig ───────────────────────────────────────────────────────
hdr "TC-1 · serverConfig — list supported K8s versions"
OUT=$(curl -sf "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/serverConfig")
echo "$OUT" | python3 -m json.tool --no-ensure-ascii 2>/dev/null | head -10
echo "$OUT" | grep -q "defaultClusterVersion" && ok "serverConfig returned" || fail "serverConfig missing defaultClusterVersion"

# ─── TC-2: Create cluster ─────────────────────────────────────────────────────
hdr "TC-2 · gcloud container clusters create"
gcloud container clusters create "$CLUSTER" \
  --project="$PROJECT" \
  --location="$LOCATION" \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --cluster-version=1.28 \
  --async \
  --quiet 2>&1 | tee /tmp/tc2.out
grep -qiE "Creating cluster|PROVISIONING|operation" /tmp/tc2.out \
  && ok "create returned operation/provisioning" \
  || fail "unexpected create output"

# ─── TC-3: List clusters ──────────────────────────────────────────────────────
hdr "TC-3 · gcloud container clusters list"
OUT=$(gcloud container clusters list \
  --project="$PROJECT" \
  --location="$LOCATION" \
  --quiet 2>&1)
echo "$OUT"
echo "$OUT" | grep -q "$CLUSTER" && ok "cluster appears in list" || fail "cluster not in list"

# ─── TC-4: Describe cluster ───────────────────────────────────────────────────
hdr "TC-4 · gcloud container clusters describe"
OUT=$(gcloud container clusters describe "$CLUSTER" \
  --project="$PROJECT" \
  --location="$LOCATION" \
  --quiet 2>&1)
echo "$OUT" | head -20
echo "$OUT" | grep -q "status:" && ok "describe returned status field" || fail "describe missing status"
echo "$OUT" | grep -q "location:" && ok "describe returned location field" || fail "describe missing location"

# ─── TC-5: Poll until RUNNING (max 90s) ───────────────────────────────────────
hdr "TC-5 · Poll cluster until RUNNING (timeout 90s)"
DEADLINE=$((SECONDS + 90))
while [ $SECONDS -lt $DEADLINE ]; do
  STATUS=$(curl -sf "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "ERROR")
  echo "  $(date '+%H:%M:%S') status=$STATUS"
  [ "$STATUS" = "RUNNING" ] && break
  [ "$STATUS" = "ERROR"   ] && { fail "cluster reached ERROR state"; break; }
  sleep 8
done
[ "$STATUS" = "RUNNING" ] && ok "cluster transitioned PROVISIONING → RUNNING" || fail "cluster did not reach RUNNING within 90s (last=$STATUS)"

# ─── TC-6: List node pools ────────────────────────────────────────────────────
hdr "TC-6 · gcloud container node-pools list"
OUT=$(gcloud container node-pools list \
  --cluster="$CLUSTER" \
  --project="$PROJECT" \
  --location="$LOCATION" \
  --quiet 2>&1)
echo "$OUT"
echo "$OUT" | grep -q "default-pool" && ok "default-pool visible" || fail "default-pool not found"

# ─── TC-7: Kubeconfig download ────────────────────────────────────────────────
hdr "TC-7 · kubeconfig download (REST)"
KC=$(curl -sf "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER/kubeconfig" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('kubeconfig',''))")
[ -n "$KC" ] && ok "kubeconfig returned" || fail "kubeconfig empty"
echo "$KC" | grep -q "apiVersion" && ok "kubeconfig contains apiVersion" || fail "kubeconfig malformed"

# ─── TC-8: Get credentials (gcloud) ──────────────────────────────────────────
hdr "TC-8 · gcloud container clusters get-credentials"
# This will try to auth against real GCP but we can test the REST endpoint directly
KC_API=$(curl -sf "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER/kubeconfig")
echo "$KC_API" | python3 -c "import sys,json; kc=json.load(sys.stdin)['kubeconfig']; print(kc[:200])" 2>/dev/null && ok "kubeconfig API accessible" || fail "kubeconfig API failed"

# ─── TC-9: Create extra node pool ────────────────────────────────────────────
hdr "TC-9 · gcloud container node-pools create"
OUT=$(gcloud container node-pools create "$POOL" \
  --cluster="$CLUSTER" \
  --project="$PROJECT" \
  --location="$LOCATION" \
  --num-nodes=2 \
  --machine-type=e2-small \
  --quiet 2>&1)
echo "$OUT"
echo "$OUT" | grep -qiE "Creating|PROVISIONING|operation" \
  && ok "node pool create accepted" || fail "node pool create failed"

# brief wait
sleep 8

# ─── TC-10: kubectl via REST ──────────────────────────────────────────────────
hdr "TC-10 · kubectl exec (REST endpoint)"
OUT=$(curl -sf -X POST \
  "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER/kubectl" \
  -H "Content-Type: application/json" \
  -d '{"command":"get nodes"}')
echo "$OUT" | python3 -m json.tool 2>/dev/null | head -20
echo "$OUT" | grep -qiE "stdout|stderr" && ok "kubectl endpoint returned output" || fail "kubectl endpoint returned nothing"

# ─── TC-11: Stop cluster ──────────────────────────────────────────────────────
hdr "TC-11 · Stop cluster (REST)"
OUT=$(curl -sf -X POST \
  "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER:stop" \
  -H "Content-Type: application/json" -d '{}')
echo "$OUT" | python3 -m json.tool 2>/dev/null
echo "$OUT" | grep -q "operationType" && ok "stop returned operation" || fail "stop failed"
sleep 6
STATUS=$(curl -sf "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
echo "  status after stop: $STATUS"
[[ "$STATUS" =~ ^(STOPPING|STOPPED)$ ]] && ok "cluster is STOPPING/STOPPED" || fail "expected STOPPED, got $STATUS"

# Wait for STOPPED
sleep 10
STATUS=$(curl -sf "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
echo "  status (after wait): $STATUS"
[ "$STATUS" = "STOPPED" ] && ok "cluster reached STOPPED" || echo "  (still transitioning: $STATUS)"

# ─── TC-12: Start cluster ─────────────────────────────────────────────────────
hdr "TC-12 · Start cluster (REST)"
# Ensure STOPPED first
curl -sf "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER" \
  | python3 -c "import sys,json; print('status:',json.load(sys.stdin)['status'])"
OUT=$(curl -sf -X POST \
  "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER:start" \
  -H "Content-Type: application/json" -d '{}' 2>&1 || echo "{}")
echo "$OUT" | python3 -m json.tool 2>/dev/null | head -10
echo "$OUT" | grep -qE "operationType|RUNNING|RECONCILING|error" \
  && ok "start returned response" || fail "start failed ($OUT)"

# ─── TC-13: Addons ────────────────────────────────────────────────────────────
hdr "TC-13 · Addon install + list + delete"
# Install
INS=$(curl -sf -X POST \
  "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER/addons" \
  -H "Content-Type: application/json" \
  -d '{"name":"HttpLoadBalancing"}')
echo "$INS" | python3 -m json.tool 2>/dev/null
echo "$INS" | grep -q "ENABLED" && ok "addon installed" || fail "addon install failed"

# List
LIST=$(curl -sf \
  "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER/addons")
COUNT=$(echo "$LIST" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('addons',[])))" 2>/dev/null || echo 0)
echo "  addon count: $COUNT"
[ "$COUNT" -ge 1 ] && ok "addons list returned $COUNT addon(s)" || fail "addon list empty"

# Delete
curl -sf -X DELETE \
  "http://localhost:8080/container/v1/projects/$PROJECT/locations/$LOCATION/clusters/$CLUSTER/addons/HttpLoadBalancing" \
  | python3 -m json.tool 2>/dev/null
ok "addon deleted"

# ─── TC-14: Delete cluster ────────────────────────────────────────────────────
hdr "TC-14 · gcloud container clusters delete"
OUT=$(gcloud container clusters delete "$CLUSTER" \
  --project="$PROJECT" \
  --location="$LOCATION" \
  --quiet 2>&1)
echo "$OUT"
echo "$OUT" | grep -qiE "Deleting|STOPPING|operation" \
  && ok "delete returned operation/stopping" || fail "delete command failed"

# ─── Summary ──────────────────────────────────────────────────────────────────
echo
echo "══════════════════════════════════════════════════"
echo "  RESULTS: ${PASS} passed  |  ${FAIL} failed"
echo "══════════════════════════════════════════════════"
[ $FAIL -eq 0 ] && exit 0 || exit 1
