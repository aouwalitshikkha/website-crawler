from urllib.parse import urlparse

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from .models import PageData


class ExcelExporter:
    SOCIAL_DOMAINS = {
        "facebook.com", "www.facebook.com",
        "twitter.com", "www.twitter.com", "x.com", "www.x.com",
        "linkedin.com", "www.linkedin.com",
        "instagram.com", "www.instagram.com",
        "youtube.com", "www.youtube.com",
        "pinterest.com", "www.pinterest.com",
        "tiktok.com", "www.tiktok.com",
        "snapchat.com", "www.snapchat.com",
        "reddit.com", "www.reddit.com",
    }
    @staticmethod
    def export(pages: dict[str, PageData], path: str = "results.xlsx"):
        wb = Workbook()
        header_font = Font(bold=True, size=11)

        # Sheet 1: Link Graph — every page with all connections
        ws1 = wb.active
        ws1.title = "Link Graph"
        headers1 = [
            "URL", "Status Code", "Page Size",
            "All Inbound Links", "All External Outbound Links",
        ]
        for col, header in enumerate(headers1, 1):
            cell = ws1.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        # Sheet 2: Broken Links — only pages with broken connections
        ws2 = wb.create_sheet("Broken Links")
        headers2 = [
            "URL", "Status Code", "Page Size",
            "Broken Inbound Links", "Broken External Outbound Links",
        ]
        for col, header in enumerate(headers2, 1):
            cell = ws2.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        row1 = 2
        row2 = 2

        for url in sorted(pages.keys()):
            page = pages[url]

            # Sheet 1 — every known page
            ws1.cell(row=row1, column=1, value=url)
            ws1.cell(row=row1, column=2, value=page.status_code)
            ws1.cell(
                row=row1, column=3,
                value=ExcelExporter._format_size(page.page_size)
            )
            ws1.cell(
                row=row1, column=4,
                value=", ".join(sorted(page.inbound)) if page.inbound else ""
            )
            ws1.cell(
                row=row1, column=5,
                value=ExcelExporter._format_all_external(page.external_outbound)
            )
            row1 += 1

            # Sheet 2 — only pages with at least one broken link
            broken_inbound = ExcelExporter._format_broken_inbound(
                page.inbound, page.status_code
            )
            broken_outbound = ExcelExporter._format_broken_external(
                page.external_outbound
            )
            if broken_inbound or broken_outbound:
                ws2.cell(row=row2, column=1, value=url)
                ws2.cell(row=row2, column=2, value=page.status_code)
                ws2.cell(
                    row=row2, column=3,
                    value=ExcelExporter._format_size(page.page_size)
                )
                ws2.cell(row=row2, column=4, value=broken_inbound)
                ws2.cell(row=row2, column=5, value=broken_outbound)
                row2 += 1

        # Sheet 3: Error References — each non-200 URL and where it's referenced from
        ws3 = wb.create_sheet("Error References")
        headers3 = ["Error Page", "Reference Page"]
        for col, header in enumerate(headers3, 1):
            cell = ws3.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        ref_rows: set[tuple[str, str]] = set()
        for url in sorted(pages.keys()):
            page = pages[url]
            if page.status_code not in (0, 200):
                for ref in sorted(page.inbound):
                    ref_rows.add((url, ref))
            for ext_url, ext_status in page.external_outbound.items():
                if ext_status not in (200,) and not ExcelExporter._is_social(ext_url):
                    ref_rows.add((ext_url, url))

        for i, (error_url, ref_url) in enumerate(sorted(ref_rows), 2):
            ws3.cell(row=i, column=1, value=error_url)
            ws3.cell(row=i, column=2, value=ref_url)

        # Sheet 4: Meta Data — meta tags for every page
        ws4 = wb.create_sheet("Meta Data")
        headers4 = [
            "URL", "Status Code", "Meta Title", "Meta Description",
            "Meta Robots", "Title Length", "Description Length",
        ]
        for col, header in enumerate(headers4, 1):
            cell = ws4.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        row4 = 2
        for url in sorted(pages.keys()):
            page = pages[url]
            ws4.cell(row=row4, column=1, value=url)
            ws4.cell(row=row4, column=2, value=page.status_code)
            ws4.cell(row=row4, column=3, value=page.meta_title)
            ws4.cell(row=row4, column=4, value=page.meta_description)
            ws4.cell(row=row4, column=5, value=page.meta_robots or "(absent)")
            ws4.cell(row=row4, column=6, value=len(page.meta_title))
            ws4.cell(row=row4, column=7, value=len(page.meta_description))
            row4 += 1

        for ws in [ws1, ws2, ws3, ws4]:
            ws.column_dimensions["A"].width = 60
            ws.column_dimensions["B"].width = 14
            if ws in (ws1, ws2):
                ws.column_dimensions["C"].width = 14
                ws.column_dimensions["D"].width = 80
                ws.column_dimensions["E"].width = 80
            elif ws is ws4:
                ws.column_dimensions["C"].width = 60
                ws.column_dimensions["D"].width = 80
                ws.column_dimensions["E"].width = 16
                ws.column_dimensions["F"].width = 16
                ws.column_dimensions["G"].width = 20

        wb.save(path)
        total = len(pages)
        broken_count = row2 - 2
        print(f"Saved: {path} ({total} pages, {broken_count} with broken links)")

    @staticmethod
    def _format_all_external(links: dict[str, int]) -> str:
        if not links:
            return ""
        return ", ".join(
            f"{url} ({status})" for url, status in sorted(links.items())
            if not ExcelExporter._is_social(url)
        )

    @staticmethod
    def _format_size(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    @staticmethod
    def _format_broken_inbound(
        links: set[str], own_status: int
    ) -> str:
        if not links or own_status < 400:
            return ""
        return ", ".join(
            f"{link} ({own_status})" for link in sorted(links)
        )

    @staticmethod
    def _format_broken_external(links: dict[str, int]) -> str:
        if not links:
            return ""
        return ", ".join(
            f"{url} ({status})" for url, status in sorted(links.items())
            if status not in (200,) and not ExcelExporter._is_social(url)
        )

    @staticmethod
    def _is_social(url: str) -> bool:
        domain = urlparse(url).netloc.lstrip("www.")
        return domain in ExcelExporter.SOCIAL_DOMAINS
