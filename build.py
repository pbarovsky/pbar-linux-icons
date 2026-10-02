#!/usr/bin/env python3
"""Сборка темы pbar_icons.

  - цветные значки (apps, mimetypes, places) — Neuwaita
  - папки (все цвета и типы) — MacTahoe-dark / MacTahoe
  - архивы (zip, tar, 7z, rar…) — MacTahoe
  - symbolic / трей / стрелки / точки — Papirus-Dark
    (symbolic перекрашены в светлый цвет под тёмную тему)
  - всё остальное — Papirus-Dark -> breeze-dark -> hicolor

Особенность KDE: KIconLoader ищет имя (и его «обрезки»: audio-volume-high ->
audio-volume -> audio, а также audio-x-generic) целиком внутри одной темы,
прежде чем перейти к унаследованной. Поэтому имена Papirus/breeze, которые
в нашей теме совпали бы с чем-то «похожим», явно прокидываются ссылками
в fallback/.

Перезапускать после обновления исходных тем: ./build.py
"""
import configparser
import os
import re
import shutil
import subprocess
from pathlib import Path

HOME = Path.home()
NEUWAITA = HOME / ".local/share/icons/Neuwaita"
# Тёмный вариант первым: мелкие (контурные) папки в нём светлые
MACTAHOE = [HOME / ".local/share/icons/MacTahoe-dark", HOME / ".local/share/icons/MacTahoe"]
FALLBACKS = [  # (метка, путь) в порядке наследования
    ("papirus", HOME / ".local/share/icons/Papirus-Dark"),
    ("breeze", Path("/usr/share/icons/breeze-dark")),
]
OUT = Path(__file__).resolve().parent

# Светлый цвет по умолчанию: его видно там, где никто не перекрашивает иконку
DEFAULT_FG = "#dedede"
# Имена Neuwaita, которые в трее должны быть монохромными
NEUWAITA_DROP = {"network-wired"}
# Не подменяем на symbolic (в диалогах они должны оставаться цветными)
NO_MONO_ALIAS = re.compile(r"^(dialog-|process-working)")


def names_in(d: Path) -> set[str]:
    if not d.is_dir():
        return set()
    return {p.stem for p in d.iterdir() if p.suffix in (".svg", ".png")}


def read_index(theme: Path) -> configparser.ConfigParser:
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    cp.read(theme / "index.theme", encoding="utf-8")
    return cp


# ---------------------------------------------------------------- очистка
for p in OUT.iterdir():
    if p.is_dir() and not p.name.startswith("."):
        shutil.rmtree(p)
(OUT / "icon-theme.cache").unlink(missing_ok=True)

sections: dict[str, dict[str, str]] = {}  # dir -> параметры для index.theme
ours: set[str] = set()                     # все имена в нашей теме


def add_dir(rel: str, **params):
    sections.setdefault(rel, params)
    (OUT / rel).mkdir(parents=True, exist_ok=True)
    return OUT / rel


# ------------------------------------------------------- 1. Neuwaita
CTX = {"apps": "Applications", "mimetypes": "MimeTypes", "places": "Places",
       "status": "Status", "emblems": "Emblems", "actions": "Actions",
       "devices": "Devices", "categories": "Categories"}
for cat in ("apps", "mimetypes", "places"):
    rel = f"scalable/{cat}"
    dst = add_dir(rel, Context=CTX[cat], Size="128", MinSize="8", MaxSize="512", Type="Scalable")
    for f in (NEUWAITA / rel).iterdir():
        n = f.stem
        # папки берём из MacTahoe
        if cat == "places" and (n.startswith("folder") or n in ("user-home", "user-desktop")):
            continue
        if n.startswith("inode-directory") or n in NEUWAITA_DROP:
            continue
        shutil.copy2(f, dst / f.name, follow_symlinks=False)
    ours |= names_in(dst)
# ссылки, указывавшие на удалённое, убираем
for f in (OUT / "scalable").rglob("*"):
    if f.is_symlink() and not f.exists():
        f.unlink()

# ------------------------------------------------------ 2. Папки MacTahoe
# 16/22/24 — монохромные контурные (в MacTahoe-dark — светлые), scalable —
# цветные, со всеми вариантами: цвета (folder-red, folder-blue, folder-brown…)
# и типы (folder-music, folder-mail, folder-tar…). Их предлагает Dolphin
# в «Цвет папки» / «Значок папки».
# Symbolic-иконки папок не берём — symbolic у нас из Papirus.
mt_idx = read_index(MACTAHOE[-1])


def is_folder_name(n: str) -> bool:
    return ("folder" in n or n in ("inode-directory", "desktop")
            or re.fullmatch(r"([a-z]+-)?user-(home|desktop|images|pictures)", n) is not None)


folder_dirs = []
for size in ("16", "22", "24", "scalable"):
    srcs = [t / "places" / size for t in MACTAHOE if (t / "places" / size).is_dir()]
    names = set()
    for src in srcs:
        names |= {n for n in names_in(src) if is_folder_name(n)}
    dst = add_dir(f"folders/{size}", **dict(mt_idx.items(f"places/{size}")))
    for n in sorted(names):
        f = next((src / f"{n}.svg" for src in srcs if (src / f"{n}.svg").exists()), None)
        if f is None:  # только висячие ссылки
            continue
        link = os.readlink(f) if f.is_symlink() else None
        if link and "/" not in link and Path(link).stem in names:
            os.symlink(link, dst / f.name)
        else:
            shutil.copy(f, dst / f.name)
    for f in dst.iterdir():
        if f.is_symlink() and not f.exists():
            f.unlink()
    ours |= names_in(dst)
    folder_dirs.append(dst)

# ------------- 3. Имена папок Papirus/KDE/Neuwaita, которых нет в MacTahoe
papirus = FALLBACKS[0][1]
places_names = set()
for d in papirus.glob("*/places"):
    places_names |= names_in(d)
colors = {m.group(1) for n in places_names
          if (m := re.fullmatch(r"folder-([a-z]+)-documents", n))}
color_re = re.compile(rf"^(folder|user)-({'|'.join(sorted(colors))})(-|$)")
folder_names = {n for n in places_names
                if n.startswith("folder") and not color_re.match(n) and "symbolic" not in n}
folder_names |= {n for n in names_in(NEUWAITA / "scalable/places") if n.startswith("folder")}
ALIAS = {
    "folder-docs-alt": "folder-documents", "folder-wallpapers": "folder-images",
    "folder-screenshot": "folder-images", "folder-books": "folder-book",
    "folder-dev": "folder-development", "folder-workspace": "folder-projects",
    "folder-study": "folder-documents", "folder-apps": "folder-extension",
}
folder_names |= set(ALIAS)
for d in folder_dirs:
    for n in sorted(folder_names):
        if (d / f"{n}.svg").exists():
            continue
        target = ALIAS.get(n, "folder")
        if n.endswith("-open"):
            target = "folder-open"
        elif n.endswith("drag-accept"):
            target = "folder-drag-accept"
        if not (d / f"{target}.svg").exists():
            target = "folder"
        os.symlink(f"{target}.svg", d / f"{n}.svg")
    ours |= names_in(d)

# ------------------------------------------------- 3a. Архивы из MacTahoe
# Neuwaita архивов почти не рисует, без этого zip/tar/7z/rar были бы из Papirus
ARCHIVE_RE = re.compile(
    r"^(application-|gnome-mime-application-)?(x-)?"
    r"(zip|7zip|7z-compressed|7z-compressed-tar|archive|archive-zip|archive-blank|"
    r"tar|tarz|compressed-tar|compress|compress-tar|compressed|"
    r"gzip|bzip|bzip-compressed|bzip-compressed-tar|bzip2-compressed|bzip2-compressed-tar|"
    r"xz|xz-compressed-tar|lzma|lzma-compressed-tar|lzip|lzip-compressed-tar|lzop|"
    r"lrzip|lrzip-compressed-tar|lz4|lz4-compressed-tar|zstd|zstd-compressed-tar|zlib|"
    r"rar|rar-compressed|vnd\.rar|cpio|cpio-compress|cpio-compressed|arj|ace|lha|lhz|zoo|"
    r"stuffit|shar|ar|pak|vnd\.ms-cab-compressed|7z-ace|7z-arj|asar)$"
    r"|^(zip|rar|tar|tgz|7zip|archive|package|package-x-generic)$"
)
mt_mimes = MACTAHOE[-1] / "mimes"
archive_dirs = []
for size in ("16", "22", "scalable"):
    src = mt_mimes / size
    names = {n for n in names_in(src) if ARCHIVE_RE.match(n)}
    dst = add_dir(f"archives/{size}", **dict(mt_idx.items(f"mimes/{size}")))
    for n in sorted(names):
        f = src / f"{n}.svg"
        if not f.exists():
            continue
        link = os.readlink(f) if f.is_symlink() else None
        if link and "/" not in link and Path(link).stem in names:
            os.symlink(link, dst / f.name)
        else:
            shutil.copy(f, dst / f.name)
    for f in dst.iterdir():
        if f.is_symlink() and not f.exists():
            f.unlink()
    archive_dirs.append(dst)
archive_names = set().union(*(names_in(d) for d in archive_dirs))
# одноимённые иконки Neuwaita убираем, чтобы не спорили с MacTahoe
for n in archive_names:
    (OUT / "scalable/mimetypes" / f"{n}.svg").unlink(missing_ok=True)
# архивные типы Papirus, которых нет в MacTahoe -> общий архив MacTahoe
for d in papirus.glob("*/mimetypes"):
    for n in names_in(d):
        if ARCHIVE_RE.match(n) and n not in archive_names:
            archive_names.add(n)
            for ad in archive_dirs:
                if (ad / "application-x-archive.svg").exists():
                    os.symlink("application-x-archive.svg", ad / f"{n}.svg")
ours |= archive_names
for f in (OUT / "scalable/mimetypes").iterdir():
    if f.is_symlink() and not f.exists():
        f.unlink()

# ---------- 3b. Значки файловых менеджеров = стандартная голубая папка MacTahoe
FILE_MANAGER_ICONS = [
    "org.gnome.Nautilus", "nautilus", "org.kde.dolphin", "dolphin",
    "system-file-manager", "file-manager", "filemanager-app",
]
apps_dir = OUT / "scalable/apps"
for n in FILE_MANAGER_ICONS:
    (apps_dir / f"{n}.svg").unlink(missing_ok=True)
    os.symlink("../../folders/scalable/folder.svg", apps_dir / f"{n}.svg")
    ours.add(n)

# ----------------------- 4. Symbolic / панель / трей — из Papirus-Dark
# Иконки панели и действий Papirus-Dark уже светлые (#dfdfdf) и берутся через
# наследование. А symbolic у Papirus-Dark общие с Papirus: ColorScheme-Text =
# #444444, и там, где Plasma/GTK иконку не перекрашивает, она тёмная.
# Поэтому кладём в тему их копии со светлым цветом.
# Каталоги symbolic зеркалятся как есть, со своими размерами: в Papirus
# 22x22/24x24-версии нарисованы с полями, и если растянуть 16-пиксельную,
# значок в трее станет крупнее, чем в самом Papirus.
pidx = read_index(papirus)
base_ours = set(ours)
papirus_all: set[str] = set()
sym_dirs: list[Path] = []          # скопированные (не ссылочные) каталоги
copied: dict[Path, Path] = {}      # realpath в Papirus -> каталог у нас
for d in pidx.get("Icon Theme", "Directories", fallback="").split(","):
    src = papirus / d
    papirus_all |= names_in(src)
    if "/symbolic" not in d or not src.is_dir():
        continue
    add_dir(d, **dict(pidx.items(d)))
    dst = OUT / d
    real = src.resolve()
    if real in copied:
        # в Papirus это ссылка на другой каталог (32x32 -> 16x16, @2x) — так же и у нас
        dst.rmdir()
        os.symlink(os.path.relpath(copied[real], dst.parent), dst)
        continue
    copied[real] = dst
    sym_dirs.append(dst)
    for f in sorted(src.iterdir()):
        if f.suffix != ".svg" or f.stem in base_ours or not f.exists():
            continue
        svg = f.read_text(encoding="utf-8")
        svg = re.sub(r"(\.ColorScheme-Text\s*\{\s*color:\s*)#[0-9a-fA-F]{3,6}", rf"\g<1>{DEFAULT_FG}", svg)
        (dst / f.name).write_text(svg, encoding="utf-8")
    ours |= names_in(dst)

# Plasma часто просит имя без -symbolic, которого в Papirus нет, а есть только
# X-symbolic (brightness-high, klipper…). Иначе KDE находит «обрезок» —
# например, цветную иконку приложения brightness.
# Плюс имена Plasma, которых в Papirus нет совсем (имя KDE -> symbolic Papirus).
KDE_TO_PAPIRUS = {"video-display-brightness": "display-brightness"}
sym_names = {n[: -len("-symbolic")] for n in ours if n.endswith("-symbolic")}
aliases = {n: n for n in sym_names
           if n not in ours and n not in papirus_all and not NO_MONO_ALIAS.match(n)}
for kde, pap in KDE_TO_PAPIRUS.items():
    for suffix in ("", "-symbolic"):
        if kde + suffix not in ours:
            aliases[kde + suffix] = pap
for dst in sym_dirs:
    for n, target in aliases.items():
        t = dst / f"{target}-symbolic.svg"
        if t.exists() and not (dst / f"{n}.svg").exists():
            os.symlink(t.name, dst / f"{n}.svg")
ours |= set(aliases)

# --------------------- 5. Явный фолбэк на Papirus-Dark / breeze-dark для KDE
def chain(n: str):
    sym = n.endswith("-symbolic")
    base = n[: -len("-symbolic")] if sym else n
    parts = base.split("-")
    for i in range(len(parts) - 1, 0, -1):
        v = "-".join(parts[:i])
        yield v
        yield v + "-symbolic"
    yield parts[0] + "-x-generic"
    yield parts[0] + "-x-generic-symbolic"


fb_count = 0
fb_copied: dict[Path, Path] = {}  # исходный файл -> его копия у нас
for label, theme in FALLBACKS:
    idx = read_index(theme)
    dirs = [d for d in idx.get("Icon Theme", "Directories", fallback="").split(",") if d]
    per_name: dict[str, list[tuple[str, Path]]] = {}
    for d in dirs:
        if not idx.has_section(d) or idx.get(d, "Scale", fallback="1") != "1":
            continue
        src = theme / d
        for n in names_in(src):
            per_name.setdefault(n, []).append((d, src))
    for n, locs in sorted(per_name.items()):
        if n in ours or not any(v in ours for v in chain(n)):
            continue
        for d, src in locs:
            f = next((src / f"{n}{ext}" for ext in (".svg", ".png") if (src / f"{n}{ext}").exists()), None)
            if f is None:
                continue
            rel = f"fallback/{label}/{d}"
            dst = add_dir(rel, **dict(idx.items(d)))
            # копируем, а не ссылаемся: тема должна работать на любой машине;
            # одинаковые файлы — одна копия и относительные ссылки на неё
            real = f.resolve()
            if real in fb_copied:
                os.symlink(os.path.relpath(fb_copied[real], dst), dst / f.name)
            else:
                shutil.copy(real, dst / f.name)
                fb_copied[real] = dst / f.name
        ours.add(n)
        fb_count += 1

# -------------------------------------------------------- 6. index.theme
dirs = sorted(sections)
lines = [
    "[Icon Theme]",
    "Name=pbar_icons",
    "Comment=Neuwaita + MacTahoe folders and archives, Papirus-Dark symbolic and fallback",
    "Inherits=Papirus-Dark,breeze-dark,hicolor",
    "Example=folder",
    "",
    "# KDE",
    "DisplayDepth=32",
    "LinkOverlay=link_overlay",
    "LockOverlay=lock_overlay",
    "ZipOverlay=zip_overlay",
    "DesktopDefault=48",
    "DesktopSizes=16,22,32,48,64,72,96,128",
    "ToolbarDefault=22",
    "ToolbarSizes=16,22,32,48",
    "MainToolbarDefault=22",
    "MainToolbarSizes=16,22,32,48",
    "SmallDefault=16",
    "SmallSizes=16",
    "PanelDefault=32",
    "PanelSizes=16,22,32,48,64,72,96,128",
    "",
    "Directories=" + ",".join(dirs),
    "",
]
for d in dirs:
    lines.append(f"[{d}]")
    lines += [f"{k}={v}" for k, v in sections[d].items()]
    lines.append("")
(OUT / "index.theme").write_text("\n".join(lines), encoding="utf-8")

subprocess.run(["gtk-update-icon-cache", "-f", "-q", str(OUT)], check=False)
print(f"Готово: {OUT}  (имён: {len(ours)}, явных фолбэков: {fb_count})")
