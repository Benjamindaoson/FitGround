.PHONY: setup smoke benchmark demo hero

setup:
	python3 -m pip install -e . --quiet
	cd studio && npm install

smoke:
	PYTHONPATH=src python3 -m pytest -q

benchmark:
	PYTHONPATH=src python3 scripts/run_full_benchmark.py --stage all --output-dir artifacts/benchmark

demo:
	cd studio && npm run dev

hero:
	@echo "Run on the GPU flux env:"
	@echo "  source scripts/gpu/flux_env.sh && python scripts/gpu/hero_pipeline.py"
