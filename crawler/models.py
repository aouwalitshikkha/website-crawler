from dataclasses import dataclass, field


@dataclass
class FetchResult:
    status_code: int
    html: str = ""
    error: str | None = None


@dataclass
class PageData:
    url: str
    status_code: int
    inbound: set[str] = field(default_factory=set)
    outbound: set[str] = field(default_factory=set)
