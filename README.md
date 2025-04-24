# fastapi-sitemap

Zero‑config sitemap generator & route for FastAPI / Starlette.

## Basic Usage

```python
from fastapi import FastAPI
from fastapi_sitemap import SiteMap, URLInfo

app = FastAPI()

sitemap = SiteMap(
    app=app,
    base_url="https://example.com",
    exclude_patterns=["^/api/", "^/docs/"],  # optional: exclude patterns
    gzip_output=True,  # optional: enable gzip compression
)
sitemap.attach()  # now GET /sitemap.xml is live
```

## Adding Custom URLs

Use the `@source` decorator to add custom URLs to your sitemap:

```python
@sitemap.source
def extra_urls():
    # Simple URL
    yield URLInfo("https://example.com/about")

    # URL with metadata
    yield URLInfo(
        "https://example.com/priority",
        changefreq="daily",
        priority=0.8,
        lastmod="2024-01-01"
    )
```

## Command Line Usage

Generate sitemap files at build time:

```bash
# Using a config file
python -m fastapi_sitemap.cli generate -c sitemap_config.py -o ./public

# Or directly with app reference
python -m fastapi_sitemap.cli generate -a myapp.main:app -u https://example.com -o ./public
```

## Configuration Options

- `app`: Your FastAPI application (required)
- `base_url`: Your site's canonical URL (required)
- `static_dirs`: List of directories containing static HTML files
- `exclude_patterns`: List of regex patterns to exclude from sitemap
- `exclude_deps`: Set of dependency names to exclude from sitemap
- `include_dynamic`: Whether to include dynamic routes (default: False)
- `changefreq`: Default change frequency for URLs (default: "weekly")
- `priority_map`: Dictionary mapping paths to priority values
- `gzip_output`: Whether to enable gzip compression (default: False)

## Example Configuration

```python
# sitemap_config.py
from fastapi import FastAPI
from fastapi_sitemap import SiteMap, URLInfo

app = FastAPI()

sitemap = SiteMap(
    app=app,
    base_url="https://example.com",
    static_dirs=["static", "docs"],
    exclude_patterns=["^/api/", "^/admin/"],
    include_dynamic=True,
    changefreq="daily",
    priority_map={
        "/": 1.0,
        "/about": 0.8,
    },
    gzip_output=True,
)

@sitemap.source
def extra_urls():
    yield URLInfo("https://example.com/custom")
```

---
**LICENSE** (MIT)
```text
MIT License

Copyright (c) 2025 Erik Aronesty

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction... (standard MIT text)
