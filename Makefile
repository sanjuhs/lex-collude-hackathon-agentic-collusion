.PHONY: setup test demo research paper site reproduce serve
setup:
	bash scripts/setup.sh
test:
	.venv/bin/python -m unittest discover -s tests -v
demo:
	@run_dir=$$(mktemp -d /tmp/lexcollude-demo.XXXXXX); .venv/bin/python -m lexcollude run --backend scripted --output "$$run_dir/run"; .venv/bin/python scripts/verify_run.py "$$run_dir/run"
research:
	.venv/bin/python -m pip install --no-cache-dir -e '.[research]'
	.venv/bin/python scripts/build_research.py
paper:
	.venv/bin/python scripts/build_paper.py
site:
	.venv/bin/python scripts/build_site.py
reproduce:
	$(MAKE) research
	$(MAKE) paper
	$(MAKE) site
serve:
	.venv/bin/python -m http.server 8080 --bind 127.0.0.1 --directory site
