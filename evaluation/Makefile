# IHP SG13G2 RF evaluation pipeline. See README.md for the full description.
# `make help` lists every target. Each target's `## ` text drives that help output.

MAKEFILE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
PYTHON := python3
# Keep GDS_DIR/IMAGES_DIR as plain `:=` with NO trailing inline comment - make folds
# the whitespace before a `#` into the value and would corrupt the paths.
GDS_DIR    := $(MAKEFILE_DIR)/gds
IMAGES_DIR := $(MAKEFILE_DIR)/images

# Palace model settings, read by palace_sim.py (CONDUCTOR_MODEL needs gds2palace >= 0.9.0):
# surface | solve_inside | solve_inside_skin, and the mesh cell size in the conductors (um)
CONDUCTOR_MODEL  ?= solve_inside_skin
REFINED_CELLSIZE ?= 2
export CONDUCTOR_MODEL REFINED_CELLSIZE

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make <target>'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-24s %s\n", $$1, $$2}'
.PHONY: help

# --- generate ---
generate-blc: ## Generate the branch-line-coupler GDS sweep (gds/blc)
	cd $(MAKEFILE_DIR) && $(PYTHON) generate_blc.py
.PHONY: generate-blc

generate-wpd: ## Generate the Wilkinson-power-divider GDS sweep (gds/wpd)
	cd $(MAKEFILE_DIR) && $(PYTHON) generate_wpd.py
.PHONY: generate-wpd

BPF_FREQS ?= 60 160 300
generate-bpf: ## Generate the hairpin BPF of the paper (gds/bpf; Butterworth, order 3, 5 % BW; BPF_FREQS in GHz)
	cd $(MAKEFILE_DIR) && $(PYTHON) generate_bpf.py $(BPF_FREQS)
.PHONY: generate-bpf

generate-tline-sparams: ## Generate the tline S-parameter verification sweep (gds/tline_sparams)
	cd $(MAKEFILE_DIR) && $(PYTHON) generate_tline_sparams.py
.PHONY: generate-tline-sparams

generate-tline-z0: ## Generate the tline Z0(w) sweep (gds/tline_z0)
	cd $(MAKEFILE_DIR) && $(PYTHON) generate_tline_z0.py
.PHONY: generate-tline-z0

generate-tline-loss: ## Generate the tline loss(w)/mm sweep (gds/tline_loss)
	cd $(MAKEFILE_DIR) && $(PYTHON) generate_tline_loss.py
.PHONY: generate-tline-loss

generate-tline: generate-tline-sparams generate-tline-z0 generate-tline-loss ## Generate all tline GDS sweeps
.PHONY: generate-tline

generate: generate-blc generate-wpd generate-tline ## Generate all GDS sweeps
.PHONY: generate

# --- sim (slow: many Palace runs per sweep) ---
sim-blc: ## Run Palace simulations on all generated BLC GDS files
	cd $(MAKEFILE_DIR) && ./run_more_sims.sh $(GDS_DIR)/blc
.PHONY: sim-blc

sim-wpd: ## Run Palace simulations on all generated WPD GDS files
	cd $(MAKEFILE_DIR) && ./run_more_sims.sh $(GDS_DIR)/wpd
.PHONY: sim-wpd

sim-bpf: ## Run Palace simulations on all generated BPF GDS files
	cd $(MAKEFILE_DIR) && ./run_more_sims.sh $(GDS_DIR)/bpf
.PHONY: sim-bpf

sim-tline-sparams: ## Run Palace simulations on the tline S-parameter verification sweep
	cd $(MAKEFILE_DIR) && ./run_more_sims.sh $(GDS_DIR)/tline_sparams
.PHONY: sim-tline-sparams

sim-tline-z0: ## Run Palace simulations on the tline Z0(w) sweep
	cd $(MAKEFILE_DIR) && ./run_more_sims.sh $(GDS_DIR)/tline_z0
.PHONY: sim-tline-z0

sim-tline-loss: ## Run Palace simulations on the tline loss(w)/mm sweep
	cd $(MAKEFILE_DIR) && ./run_more_sims.sh $(GDS_DIR)/tline_loss
.PHONY: sim-tline-loss

sim-tline: sim-tline-sparams sim-tline-z0 sim-tline-loss ## Run Palace simulations on all tline GDS sweeps
.PHONY: sim-tline

sim: sim-blc sim-wpd sim-tline ## Run all Palace simulations, then drop intermediates (keeps .sNp)
	$(MAKE) clean-intermediates
.PHONY: sim

server: ## Unattended full re-run inside the IIC-OSIC-TOOLS image: generate + sim (resumable) + plot, see server_run.sh
	cd $(MAKEFILE_DIR) && ./server_run.sh
.PHONY: server

# --- plot ---
Z0_SHOW ?= --show
FREQ ?=
EVAL_FREQ ?=
plot-tline-z0: ## Plot Z0(w) by ground layer (FREQ=/EVAL_FREQ= to pick frequencies, Z0_SHOW= for batch)
	cd $(MAKEFILE_DIR) && for f in $(if $(FREQ),$(FREQ),$$(ls -d $(GDS_DIR)/tline_z0/*GHz 2>/dev/null | sed -E 's/.*_([0-9.]+)GHz$$/\1/' | sort -n -u)); do \
		$(PYTHON) plot_tline.py z0 $(GDS_DIR)/tline_z0 --freq $$f $(if $(EVAL_FREQ),--eval-freq $(EVAL_FREQ)) --length-um 1000 $(Z0_SHOW); \
	done
.PHONY: plot-tline-z0

plot-tline-z0-freq: ## Plot Zc vs frequency (dispersion) per stack + open interactive window
	cd $(MAKEFILE_DIR) && $(PYTHON) plot_tline.py z0-freq $(GDS_DIR)/tline_z0 $(Z0_SHOW)
.PHONY: plot-tline-z0-freq

SIGNAL ?= topmetal2
GROUND ?= metal5
plot-tline-z0-3d: ## 3D surface of Zc over (freq, width) for one stack (SIGNAL=/GROUND= to pick)
	cd $(MAKEFILE_DIR) && $(PYTHON) plot_tline.py z0-3d $(GDS_DIR)/tline_z0 --signal $(SIGNAL) --ground $(GROUND) $(Z0_SHOW)
.PHONY: plot-tline-z0-3d

plot-tline-mismatch: ## Loss from |S21| vs NRW-extracted loss against Zc, single line (FREQ=/EVAL_FREQ=, Z0_SHOW= for batch)
	cd $(MAKEFILE_DIR) && for f in $(if $(FREQ),$(FREQ),$$(ls -d $(GDS_DIR)/tline_z0/*GHz 2>/dev/null | sed -E 's/.*_([0-9.]+)GHz$$/\1/' | sort -n -u)); do \
		$(PYTHON) plot_tline.py mismatch $(GDS_DIR)/tline_z0 --freq $$f $(if $(EVAL_FREQ),--eval-freq $(EVAL_FREQ)) --length-um 1000 $(Z0_SHOW); \
	done
.PHONY: plot-tline-mismatch

plot-tline-loss: ## Plot loss(w)/mm faceted by ground layer, for every simulated frequency (two-length de-embedded)
	cd $(MAKEFILE_DIR) && for f in $(if $(FREQ),$(FREQ),$$(ls -d $(GDS_DIR)/tline_loss/*GHz 2>/dev/null | sed -E 's/.*_([0-9.]+)GHz$$/\1/' | sort -n -u)); do \
		$(PYTHON) plot_tline.py loss $(GDS_DIR)/tline_loss --freq $$f $(if $(EVAL_FREQ),--eval-freq $(EVAL_FREQ)) --length1-um 500 --length2-um 1000; \
	done
.PHONY: plot-tline-loss

plot-tline-design: ## Z0-vs-loss design chart, one point per stack+width (needs z0 AND loss sims)
	cd $(MAKEFILE_DIR) && for f in $(if $(FREQ),$(FREQ),$$(ls -d $(GDS_DIR)/tline_loss/*GHz 2>/dev/null | sed -E 's/.*_([0-9.]+)GHz$$/\1/' | sort -n -u)); do \
		$(PYTHON) plot_tline.py design $(GDS_DIR)/tline_z0 $(GDS_DIR)/tline_loss --freq $$f $(Z0_SHOW); \
	done
.PHONY: plot-tline-design

plot-tline-sparams: ## Overlay raw S21/S11 vs freq for hand-picked files (set FILES="...")
	@test -n "$(FILES)" || { echo 'set FILES, e.g. make plot-tline-sparams FILES="gds/tline_sparams/a gds/tline_sparams/b"'; exit 1; }
	cd $(MAKEFILE_DIR) && $(PYTHON) plot_tline.py sparams $(FILES)
.PHONY: plot-tline-sparams

plot-tline: Z0_SHOW :=
plot-tline: plot-tline-z0 plot-tline-z0-freq plot-tline-z0-3d plot-tline-mismatch plot-tline-loss plot-tline-design ## Generate all tline plots into images/
.PHONY: plot-tline

plot-blc: ## Plot branch-line-coupler S-params, imbalance, phase + summary (images/)
	cd $(MAKEFILE_DIR) && $(PYTHON) plot_blc.py $(GDS_DIR)/blc
.PHONY: plot-blc

plot-wpd: ## Plot Wilkinson-divider S-params, imbalance, phase + summary (images/)
	cd $(MAKEFILE_DIR) && $(PYTHON) plot_wpd.py $(GDS_DIR)/wpd
.PHONY: plot-wpd

plot-bpf: ## Plot BPF S11/S21 over f/f0 + summary, curve CSVs in images/bpf_curves (BPF_PLOT_ARGS=--raw for raw files)
	cd $(MAKEFILE_DIR) && $(PYTHON) plot_bpf.py $(GDS_DIR)/bpf $(BPF_PLOT_ARGS)
.PHONY: plot-bpf

plot: plot-tline plot-blc plot-wpd ## Generate every plot (tline + blc + wpd)
.PHONY: plot

# --- img (layout preview PNGs; needs PDK_ROOT/PDK set to the IHP PDK) ---
IMG_DIR          := $(IMAGES_DIR)
IMG_OVERSAMPLING ?= 4
IMG_FREQ         ?= 200
IMG_BG           ?= black

img-blc: ## Render the TM2/M5 branch-line-coupler at IMG_FREQ GHz, black (images/)
	mkdir -p $(IMG_DIR)
	cd $(MAKEFILE_DIR) && f=$(GDS_DIR)/blc/blc_$(IMG_FREQ)GHz.gds; \
		test -f "$$f" || { echo "no such layout: $$f (run make generate-blc)"; exit 1; }; \
		$(PYTHON) lay2img.py "$$f" $(IMG_DIR)/$$(basename "$$f" .gds).png --oversampling $(IMG_OVERSAMPLING) --background $(IMG_BG)
.PHONY: img-blc

img-wpd: ## Render the TM2/M5 Wilkinson-power-divider at IMG_FREQ GHz, black (images/)
	mkdir -p $(IMG_DIR)
	cd $(MAKEFILE_DIR) && f=$(GDS_DIR)/wpd/wpd_$(IMG_FREQ)GHz.gds; \
		test -f "$$f" || { echo "no such layout: $$f (run make generate-wpd)"; exit 1; }; \
		$(PYTHON) lay2img.py "$$f" $(IMG_DIR)/$$(basename "$$f" .gds).png --oversampling $(IMG_OVERSAMPLING) --background $(IMG_BG)
.PHONY: img-wpd

img-tline: ## Render the TM2/M5 w20um l500um loss tline at IMG_FREQ GHz, black (images/)
	mkdir -p $(IMG_DIR)
	cd $(MAKEFILE_DIR) && f=$(GDS_DIR)/tline_loss/tline_topmetal2_over_metal5_w20um_l500um_$(IMG_FREQ)GHz.gds; \
		test -f "$$f" || { echo "no such layout: $$f (run make generate-tline-loss)"; exit 1; }; \
		$(PYTHON) lay2img.py "$$f" $(IMG_DIR)/$$(basename "$$f" .gds).png --oversampling $(IMG_OVERSAMPLING) --background $(IMG_BG)
.PHONY: img-tline

img: ## Render layout PNGs for hand-picked GDS files, black (set FILES="a.gds b.gds ...")
	@test -n "$(FILES)" || { echo 'set FILES, e.g. make img FILES="gds/blc/blc_160GHz.gds gds/wpd/wpd_160GHz.gds"'; exit 1; }
	mkdir -p $(IMG_DIR)
	cd $(MAKEFILE_DIR) && for f in $(FILES); do \
		$(PYTHON) lay2img.py "$$f" $(IMG_DIR)/$$(basename "$$f" .gds).png --oversampling $(IMG_OVERSAMPLING) --background $(IMG_BG); \
	done
.PHONY: img

img-all: img-blc img-wpd img-tline ## Render TM2/M5 blc + wpd + tline at IMG_FREQ GHz, black (images/)
.PHONY: img-all

all: generate sim plot ## Generate every GDS sweep, simulate, and plot all of it (very slow)
.PHONY: all

# --- cleanup ---
clean-sim-raw: ## Delete meshes + raw Palace output, keep .sNp results + port_information.json (saves most disk)
	find $(GDS_DIR) -type f -name '*.msh' -delete 2>/dev/null || true
	find $(GDS_DIR) -type d -name 'paraview' -prune -exec rm -rf {} + 2>/dev/null || true
	find $(GDS_DIR) -type f \( -name 'port-*.csv' -o -name 'domain-E.csv' -o -name 'error-indicators.csv' \) -delete 2>/dev/null || true
	find $(GDS_DIR) -type f -name '*.json' ! -name 'port_information*.json' -delete 2>/dev/null || true
.PHONY: clean-sim-raw

clean-layouts: ## Delete the generated .gds layout files (regenerate with `make generate`)
	find $(GDS_DIR) -type f -name '*.gds' -delete 2>/dev/null || true
.PHONY: clean-layouts

clean-intermediates: clean-sim-raw clean-layouts ## Delete all sim intermediates + layouts, keep only .sNp results
.PHONY: clean-intermediates

clean: ## DELETE all generated GDS + sim data incl. .sNp results (destructive, local only)
	rm -rf $(GDS_DIR)
.PHONY: clean

clean-images: ## Remove generated plots, CSVs + layout previews (images/)
	rm -rf $(IMAGES_DIR)
.PHONY: clean-images

clean-all: clean clean-images ## Remove everything generated (gds/ + images/)
.PHONY: clean-all
