#!/usr/bin/env bash
set -euo pipefail

echo "[bootstrap] Cloning and installing TripoSR and Zero123++ (if not present)"

if [ ! -d /opt/TripoSR ]; then
  git clone https://github.com/facebookresearch/TripoSR.git /opt/TripoSR || true
  (cd /opt/TripoSR && pip3 install -e .) || true
fi

if [ ! -d /opt/zero123plus ]; then
  git clone https://github.com/ashawkey/zero123plus.git /opt/zero123plus || true
  (cd /opt/zero123plus && pip3 install -e .) || true
fi

echo "[bootstrap] Done"


