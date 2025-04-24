from __future__ import annotations

import gzip
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, FastAPI, Response
from fastapi.routing import APIRoute

log = logging.getLogger(__name__)


# Public data class
class URLInfo:  # pragma: no cover
    """Simple container for one <url> entry."""

    __slots__ = ("loc", "lastmod", "changefreq", "priority")

    def __init__(
        self,
        loc: str,
        *,
        lastmod: Optional[str] = None,
        changefreq: Optional[str] = None,
        priority: Optional[float] = None,
    ) -> None:
        self.loc = loc
        self.lastmod = lastmod or datetime.utcnow().date().isoformat()
        self.changefreq = changefreq
        self.priority = priority

    def to_element(self) -> Element:
        url = Element("url")
        SubElement(url, "loc").text = self.loc
        if self.lastmod:
            SubElement(url, "lastmod").text = self.lastmod
        if self.changefreq:
            SubElement(url, "changefreq").text = self.changefreq
        if self.priority is not None:
            SubElement(url, "priority").text = f"{self.priority:.1f}"
        return url


class SiteMap:
    """Generate and serve sitemap(s) for a FastAPI/Starlette app."""

    def __init__(
        self,
        *,
        app: FastAPI | APIRouter,
        base_url: str,
        static_dirs: Sequence[str] | None = None,
        exclude_deps: Set[str] | None = None,
        exclude_patterns: Sequence[str] | None = None,
        include_dynamic: bool = False,
        changefreq: str | None = "weekly",
        priority_map: Dict[str, float] | None = None,
        gzip: bool = False,
    ) -> None:
        self.app = app
        self.base_url = base_url.rstrip("/")
        self.static_dirs = [Path(p) for p in (static_dirs or [])]
        self.exclude_deps = exclude_deps or set()
        if exclude_patterns is None:
            # suitable defaults
            exclude_patterns = [
                r"^/api/",
                r"^/docs/",
                r"^/favicon\.ico$",
                r"^/robots\.txt$",
            ]
        self.exclude_patterns = [re.compile(p) for p in (exclude_patterns or [])]
        self.include_dynamic = include_dynamic
        self.default_changefreq = changefreq
        self.priority_map = priority_map or {}
        self.gzip = gzip

        self._extra_sources: List[Callable[[], Iterable[URLInfo]]] = []

    # ---------- public API ----------
    def source(self, fn: Callable[[], Iterable[URLInfo]]) -> Callable[[], Iterable[URLInfo]]:
        """Register *fn* as an additional URL generator.

        `fn()` must yield or return an iterable of URLInfo objects.
        """
        self._extra_sources.append(fn)
        return fn

    def attach(self, route: str = "/sitemap.xml") -> None:
        """Register a GET endpoint that returns the generated sitemap."""

        sitemap_xml = self._build_xml(list(self._collect_urls()))

        async def _serve():
            return Response(sitemap_xml, media_type="application/xml")

        self.app.add_api_route(route, _serve, methods=["GET"], include_in_schema=False)

        if self.gzip:
            payload = gzip.compress(sitemap_xml)
            gzipped_route = route + ".gz"

            def _serve_gzipped():
                return Response(payload, media_type="application/gzip")

            self.app.add_api_route(
                gzipped_route, _serve_gzipped, methods=["GET"], include_in_schema=False
            )
        log.info("fastapi-sitemap attached at %s", route)

    def generate(self, out_dir: str | Path) -> List[Path]:
        """Write sitemap.xml (and possible .gz) to *out_dir*; return paths."""

        out_path = Path(out_dir).expanduser().resolve()
        out_path.mkdir(parents=True, exist_ok=True)
        xml_bytes = self._build_xml(self._collect_urls())
        filenames: list[Path] = []

        xml_file = out_path / "sitemap.xml"
        xml_file.write_bytes(xml_bytes)
        filenames.append(xml_file)

        if self.gzip:
            gz_file = out_path / "sitemap.xml.gz"
            gz_file.write_bytes(gzip.compress(xml_bytes))
            filenames.append(gz_file)
        return filenames

    # ---------- internal ----------

    def _collect_urls(self) -> Iterable[URLInfo]:
        yield from self._from_static()
        yield from self._from_routes()
        for fn in self._extra_sources:
            yield from fn()

    def _from_routes(self) -> Iterable[URLInfo]:
        for route in self.app.routes:
            if not isinstance(route, APIRoute):
                continue
            if "GET" not in route.methods:
                continue
            if not self.include_dynamic and ("{" in route.path or "}" in route.path):
                continue
            if any(dep.call.__name__ in self.exclude_deps for dep in route.dependant.dependencies):
                continue
            if any(p.search(route.path) for p in self.exclude_patterns):
                continue
            url = self.base_url + route.path
            yield URLInfo(
                url,
                changefreq=self.default_changefreq,
                priority=self.priority_map.get(route.path),
            )

    def _from_static(self) -> Iterable[URLInfo]:
        for root in self.static_dirs:
            for path in root.rglob("*.html"):
                rel = "/" + str(path.relative_to(root)).replace("\\", "/")
                yield URLInfo(
                    self.base_url + rel,
                    lastmod=datetime.utcfromtimestamp(path.stat().st_mtime).date().isoformat(),
                    changefreq="monthly",
                    priority=self.priority_map.get(rel),
                )

    def _build_xml(self, urls: Iterable[URLInfo]) -> bytes:
        urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        for info in urls:
            urlset.append(info.to_element())
        return tostring(urlset, encoding="utf-8", xml_declaration=True)
