import io
import zipfile
import pytest

from backend.app.parsers.ofd_parser import OFDParser, OFDPageResult


def _create_minimal_ofd() -> bytes:
    """构建一个最小合法 OFD 文件用于测试。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("OFD.xml", """<?xml version="1.0" encoding="UTF-8"?>
<ofd:OFD xmlns:ofd="http://www.ofdspec.org" DocType="OFD">
  <ofd:DocBody>
    <ofd:DocInfo>
      <ofd:Title>Test</ofd:Title>
    </ofd:DocInfo>
    <ofd:DocRoot>Doc_0/Document.xml</ofd:DocRoot>
  </ofd:DocBody>
</ofd:OFD>""")

        zf.writestr("Doc_0/Document.xml", """<?xml version="1.0" encoding="UTF-8"?>
<ofd:Document xmlns:ofd="http://www.ofdspec.org">
  <ofd:CommonData>
    <ofd:MaxUnitID>1</ofd:MaxUnitID>
    <ofd:PageArea>
      <ofd:PhysicalBox>0 0 210 297</ofd:PhysicalBox>
    </ofd:PageArea>
    <ofd:PublicRes>PublicRes.xml</ofd:PublicRes>
  </ofd:CommonData>
  <ofd:Pages>
    <ofd:Page ID="1" BaseLoc="Pages/Page_0/Content.xml"/>
  </ofd:Pages>
</ofd:Document>""")

        zf.writestr("Doc_0/PublicRes.xml", """<?xml version="1.0" encoding="UTF-8"?>
<Res xmlns="http://www.ofdspec.org">
  <Fonts>
    <Font ID="1" FontName="SimSun"/>
  </Fonts>
</Res>""")

        zf.writestr("Doc_0/Pages/Page_0/Content.xml", """<?xml version="1.0" encoding="UTF-8"?>
<ofd:Page xmlns:ofd="http://www.ofdspec.org">
  <ofd:Content>
    <ofd:Layer>
      <TextObject ID="10" Boundary="10 20 180 30" Font="1" Size="12">
        <TextCode X="10" Y="40" DeltaX="12">Hello OFD</TextCode>
      </TextObject>
    </ofd:Layer>
  </ofd:Content>
</ofd:Page>""")

    return buf.getvalue()


@pytest.fixture
def sample_ofd_path(tmp_path):
    ofd_file = tmp_path / "test.ofd"
    ofd_file.write_bytes(_create_minimal_ofd())
    return ofd_file


def test_parse_returns_pages(sample_ofd_path):
    parser = OFDParser()
    pages = parser.parse(sample_ofd_path)
    assert isinstance(pages, list)
    assert len(pages) == 1


def test_page_has_required_fields(sample_ofd_path):
    parser = OFDParser()
    pages = parser.parse(sample_ofd_path)
    page = pages[0]
    assert "page_num" in page
    assert "width" in page
    assert "height" in page
    assert "text_blocks" in page


def test_page_dimensions_from_physical_box(sample_ofd_path):
    parser = OFDParser()
    pages = parser.parse(sample_ofd_path)
    page = pages[0]
    # PhysicalBox = "0 0 210 297"
    assert page["width"] == 210
    assert page["height"] == 297


def test_parse_nonexistent_file():
    parser = OFDParser()
    with pytest.raises(FileNotFoundError):
        parser.parse("/nonexistent/file.ofd")


def test_parse_invalid_zip(tmp_path):
    bad_file = tmp_path / "bad.ofd"
    bad_file.write_text("not a zip file")
    parser = OFDParser()
    with pytest.raises(ValueError):
        parser.parse(bad_file)
