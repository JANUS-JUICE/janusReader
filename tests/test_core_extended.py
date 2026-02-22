from io import StringIO
from pathlib import Path
import xml.dom.minidom as md

import numpy as np
import pytest
from click.testing import CliRunner
from rich.console import Console

import JanusReader.core as core
from JanusReader.core import JanusReader, action, getElement, getValue


LBLX_TEMPLATE = """<?xml version='1.0' encoding='UTF-8'?>
<pds:Product_Observational
    xmlns:pds='urn:nasa:pds'
    xmlns:img='urn:nasa:pds:img'
    xmlns:psa='urn:esa:psa'
    xmlns:juice_janus='urn:esa:juice:janus'>
  <pds:Identification_Area>
    <pds:title>Test Product</pds:title>
    <pds:Modification_Detail><pds:version_id>1.0</pds:version_id></pds:Modification_Detail>
  </pds:Identification_Area>
  <pds:Observation_Area>
    <pds:comment>synthetic label</pds:comment>
    <pds:Time_Coordinates>
      <pds:start_date_time>2025-01-01T00:00:00.000000Z</pds:start_date_time>
      <pds:stop_date_time>2025-01-01T00:00:01.000000Z</pds:stop_date_time>
    </pds:Time_Coordinates>
    <pds:Primary_Result_Summary>
      <pds:processing_level>{processing_level}</pds:processing_level>
    </pds:Primary_Result_Summary>
    <pds:Target_Identification><pds:name>Europa</pds:name></pds:Target_Identification>
    <pds:Mission_Area>
      <psa:Mission_Information />
      <psa:spacecraft_clock_start_count>1/0000</psa:spacecraft_clock_start_count>
      <psa:spacecraft_clock_stop_count>1/0001</psa:spacecraft_clock_stop_count>
      <psa:mission_phase_name>Cruise</psa:mission_phase_name>
      <psa:mission_phase_identifier>CRU</psa:mission_phase_identifier>
      <psa:start_orbit_number>10</psa:start_orbit_number>
      <psa:stop_orbit_number>10</psa:stop_orbit_number>
    </pds:Mission_Area>
    <psa:Observation_Context>
      <psa:instrument_pointing_mode>NADIR</psa:instrument_pointing_mode>
      <psa:observation_identifier>OBS-1</psa:observation_identifier>
    </psa:Observation_Context>
    <img:Optical_Filter>
      <img:filter_name>RED</img:filter_name>
      <img:filter_number>1</img:filter_number>
      <img:bandwidth>50</img:bandwidth>
      <img:center_filter_wavelength>650</img:center_filter_wavelength>
    </img:Optical_Filter>
    <juice_janus:Acquisition_Properties>
      <juice_janus:cover_status_hw>CLOSED</juice_janus:cover_status_hw>
      <juice_janus:cover_status_sw>CLOSED</juice_janus:cover_status_sw>
      <juice_janus:instrument_mode>SCIENCE</juice_janus:instrument_mode>
      <juice_janus:image_session_id>5</juice_janus:image_session_id>
      <juice_janus:image_number>2</juice_janus:image_number>
      <juice_janus:filter_wheel_direction>FWD</juice_janus:filter_wheel_direction>
      <juice_janus:filter_wheel_snapin>1</juice_janus:filter_wheel_snapin>
    </juice_janus:Acquisition_Properties>
    <juice_janus:Onboard_Processing>
      <juice_janus:bad_pixel_correction>1</juice_janus:bad_pixel_correction>
      <juice_janus:bad_pixel_map_name>BPM</juice_janus:bad_pixel_map_name>
      <juice_janus:bad_pixel_count>0</juice_janus:bad_pixel_count>
      <juice_janus:fpn_correction>1</juice_janus:fpn_correction>
      <juice_janus:fpn_map_name>FPN</juice_janus:fpn_map_name>
      <juice_janus:spike_maximum_value>1</juice_janus:spike_maximum_value>
      <juice_janus:spike_distance>2</juice_janus:spike_distance>
      <juice_janus:spike_count>0</juice_janus:spike_count>
      <juice_janus:spike_correction>1</juice_janus:spike_correction>
    </juice_janus:Onboard_Processing>
    <juice_janus:Onground_Processing>
      <juice_janus:asw_tick_len>1</juice_janus:asw_tick_len>
      <juice_janus:peu_tick_len>1</juice_janus:peu_tick_len>
      <juice_janus:lost_packets_count>0</juice_janus:lost_packets_count>
      <juice_janus:lost_cmprs_pixels>0</juice_janus:lost_cmprs_pixels>
    </juice_janus:Onground_Processing>
    <psa:Processing_Context>
      <psa:processing_software_title>janus-pipeline</psa:processing_software_title>
      <psa:processing_software_version>1.2.3</psa:processing_software_version>
      <psa:Processing_Input_Identification>
        <psa:type>RAW</psa:type>
        <psa:file_name>input.vic</psa:file_name>
      </psa:Processing_Input_Identification>
    </psa:Processing_Context>
  </pds:Observation_Area>
  <img:Exposure><img:exposure_duration>12.5</img:exposure_duration></img:Exposure>
  <img:Subframe>
    <img:first_line>0</img:first_line>
    <img:first_sample>0</img:first_sample>
    <img:lines>{lines}</img:lines>
    <img:samples>{samples}</img:samples>
    <img:subframe_type>FULL</img:subframe_type>
  </img:Subframe>
  <img:Instrument_State>
    <img:Device_Temperature>
      <img:device_name>SENSOR_A</img:device_name>
      <img:temperature_value unit='C'>20</img:temperature_value>
    </img:Device_Temperature>
  </img:Instrument_State>
  <pds:File_Area_Observational>
    <pds:creation_date_time>{creation_date_time}</pds:creation_date_time>
    <pds:Array_2D_Image>
      <pds:offset>{offset}</pds:offset>
      <pds:Axis_Array><pds:elements>{lines}</pds:elements></pds:Axis_Array>
      <pds:Axis_Array><pds:elements>{samples}</pds:elements></pds:Axis_Array>
    </pds:Array_2D_Image>
  </pds:File_Area_Observational>
</pds:Product_Observational>
"""


def _write_lblx(
    path: Path,
    processing_level: str,
    lines: int,
    samples: int,
    offset: int,
    creation_has_z: bool | None = None,
):
    if creation_has_z is None:
        creation_has_z = path.suffix != ".vic"
    creation = (
        "2025-01-01T00:00:02.000000Z"
        if creation_has_z
        else "2025-01-01T00:00:02.000000"
    )
    text = LBLX_TEMPLATE.format(
        processing_level=processing_level,
        lines=lines,
        samples=samples,
        offset=offset,
        creation_date_time=creation,
    )
    path.with_suffix(".lblx").write_text(text, encoding="utf-8")


def test_get_value_duplicate_tag_prints_warning_and_returns_first():
    core.cons = Console(file=StringIO(), force_terminal=False)
    doc = md.parseString("<root><dup>1</dup><dup>2</dup></root>").documentElement

    value = getValue(doc, "dup")

    assert value == 1


def test_get_element_can_select_last_node_with_negative_index():
    doc = md.parseString("<root><item>1</item><item>2</item></root>").documentElement

    last = getElement(doc, "item", -1)

    assert last.firstChild.data == "2"


def test_reader_show_all_renders_extended_sections_for_dat(tmp_path: Path):
    file_path = tmp_path / "a_b_c_c03_d_e_tail.dat"
    data = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    file_path.write_bytes(data.tobytes())
    _write_lblx(file_path, "calibrated", lines=2, samples=2, offset=0)

    stream = StringIO()
    reader = JanusReader(file_path, console=Console(file=stream, force_terminal=False))
    reader.Show(all=True)
    rendered = stream.getvalue()

    assert "Processing Context" in rendered
    assert "Skipped Calibration" in rendered
    assert "Dead Pixels" in rendered


def test_reader_show_compact_renders_general_panel(tmp_path: Path):
    file_path = tmp_path / "raw_product.vic"
    lines, samples, offset = 1, 2, 4
    pixels = np.array([[7, 8]], dtype=np.uint16)
    file_path.write_bytes((b"X" * offset) + pixels.tobytes())
    _write_lblx(file_path, "raw", lines=lines, samples=samples, offset=offset)

    stream = StringIO()
    reader = JanusReader(file_path, console=Console(file=stream, force_terminal=False))
    reader.Show(all=False)
    rendered = stream.getvalue()

    assert "General information" in rendered
    assert f"Label for {file_path.name}" in rendered


def test_xml_input_with_cal_name_resolves_to_dat(tmp_path: Path):
    xml_input = tmp_path / "a_b_cal_c00_d_e_tail.xml"
    dat_file = xml_input.with_suffix(".dat")
    dat_file.write_bytes(np.array([[1.0]], dtype=np.float32).tobytes())
    _write_lblx(dat_file, "calibrated", lines=1, samples=1, offset=0)

    reader = JanusReader(str(xml_input), console=Console(), vicar=False)

    assert reader.fileName.suffix == ".dat"
    assert reader.level == "calibrated"


def test_vicar_option_is_ignored_for_dat_and_warns(tmp_path: Path):
    file_path = tmp_path / "a_b_c_c00_d_e_tail.dat"
    file_path.write_bytes(np.array([[3.0]], dtype=np.float32).tobytes())
    _write_lblx(file_path, "calibrated", lines=1, samples=1, offset=0)

    stream = StringIO()
    JanusReader(
        file_path,
        console=Console(file=stream, force_terminal=False),
        vicar=True,
    )

    assert "VICAR option ignored" in stream.getvalue()


def test_vicar_option_parses_header_for_vic_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    file_path = tmp_path / "valid.vic"
    header_size = 20
    header = b"LBLSIZE=20 " + (b"A" * 10)
    pixels = np.array([[10]], dtype=np.uint16).tobytes()
    file_path.write_bytes(header + pixels)
    _write_lblx(file_path, "raw", lines=1, samples=1, offset=header_size, creation_has_z=False)

    monkeypatch.setattr(core, "load_header", lambda _: {"parsed": True})

    reader = JanusReader(file_path, console=Console(), vicar=True)

    assert reader.vicar == {"parsed": True}
    assert reader.label_size == 20


def test_action_proc_for_raw_file_prints_not_calibrated(tmp_path: Path):
    file_path = tmp_path / "raw_product.vic"
    file_path.write_bytes((b"X" * 4) + np.array([[1]], dtype=np.uint16).tobytes())
    _write_lblx(file_path, "raw", lines=1, samples=1, offset=4)

    result = CliRunner().invoke(action, [str(file_path), "--show-skipped-process"])

    assert result.exit_code == 0
    assert "Not a calibrated data file" in result.output


def test_action_proc_for_dat_file_prints_skipped_steps(tmp_path: Path):
    file_path = tmp_path / "a_b_c_c03_d_e_tail.dat"
    file_path.write_bytes(np.array([[5.0]], dtype=np.float32).tobytes())
    _write_lblx(file_path, "calibrated", lines=1, samples=1, offset=0)

    result = CliRunner().invoke(action, [str(file_path), "--show-skipped-process"])

    assert result.exit_code == 0
    assert "Skipped Calibration" in result.output
    assert "Dead Pixels" in result.output


def test_action_without_proc_prints_label(tmp_path: Path):
    file_path = tmp_path / "raw_product.vic"
    file_path.write_bytes((b"X" * 4) + np.array([[1]], dtype=np.uint16).tobytes())
    _write_lblx(file_path, "raw", lines=1, samples=1, offset=4)

    result = CliRunner().invoke(action, [str(file_path)])

    assert result.exit_code == 0
    assert f"Label for {file_path.name}" in result.output
