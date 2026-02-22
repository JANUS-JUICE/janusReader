from JanusReader.vicar_head import load_header


def test_load_header_parses_scalars_and_groups():
    header = "INT=7 FLOAT=3.5 STR='abc' ARR=(1,2,3) MIXED=(1,2.5,'x')"

    parsed = load_header(header)

    assert parsed["INT"] == 7
    assert parsed["FLOAT"] == 3.5
    assert parsed["STR"] == "abc"
    assert parsed["ARR"] == [1, 2, 3]
    assert parsed["MIXED"] == [1, 2.5, "x"]


def test_load_header_handles_spaces_inside_groups():
    header = "GROUP=( 10,  20 ,30 )"

    parsed = load_header(header)

    assert parsed["GROUP"] == [10, 20, 30]
