from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class LinkParser:
    @staticmethod
    def get_domain(url: str) -> str:
        return urlparse(url).netloc

    @staticmethod
    def extract_links(html: str, base_url: str, domain: str) -> set[str]:
        soup = BeautifulSoup(html, "lxml")
        links = set()
        domain_parts_len = len(domain.split("."))

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                clean_url += f"?{parsed.query}"

            link_domain = parsed.netloc
            if link_domain == domain:
                links.add(clean_url)
            else:
                link_parts = link_domain.split(".")
                if len(link_parts) > domain_parts_len and link_domain.endswith("." + domain):
                    links.add(clean_url)

        return links
