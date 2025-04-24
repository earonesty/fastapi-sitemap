import argparse
import importlib
from pathlib import Path

from fastapi_sitemap import SiteMap


def _import_app(dotted: str):
    """Import an app given `module.sub:app`."""
    if ":" not in dotted:
        raise SystemExit("APP must be 'module.sub:attr'")
    mod_name, attr = dotted.split(":", 1)
    mod = importlib.import_module(mod_name)
    try:
        return getattr(mod, attr)
    except AttributeError as e:
        raise SystemExit(f"{attr!r} not found in {mod_name}") from e


def _write_stub(target: Path, dotted_app: str, base_url: str, exclude_patterns: list[str]):
    mod_name, attr = dotted_app.split(":")
    target.write_text(
        "from fastapi_sitemap import SiteMap\n"
        f"from {mod_name} import {attr} as app\n\n"
        f"sitemap = SiteMap(app=app, base_url='{base_url}', exclude_patterns={exclude_patterns})\n"
    )
    print(f"Stub written -> {target}")


def _load_sitemap(
    config: str | None, dotted_app: str | None, exclude_patterns: list[str], base_url: str
) -> SiteMap:
    if config:
        spec = importlib.util.spec_from_file_location("sitemap_config", config)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore

        # presumabley the config file has already set the base_url, and the app
        ret = mod.sitemap
        assert ret.base_url, "base_url must be set"
        assert ret.app, "app must be set"
    else:
        app = _import_app(dotted_app)
        assert app, "app must be set"
        assert base_url, "base_url must be set"
        ret = SiteMap(app=app, base_url=base_url, exclude_patterns=exclude_patterns)
    if not ret:
        raise SystemExit("Provide either --config or --app")
    return ret


def main(argv=None):
    p = argparse.ArgumentParser(prog="fastapi-sitemap")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common_args(p: argparse.ArgumentParser):
        p.add_argument("--app", "-a", help="module.sub:app")
        p.add_argument("--base_url", "-u", help="canonical site URL")
        p.add_argument(
            "--exclude-patterns",
            "-e",
            nargs="+",
            help="exclude patterns",
            default=[
                "^/api/",
                "^/docs/",
                "^/favicon\\.ico$",
                "^/robots\\.txt$",
            ],
        )
        return p

    init_p = sub.add_parser("init", help="create sitemap_config.py stub")
    common_args(init_p)
    init_p.add_argument("--out", "-o", default="sitemap_config.py")

    gen_p = sub.add_parser("generate", help="generate sitemap files")
    gen_p.add_argument("--config", "-c", help="path to sitemap_config.py")
    gen_p.add_argument("--out", "-o", default="public", help="output dir")
    gen_p.add_argument("--gzip", "-z", action="store_true")
    common_args(gen_p)

    args = p.parse_args(argv)

    if args.cmd == "init":
        _write_stub(Path(args.out), args.app, args.base_url, args.exclude_patterns)
        return

    try:
        # generate
        sitemap = _load_sitemap(args.config, args.app, args.exclude_patterns, args.base_url)
        sitemap.gzip = args.gzip
        written = sitemap.generate(args.out)
        for path in written:
            print(path)
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    main()
