"""CLI entry point for fitground-audit."""

from fitground.data.pipeline import run_pipeline


def main() -> None:
    run_pipeline()
