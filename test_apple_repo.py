#
# partcad-openusd-apple, 2026
#
# Licensed under Apache License, Version 2.0.
#
"""Tests of the Apple plugin, with developer.apple.com answered from a table.

The gallery's page has the markup the gallery's has - '<a rel="ar"
href=".../models/<folder>/<file>.usdz">' - and the models are made-up USDZ
packages. Nothing here touches the network.
"""

import base64
import importlib.util
import os
import re
import runpy

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PLUGIN = os.path.join(_HERE, "apple_repo.py")
_SPEC = importlib.util.spec_from_file_location("apple_repo_under_test", _PLUGIN)
plugin = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(plugin)
ua = plugin.ua

MODEL = ua.write_usdz([("teapot.usdc", b"PXR-USDC")])
PAGE = (
    '<a rel="ar" href="/quick-look-gallery/models/teapot/teapot.usdz"><img src="teapot.png"></a>'
    '<a rel="ar" href="/quick-look-gallery/models/newthing/new_thing.usdz"><img src="x.png"></a>'
    '<a rel="ar" href="/quick-look-gallery/models/hab/hab_en.reality"><img src="hab.png"></a>'
).encode()


class Wire:
    def __init__(self, table):
        self.table = dict(table)
        self.asked = []

    def __call__(self, url, headers=None, method=None, timeout=120):
        self.asked.append(url)
        if url not in self.table:
            return ua.Response(404, {}, b"", url)
        return ua.Response(200, {}, self.table[url], url)


@pytest.fixture
def apple(tmp_path, monkeypatch):
    monkeypatch.setenv("PARTCAD_OPENUSD_APPLE_CACHE", str(tmp_path))

    def make(table=None):
        made = plugin.Apple({"parameters": {}})
        made.http.request = Wire(
            table
            if table is not None
            else {
                plugin.GALLERY: PAGE,
                plugin.SITE + plugin.MODELS + "teapot/teapot.usdz": MODEL,
                plugin.SITE + plugin.MODELS + "toycar/toy_car.usdz": b"<html><body>the gallery</body></html>",
            }
        )
        return made

    return make


def test_a_part_per_model_the_gallery_has_or_had_and_no_reality_file(apple):
    parts = apple().get("objects/part")
    assert "teapot" in parts and "newthing" in parts and "toycar" in parts
    assert "hab" not in parts
    assert len(parts) == len(plugin.KNOWN) + 1
    assert parts["teapot"]["type"] == "usd"
    assert parts["teapot"]["license"] == "LicenseRef-Apple-Website-Terms"


def test_a_model_is_handed_over_as_apple_publishes_it(apple):
    assert base64.b64decode(apple().get("files/teapot.usdz")) == MODEL


def test_a_page_in_a_models_place_is_refused_for_what_it_is(apple, capsys):
    assert ua.serve(apple(), "files/toycar.usdz") is None
    assert "not a USDZ model (a web page)" in capsys.readouterr().err


def test_without_the_gallery_the_models_it_had_are_listed(apple, capsys):
    parts = apple(table={}).get("objects/part")
    assert sorted(parts) == sorted(path.split("/")[0] for path in plugin.KNOWN)
    assert "only the models it is known to have" in capsys.readouterr().err


def test_only_the_gallerys_own_path_is_asked(apple):
    made = apple()
    made.get("files/teapot.usdz")
    assert not any("/augmented-reality/" in url for url in made.http.request.asked)


def test_the_plugin_is_named_as_the_package_declares_it():
    with open(os.path.join(_HERE, "partcad.yaml")) as f:
        text = f.read()
    name = re.search(r"^name: (\S+)", text, re.M).group(1)
    assert re.search(r"^  apple_repo:\n    type: basic\n    path: apple_repo.py", text, re.M)
    assert plugin.Apple.PLUGIN == name + ":apple_repo"


def test_partcad_runs_it_and_reads_the_answer_from_output(tmp_path, monkeypatch):
    monkeypatch.setenv("PARTCAD_OPENUSD_APPLE_CACHE", str(tmp_path))
    result = runpy.run_path(_PLUGIN, init_globals={"request": {"key": "meta", "parameters": {}}}, run_name="get")
    assert result["output"]["result"]["manufacturable"] is False
