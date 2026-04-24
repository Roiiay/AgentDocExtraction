import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import List, TypedDict


NS = {"ofd": "http://www.ofdspec.org"}


class TextBlock(TypedDict):
    text: str
    boundary: tuple[float, float, float, float]  # x, y, w, h
    font_id: str
    font_size: float


class OFDPageResult(TypedDict):
    page_num: int
    width: int
    height: int
    text_blocks: List[TextBlock]


class OFDParser:
    """解析 OFD 文件（ZIP + XML），提取页面结构。"""

    def parse(self, ofd_path: str | Path) -> List[OFDPageResult]:
        ofd_path = Path(ofd_path)
        if not ofd_path.exists():
            raise FileNotFoundError(f"OFD file not found: {ofd_path}")

        try:
            zf = zipfile.ZipFile(str(ofd_path), "r")
        except zipfile.BadZipFile:
            raise ValueError(f"Not a valid OFD/ZIP file: {ofd_path}")

        try:
            # 1. 解析 OFD.xml -> 获取 DocRoot
            doc_root_rel = self._get_doc_root(zf)

            # 2. 解析 Document.xml -> 获取页面列表和页面尺寸
            doc_dir = str(Path(doc_root_rel).parent)
            pages_info, page_width, page_height = self._parse_document(zf, doc_dir, doc_root_rel)

            # 3. 解析每一页的 Content.xml
            results: List[OFDPageResult] = []
            for idx, page_loc in enumerate(pages_info):
                content_path = f"{doc_dir}/{page_loc}"
                text_blocks = self._parse_page_content(zf, content_path)
                results.append(
                    OFDPageResult(
                        page_num=idx,
                        width=page_width,
                        height=page_height,
                        text_blocks=text_blocks,
                    )
                )

            return results
        finally:
            zf.close()

    def _get_doc_root(self, zf: zipfile.ZipFile) -> str:
        root_xml = zf.read("OFD.xml")
        root = ET.fromstring(root_xml)
        doc_body = root.find("ofd:DocBody", NS)
        if doc_body is None:
            raise ValueError("Invalid OFD: missing DocBody")
        doc_root_el = doc_body.find("ofd:DocRoot", NS)
        if doc_root_el is None or not doc_root_el.text:
            raise ValueError("Invalid OFD: missing DocRoot")
        return doc_root_el.text.strip()

    def _parse_document(
        self, zf: zipfile.ZipFile, doc_dir: str, doc_root_rel: str
    ) -> tuple[List[str], int, int]:
        doc_xml = zf.read(doc_root_rel)
        root = ET.fromstring(doc_xml)

        # 页面尺寸
        page_area = root.find(".//ofd:PageArea/ofd:PhysicalBox", NS)
        if page_area is not None and page_area.text:
            parts = page_area.text.strip().split()
            width, height = int(float(parts[2])), int(float(parts[3]))
        else:
            width, height = 210, 297  # A4 默认

        # 页面列表
        pages_el = root.find("ofd:Pages", NS)
        page_locs: List[str] = []
        if pages_el is not None:
            for page_el in pages_el.findall("ofd:Page", NS):
                base_loc = page_el.get("BaseLoc", "")
                if base_loc:
                    page_locs.append(base_loc)

        return page_locs, width, height

    def _parse_page_content(
        self, zf: zipfile.ZipFile, content_path: str
    ) -> List[TextBlock]:
        try:
            content_xml = zf.read(content_path)
        except KeyError:
            return []

        root = ET.fromstring(content_xml)
        blocks: List[TextBlock] = []

        # TODO: 当前仅提取 TextObject，忽略 ImageObject / PathObject（图章、签名、图形等），
        #       后续需要扩展以支持这些元素，避免静默丢失内容

        for text_obj in root.iter("{http://www.ofdspec.org}TextObject"):
            boundary_str = text_obj.get("Boundary", "")
            font_id = text_obj.get("Font", "")
            size = float(text_obj.get("Size", "12"))

            boundary = (0.0, 0.0, 0.0, 0.0)
            if boundary_str:
                parts = boundary_str.split()
                boundary = tuple(float(p) for p in parts)

            # 提取文本内容
            text_parts: List[str] = []
            for tc in text_obj.iter("{http://www.ofdspec.org}TextCode"):
                if tc.text:
                    text_parts.append(tc.text)
            text = "".join(text_parts)

            blocks.append(
                TextBlock(
                    text=text,
                    boundary=boundary,
                    font_id=font_id,
                    font_size=size,
                )
            )

        return blocks
