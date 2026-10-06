import json

from open_strategy_lab.demo import run_grant_demo


def test_grant_demo_generates_reviewer_artifacts(tmp_path):
    report = run_grant_demo(tmp_path)

    assert report["network_required"] is False
    assert report["profitability_claim"] is False
    assert report["paper_vs_batch_final_equity_delta"] < 1e-9

    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "walk_forward_folds.csv").exists()
    assert (tmp_path / "paper_fills.csv").exists()
    assert (tmp_path / "README.md").exists()

    saved = json.loads(
        (tmp_path / "summary.json").read_text(encoding="utf-8")
    )
    assert saved["demo_type"] == "deterministic_offline_research_demo"
    assert saved["walk_forward"]["folds"] >= 1
