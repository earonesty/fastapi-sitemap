import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI


def create_test_config(tmp_path: Path, gzip: bool = False) -> Path:
    """Create a test config file that sets up a simple sitemap."""
    config = tmp_path / "sitemap_config.py"
    config.write_text(
        f"""
from fastapi import FastAPI
from fastapi_sitemap import SiteMap

app = FastAPI()

@app.get("/")
async def index():
    return {{"hello": "world"}}

sitemap = SiteMap(
    app=app,
    base_url="https://example.com",
    gzip={gzip},
)
"""
    )
    return config


def test_cli_init(tmp_path: Path):
    """Test the CLI init command."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fastapi_sitemap",
            "init",
            "--app",
            "tests.test_cli:app",
            "--base_url",
            "https://example.com",
            "--out",
            str(tmp_path / "sitemap_config.py"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (tmp_path / "sitemap_config.py").exists()


def test_cli_generate(tmp_path: Path):
    """Test the CLI generate command."""
    config = create_test_config(tmp_path)
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    # Run the CLI
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fastapi_sitemap",
            "generate",
            "--config",
            str(config),
            "--out",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "sitemap.xml" in result.stdout

    # Verify output files
    assert (out_dir / "sitemap.xml").exists()
    assert not (out_dir / "sitemap.xml.gz").exists()


def test_cli_generate_gzip(tmp_path: Path):
    """Test the CLI generate command with gzip enabled."""
    config = create_test_config(tmp_path, gzip=True)
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    # Run the CLI
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fastapi_sitemap",
            "generate",
            "--config",
            str(config),
            "--out",
            str(out_dir),
            "--gzip",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "sitemap.xml" in result.stdout
    assert "sitemap.xml.gz" in result.stdout

    # Verify output files
    assert (out_dir / "sitemap.xml").exists()
    assert (out_dir / "sitemap.xml.gz").exists()


app = FastAPI()


@app.get("/")
async def index():
    return {{"hello": "world"}}


def test_cli_generate_direct_app(tmp_path: Path):
    """Test the CLI generate command with direct app specification."""
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    # Run the CLI
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fastapi_sitemap",
            "generate",
            "--app",
            "tests.test_cli:app",
            "--base_url",
            "https://example.com",
            "--out",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
    assert result.returncode == 0
    assert "sitemap.xml" in result.stdout

    # Verify output files
    assert (out_dir / "sitemap.xml").exists()


def test_cli_exclude_patterns(tmp_path: Path):
    """Test the CLI with exclude patterns."""
    config = create_test_config(tmp_path)
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    # Run the CLI with exclude patterns
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fastapi_sitemap",
            "generate",
            "--config",
            str(config),
            "--out",
            str(out_dir),
            "--exclude-patterns",
            "^/api/",
            "^/docs/",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
    assert result.returncode == 0
    assert "sitemap.xml" in result.stdout

    # Verify output files
    assert (out_dir / "sitemap.xml").exists()
