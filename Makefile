# =============================================================================
# Configuration
# =============================================================================

SEMESTER        ?= H2025
REPORT_WRITERS  ?= 12
PYTHON          ?= python3
PIP             ?= pip3
VENV_DIR        ?= venv
REQUIREMENTS    ?= requirements.txt

# =============================================================================
# OS-specific dependency installation
# =============================================================================

## Install Mac dependencies
install-mac:
	brew install $(PYTHON)
	brew install phantomjs
	brew install rename
	brew install pandoc
	$(PIP) install -r $(REQUIREMENTS)

## Install Linux dependencies (requires sudo in most setups)
install-linux:
	sudo apt update
	sudo apt install -y $(PYTHON) python3-pip pandoc
	sudo apt-get install -y texlive-full
	$(PIP) install -r $(REQUIREMENTS)

# =============================================================================
# Python environment
# =============================================================================

## Setup target: create virtual environment and install dependencies
setup: venv
	$(PIP) install -r $(REQUIREMENTS)

## Virtual Environment
venv:
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Activate virtual environment by running 'source $(VENV_DIR)/bin/activate'"

## Install pip dependencies (system pip)
pip-install:
	pip install -r $(REQUIREMENTS)

## Install pip3 dependencies (system pip3)
pip3-install:
	$(PIP) install -r $(REQUIREMENTS)

# =============================================================================
# Data acquisition and preparation
# =============================================================================

## Download reports
download:
	$(PYTHON) fui_kk/download_reports.py

## Download course list
download_course_list:
	$(PYTHON) fui_kk/download_course_list.py -o courses/courses_info.json

## Sort downloaded files
sort_downloads:
	$(PYTHON) fui_kk/sort_downloads.py

## Setup sample data
sample_data:
	git submodule init
	git submodule update
	cp -r sample_data data

# =============================================================================
# Processing and generation
# =============================================================================

## Custom data scales processing
scales:
	$(PYTHON) fui_kk/scales.py all

## Process responses
responses:
	$(PYTHON) fui_kk/responses.py -s all

## JSON generation from courses and semester data
json: course semester courses

course:
	$(PYTHON) fui_kk/course.py data

semester:
	$(PYTHON) fui_kk/semester.py

courses:
	$(PYTHON) fui_kk/courses.py

## Generate plots
plots:
	rm -rf ./data/$(SEMESTER)/outputs/plots
	$(PYTHON) fui_kk/plot_courses.py $(SEMESTER)

# =============================================================================
# TeX / PDF / Web
# =============================================================================

## TeX report generation
tex:
	perl -i.bak -pe 's/\x61\xCC\x8A/\xC3\xA5/g' ./data/*/inputs/md/*.md
	find ./data -type f -name '*.md.bak' -delete
	bash ./fui_kk/tex.sh $(SEMESTER)
	$(PYTHON) fui_kk/participation_summary.py $(SEMESTER)
	$(PYTHON) fui_kk/tex_combine.py -s $(SEMESTER)

## PDFs generation from TeX
pdf: tex
	bash ./fui_kk/pdf.sh $(SEMESTER)

## Generate the webpages
web:
	bash ./fui_kk/web.sh $(SEMESTER)
	$(PYTHON) ./fui_kk/web_reports.py data/$(SEMESTER)

## Preview webpage on docs folder with warning message
web-preview: web
	@echo "---------------------------------------------"
	@echo " WARNING: Do NOT commit changes to ./docs if"
	@echo " you are working with real data!"
	@echo "---------------------------------------------"
	rm -rf ./docs
	mkdir ./docs
	cp -r ./data/$(SEMESTER)/outputs/web/upload/$(SEMESTER)/* ./docs
	$(PYTHON) ./fui_kk/adapt_preview_html.py

## Open generated reports
open:
	open data/$(SEMESTER)/outputs/report/fui-kk_report*.pdf

# =============================================================================
# Misc operations
# =============================================================================

## Assign courses to report writers and output to JSON
assign-courses:
	$(PYTHON) fui_kk/course_divide.py names $(SEMESTER) > REPORT_WRITERS.json
	cat REPORT_WRITERS.json

## Upload raw data
upload_raw:
	$(PYTHON) fui_kk/upload_raw_data.py -v -s $(SEMESTER)

## Compute score
score:
	$(PYTHON) ./fui_kk/score.py all

# =============================================================================
# Cleaning
# =============================================================================

## Clean data outputs
clean-output:
	find ./data -type d -name "outputs" -exec rm -rf {} +

## Clean entire data folder
clean-data:
	rm -rf ./data/

## Clean downloads
clean-downloads:
	rm -rf ./downloads

## Clean everything including resources
super-clean: clean-data clean-downloads clean-output

# =============================================================================
# Composite targets
# =============================================================================

## Full pipeline
all: responses scales json plots tex pdf web

# =============================================================================
# Help
# =============================================================================

help:
	@echo "Available targets:"
	@echo "  install-mac          - Install dependencies on macOS"
	@echo "  install-linux        - Install dependencies on Linux"
	@echo "  setup                - Create venv and install requirements"
	@echo "  venv                 - Create virtual environment"
	@echo "  pip-install          - Install Python deps (system pip)"
	@echo "  pip3-install         - Install Python deps (system pip3)"
	@echo "  download             - Download reports"
	@echo "  download_course_list - Download course list metadata"
	@echo "  sort_downloads       - Sort downloaded data"
	@echo "  sample_data          - Setup sample data"
	@echo "  responses            - Process responses"
	@echo "  scales               - Process custom scales"
	@echo "  json                 - Generate JSON (course+semester+courses)"
	@echo "  course               - Generate per-course JSON"
	@echo "  semester             - Generate semester JSON"
	@echo "  courses              - Generate courses JSON"
	@echo "  plots                - Generate plots"
	@echo "  tex                  - Generate TeX reports"
	@echo "  pdf                  - Generate PDFs"
	@echo "  web                  - Generate webpages"
	@echo "  web-preview          - Generate docs/ preview with warning"
	@echo "  open                 - Open generated reports"
	@echo "  upload_raw           - Upload raw data"
	@echo "  score                - Compute scores"
	@echo "  clean-output         - Remove output folders under data/"
	@echo "  clean-data           - Remove data/ folder"
	@echo "  clean-downloads      - Remove downloads/ folder"
	@echo "  super-clean          - Remove data, downloads, and outputs"
	@echo "  assign-courses       - Assign courses to report writers"
	@echo "  all                  - Run full pipeline"

# =============================================================================
# Phony targets
# =============================================================================

.PHONY: \
	install-mac install-linux \
	setup venv pip-install pip3-install \
	download download_course_list sort_downloads sample_data \
	scales responses json course semester courses \
	plots tex pdf web web-preview open \
	assign-courses upload_raw score \
	clean-output clean-data clean-downloads super-clean \
	all help
