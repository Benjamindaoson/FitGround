.PHONY: setup smoke benchmark benchmark-fast benchmark-full demo hero

setup:
	python3 -m pip install -e . --quiet
	cd studio && npm install

smoke:
	PYTHONPATH=src python3 -m pytest -q

benchmark: benchmark-fast

benchmark-fast:
	PYTHONPATH=src python3 -m pytest -q
	PYTHONPATH=src python3 scripts/gpu/finalize_closure.py
	PYTHONPATH=src python3 scripts/train/train_hero_ladder.py || true

benchmark-full:
	PYTHONPATH=src python3 scripts/run_full_benchmark.py --stage all --resume --output-dir artifacts/benchmark
	@echo "GPU physics resume: scripts/gpu/expand_visual_physics.py (does not regenerate lattice rows)"

demo:
	cd studio && npm run dev -- -p 43187

hero:
	@echo "Run on the GPU flux env:"
	@echo "  source scripts/gpu/flux_env.sh && bash scripts/gpu/run_closure.sh"
