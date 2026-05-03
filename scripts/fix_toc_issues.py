"""Edit-in-place: фикс двух проблем в Курсовая_работа.docx после apply_proper_toc.

1. Убирает page_break_before из стиля Heading 1 — чтобы не было двойных разрывов
   (build-скрипт уже вставил inline page break в каждом заголовке главы).
2. Снимает стиль Heading 1 с параграфа «СОДЕРЖАНИЕ» и применяет ему ручной формат
   (TNR 14, bold, центр) — чтобы СОДЕРЖАНИЕ не попадало в само содержание.

После запуска нужно открыть Word и заново обновить TOC: Ctrl+A → F9.

Запуск:
    .venv/Scripts/python scripts/fix_toc_issues.py
"""
import io
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor


REPO = Path(__file__).resolve().parent.parent
DOCX = (
    REPO.parent.parent.parent
    / 'Any' / 'PREU'
    / 'интеграция и управление приложениями на удаленном сервере'
    / 'Курсовая_работа.docx'
)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if not DOCX.exists():
        print(f'[err] Не найден {DOCX}')
        sys.exit(1)

    doc = Document(str(DOCX))

    # 1. Убрать page_break_before из стиля Heading 1.
    h1 = doc.styles['Heading 1']
    h1.paragraph_format.page_break_before = False
    print('[ok] Heading 1: page_break_before=False (разрыв остаётся inline в каждом заголовке)')

    # 2. Найти параграф «СОДЕРЖАНИЕ» и снять с него стиль Heading 1,
    #    применив ручное форматирование (TNR 14 bold center).
    soderzhanie = None
    for p in doc.paragraphs:
        if p.text.strip() == 'СОДЕРЖАНИЕ':
            soderzhanie = p
            break
    if soderzhanie is None:
        print('[err] Параграф «СОДЕРЖАНИЕ» не найден')
        sys.exit(1)

    soderzhanie.style = doc.styles['Normal']
    soderzhanie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    soderzhanie.paragraph_format.first_line_indent = Cm(0)
    soderzhanie.paragraph_format.line_spacing = 1.5
    soderzhanie.paragraph_format.space_before = Pt(12)
    soderzhanie.paragraph_format.space_after = Pt(12)
    for run in soderzhanie.runs:
        if run.text.strip():  # не трогаем run с page break
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
            run.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
    print('[ok] «СОДЕРЖАНИЕ»: снят стиль Heading 1, применён ручной формат '
          '— больше не попадает в TOC')

    doc.save(str(DOCX))
    print(f'[ok] сохранён: {DOCX.name} ({DOCX.stat().st_size:,} bytes)')
    print('[i] Откройте Word и снова Ctrl+A → F9 → «Обновить целиком».')


if __name__ == '__main__':
    main()
