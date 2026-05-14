from dataclasses import dataclass, field


@dataclass
class FetchResult:
    status_code: int
    html: str = ""
    error: str | None = None
    size: int = 0


@dataclass
class PageData:
    url: str
    status_code: int
    page_size: int = 0
    meta_title: str = ""
    meta_description: str = ""
    meta_robots: str = ""
    inbound: set[str] = field(default_factory=set)
    external_outbound: dict[str, int] = field(default_factory=dict)
