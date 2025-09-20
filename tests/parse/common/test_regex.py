import re

from abe.parse import common

import pytest


# TODO: test for false positives

comments = {
    "// basic": "// this is a comment",
    "//no space": "//also a comment",
    # "trailing //": "some_code();  // trailing comment",
    "empty //": "//"}
# NOTE: re.search, re.match & re.fullmatch all behave differently
# -- we're just testing re.fullmatch here
# -- re.search will catch trailing comments etc.

comments.update({
    id_.replace("//", r"\\"): sample.replace("//", r"\\")
    for id_, sample in comments.items()})
filepaths = [
    "lowercase",
    "MixedCase",
    "folder/filename",
    r"folder\filename",
    "host:folder/filename_0451.ext"]

integers = {
    "basic": "69",
    "signed": "+420",
    "leading 0s": "007",
    "negative": "-1"}
# TODO: false positive: sign w/o number

matches = {
    **{
        f"comment | {id_}": (common.comment, sample)
        for id_, sample in comments.items()},
    **{
        f"filepath | {sample}": (common.filepath, sample)
        for sample in filepaths},
    **{
        f"integer | {id_}": (common.integer, sample)
        for id_, sample in integers.items()}}


@pytest.mark.parametrize(
    "raw_pattern,sample", matches.values(), ids=matches.keys())
def test_matches(raw_pattern: str, sample: str):
    pattern = re.compile(raw_pattern)
    match = pattern.fullmatch(sample)
    assert match is not None


double = {
    "unsigned int": ("0", None, None),
    "signed int": ("+1", None, None),
    "unsigned decimal": ("2.34", ".34", None),
    "signed decimal": ("-5.67", ".67", None),
    "unsigned exponent": ("8e9", None, "e9"),
    "signed exponent": ("+1e-10", None, "e-10"),
    "unsigned exponent w/ decimal": ("2.34e5", ".34", "e5"),
    "signed exponent w/ decial": ("-6.78e+9", ".78", "e+9")}


@pytest.mark.parametrize(
    "base,decimal,exponent", double.values(), ids=double.keys())
def test_double(base: str, decimal: str, exponent: str):
    """sample matches & is grouped as expected"""
    pattern = re.compile(common.double)
    match = pattern.fullmatch(base)
    assert match is not None
    expected = (base, decimal, exponent)
    assert match.groups() == expected


keyvalues = {
    "double double quotes": ('"key" "value"', "key", "value")}
# TODO: single quote variants (NotImplemented)
# NOTE: not trying to catch multiline values w/ regex
# -- that's a problem for MapFile.parse


@pytest.mark.parametrize(
    "line,key,value", keyvalues.values(), ids=keyvalues.keys())
def test_key_values(line: str, key: str, value: str):
    """sample matches & is grouped as expected"""
    pattern = re.compile(common.key_value_pair)
    match = pattern.fullmatch(line)
    assert match is not None
    expected = (key, value)
    assert match.groups() == expected


points = {
    "basic": "( 0 0 0 )",
    "signed": "( 1 +2 -3 )",
    "decimal": "( 4.56 7.89 0 )",
    "exponent": "( 1e2 +3e-4 -5e+6 )"}


@pytest.mark.parametrize("sample", points.values(), ids=points.keys())
def test_point(sample: str):
    pattern = re.compile(common.point)
    match = pattern.fullmatch(sample)
    assert match is not None
    # TODO: test groups are correct


planes = {
    "basic": "( 0 0 0 ) ( 1 0 0 ) ( 0 1 0 )",
    "common": "( -192 64 48 ) ( -384 64 48 ) ( -192 -96 48 )",
    "rounding error": "( 0 0 1.02e-5 ) ( 0.9998 0 0 ) ( 0 1 1.6e-9 )"}


@pytest.mark.parametrize("sample", planes.values(), ids=planes.keys())
def test_plane(sample: str):
    pattern = re.compile(common.plane)
    match = pattern.fullmatch(sample)
    assert match is not None
    # TODO: test groups are correct
