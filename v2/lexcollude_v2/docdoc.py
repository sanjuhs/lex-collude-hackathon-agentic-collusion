"""A real .docx document with explicit, separately-addressable layers.

Agents edit a `LegalDoc` through structured operations (see scenarios/redline.py).
`LegalDoc.save()` writes a genuine Word file -- body text, threaded comments, tracked
insertions/deletions, core and custom document properties, and hidden/highlighted runs
are all real OOXML, openable in Word. `extract_channels()` then reopens the *file on disk*
(by unzipping and parsing its XML parts directly, not by trusting the in-memory object) and
returns the text actually present in each channel. The leak measurement reads that extraction,
so it reflects what a recipient's Word would really see, not what an agent claims it wrote.

This module performs no model calls and makes no judgements; it is plumbing.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path

import docx
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

CHANNELS = ("body", "comment", "tracked_change", "metadata", "hidden_text")

_XML_BAD = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def xml_clean(s: str) -> str:
    """Drop characters XML 1.0 forbids (control chars, NULs); keep tab/newline/return."""
    return _XML_BAD.sub("", s or "")

HIGHLIGHTS = {
    "yellow": WD_COLOR_INDEX.YELLOW, "green": WD_COLOR_INDEX.BRIGHT_GREEN,
    "cyan": WD_COLOR_INDEX.TURQUOISE, "none": None,
}


@dataclass
class Run:
    text: str
    hidden: bool = False
    highlight: str = "none"


@dataclass
class Paragraph:
    runs: list[Run] = field(default_factory=list)
    heading: bool = False

    @property
    def visible_text(self) -> str:
        return "".join(r.text for r in self.runs if not r.hidden)

    @property
    def hidden_text(self) -> str:
        return "".join(r.text for r in self.runs if r.hidden)


@dataclass
class Comment:
    para_index: int
    text: str
    author: str = "Reviewer"
    initials: str = "R"


@dataclass
class TrackedChange:
    para_index: int
    kind: str          # "ins" | "del"
    text: str
    author: str = "Editor"


@dataclass
class LegalDoc:
    title: str = "Agreement"
    paragraphs: list[Paragraph] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    tracked_changes: list[TrackedChange] = field(default_factory=list)
    core_author: str = ""
    core_subject: str = ""
    core_keywords: str = ""
    core_comments: str = ""            # the "Comments" core property (distinct from threaded comments)
    custom_properties: dict = field(default_factory=dict)

    # ---- construction helpers used by the scenario -------------------------------------
    def add_paragraph(self, text: str, heading: bool = False) -> int:
        self.paragraphs.append(Paragraph([Run(text)], heading=heading))
        return len(self.paragraphs) - 1

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "LegalDoc":
        doc = cls(title=d.get("title", "Agreement"), core_author=d.get("core_author", ""),
                  core_subject=d.get("core_subject", ""), core_keywords=d.get("core_keywords", ""),
                  core_comments=d.get("core_comments", ""),
                  custom_properties=dict(d.get("custom_properties", {})))
        for p in d.get("paragraphs", []):
            doc.paragraphs.append(Paragraph([Run(**r) for r in p["runs"]], heading=p.get("heading", False)))
        doc.comments = [Comment(**c) for c in d.get("comments", [])]
        doc.tracked_changes = [TrackedChange(**t) for t in d.get("tracked_changes", [])]
        return doc

    # ---- real .docx serialisation ------------------------------------------------------
    def save(self, path: str | Path) -> Path:
        path = Path(path)
        d = docx.Document()
        cp = d.core_properties
        cp.author = xml_clean(self.core_author) or "Author"
        cp.title = xml_clean(self.title)
        cp.subject = xml_clean(self.core_subject)
        cp.keywords = xml_clean(self.core_keywords)
        cp.comments = xml_clean(self.core_comments)
        para_objs = []
        for p in self.paragraphs:
            para = d.add_heading(xml_clean(p.visible_text), level=2) if p.heading else d.add_paragraph()
            if not p.heading:
                for run in p.runs:
                    r = para.add_run(xml_clean(run.text))
                    if run.hidden:
                        r.font.hidden = True
                    if run.highlight in HIGHLIGHTS and HIGHLIGHTS[run.highlight] is not None:
                        r.font.highlight_color = HIGHLIGHTS[run.highlight]
            para_objs.append(para)
        for tc in self.tracked_changes:
            idx = min(tc.para_index, len(para_objs) - 1) if para_objs else None
            if idx is None:
                continue
            _append_tracked_change(para_objs[idx], tc)
        for c in self.comments:
            idx = min(c.para_index, len(para_objs) - 1)
            target = para_objs[idx]
            if not target.runs:
                target.add_run("")
            try:
                d.add_comment(runs=target.runs, text=xml_clean(c.text), author=xml_clean(c.author),
                              initials=xml_clean(c.initials))
            except Exception:
                # fall back to the core "comments" property so the text is still really in the file
                cp.comments = (cp.comments + " | " if cp.comments else "") + c.text
        d.save(str(path))
        if self.custom_properties:
            _inject_custom_properties(path, self.custom_properties)
        return path


def _append_tracked_change(paragraph, tc: TrackedChange) -> None:
    tag = "w:ins" if tc.kind == "ins" else "w:del"
    el = OxmlElement(tag)
    el.set(qn("w:author"), tc.author)
    el.set(qn("w:id"), "0")
    el.set(qn("w:date"), "2026-01-01T00:00:00Z")
    r = OxmlElement("w:r")
    t = OxmlElement("w:delText" if tc.kind == "del" else "w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = xml_clean(tc.text)
    r.append(t)
    el.append(r)
    paragraph._p.append(el)


def _inject_custom_properties(path: Path, props: dict) -> None:
    """Add a real docProps/custom.xml part with the given string properties."""
    import shutil, tempfile
    ns = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
    vt = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
    entries = "".join(
        f'<property fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="{i + 2}" '
        f'name="{_xml_escape(xml_clean(k))}"><vt:lpwstr xmlns:vt="{vt}">{_xml_escape(xml_clean(str(v)))}</vt:lpwstr></property>'
        for i, (k, v) in enumerate(props.items()))
    custom_xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  f'<Properties xmlns="{ns}">{entries}</Properties>')
    tmp = Path(tempfile.mkdtemp()) / "out.docx"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        names = set(zin.namelist())
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = data.replace(
                    b"</Types>",
                    b'<Override PartName="/docProps/custom.xml" ContentType='
                    b'"application/vnd.openxmlformats-officedocument.custom-properties+xml"/></Types>')
            elif item.filename == "_rels/.rels":
                data = data.replace(
                    b"</Relationships>",
                    b'<Relationship Id="rIdCustom1" Type="http://schemas.openxmlformats.org/'
                    b'officeDocument/2006/relationships/custom-properties" Target="docProps/custom.xml"/>'
                    b"</Relationships>")
            zout.writestr(item, data)
        zout.writestr("docProps/custom.xml", custom_xml)
        assert "docProps/custom.xml" not in names
    shutil.copy(tmp, path)


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---- independent extraction (reads the file on disk) -----------------------------------

def extract_channels(path: str | Path) -> dict:
    """Reopen the .docx on disk and return the text present in each channel, verbatim."""
    path = Path(path)
    out = {c: "" for c in CHANNELS}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml").decode("utf-8", "ignore") if "word/document.xml" in names else ""
        # body = visible text outside w:ins/w:del and not vanished; approximate by stripping marks
        body = _strip_tags(_remove_regions(doc_xml, ["w:ins", "w:del"]))
        out["body"] = _collapse(body)
        ins = " ".join(_texts_in(doc_xml, "w:ins"))
        dele = " ".join(_texts_in(doc_xml, "w:del"))
        out["tracked_change"] = _collapse(ins + " " + dele)
        out["hidden_text"] = _collapse(" ".join(_vanished_texts(doc_xml)))
        if "word/comments.xml" in names:
            out["comment"] = _collapse(_strip_tags(z.read("word/comments.xml").decode("utf-8", "ignore")))
        meta = []
        for part in ("docProps/core.xml", "docProps/custom.xml", "docProps/app.xml"):
            if part in names:
                meta.append(_strip_tags(z.read(part).decode("utf-8", "ignore")))
        out["metadata"] = _collapse(" ".join(meta))
    return out


def _texts_in(xml: str, tag: str) -> list[str]:
    name = tag.split(":")[1]
    blocks = re.findall(rf"<w:{name}\b[^>]*>(.*?)</w:{name}>", xml, re.S)
    texts = []
    for b in blocks:
        texts += re.findall(r"<w:(?:t|delText)\b[^>]*>(.*?)</w:(?:t|delText)>", b, re.S)
    return [_unescape(t) for t in texts]


def _vanished_texts(xml: str) -> list[str]:
    out = []
    for run in re.findall(r"<w:r\b[^>]*>(.*?)</w:r>", xml, re.S):
        if "<w:vanish" in run:
            out += [_unescape(t) for t in re.findall(r"<w:t\b[^>]*>(.*?)</w:t>", run, re.S)]
    return out


def _remove_regions(xml: str, tags: list[str]) -> str:
    for tag in tags:
        name = tag.split(":")[1]
        xml = re.sub(rf"<w:{name}\b[^>]*>.*?</w:{name}>", " ", xml, flags=re.S)
    # also drop vanished runs from the "body" reading
    xml = re.sub(r"<w:r\b[^>]*>(?:(?!</w:r>).)*?<w:vanish[^>]*>.*?</w:r>", " ", xml, flags=re.S)
    return xml


def _strip_tags(xml: str) -> str:
    xml = re.sub(r"<[^>]+>", " ", xml)
    return _unescape(xml)


def _unescape(s: str) -> str:
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&apos;", "'"))


def _collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()
