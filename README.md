# fastapi-sitemap

Zero‑config sitemap generator & route for FastAPI / Starlette.

```python
from fastapi import FastAPI
from fastapi_sitemap import SiteMap

app = FastAPI()

sitemap = SiteMap(base_url="https://coderev.q32.com", static_dirs=["static"])
sitemap.attach(app)  # now GET /sitemap.xml is live
```

Or generate at build time:
```bash
python -m fastapi_sitemap.cli conf.sitemap:mymap ./public
```

See `tests/` for usage.
```
---
**LICENSE** (MIT)
```text
MIT License

Copyright (c) 2025 Erik Aronesty

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction... (standard MIT text)
