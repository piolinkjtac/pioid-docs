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

# --- 変換ロジックを関数化 ---
def convert_image_paths(line: str) -> str:
    """Markdownの(/images/…)とHTMLのsrc/hrefをプロジェクトルート絶対パスに書き換え"""
    line = re.sub(
        r'\(/images/([^)\s]+)\)',
        r'(/pioid-docs/images/\1)',
        line
    )
    line = re.sub(
        r'(href|src)="/images/([^"]+)"',
        r'\1="/pioid-docs/images/\2"',
        line
    )
    return line

def convert_fixed_url(line: str) -> str:
    """login.singleid.jp のURLをPIO-IDログインページに置換"""
    return line.replace(
        "(https://login.singleid.jp/)",
        "(https://www.piolink.co.jp/sec1/pioid.html)"
    )

def convert_anchor_links(line: str) -> str:
    """Markdownアンカーリンク中の singleid → pio-id"""
    return re.sub(
        r"\(#([^)]+)\)",
        lambda m: "(#" + m.group(1).replace("singleid", "pio-id") + ")",
        line
    )

def convert_uppercase_singleid(line: str) -> str:
    """大文字 SingleID → PIO-ID"""
    return line.replace("SingleID", "PIO-ID")

def convert_lowercase_singleid(line: str) -> str:
    """小文字 singleid → pioid（前後ドットは除外）"""
    return re.sub(r'(?<!\.)singleid(?!\.)', "pioid", line)

def replace_in_file(p: Path):
    """1行ずつ読み込んで各種変換を適用し、上書き保存"""
    text = p.read_text(encoding="utf-8")
    out = []
    for line in text.splitlines(keepends=True):
        # カスタムドメインを使用する場合には、コメントアウトする
        # line = convert_image_paths(line)
        line = convert_fixed_url(line)
        line = convert_anchor_links(line)
        line = convert_uppercase_singleid(line)
        line = convert_lowercase_singleid(line)
        out.append(line)
    p.write_text("".join(out), encoding="utf-8")

def process_pocguide_index():
    """docs/pioid-pocguide/index.md のリスト行を再構成"""
    idx_file = TARGET / "pioid-pocguide" / "index.md"
    if not idx_file.exists():
        print("  → pioid-pocguide/index.md not found, skip reordering")
        return

    lines = idx_file.read_text(encoding="utf-8").splitlines(keepends=True)
    # ヘッダ部分（リスト開始前まで）とアイテム
    split_at = next((i for i, l in enumerate(lines) if l.lstrip().startswith("*")), len(lines))
    header, items = lines[:split_at], lines[split_at:]

    # 1) 除外するパターンをリスト化
    exclude = [
        "./subgate_ap/",
        "./subgate/",
        "./anti_spreader_ap/",
        "./anti_spreader_switch/",
    ]
    items = [l for l in items if not any(pat in l for pat in exclude)]

    # 2) PIOLINK TiFRONT-AP を先頭へ
    piolink = next((l for l in items if "piolink_tifront-ap" in l), None)
    if piolink:
        items.remove(piolink)
        items.insert(0, piolink)

    # ファイルに書き戻し
    idx_file.write_text("".join(header + items), encoding="utf-8")
    print("  • Reordered pioid-pocguide/index.md")

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

    print("4-1) pioid-pocguide/index.md の再構成")
    process_pocguide_index()

    print("5) ブランディング資産をコピー")
    if BRAND_ASSETS.exists():
        shutil.copytree(BRAND_ASSETS, TARGET / "assets", dirs_exist_ok=True)
    if BRAND_OVERRIDES.exists():
        shutil.copytree(BRAND_OVERRIDES, TARGET / "overrides", dirs_exist_ok=True)

    # brand/assets/css/*.css → docs/css/*.css
    css_src = BRAND_ASSETS / "css"
    if css_src.exists():
        dest_css = TARGET / "css"
        dest_css.mkdir(parents=True, exist_ok=True)
        for css_file in css_src.glob("*.css"):
            shutil.copy2(css_file, dest_css / css_file.name)
            print(f"  • copied CSS: {css_file.name} → docs/css/")

    # brand/index.md → docs/index.md
    if BRAND_INDEX.exists():
        shutil.copy2(BRAND_INDEX, TARGET / "index.md")
        print("  • copied brand/index.md → docs/index.md")
    else:
        print("  → brand/index.md が見つからないためスキップ")

    print("6) mkdocs.yml を上書き")
    if BRAND_MKDOCS.resolve() != PROJECT_MKDOCS.resolve():
        shutil.copy2(BRAND_MKDOCS, PROJECT_MKDOCS)
    else:
        print("  → brand/mkdocs.yml と mkdocs.yml が同一のためスキップ")

    print("同期完了 🎉")

if __name__ == "__main__":
    main()
