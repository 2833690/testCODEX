from pathlib import Path


def test_streamlit_app_exists() -> None:
    assert Path("ui/streamlit_app.py").exists()
