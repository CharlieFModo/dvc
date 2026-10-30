from dvc.repo.push import _rebuild
from dvc_data.index import DataIndex, DataIndexEntry, Meta


class BatchInfoFS:
    protocol = "s3"

    def __init__(self, infos):
        self.infos = infos
        self.calls = []

    def join(self, *parts):
        return "/".join(parts)

    def info(self, paths, callback=None, return_exceptions=False):
        self.calls.append(paths)
        return [self.infos.get(path, FileNotFoundError(path)) for path in paths]


def test_rebuild_fetches_file_infos_in_one_batch(mocker):
    index = DataIndex(
        {
            ("data",): DataIndexEntry(key=("data",), meta=Meta(isdir=True)),
            ("data", "foo"): DataIndexEntry(key=("data", "foo"), meta=Meta()),
            ("missing",): DataIndexEntry(key=("missing",), meta=Meta()),
        }
    )
    fs = BatchInfoFS(
        {
            "remote/data/foo": {
                "type": "file",
                "size": 4,
                "ETag": '"d3b07384d113edec49eaa6238ad5ff00"',
                "VersionId": "v1",
            }
        }
    )

    new = _rebuild(index, "remote", fs, mocker.MagicMock())

    assert fs.calls == [["remote/data/foo", "remote/missing"]]
    assert new[("data",)].meta.isdir
    assert new[("data", "foo")].meta.version_id == "v1"
    assert new[("data", "foo")].meta.etag == "d3b07384d113edec49eaa6238ad5ff00"
    assert new.get(("missing",)) is None
