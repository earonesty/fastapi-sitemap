import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from fastapi_sitemap import SiteMap, URLInfo


def make_app(static_dir: Path, gzip: bool = False) -> FastAPI:
    app = FastAPI()

    @app.get("/")
    async def index():
        return {"hello": "world"}

    # pretend static html exists
    (static_dir / "about.html").write_text("<html><body>about</body></html>")

    sm = SiteMap(
        app=app,
        base_url="https://example.com",
        static_dirs=[str(static_dir)],
        gzip_output=gzip,
    )
    sm.attach()
    return app


def test_sitemap_served():
    with tempfile.TemporaryDirectory() as tmp:
        app = make_app(Path(tmp))
        c = TestClient(app)
        resp = c.get("/sitemap.xml")
        assert resp.status_code == 200
        xml = resp.content.decode()
        assert "<loc>https://example.com/</loc>" in xml
        assert "about.html" in xml


def test_sitemap_gzip():
    with tempfile.TemporaryDirectory() as tmp:
        app = make_app(Path(tmp), gzip=True)
        c = TestClient(app)
        resp = c.get("/sitemap.xml")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/gzip"


def test_generate_files(tmp_path: Path):
    app = FastAPI()
    sm = SiteMap(app=app, base_url="https://example.com")
    files = sm.generate(tmp_path)
    assert (tmp_path / "sitemap.xml") in files
    assert (tmp_path / "sitemap.xml").exists()


def test_generate_files_gzip(tmp_path: Path):
    app = FastAPI()
    sm = SiteMap(app=app, base_url="https://example.com", gzip_output=True)
    files = sm.generate(tmp_path)
    assert (tmp_path / "sitemap.xml") in files
    assert (tmp_path / "sitemap.xml.gz") in files
    assert (tmp_path / "sitemap.xml").exists()
    assert (tmp_path / "sitemap.xml.gz").exists()


def test_source_decorator():
    app = FastAPI()
    sm = SiteMap(app=app, base_url="https://example.com")

    @sm.source
    def extra_urls():
        yield URLInfo("https://example.com/extra")

    urls = list(sm._collect_urls())
    assert any(url.loc == "https://example.com/extra" for url in urls)


def test_source_decorator_multiple():
    app = FastAPI()
    sm = SiteMap(app=app, base_url="https://example.com")

    @sm.source
    def extra_urls():
        yield URLInfo("https://example.com/extra")
        yield URLInfo(
            "https://example.com/priority", changefreq="daily", priority=0.8, lastmod="2024-01-01"
        )

    @sm.source
    def more_urls():
        yield URLInfo("https://example.com/more")

    urls = list(sm._collect_urls())
    assert len(urls) == 3
    assert any(url.loc == "https://example.com/extra" for url in urls)
    assert any(url.loc == "https://example.com/more" for url in urls)

    priority_url = next(url for url in urls if url.loc == "https://example.com/priority")
    assert priority_url.changefreq == "daily"
    assert priority_url.priority == 0.8
    assert priority_url.lastmod == "2024-01-01"


def test_collect_urls_without_app():
    app = FastAPI()
    sm = SiteMap(app=app, base_url="https://example.com")
    urls = list(sm._collect_urls())
    assert len(urls) == 0  # No static dirs configured


def test_route_filtering():
    app = FastAPI()
    router = APIRouter()

    def auth_dep():
        return True

    @router.get("/public")
    async def public():
        return {"public": True}

    @router.get("/private", dependencies=[Depends(auth_dep)])
    async def private():
        return {"private": True}

    @router.get("/dynamic/{id}")
    async def dynamic(id: int):
        return {"id": id}

    # Add a non-APIRoute route
    class CustomRoute:
        def __init__(self):
            self.path = "/custom"
            self.methods = {"GET"}

    app.include_router(router)
    app.routes.append(CustomRoute())

    # Test exclude_deps
    sm = SiteMap(
        app=app,
        base_url="https://example.com",
        exclude_deps={"auth_dep"},
    )
    urls = list(sm._collect_urls())
    assert any("/public" in url.loc for url in urls)
    assert not any("/private" in url.loc for url in urls)
    assert not any("/custom" in url.loc for url in urls)  # Non-APIRoute should be skipped

    # Test exclude_patterns
    sm = SiteMap(
        app=app,
        base_url="https://example.com",
        exclude_patterns=["/private"],
    )
    urls = list(sm._collect_urls())
    assert any("/public" in url.loc for url in urls)
    assert not any("/private" in url.loc for url in urls)

    # Test include_dynamic
    sm = SiteMap(
        app=app,
        base_url="https://example.com",
        include_dynamic=True,
    )
    urls = list(sm._collect_urls())
    assert any("/dynamic/" in url.loc for url in urls)

    # Test default dynamic exclusion
    sm = SiteMap(
        app=app,
        base_url="https://example.com",
    )
    urls = list(sm._collect_urls())
    assert not any("/dynamic/" in url.loc for url in urls)

    # Test non-GET method
    @router.post("/post-only")
    async def post_only():
        return {"post": True}

    urls = list(sm._collect_urls())
    assert not any("/post-only" in url.loc for url in urls)
