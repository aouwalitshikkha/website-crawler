from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment
from pathlib import Path

from .models import PageData


class ExcelExporter:
    @staticmethod
    def export(pages: dict[str, PageData], path: str = "results.xlsx"):
        if Path(path).exists():
            wb = load_workbook(path)
            ws = wb.active
        else:
            wb = Workbook()
            ws = wb.active
            ws.title = "Crawl Results"
            headers = ["URL", "Status Code", "Inbound Links", "External Outbound Links"]
            header_font = Font(bold=True, size=11)
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

        saved_urls: set[str] = set()
        for row in range(2, ws.max_row + 1):
            val = ws.cell(row=row, column=1).value
            if val:
                saved_urls.add(val)

        row = ws.max_row + 1
        new_count = 0
        for url in sorted(pages.keys()):
            if url in saved_urls:
                continue
            page = pages[url]
            ws.cell(row=row, column=1, value=url)
            ws.cell(row=row, column=2, value=page.status_code)
            ws.cell(
                row=row, column=3,
                value=ExcelExporter._format_set_links(page.inbound, pages)
            )
            ws.cell(
                row=row, column=4,
                value=ExcelExporter._format_dict_links(page.external_outbound)
            )
            row += 1
            new_count += 1

        ws.column_dimensions["A"].width = max(ws.column_dimensions["A"].width or 60, 60)
        ws.column_dimensions["B"].width = 14
        ws.column_dimensions["C"].width = 80
        ws.column_dimensions["D"].width = 80

        wb.save(path)
        print(f"Saved: {path} ({new_count} new rows)")

    @staticmethod
    def _format_set_links(links: set[str],
                          pages: dict[str, PageData]) -> str:
        if not links:
            return ""
        formatted = []
        for link in sorted(links):
            status = (
                pages[link].status_code if link in pages else "?"
            )
            formatted.append(f"{link} ({status})")
        return ", ".join(formatted)

    @staticmethod
    def _format_dict_links(links: dict[str, int]) -> str:
        if not links:
            return ""
        formatted = []
        for link, status in sorted(links.items()):
            formatted.append(f"{link} ({status})")
        return ", ".join(formatted)
