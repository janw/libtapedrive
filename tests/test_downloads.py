from os import path, makedirs

import pytest

from libtapedrive.downloads import _download_file


@pytest.mark.vcr
def test_download_file(tmpdir):
    makedirs(tmpdir, exist_ok=True)
    output = path.join(tmpdir, "testfile.bin")
    url = "https://github.com/janw/libtapedrive/raw/master/tests/fixtures/testfile.bin"
    expected_size = 54

    output_size = _download_file(url, output, chunk_size=100, progress=False)

    assert output_size == expected_size
    with open(output) as fp:
        assert "This is a testfile for downloading." in fp.read()
