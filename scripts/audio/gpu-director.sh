#!/usr/bin/env bash
# gpu-director — manage the heterogeneous GPU pool for AI workloads.
#
# The cluster has NVIDIA (CUDA) + AMD (ROCm/Vulkan) GPUs. Miners occupy most
# NVIDIA cards. This director:
#   - inventories the pool (which GPUs exist, what's mining, what's free)
#   - pauses/resumes miners per host (revenue-logged)
#   - dispatches an AI job to a specific GPU via the right visibility var
#     (CUDA_VISIBLE_DEVICES for NVIDIA, ROCR_VISIBLE_DEVICES/HIP_VISIBLE_DEVICES
#      for AMD, GGML_VULKAN_DEVICE for llama.cpp-Vulkan)
#
# Usage:
#   gpu-director.sh status                      # inventory + mining state
#   gpu-director.sh pause [host...]             # stop miners (default: all)
#   gpu-director.sh resume [host...]            # start miners (default: all)
#   gpu-director.sh run --gpu <id> --cmd "<cmd>"  # run a job on one GPU
#
# GPU ids (forge example): nvidia:0 nvidia:1 amd:0 amd:1 (per host, host:gpu)

set -euo pipefail

LOG="/var/log/gpu-director.log"
MINER_UNITS=(
  "zephyr:peakminer-3060ti.service"
  "nexus:peakminer-nexus-3060ti.service"
  "forge:peakminer-dropin-forge-4060-0.service"
  "forge:peakminer-dropin-forge-4060-1.service"
)
HOSTS=(zephyr nexus forge)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

reachable() { ssh -o ConnectTimeout=3 -o BatchMode=yes "$1" true 2>/dev/null; }

status() {
  echo "=== GPU Director — Cluster Inventory ==="
  echo "--- zephyr (local) ---"
  nvidia-smi --query-gpu=index,name,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null || echo "no nvidia"
  for h in nexus forge; do
    echo "--- $h ---"
    if reachable "$h"; then
      ssh "$h" "nvidia-smi --query-gpu=index,name,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null; echo 'AMD:'; ls /dev/dri/renderD* 2>/dev/null | wc -l" 2>/dev/null || echo "unreachable"
    else
      echo "unreachable"
    fi
  done
  echo "--- Mining state ---"
  for entry in "${MINER_UNITS[@]}"; do
    host="${entry%%:*}"; unit="${entry##*:}"
    if [ "$host" = "zephyr" ] || reachable "$host"; then
      if [ "$host" = "zephyr" ]; then
        state=$(systemctl is-active "$unit" 2>/dev/null || echo "unknown")
      else
        state=$(ssh "$host" "systemctl is-active '$unit' 2>/dev/null" 2>/dev/null || echo "unknown")
      fi
      echo "  $host:$unit = $state"
    else
      echo "  $host:$unit = unreachable"
    fi
  done
}

pause() {
  local targets=("$@")
  [ ${#targets[@]} -eq 0 ] && targets=("${HOSTS[@]}")
  log "=== PAUSE miners on: ${targets[*]} ==="
  for host in "${targets[@]}"; do
    for entry in "${MINER_UNITS[@]}"; do
      [[ "$entry" == "$host:"* ]] || continue
      unit="${entry##*:}"
      if [ "$host" = "zephyr" ] || reachable "$host"; then
        if [ "$host" = "zephyr" ]; then
          systemctl stop "$unit" 2>/dev/null && log "  PAUSED $host:$unit" || log "  (stop failed/already stopped) $host:$unit"
        else
          ssh "$host" "systemctl stop '$unit'" 2>/dev/null && log "  PAUSED $host:$unit" || log "  (stop failed/already stopped) $host:$unit"
        fi
      fi
    done
  done
}

resume() {
  local targets=("$@")
  [ ${#targets[@]} -eq 0 ] && targets=("${HOSTS[@]}")
  log "=== RESUME miners on: ${targets[*]} ==="
  for host in "${targets[@]}"; do
    for entry in "${MINER_UNITS[@]}"; do
      [[ "$entry" == "$host:"* ]] || continue
      unit="${entry##*:}"
      if [ "$host" = "zephyr" ] || reachable "$host"; then
        if [ "$host" = "zephyr" ]; then
          systemctl start "$unit" 2>/dev/null && log "  RESUMED $host:$unit" || log "  (start failed) $host:$unit"
        else
          ssh "$host" "systemctl start '$unit'" 2>/dev/null && log "  RESUMED $host:$unit" || log "  (start failed) $host:$unit"
        fi
      fi
    done
  done
}

# run --gpu <host:type:idx> --cmd "<cmd>"
run_job() {
  local gpu_spec="" cmd=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --gpu) gpu_spec="$2"; shift 2 ;;
      --cmd) cmd="$2"; shift 2 ;;
      *) echo "unknown: $1"; exit 2 ;;
    esac
  done
  [ -n "$gpu_spec" ] && [ -n "$cmd" ] || { echo "run needs --gpu host:type:idx and --cmd"; exit 2; }
  IFS=':' read -r host gtype gidx <<< "$gpu_spec"
  log "RUN on $host ($gtype GPU idx $gidx): $cmd"
  case "$gtype" in
    nvidia)
      if [ "$host" = "zephyr" ]; then
        CUDA_VISIBLE_DEVICES="$gidx" bash -c "$cmd"
      else
        ssh "$host" "CUDA_VISIBLE_DEVICES='$gidx' bash -c '$cmd'"
      fi
      ;;
    amd|vulkan)
      if [ "$host" = "zephyr" ]; then
        HIP_VISIBLE_DEVICES="$gidx" ROCR_VISIBLE_DEVICES="$gidx" GGML_VULKAN_DEVICE="$gidx" bash -c "$cmd"
      else
        ssh "$host" "HIP_VISIBLE_DEVICES='$gidx' ROCR_VISIBLE_DEVICES='$gidx' GGML_VULKAN_DEVICE='$gidx' bash -c '$cmd'"
      fi
      ;;
    *) echo "unknown gpu type: $gtype (nvidia|amd|vulkan)"; exit 2 ;;
  esac
  log "DONE: $cmd"
}

case "${1:-}" in
  status) status ;;
  pause) shift; pause "$@" ;;
  resume) shift; resume "$@" ;;
  run) shift; run_job "$@" ;;
  *) echo "usage: $0 {status|pause [hosts]|resume [hosts]|run --gpu host:type:idx --cmd}"; exit 2 ;;
esac
