# Модули 0.9.0
main.py — только запуск и настройка журнала.
support — DPI/клавиши.
project/schema.py —7/условия/команды; extra_validation.py — новые поля;
migrate.py —1–6→7; storage.py — загрузка/ресурсы/атомарное сохранение.
engine/player.py — герой; passage.py — направленная проходимость/тела;
npcs.py — автономные маршруты; world.py — события/команды/диалоги;
resources.py — кадры/масштаб; scene.py — общий render; thumbnail.py — миниатюры;
text.py — пагинация; take.py — sampling; exporter.py — поток FFmpeg.
editor/app.py — контроллер; actions.py — команды меню; menus.py — меню;
event_ui.py — страницы; event_list.py — поиск/миниатюры/навигация;
movement_ui.py — маршрут NPC; passage_ui.py — кисть краёв; overlay.py — рамки;
graphics_ui.py — опора/размер; assets_ui.py — импорт/выбор кадра;
door_ui.py — генератор обычных страниц двери; templates.py — рычаг;
command_tree.py — строки/ветки; command_ui.py — форма; conditions.py — флаги;
settings.py — видео/шрифт; modal.py — grab/pause; log_ui.py — диагностика;
export_ui.py — прогресс worker.
copy_old_assets.py — необязательное чтение9 baseline PNG из0.8.0.
tests —14 предыдущих проверок +17 новых. GUI tests нет.
navigation.py — масштабирование и вписывание карты.

0.9.1: render_cache.py — bounded bitmap cache; transition.py — out/commit/in; scroll_panel.py — локальная прокрутка/размер окна; obstacle_overlay.py — яркая проходимость; frame_loop.py — цикл кадра отдельно от контроллера; start_launcher.py — запуск из нового или старого venv.
