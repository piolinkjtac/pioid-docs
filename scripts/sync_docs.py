#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

# --- 設定パス ---
ROOT            = Path(__file__).parent.parent
UPSTREAM        = ROOT / "upstream" / "docs"
TARGET          = ROOT / "docs"
BRAND_ASSETS    = ROOT / "brand" / "assets"
BRAND_OVERRIDES = ROOT / "brand" / "overrides"
BRAND_MKDOCS    = ROOT / "brand" / "mkdocs.yml"
BRAND_INDEX     = ROOT / "brand" / "index.md"
PROJECT_MKDOCS  = ROOT / "mkdocs.yml"

def rename_path(p: Path):
    """singleid- / singleid_ を pioid- / pioid_ に置換してリネーム"""
    new = Path(str(p)
               .replace("singleid-", "pioid-")
               .replace("singleid_", "pioid_"))
    if p.is_dir() and new.exists():
        print(f"  → Skipping rename of existing dir: {p} -> {new}")
        return new
    new.parent.mkdir(parents=True, exist_ok=True)
    p.rename(new)
    return new

def replace_in_file(p: Path):
    text = p.read_text(encoding="utf-8")
    out = []
    for line in text.splitlines(keepends=True):
        # 0) 固定 URL の置換
        line = line.replace(
            "(https://login.singleid.jp/)",
            "(https://www.piolink.co.jp/sec1/pioid.html)"
        )
        # 1) アンカーリンク中の singleid → pio-id
        line = re.sub(
            r"\(#([^)]+)\)",
            lambda m: "(#" + m.group(1).replace("singleid", "pio-id") + ")",
            line
        )
        # 2) 大文字 “SingleID” はすべて “PIO-ID” に置換
        line = line.replace("SingleID", "PIO-ID")
        # 3) 小文字 “singleid” は、前後がドットでなければ “pioid” に置換
        line = re.sub(r'(?<!\.)singleid(?!\.)', "pioid", line)
        out.append(line)
    p.write_text("".join(out), encoding="utf-8")

def main():
    print("1) 初期化: docs/ を空に")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)

    print("2) upstream からコピー")
    shutil.copytree(UPSTREAM, TARGET, dirs_exist_ok=True)

    print("3) ファイル／ディレクトリ名のリネーム (深い階層から処理)")
    paths = list(TARGET.rglob("*"))
    paths.sort(key=lambda p: len(p.parts), reverse=True)
    for path in paths:
        if "singleid-" in str(path) or "singleid_" in str(path):
            rename_path(path)

    print("4) Markdown 内の置換")
    for md in TARGET.rglob("*.md"):
        replace_in_file(md)

    print("5) ブランディング資産をコピー")
    if BRAND_ASSETS.exists():
        shutil.copytree(BRAND_ASSETS, TARGET / "assets", dirs_exist_ok=True)
    if BRAND_OVERRIDES.exists():
        shutil.copytree(BRAND_OVERRIDES, TARGET / "overrides", dirs_exist_ok=True)

    # 追加：brand/assets/css/*.css → docs/css/*.css
    css_src = BRAND_ASSETS / "css"
    if css_src.exists():
        dest_css = TARGET / "css"
        dest_css.mkdir(parents=True, exist_ok=True)
        for css_file in css_src.glob("*.css"):
            shutil.copy2(css_file, dest_css / css_file.name)
            print(f"  • copied CSS: {css_file.name} → docs/css/")

    # 追加：brand/index.md → docs/index.md
    if BRAND_INDEX.exists():
        shutil.copy2(BRAND_INDEX, TARGET / "index.md")
        print("  • copied brand/index.md → docs/index.md")
    else:
        print("  → brand/index.md が見つからないためスキップ")

    print("6) mkdocs.yml を上書き")
    # brand と project mkdocs.yml が同じならスキップ
    if BRAND_MKDOCS.resolve() != PROJECT_MKDOCS.resolve():
        shutil.copy2(BRAND_MKDOCS, PROJECT_MKDOCS)
    else:
        print("  → brand/mkdocs.yml と mkdocs.yml が同一のためスキップ")

    print("同期完了 🎉")

if __name__ == "__main__":
    main()
