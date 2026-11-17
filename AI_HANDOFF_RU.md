# Дополнение0.9.1
Читать UPDATE_NOTES_091_RU.md и TEST_STATUS_RU.md. Установщик создаёт копию рядом с0.9.0, не меняет оригинал. Схема7. Новые модули engine/render_cache.py, transition.py; editor/scroll_panel.py, obstacle_overlay.py, frame_loop.py. World.view_state только синхронное чтение, snapshot для записи копирует. NPCsync кешируется по карте/событиям/флагам, при ручном редактировании вызывать invalidate. App.invalidate делает это. Фон масштабируется один раз при вмещении48MiB, камера crop; огромные карты fallback. Fade в snapshot и Take.sample, коммит карты строго в чёрном, pending возобновляется после in. Тесты прежней мгновенной передачи задают transition_seconds=0; не удалять отдельные fade tests. GUI не проверен.

# Передача проекта 0.9.0
Основа — присланный пользователем sources.txt 0.8.0, не посторонний PNGtuber main.
Python3.12 Windows; Tk+PIL, системное меню сохранить. Нужны полные ZIP, один
финальный архив, не потоки кода в чате. Модульность важна, main только запуск.
Новая схема7, v6→7 без потерь страниц. v1–5 миграция оставлена с ограничениями.
Открытие старого формата назначает НОВОЕ имя *_090_timestamp.json; не перезаписывать.
Пути ресурсов не портативный bundle. Не удалять папку исходного проекта.

Главные новые модули: engine/npcs.py, passage.py, thumbnail.py;
editor/event_list.py, passage_ui.py, overlay.py, graphics_ui.py, movement_ui.py,
door_ui.py, log_ui.py. README_RU.md — инструкция всех новых функций.
NPCs.states ключ map:event, snapshot actors текущей карты (id→state).
sync вычисляет active_page, при изменении индекса страницы сбрасывает маршрут,
НЕ позицию. NPC кэш живёт сеанс, другие карты не симулируются.
NPC шаги равны tile_size, target интерполируется, obstacles cancel step,
mode fixed/random/approach/route. При диалоге world.update заморожен.
Столкновения passage.allowed: клетка blocked, edges=[x,y,direction] запрет ВЫХОДА,
_bodies временный список при движении. 0↓1←2→3↑. Стена = парные directed edges.
Коллизии NPC всегда, героя optional. Тело события упрощено, не размер спрайта.
Scene.draw editor=True игнорирует runtime actors. Preview/export учитывает их.
Take.sample интерполирует actors только same map/same page. phase текущего шага.
Параметры ресурса scale/anchor общие для всех ссылок, не per-instance.
Двери генерируют ordinary pages. comment/separator — no-op commands.
Все модули менее300 строк, код разжат AST unparse (без слепления semicolon).

Из TXT невозможно получить исходные бинарные картинки. Встроенные технические
ресурсы заново нарисованы в совместимых размерах. COPY_OLD_ASSETS.bat может
скопировать ровно9 baseline PNG из установленной0.8.0 при совпадении размеров.
JSON/свои ресурсы не копирует. Пользовательские проекты открываются из старой папки.

31 тест passed; реальный системный ffmpeg encode/decode18 кадров1920×1080.
Тесты UI отсутствуют: _tkinter недоступен в среде сборки. НЕ утверждать GUI tested.
Нужен первый прогон Windows: sidebar/layout, страничные формы, master дверей,
редактор маршрутов, импорт/переключение кадров, закрытие модальных окон.
Следующее: фиксировать локальные ошибки, не переписывать движок/экспорт без нужды.
