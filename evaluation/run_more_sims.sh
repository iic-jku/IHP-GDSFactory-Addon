#!/bin/bash
# Simulate every GDS file in the given folders (or the given files), then convert
# the Palace results to Touchstone with combine_snp.py.
#
# With SKIP_DONE=1, a model whose .sim_done marker matches the current
# CONDUCTOR_MODEL / REFINED_CELLSIZE is skipped, so an interrupted sweep resumes
# where it stopped. A failed model is reported and the sweep continues; the script
# exits non-zero at the end if any model failed.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <folder_or_file> [folder_or_file ...]"
  exit 1
fi

gds_files=()

for input_path in "$@"; do
  if [ -d "$input_path" ]; then
    while IFS= read -r file; do
      gds_files+=("$file")
    done < <(find "$input_path" -maxdepth 1 -type f -iname "*.gds" | sort)
  elif [ -f "$input_path" ]; then
    gds_files+=("$input_path")
  else
    echo "Skipping: $input_path (not a valid file/folder)"
  fi
done

if [ "${#gds_files[@]}" -eq 0 ]; then
  echo "No .gds files found in provided inputs."
  exit 1
fi

expected_marker=$(printf 'conductor_model=%s\nrefined_cellsize=%s' \
    "${CONDUCTOR_MODEL:-solve_inside_skin}" "${REFINED_CELLSIZE:-2}")

failed=()
n=0
for gds in "${gds_files[@]}"; do
  n=$((n + 1))
  marker="${gds%.*}/.sim_done"
  if [ "${SKIP_DONE:-0}" = "1" ] && [ -f "$marker" ] && [ "$(cat "$marker")" = "$expected_marker" ]; then
    echo "[$n/${#gds_files[@]}] already done, skipping: $gds"
    continue
  fi

  echo "=============================="
  echo "[$n/${#gds_files[@]}] $(date '+%F %T') Running simulation for: $gds"
  echo "=============================="

  "$SCRIPT_DIR/run_sim.sh" "$gds" || failed+=("$gds")
done

# combine_snp.py converts everything below the current directory, so run it per input
for input_path in "$@"; do
  if [ -d "$input_path" ]; then
    (cd "$input_path" && python3 "$SCRIPT_DIR/combine_snp.py")
  elif [ -d "${input_path%.*}" ]; then
    (cd "${input_path%.*}" && python3 "$SCRIPT_DIR/combine_snp.py")
  fi
done

if [ "${#failed[@]}" -gt 0 ]; then
  echo "${#failed[@]} of ${#gds_files[@]} simulations FAILED:"
  printf '  %s\n' "${failed[@]}"
  exit 1
fi
