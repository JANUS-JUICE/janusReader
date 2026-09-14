from pathlib import Path

import numpy as np
import pytest
from rich.console import Console

from JanusReader.core import JanusReader
from JanusReader.exceptions import NOT_VALID_VICAR_FILE


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


def test_reads_raw_vic_image(tmp_path: Path):
    file_path = tmp_path / "raw_product.vic"
    lines, samples, offset = 2, 3, 8

    pixels = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.uint16)
    file_path.write_bytes((b"X" * offset) + pixels.tobytes())
    _write_lblx(file_path, "raw", lines, samples, offset)

    reader = JanusReader(file_path, console=Console(), vicar=False)

    assert reader.level == "raw"
    assert reader.image.shape == (2, 3)
    assert np.array_equal(reader.image, pixels)


def test_reads_calibrated_dat_image_and_skipped_steps(tmp_path: Path):
    file_path = tmp_path / "a_b_c_c03_d_e_tail.dat"
    lines, samples = 2, 2
    data = np.array([[1.0, 2.0], [3.5, 4.5]], dtype=np.float32)
    file_path.write_bytes(data.tobytes())
    _write_lblx(file_path, "calibrated", lines, samples, offset=0)

    reader = JanusReader(file_path, console=Console(), vicar=False)

    assert reader.level == "calibrated"
    assert reader.image.dtype == np.float32
    assert np.array_equal(reader.image, data)
    assert reader.skippedCalibrationSteps is not None
    assert reader.skippedCalibrationSteps.steps == ["Dead Pixels", "Bad Pixels"]


def test_lblx_input_resolves_to_raw_vic(tmp_path: Path):
    base = tmp_path / "sample_raw_file.vic"
    lines, samples, offset = 1, 2, 4

    data = np.array([[7, 9]], dtype=np.uint16)
    base.write_bytes((b"0" * offset) + data.tobytes())
    _write_lblx(base, "raw", lines, samples, offset, creation_has_z=True)

    reader = JanusReader(base.with_suffix(".lblx"), console=Console(), vicar=False)

    assert reader.fileName.suffix == ".vic"
    assert np.array_equal(reader.image, data)


def test_invalid_vicar_header_raises(tmp_path: Path):
    file_path = tmp_path / "invalid.vic"
    file_path.write_bytes(b"NOT_A_VICAR_HEADER")

    with pytest.raises(NOT_VALID_VICAR_FILE):
        JanusReader(file_path, console=Console(), vicar=True)
