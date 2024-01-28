import re
from typing import Any

from app.source.base import RSSTask
from scrapy.http import HtmlResponse

CATEGORY_MAP = {
    "cs.AI": "Artificial Intelligence",
    "cs.AR": "Hardware Architecture",
    "cs.CC": "Computational Complexity",
    "cs.CE": "Computational Engineering, Finance, and Science",
    "cs.CG": "Computational Geometry",
    "cs.CL": "Computation and Language",
    "cs.CR": "Cryptography and Security",
    "cs.CV": "Computer Vision and Pattern Recognition",
    "cs.CY": "Computers and Society",
    "cs.DB": "Databases",
    "cs.DC": "Distributed, Parallel, and Cluster Computing",
    "cs.DL": "Digital Libraries",
    "cs.DM": "Discrete Mathematics",
    "cs.DS": "Data Structures and Algorithms",
    "cs.ET": "Emerging Technologies",
    "cs.FL": "Formal Languages and Automata Theory",
    "cs.GL": "General Literature",
    "cs.GR": "Graphics",
    "cs.GT": "Computer Science and Game Theory",
    "cs.HC": "Human-Computer Interaction",
    "cs.IR": "Information Retrieval",
    "cs.IT": "Information Theory",
    "cs.LG": "Learning",
    "cs.LO": "Logic in Computer Science",
    "cs.MA": "Multiagent Systems",
    "cs.MM": "Multimedia",
}


class Arxiv(RSSTask):
    url: str = "http://export.arxiv.org/rss/cs"
    name: str = "Arxiv"

    @staticmethod
    def parse(entry: dict) -> dict[str, Any]:
        return {
            "title": entry["title"],
            "authors": entry["author"],
            "url": entry["link"],
            "abstract": entry["summary"],
        }

    def post_parse(self, entry: dict[str, Any]) -> dict[str, Any]:
        category = re.findall(r"\[(.*?)\]", entry["title"])[0]
        entry["title"] = entry["title"].split("(", 1)[0]
        entry["authors"] = (
            HtmlResponse(url="", body=entry["authors"], encoding="utf-8")
            .css("a::text")
            .getall()
        )
        entry["abstract"] = (
            HtmlResponse(url="", body=entry["abstract"], encoding="utf-8")
            .css("p::text")
            .get()
        )
        entry["category"] = category
        return entry
