#!/bin/bash
# Simulate one GDS file: build the Palace model with palace_sim.py, then run Palace.
# Exits non-zero if either step fails. On success it writes <model dir>/.sim_done,
# which run_more_sims.sh uses to skip finished models when a sweep is resumed.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# input argument
GDS_FILE="$(realpath "$1")"

# strip extension -> folder name
BASENAME="${GDS_FILE%.*}"

# palace_sim.py names the model after the GDS file, so the data directory,
# the Palace output directory and the .sNp all carry MODEL rather than the script name
MODEL="$(basename "$BASENAME")"

echo "GDS file   : $GDS_FILE"
echo "Folder name: $BASENAME"

# start from an empty model folder, so a failed run can't leave the previous
# result (e.g. an older conductor model) behind to be picked up by the plots
rm -rf "$BASENAME"

# create palace config file
python3 "$SCRIPT_DIR/palace_sim.py" "$GDS_FILE" || { echo "palace_sim.py failed for $GDS_FILE"; exit 1; }

# change directory and run palace
cd "${BASENAME}/${MODEL}_data" || exit 1
# MPI ranks: all physical cores unless PALACE_NP is set (lower it on machines shared
# with other users). Not nproc: that counts hyperthreads, and Open MPI only grants one
# slot per physical core, so mpirun refuses to start with nproc ranks on SMT machines.
PHYS_CORES=$(lscpu -p=Core,Socket 2>/dev/null | grep -v '^#' | sort -u | wc -l)
(( PHYS_CORES < 1 )) && PHYS_CORES=$(nproc)
NP=${PALACE_NP:-$PHYS_CORES}
(( NP < 1 )) && NP=1
palace -np "$NP" config.json || { echo "Palace failed for $GDS_FILE"; exit 1; }

# record what this result was simulated with
printf 'conductor_model=%s\nrefined_cellsize=%s\n' \
    "${CONDUCTOR_MODEL:-solve_inside_skin}" "${REFINED_CELLSIZE:-2}" > "${BASENAME}/.sim_done"

echo "${BASENAME} completed."
