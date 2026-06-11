"""Quick importer that tries to import all modules under the `app` package
and reports failures. Use this to quickly surface syntax/import errors
without touching the virtualenv site-packages.

Run from project root with the venv python:
  .venv\Scripts\python.exe scripts\check_imports.py
"""
import pkgutil
import importlib
import sys
from pathlib import Path


def iter_app_modules(package_name: str = "app"):
    try:
        pkg = importlib.import_module(package_name)
    except Exception as e:
        print(f"Failed to import base package '{package_name}': {e}")
        return

    package_path = Path(pkg.__file__).parent
    for finder, name, ispkg in pkgutil.walk_packages([str(package_path)], prefix=package_name + "."):
        yield name


def main():
    failures = []
    for modname in iter_app_modules():
        try:
            importlib.import_module(modname)
            print(f"OK   {modname}")
        except Exception as e:
            print(f"FAIL {modname}: {e}")
            failures.append((modname, e))

    print("\nSummary:")
    print(f"  Modules checked: {len(list(iter_app_modules()))}")
    print(f"  Failures: {len(failures)}")
    if failures:
        print("\nFailed modules (first 10):")
        for mod, err in failures[:10]:
            print(f" - {mod}: {err}")
        sys.exit(2)


if __name__ == "__main__":
    main()
