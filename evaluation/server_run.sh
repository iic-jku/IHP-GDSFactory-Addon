#!/bin/bash
# Unattended re-run of the whole evaluation inside the IIC-OSIC-TOOLS image
# (gds2palace >= 0.9.0, i.e. the nightly image or 2026.11+):
#
#   cd <repo>/evaluation
#   git pull
#   nohup ./server_run.sh > /dev/null 2>&1 &     # or run it inside tmux/screen
#
# Generates every sweep, simulates it, converts the results to .sNp and redraws
# the plots. Output is logged to logs/server_<date>.log (follow it with tail -f).
# Run it again after an interruption: models that already finished with the same
# settings are skipped.
#
# Environment overrides (defaults in brackets):
#   SWEEPS            sweeps to run, in order [blc wpd tline-sparams tline-z0 tline-loss]
#   CONDUCTOR_MODEL   surface | solve_inside | solve_inside_skin [solve_inside_skin]
#   REFINED_CELLSIZE  mesh cell size in the conductors, um [2]
#   PALACE_NP         MPI processes per Palace run [all physical cores]

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR" || exit 1

SWEEPS=${SWEEPS:-"blc wpd tline-sparams tline-z0 tline-loss"}
export CONDUCTOR_MODEL=${CONDUCTOR_MODEL:-solve_inside_skin}
export REFINED_CELLSIZE=${REFINED_CELLSIZE:-2}
export MPLBACKEND=Agg

mkdir -p logs
LOG="logs/server_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1

start=$(date +%s)
echo "=== server_run.sh started $(date '+%F %T') on $(hostname), log: $SCRIPT_DIR/$LOG"

die() {
    echo "ERROR: $*"
    exit 1
}

# --- environment checks -------------------------------------------------------
# The image doesn't ship the ihp package, use this checkout. The image puts its
# system site-packages on PYTHONPATH, which also wins over any activated venv.
[ -n "$VIRTUAL_ENV" ] && echo "WARNING: venv $VIRTUAL_ENV is active, the image's PYTHONPATH packages take precedence over it"
export PYTHONPATH="$REPO_DIR${PYTHONPATH:+:$PYTHONPATH}"

# ihp needs doroutes, which the image doesn't have; 0.4.0 works with the image's kfactory
if ! python3 -c "import doroutes" 2>/dev/null; then
    echo "Installing doroutes into the user site-packages"
    pip3 install --user --break-system-packages "doroutes==0.4.0" || die "could not install doroutes"
fi

[ -d "${PDK_ROOT:-/foss/pdks}/ihp-sg13g2" ] || die "IHP PDK not found under PDK_ROOT=${PDK_ROOT:-/foss/pdks}"
command -v palace > /dev/null || die "palace not on PATH, run this inside the IIC-OSIC-TOOLS image"
python3 -c "import ihp" || die "cannot import ihp from $REPO_DIR"

if [ "$CONDUCTOR_MODEL" != surface ]; then
    python3 - <<'EOF' || die "conductor_model $CONDUCTOR_MODEL needs gds2palace >= 0.9.0 (use the nightly image, ghcr.io/iic-jku/iic-osic-tools:nightly)"
import gds2palace, sys
sys.exit(tuple(int(x) for x in gds2palace.__version__.split(".")[:2]) < (0, 9))
EOF
fi

echo "repo:             $(git -C "$REPO_DIR" log -1 --format='%h %s' 2>/dev/null)"
echo "image:            $(cat /dockerstartup/build.txt 2>/dev/null || echo unknown)"
python3 -c "import gds2palace, gdsfactory, skrf; print(f'gds2palace:       {gds2palace.__version__}\ngdsfactory:       {gdsfactory.__version__}\nscikit-rf:        {skrf.__version__}')"
echo "palace:           $(palace --version 2>/dev/null | head -1)"
echo "conductor_model:  $CONDUCTOR_MODEL"
echo "refined_cellsize: $REFINED_CELLSIZE um"
echo "MPI processes:    ${PALACE_NP:-all physical cores} ($(lscpu -p=Core,Socket 2>/dev/null | grep -v '^#' | sort -u | wc -l) cores, $(nproc) threads)"
echo "sweeps:           $SWEEPS"

# --- generate + simulate -------------------------------------------------------
failed=()
for sweep in $SWEEPS; do
    echo
    echo "=== $(date '+%F %T') sweep $sweep"
    make --no-print-directory "generate-$sweep" || { failed+=("generate-$sweep"); continue; }
    SKIP_DONE=1 make --no-print-directory "sim-$sweep" || failed+=("sim-$sweep")
done

# --- plots ---------------------------------------------------------------------
echo
echo "=== $(date '+%F %T') plots"
make --no-print-directory plot || failed+=("plot")

# meshes and raw Palace output are large; keep them if something failed, for debugging
if [ "${#failed[@]}" -eq 0 ]; then
    make --no-print-directory clean-sim-raw
fi

elapsed=$(($(date +%s) - start))
echo
echo "=== server_run.sh finished $(date '+%F %T') after $((elapsed / 3600))h $((elapsed % 3600 / 60))min"
if [ "${#failed[@]}" -gt 0 ]; then
    echo "FAILED steps: ${failed[*]} (see the log above, re-run ./server_run.sh to retry them)"
    exit 1
fi
echo "All sweeps done. New results: gds/**/*.sNp and images/"
