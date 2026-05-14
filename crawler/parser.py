from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class LinkParser:
    @staticmethod
    def get_domain(url: str) -> str:
        return urlparse(url).netloc.lstrip("www.")

    @staticmethod
    def is_external(url: str, domain: str) -> bool:
        parsed = urlparse(url)
        link_domain = parsed.netloc
        if not link_domain:
            return True
        if link_domain == domain:
            return False
        domain_parts = domain.split(".")
        link_parts = link_domain.split(".")
        if len(link_parts) > len(domain_parts) and link_domain.endswith("." + domain):
            return False
        return True

    @staticmethod
    def extract_links(html: str, base_url: str) -> set[str]:
        soup = BeautifulSoup(html, "lxml")
        links = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)
            if not parsed.netloc:
                continue
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                clean_url += f"?{parsed.query}"
            links.add(clean_url)

        return links
