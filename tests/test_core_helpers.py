from io import StringIO
import xml.dom.minidom as md

from rich.console import Console

import JanusReader.core as core
from JanusReader.core import SkippedSteps, getValue


def _node(xml: str):
    return md.parseString(xml).documentElement


def test_get_value_casts_int_and_float_and_preserves_version_id():
    node = _node(
        """
        <root>
            <num>42</num>
            <flt>12.5</flt>
            <version_id>01.02</version_id>
        </root>
        """
    )

    assert getValue(node, "num") == 42
    assert getValue(node, "flt") == 12.5
    assert getValue(node, "version_id") == "01.02"


def test_get_value_returns_none_when_missing_tag():
    core.cons = Console(file=StringIO(), force_terminal=False)
    node = _node("<root><a>1</a></root>")

    assert getValue(node, "missing") is None


def test_skipped_steps_decoding():
    steps = SkippedSteps("03")

    assert steps.steps == ["Dead Pixels", "Bad Pixels"]


def test_unprefixed_pds_lookup_does_not_match_other_namespaces():
    node = _node(
        '<pds:root xmlns:pds="urn:nasa:pds" xmlns:psa="urn:esa:psa">'
        '<psa:title>Wrong title</psa:title><pds:title>Product title</pds:title>'
        '</pds:root>'
    )

    assert getValue(node, "title") == "Product title"
