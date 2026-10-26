#!/usr/bin/env python3
"""Fetch a paper and unpack it into papers/<slug>/ for reading.

    python tools/fetch_paper.py <source> [--slug SLUG]

<source> can be:
  * an arXiv URL or id            https://arxiv.org/abs/2401.01234, 2401.01234
  * a DOI or doi.org URL           10.1029/2018GL077456
  * a journal / preprint page      (anything exposing a citation_pdf_url meta tag)
  * a direct PDF URL
  * a local PDF                    inbox/my-paper.pdf

Produces:
  papers/<slug>/paper.pdf       the PDF
  papers/<slug>/paper.md        text, page by page
  papers/<slug>/pages/p01.png   page renders (look at these for figures and equations)
  papers/<slug>/figures/        embedded raster figures
  papers/<slug>/source/         LaTeX source (arXiv only): the exact equations
  papers/<slug>/meta.json       title, authors, year, venue, doi, url, abstract

Prints the slug on the last line. Exit code 2 = no PDF reachable (paywalled):
ask for the PDF to be uploaded to inbox/.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import re
import shutil
import sys
import tarfile
import unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import pymupdf
import requests

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; explainers-fetch/0.1; +https://github.com/jkingslake/explainers)"}
ARXIV_RE = re.compile(r"(?:arxiv\.org/(?:abs|pdf|html)/)?(\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?", re.I)
DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s\"<>?#]+)")


class Paywalled(Exception):
    pass


# ------------------------------------------------------------------ helpers
def get(url: str, **kw) -> requests.Response:
    r = requests.get(url, headers=UA, timeout=60, allow_redirects=True, **kw)
    r.raise_for_status()
    return r


def is_pdf(content: bytes) -> bool:
    return content[:5] == b"%PDF-"


def slugify(meta: dict) -> str:
    surname = (meta.get("authors") or ["paper"])[0].split()[-1]
    title_words = [w for w in re.findall(r"[A-Za-z0-9]+", meta.get("title", "")) if len(w) > 3][:3]
    parts = [surname, str(meta.get("year") or ""), *title_words]
    s = "-".join(p for p in parts if p).lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9\-]+", "", s)[:60] or "paper"


class MetaTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags: dict[str, list[str]] = {}

    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            a = dict(attrs)
            name = (a.get("name") or a.get("property") or "").lower()
            if name and a.get("content"):
                self.tags.setdefault(name, []).append(a["content"])


# ------------------------------------------------------------------ sources
def from_arxiv(arxiv_id: str) -> tuple[dict, bytes, bytes | None]:
    atom = get("https://export.arxiv.org/api/query", params={"id_list": arxiv_id}).text
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    entry = ET.fromstring(atom).find("a:entry", ns)
    if entry is None or entry.find("a:title", ns) is None:
        raise SystemExit(f"arXiv id {arxiv_id} not found")
    text = lambda tag: " ".join((entry.findtext(tag, default="", namespaces=ns) or "").split())
    doi = entry.findtext("arxiv:doi", default="", namespaces=ns)
    meta = {
        "title": text("a:title"),
        "authors": [a.findtext("a:name", namespaces=ns) for a in entry.findall("a:author", ns)],
        "year": text("a:published")[:4],
        "venue": entry.findtext("arxiv:journal_ref", default="", namespaces=ns) or "arXiv",
        "doi": doi,
        "arxiv_id": arxiv_id,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "abstract": text("a:summary"),
    }
    pdf = get(f"https://arxiv.org/pdf/{arxiv_id}").content
    try:
        src = get(f"https://arxiv.org/e-print/{arxiv_id}").content
    except requests.RequestException:
        src = None
    return meta, pdf, src


def crossref(doi: str) -> dict:
    try:
        msg = get(f"https://api.crossref.org/works/{doi}").json()["message"]
    except requests.RequestException:
        return {}
    return {
        "title": " ".join((msg.get("title") or [""])[0].split()),
        "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in msg.get("author", [])],
        "year": str((msg.get("issued", {}).get("date-parts") or [[""]])[0][0]),
        "venue": (msg.get("container-title") or [""])[0],
        "abstract": re.sub(r"<[^>]+>", "", msg.get("abstract", "")).strip(),
        "_pdf_links": [l["URL"] for l in msg.get("link", []) if "pdf" in l.get("content-type", "")],
    }


def open_access_copies(doi: str) -> tuple[str | None, list[str]]:
    """(arXiv id if the paper is on arXiv, [candidate PDF URLs]) from public indexes."""
    arxiv_id, urls = None, []
    try:
        ss = get(
            f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
            params={"fields": "externalIds,openAccessPdf"},
        ).json()
        arxiv_id = (ss.get("externalIds") or {}).get("ArXiv")
        if (ss.get("openAccessPdf") or {}).get("url"):
            urls.append(ss["openAccessPdf"]["url"])
    except requests.RequestException:
        pass
    try:
        hits = get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": f'DOI:"{doi}"', "resultType": "core", "format": "json"},
        ).json()["resultList"]["result"]
        for hit in hits:
            for ft in (hit.get("fullTextUrlList") or {}).get("fullTextUrl", []):
                if ft.get("documentStyle") == "pdf" or ft["url"].endswith(".pdf"):
                    urls.append(ft["url"])
    except (requests.RequestException, KeyError):
        pass
    try:  # set OPENALEX_API_KEY if the shared anonymous budget is exhausted
        key = {"api_key": os.environ["OPENALEX_API_KEY"]} if os.environ.get("OPENALEX_API_KEY") else {}
        work = get(f"https://api.openalex.org/works/doi:{doi}", params=key).json()
        for loc in work.get("locations", []):
            m = ARXIV_RE.search(loc.get("landing_page_url") or "")
            if m and "arxiv" in (loc.get("landing_page_url") or ""):
                arxiv_id = arxiv_id or m.group(1)
            if loc.get("pdf_url"):
                urls.append(loc["pdf_url"])
    except requests.RequestException:
        pass
    return arxiv_id, urls


def from_doi(doi: str) -> tuple[dict, bytes, bytes | None]:
    doi = doi.rstrip(".,;)")
    meta = {"doi": doi, "url": f"https://doi.org/{doi}", **crossref(doi)}
    publisher_pdfs = meta.pop("_pdf_links", [])
    arxiv_id, oa_urls = open_access_copies(doi)
    if arxiv_id:  # arXiv also gives us the LaTeX source
        arxiv_meta, pdf, tex = from_arxiv(arxiv_id)
        return {**arxiv_meta, **{k: v for k, v in meta.items() if v}}, pdf, tex

    tried = list(dict.fromkeys([*oa_urls, *publisher_pdfs, f"https://doi.org/{doi}"]))
    for url in tried:
        try:
            pdf = pdf_from_url(url)
            meta["pdf_url"] = url
            return meta, pdf, None
        except (requests.RequestException, Paywalled):
            continue
    raise Paywalled(meta.get("title") or doi, tried)


def pdf_from_url(url: str) -> bytes:
    r = get(url)
    if is_pdf(r.content):
        return r.content
    tags = MetaTags()
    tags.feed(r.text)
    for pdf_url in tags.tags.get("citation_pdf_url", []):
        try:
            c = get(pdf_url).content
            if is_pdf(c):
                return c
        except requests.RequestException:
            continue
    raise Paywalled(url)


def from_page(url: str) -> tuple[dict, bytes, bytes | None]:
    r = get(url)
    if is_pdf(r.content):
        return {"url": url}, r.content, None
    tags = MetaTags()
    tags.feed(r.text)
    t = tags.tags
    doi = (t.get("citation_doi") or t.get("dc.identifier") or [""])[0].removeprefix("doi:")
    if DOI_RE.match(doi):
        meta, pdf, src = from_doi(doi)
        return {**meta, "url": url}, pdf, src
    meta = {
        "title": (t.get("citation_title") or t.get("og:title") or [""])[0],
        "authors": t.get("citation_author", []),
        "year": (t.get("citation_publication_date") or t.get("citation_date") or [""])[0][:4],
        "venue": (t.get("citation_journal_title") or t.get("og:site_name") or [""])[0],
        "url": url,
    }
    return meta, pdf_from_url(url), None


def from_file(path: Path) -> tuple[dict, bytes, bytes | None]:
    pdf = path.read_bytes()
    if not is_pdf(pdf):
        raise SystemExit(f"{path} is not a PDF")
    info = pymupdf.open(stream=pdf, filetype="pdf").metadata or {}
    meta = {
        "title": info.get("title") or path.stem.replace("_", " ").replace("-", " "),
        "authors": [a.strip() for a in re.split(r"[;,]| and ", info.get("author") or "") if a.strip()],
        "year": (info.get("creationDate") or "")[2:6],
        "url": "",
    }
    # An arXiv stamp or a DOI on the first page lets us fill in proper metadata.
    first_page = pymupdf.open(stream=pdf, filetype="pdf")[0].get_text()
    if stamp := re.search(r"arXiv:(\d{4}\.\d{4,5})", first_page):
        try:
            arxiv_meta, _, src = from_arxiv(stamp.group(1))
            return arxiv_meta, pdf, src
        except (requests.RequestException, SystemExit):
            pass
    m = DOI_RE.search(first_page)
    if m:
        doi = m.group(1).rstrip(".,;)")
        found = crossref(doi)
        found.pop("_pdf_links", None)
        if found.get("title"):
            meta |= found | {"doi": doi, "url": f"https://doi.org/{doi}"}
    return meta, pdf, None


# ------------------------------------------------------------------ unpack
def unpack(out: Path, pdf: bytes, src: bytes | None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "paper.pdf").write_bytes(pdf)
    doc = pymupdf.open(stream=pdf, filetype="pdf")

    with open(out / "paper.md", "w") as f:
        for i, page in enumerate(doc, 1):
            f.write(f"\n\n## Page {i}\n\n{page.get_text()}")

    pages = out / "pages"
    pages.mkdir(exist_ok=True)
    for i, page in enumerate(doc, 1):
        page.get_pixmap(dpi=110).save(pages / f"p{i:02d}.png")

    figs = out / "figures"
    figs.mkdir(exist_ok=True)
    for i, page in enumerate(doc, 1):
        for j, img in enumerate(page.get_images(full=True), 1):
            try:
                pix = pymupdf.Pixmap(doc, img[0])
                if pix.width < 250 or pix.height < 150:
                    continue
                if pix.n - pix.alpha >= 4:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                pix.save(figs / f"p{i:02d}-{j}.png")
            except Exception:
                continue

    if src:
        dest = out / "source"
        dest.mkdir(exist_ok=True)
        try:
            with tarfile.open(fileobj=io.BytesIO(src)) as tar:
                tar.extractall(dest, filter="data")
        except tarfile.ReadError:
            try:  # single gzipped .tex file
                (dest / "main.tex").write_bytes(gzip.decompress(src))
            except OSError:
                shutil.rmtree(dest)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--slug")
    args = ap.parse_args()
    s = args.source.strip()

    try:
        if Path(s).expanduser().exists():
            meta, pdf, src = from_file(Path(s).expanduser())
        elif (m := ARXIV_RE.fullmatch(s)) or ("arxiv.org" in s and (m := ARXIV_RE.search(s))):
            meta, pdf, src = from_arxiv(m.group(1))
        elif (m := DOI_RE.search(s)) and ("doi.org" in s or s.startswith("10.") or s.lower().startswith("doi:")):
            meta, pdf, src = from_doi(m.group(1))
        elif s.startswith("http"):
            meta, pdf, src = from_page(s)
        else:
            raise SystemExit(f"Don't know how to fetch {s!r}")
    except Paywalled as e:
        what, *rest = e.args
        print(f"Could not download a PDF for: {what}", file=sys.stderr)
        if rest and rest[0]:
            print("Tried (some may work in a browser; e.g. author-manuscript copies):", file=sys.stderr)
            for url in rest[0]:
                print(f"  {url}", file=sys.stderr)
        print("Upload the PDF to inbox/ (or attach it) and run again with that path.", file=sys.stderr)
        sys.exit(2)

    meta.setdefault("source_input", s)
    slug = args.slug or slugify(meta)
    out = ROOT / "papers" / slug
    unpack(out, pdf, src)
    meta["pages"] = len(pymupdf.open(out / "paper.pdf"))
    meta["has_latex_source"] = (out / "source").exists()
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2)[:1500])
    print(slug)


if __name__ == "__main__":
    main()
