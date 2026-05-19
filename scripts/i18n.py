import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "app" / "translations"
MESSAGES_POT = TRANSLATIONS / "messages.pot"
LOCALES = ("en", "ru", "uk")


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def extract() -> None:
    TRANSLATIONS.mkdir(parents=True, exist_ok=True)
    run(
        "pybabel",
        "extract",
        "-F",
        "babel.cfg",
        "-o",
        str(MESSAGES_POT),
        ".",
    )


def init(locale: str) -> None:
    if not MESSAGES_POT.exists():
        extract()
    run(
        "pybabel",
        "init",
        "-i",
        str(MESSAGES_POT),
        "-d",
        str(TRANSLATIONS),
        "-l",
        locale,
    )


def update() -> None:
    if not MESSAGES_POT.exists():
        extract()
    for locale in LOCALES:
        po = TRANSLATIONS / locale / "LC_MESSAGES" / "messages.po"
        if po.exists():
            run(
                "pybabel",
                "update",
                "-i",
                str(MESSAGES_POT),
                "-d",
                str(TRANSLATIONS),
                "-l",
                locale,
            )
        else:
            init(locale)


def compile_catalogs() -> None:
    run("pybabel", "compile", "-d", str(TRANSLATIONS))


def check() -> None:
    for locale in LOCALES:
        po = TRANSLATIONS / locale / "LC_MESSAGES" / "messages.po"
        mo = TRANSLATIONS / locale / "LC_MESSAGES" / "messages.mo"
        if not po.exists():
            raise SystemExit(f"Missing catalog: {po}")
        if not mo.exists():
            raise SystemExit(f"Missing compiled catalog: {mo}")
        content = po.read_text(encoding="utf-8")
        if "#, fuzzy" in content:
            raise SystemExit(f"Fuzzy translations must be resolved before deploy: {po}")
    compile_catalogs()


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage Flask-Babel catalogs.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("extract", help="Extract translatable strings to messages.pot.")
    sub.add_parser("update", help="Update existing locale catalogs from messages.pot.")
    sub.add_parser("compile", help="Compile .po catalogs into .mo files.")
    sub.add_parser("check", help="Verify catalogs exist and compile.")
    init_parser = sub.add_parser("init", help="Initialize a new locale catalog.")
    init_parser.add_argument("locale")

    args = parser.parse_args()
    if args.command == "extract":
        extract()
    elif args.command == "update":
        update()
    elif args.command == "compile":
        compile_catalogs()
    elif args.command == "check":
        check()
    elif args.command == "init":
        init(args.locale)


if __name__ == "__main__":
    main()
