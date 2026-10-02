# pbar_icons

Тема иконок для Linux, собранная из нескольких тем. Рассчитана на тёмное оформление (KDE Plasma или GNOME).

## Из чего состоит

| Что | Откуда |
|---|---|
| Иконки приложений и типов файлов | [Neuwaita](https://github.com/RusticBard/Neuwaita) |
| Папки, включая цветные и тематические | [MacTahoe](https://github.com/vinceliuice/MacTahoe-icon-theme) |
| Иконки архивов (zip, tar, 7z, rar и др.) | MacTahoe |
| Иконки Nautilus и Dolphin | голубая папка MacTahoe |
| Монохромные иконки: трей, панель, кнопки в приложениях | [Papirus-Dark](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme) |
| Всё остальное | Papirus-Dark, затем breeze-dark и hicolor |

Монохромные иконки Papirus перекрашены в светлый цвет, чтобы их было видно на тёмном фоне.

Папки MacTahoe работают и в меню Dolphin «Цвет папки»: можно выбрать синюю, красную, коричневую и другие цвета, а также папки «Музыка», «Почта», «Архив» и т. д.

## Зависимости

Нужен установленный **Papirus** (вместе с ним ставится Papirus-Dark). Из него берутся иконки, которых нет в этой теме: приложения, не нарисованные в Neuwaita, значки трея, кнопки и т. п. Без Papirus тема тоже запустится, но многие иконки будут взяты из breeze или hicolor, а часть не найдётся вовсе.

Установка Papirus:

```
# Ubuntu / Debian
sudo apt install papirus-icon-theme

# Fedora
sudo dnf install papirus-icon-theme

# Arch
sudo pacman -S papirus-icon-theme
```

Ставить Neuwaita и MacTahoe не нужно: нужные иконки из них уже лежат в репозитории.

breeze-dark необязателен. В KDE он есть по умолчанию, а нужные из него иконки тоже скопированы в тему.

## Установка

KDE ищет темы иконок только в `~/.local/share/icons` и `/usr/share/icons`. Каталог `~/.icons` для KDE не подходит.

```
git clone https://github.com/pbarovsky/pbar-linux-icons.git ~/.local/share/icons/pbar_icons
```

Имя каталога должно быть `pbar_icons`: так тема называется в настройках.

## Как включить

**KDE Plasma:** Параметры системы → Внешний вид → Значки → pbar_icons.

Или из терминала:

```
/usr/lib/x86_64-linux-gnu/libexec/plasma-changeicons pbar_icons
```

На некоторых дистрибутивах путь другой, например `/usr/libexec/plasma-changeicons`.

Если после смены темы часть иконок осталась старой, очистите кэш и перезапустите панель:

```
rm -f ~/.cache/icon-cache.kcache
plasmashell --replace & disown
```

**GNOME:**

```
gsettings set org.gnome.desktop.interface icon-theme pbar_icons
```

**GTK-приложения в KDE:** в файлах `~/.config/gtk-3.0/settings.ini` и `~/.config/gtk-4.0/settings.ini` укажите:

```
gtk-icon-theme-name=pbar_icons
```

## Обновление

```
git -C ~/.local/share/icons/pbar_icons pull
```

## Пересборка

Тема собирается скриптом `build.py`. Пересобирать её нужно, только если вы меняете состав темы или обновляете исходные темы. Для обычной установки это не требуется.

Для сборки нужны Python 3 и установленные исходные темы. Пути к ним указаны в начале `build.py`:

- `~/.local/share/icons/Neuwaita`
- `~/.local/share/icons/MacTahoe` и `~/.local/share/icons/MacTahoe-dark`
- `~/.local/share/icons/Papirus-Dark`
- `/usr/share/icons/breeze-dark`

Запуск:

```
./build.py
```

Скрипт удаляет все каталоги с иконками и собирает их заново. Затем он пишет `index.theme` и обновляет `icon-theme.cache`, если установлен `gtk-update-icon-cache`.

### Почему в теме много копий иконок Papirus

KDE ищет иконку сначала целиком внутри основной темы. Если иконки с точным именем нет, KDE берёт из этой же темы похожую: вместо `audio-volume-high` подойдёт `audio-x-generic`. До Papirus он в этом случае уже не доходит. Поэтому такие иконки Papirus и breeze-dark скопированы в каталог `fallback/`, чтобы KDE находил их до того, как подставит неподходящую.

## Лицензия

Neuwaita, MacTahoe и Papirus распространяются под GNU GPL v3, поэтому эта тема тоже распространяется под GPL v3 (см. `LICENSE`). Авторские права на иконки принадлежат авторам исходных тем.
