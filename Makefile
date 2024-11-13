# Variables SETTINGS
SEMESTER = V2024
REPORT_WRITERS = 12
MOUNT_PATH = /Volumes/fui/kursevaluering
# MOUNT_PATH = Z:/fui
# MOUNT_PATH = /mnt/fui

# Install Mac dependencies
install-mac:
	brew install python3
	brew install phantomjs
	brew install rename
	brew install pandoc
	pip3 install -r requirements.txt

# Install Linux dependencies
install-linux:
	apt install python3
	apt install python3-pip
	apt install pandoc
	apt-get install texlive-full
	pip3 install -r requirements.txt

# Setup target: install dependencies and create virtual environment
setup: venv
	pip install -r requirements.txt

# Virtual Environment
venv:
	python3 -m venv venv
	@echo "Activate virtual environment by running 'source venv/bin/activate'"

# Download reports
download:
	python3 fui_kk/download_reports.py

download_course_list:
	python3 fui_kk/download_course_list.py -o courses/courses_info.json

sort_downloads:
	python3 fui_kk/sort_downloads.py 

# Setup sample data
sample_data:
	git submodule init
	git submodule update
	cp -r sample_data data

# Custom data scales processing
scales:
	python3 fui_kk/scales.py all

# Process responses
responses:
	python3 fui_kk/responses.py -s all

# JSON generation from courses and semester data
json: course semester courses

course:
	python3 fui_kk/course.py data

semester:
	python3 fui_kk/semester.py

courses:
	python3 fui_kk/courses.py

# Generate plots
plots:
	rm -rf ./data/$(SEMESTER)/outputs/plots 
	python3 fui_kk/plot_courses.py all

# TeX report generation
tex:
	perl -i.bak -pe 's/\x61\xCC\x8A/\xC3\xA5/g' ./data/*/inputs/md/*.md
	find ./data -type f -name *.md.bak -delete
	bash ./fui_kk/tex.sh $(SEMESTER)
	python3 fui_kk/participation_summary.py $(SEMESTER)
	python3 fui_kk/tex_combine.py -s $(SEMESTER)

# PDFs generation from TeX
pdf: tex
	bash ./fui_kk/pdf.sh $(SEMESTER)

# Full pipeline for all targets above
all: responses scales json plots tex pdf web

# Assign courses to report writers and output to JSON
assign-courses:
	python3 fui_kk/course_divide.py names $(SEMESTER) > REPORT_WRITERS.json
	cat REPORT_WRITERS.json

# Open generated reports
open:
	open data/$(SEMESTER)/outputs/report/fui-kk_report*.pdf

# Generate the webpages
web:
	bash ./fui_kk/web.sh $(SEMESTER)
	python3 ./fui_kk/web_reports.py data/$(SEMESTER)

# Preview webpage on docs folder with warning message
web-preview: web
	@echo "---------------------------------------------"
	@echo " WARNING: Do NOT commit changes to ./docs if"
	@echo " you are working with real data!"
	@echo "---------------------------------------------"
	rm -rf ./docs
	mkdir ./docs
	cp -r ./data/$(SEMESTER)/outputs/web/upload/$(SEMESTER)/* ./docs
	python3 ./fui_kk/adapt_preview_html.py

# Upload raw data
upload_raw:
	@echo "Mount fui folder to MOUNT_PATH using DAV before running:"
	python3 fui_kk/upload_reports.py -v --input ./data --output $(MOUNT_PATH)/KURS/ --semester $(SEMESTER)

# Compute score
score:
	python3 ./fui_kk/score.py all

# Clean data folders
clean-output:
	find ./data -type d -name "outputs" -exec rm -rf {} +

# Clean data folders
clean-data:
	rm -rf ./data/

clean-downloads:
	rm -rf ./downloads

# Clean everything including resources
super-clean: clean-output, clean-data, clean-downloads

# Install pip dependencies
pip-install:
	pip install -r requirements.txt

pip3-install:
	pip3 install -r requirements.txt

# Print available targets
help:
	@echo "Available targets:"
	@echo "  install-mac"
	@echo "  install-linux"
	@echo "  setup"
	@echo "  download"
	@echo "  sample_data"
	@echo "  responses"
	@echo "  scales"
	@echo "  json"
	@echo "  tex"
	@echo "  pdf"
	@echo "  plots"
	@echo "  all"
	@echo "  open"
	@echo "  web"
	@echo "  web-preview"
	@echo "  upload_raw"
	@echo "  score"
	@echo "  clean"
	@echo "  super-clean"
	@echo "  pip-install"
	@echo "  pip3-install"
	@echo "  venv"
	@echo "  assign-courses"

.PHONY: default install-mac install-linux setup download sample_data responses scales json tex pdf plots all open web upload_raw score clean super-clean pip-install pip3-install venv assign-courses help courses source
