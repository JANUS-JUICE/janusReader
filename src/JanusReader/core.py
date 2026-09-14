import errno
import os
import xml.dom.minidom as md
from pathlib import Path

import numpy as np
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from JanusReader.exceptions import NOT_VALID_VICAR_FILE
from JanusReader.vicar_head import load_header
from datetime import datetime
from semantic_version_tools import Vers
from importlib.metadata import version as get_version

installed_version = get_version('JanusReader')
version=Vers(installed_version)
__version__ = version.full()



class MSG:
    """Data class for the message labelling"""

    DEBUG = "[blue][DEBUG][/blue]"
    WARNING = "[yellow][WARNING][/yellow]"
    ERROR = "[red][ERROR][/red]"


cons = Console()


def _get_elements(doc: md.Document | md.Element, label: str):
    """Resolve unprefixed PDS tags in the product namespace, not other schemas."""
    if ":" in label:
        return doc.getElementsByTagName(label)
    document = doc if isinstance(doc, md.Document) else doc.ownerDocument
    namespace = document.documentElement.namespaceURI
    return doc.getElementsByTagNameNS(namespace, label)


def getElement(doc: md.Document | md.Element, label: str, el: int = 0) -> md.Element:
    """Select a descendant, including negative indices for the latest revision."""
    elements = _get_elements(doc, label)
    if not elements:
        raise IndexError(f"Tag '{label}' not found")
    return elements[el]


def getValue(nodeList: md.Document | md.Element, label: str) -> str | int | float | None:
    """Read label values with JanusReader's historical conversion semantics."""
    elements = _get_elements(nodeList, label)
    if not elements:
        cons.print(f"{MSG.WARNING} Missing label {label}. The label might have been removed or renamed.")
        return None
    if len(elements) > 1:
        cons.print(f"{MSG.WARNING} More than one label {label}. The label might have been duplicated.")
    data = "".join(
        child.data for child in elements[0].childNodes
        if child.nodeType in (child.TEXT_NODE, child.CDATA_SECTION_NODE)
    ).strip()
    if "version_id" in label:
        return data
    if data.isdigit():
        return int(data)
    if data.replace(".", "", 1).isdigit() and data.count(".") == 1:
        return float(data)
    return data


class State:
    def __init__(self, item):
        self.name = getValue(item, "img:device_name").lower()
        self.value = getValue(item, "img:temperature_value")

        self.unit = getElement(item, "img:temperature_value").getAttribute("unit")


class InstrumentState:
    def __init__(self, stat):
        elem = stat.getElementsByTagName("img:Device_Temperature")
        self.states = []
        for item in elem:
            self.states.append(State(item))

    def Get(self, name: str):
        for item in self.states:
            if item.name == name.lower():
                return item.value
        return None

    def Show(self):
        tb = Table(
            expand=False,
            show_header=False,
            show_lines=False,
            box=box.SIMPLE_HEAD,
            title="Instrument State",
            title_style="italic yellow",
        )
        tb.add_column(style="yellow", justify="left")
        tb.add_column()
        tb.add_column()
        for item in self.states:
            tb.add_row(
                " ".join(item.name.split("_")).title(), "", f"{item.value} {item.unit}"
            )
        return tb


class Filter:
    def __init__(self, filter):
        self.filterName = getValue(filter, "img:filter_name")
        self.filtNumber = getValue(filter, "img:filter_number")
        self.bandwidth = getValue(filter, "img:bandwidth")
        self.filterWavelength = getValue(filter, "img:center_filter_wavelength")

    def Show(self):
        tb = Table(
            expand=False,
            show_header=False,
            show_lines=False,
            box=box.SIMPLE_HEAD,
            title="Filters Parameters",
            title_style="italic yellow",
        )
        tb.add_column(style="yellow", justify="left")
        tb.add_column()
        tb.add_column()
        tb.add_row("Filter Name", "", self.filterName)
        tb.add_row("Filter Number", "", str(self.filtNumber))
        tb.add_row("Bandwidth", "", f"{str(self.bandwidth)} nm")
        tb.add_row("Filter Center wavelegth", "", f"{str(self.filterWavelength)} nm")

        return tb


class AcquisitionParameter:
    def __init__(self, acq):
        # cover_status_hw/sw, instrument_mode, image_session_id,
        # image_number, filter_wheel_direction, filter_wheel_snapin:
        # tm2raw no longer writes these under Acquisition_Properties --
        # dropped here to match. Display-only (JanusCal's calibration
        # logic never references them), so nothing downstream needs a
        # replacement value.
        self.multifilter = None
        pass

    def Show(self):
        tb = Table(
            expand=False,
            show_header=False,
            show_lines=False,
            box=box.SIMPLE_HEAD,
            title="Acquisition Parameters",
            title_style="italic yellow",
        )
        tb.add_column(style="yellow", justify="left")
        tb.add_column()
        tb.add_column()
        tb.add_row("Multifilter", "", str(self.multifilter))
        return tb


class SubFrame:
    def __init__(self, proc) -> None:
        self.firstLine = getValue(proc, "img:first_line")
        self.firstSample = getValue(proc, "img:first_sample")
        self.lines = getValue(proc, "img:lines")
        self.samples = getValue(proc, "img:samples")
        self.subFrameType = getValue(proc, "img:subframe_type")

    def Show(self):
        tb = Table(
            expand=False,
            show_header=False,
            show_lines=False,
            box=box.SIMPLE_HEAD,
            title="SubFrame Parameters",
            title_style="italic yellow",
        )
        tb.add_column(style="yellow", justify="left")
        tb.add_column()
        tb.add_column()
        tb.add_row("First Sample", "", str(self.firstSample))
        tb.add_row("First Line", "", str(self.firstLine))
        tb.add_row("Sample", "", str(self.samples))
        tb.add_row("Lines", "", str(self.lines))
        tb.add_row("Subframe Type", "", self.subFrameType)
        return tb


class OnBoardProcessing:
    def __init__(self, proc):
        # bad_pixel_correction/bad_pixel_map_name/fpn_correction/fpn_map_name:
        # tm2raw no longer writes these under Onboard_Processing -- dropped
        # here to match (display-only, see AcquisitionParameter above).
        self.badPixelCount = getValue(proc, "juice_janus:bad_pixel_count")
        self.spikeMaximumValue = getValue(proc, "juice_janus:spike_maximum_value")
        self.spikeDistance = getValue(proc, "juice_janus:spike_distance")
        self.spikeCount = getValue(proc, "juice_janus:spike_count")
        self.spikeCorrection = getValue(proc, "juice_janus:spike_correction")

    def Show(self):
        tb = Table(
            expand=False,
            show_header=False,
            show_lines=False,
            box=box.SIMPLE_HEAD,
            title="Onboard Processing",
            title_style="italic yellow",
        )
        tb.add_column(style="yellow", justify="left")
        tb.add_column()
        tb.add_column()
        tb.add_row("Bad Pixel Count", "", str(self.badPixelCount))
        tb.add_section()
        tb.add_row("Spike Maximum Value", "", str(self.spikeMaximumValue))
        tb.add_row("Spike Distance", "", str(self.spikeDistance))
        tb.add_row("Spike Distance", "", str(self.spikeDistance))
        tb.add_row("Spike Correction", "", str(self.spikeCorrection))
        return tb


class OnGroundProcessing:
    def __init__(self, proc):
        # peu_tick_len: tm2raw no longer writes this under
        # Onground_Processing -- dropped here to match (display-only).
        self.aswTickLen = getValue(proc, "juice_janus:asw_tick_len")
        self.lostPacketCount = getValue(proc, "juice_janus:lost_packets_count")
        self.lostCmprsPixels = getValue(proc, "juice_janus:lost_cmprs_pixels")

    def Show(self):
        tb = Table(
            expand=False,
            show_header=False,
            show_lines=False,
            box=box.SIMPLE_HEAD,
            title="On Ground Processing",
            title_style="italic yellow",
        )
        tb.add_column(style="yellow", justify="left")
        tb.add_column()
        tb.add_column()
        tb.add_row("ASW Tick Length", "", str(self.aswTickLen))
        tb.add_row("Lost Packets Count", "", str(self.lostPacketCount))
        tb.add_row("Lost Compressed Pixels", "", str(self.lostCmprsPixels))
        return tb


class ProcessingInput:
    def __init__(self, proc):
        self.processingInputType = getValue(proc, "psa:type")
        self.processingInputFile = getValue(proc, "psa:file_name")


class ProcessingContext:
    def __init__(self, proc):
        self.softwareTitle = getValue(proc, "psa:processing_software_title")
        self.softwareVersion = getValue(proc, "psa:processing_software_version")
        elem = proc.getElementsByTagName("psa:Processing_Input_Identification")
        self.inputs = []
        for item in elem:
            self.inputs.append(ProcessingInput(item))

    def Get(self, name: str):
        for item in self.inputs:
            if item.name == name.lower():
                return item.value
        return None

    def Show(self):
        tb = Table(
            expand=False,
            show_header=False,
            show_lines=False,
            box=box.SIMPLE_HEAD,
            title="Processing Context",
            title_style="italic yellow",
        )
        tb.add_column(style="yellow", justify="left")
        tb.add_column()
        tb.add_column()
        tb.add_row(
            "Software Title", "", f"{self.softwareTitle} ({self.softwareVersion})"
        )
        for item in self.inputs:
            tb.add_row(item.processingInputType, "", f"{item.processingInputFile}")

        return tb


class SkippedSteps:
    def __init__(self, code):
        self.code = code
        self.steps = []
        integer_value = int(code, 16)

        # Convertire l'intero in una stringa binaria (rimuovendo il prefisso "0b")
        binary_string = bin(integer_value)[2:]

        # Aggiungere zeri iniziali per avere una lunghezza multipla di 4
        # Questo è utile per rappresentare correttamente l'intera lunghezza del numero esadecimale
        binary_string = binary_string.zfill(len(code) * 4)
        steps_dec = [
            "Dead Pixels",
            "Bad Pixels",
            "Saturated Pixels",
            "Dark Correction",
            "Offset Correction",
            "Radiometric Correction",
        ]
        for index, bit in enumerate(binary_string[::-1]):
            if bit == "1":
                self.steps.append(steps_dec[index])

    def Show(self):
        tb = Table(
            expand=False,
            show_header=False,
            show_lines=False,
            box=box.SIMPLE_HEAD,
            title="Skipped Calibration Steps",
            title_style="italic yellow",
        )
        tb.add_column(style="yellow", justify="left")
        tb.add_column()
        tb.add_column()
        if len(self.steps) == 0:
            tb.add_row("No calibration steps skipped", "", "")
        else:
            for idx, item in enumerate(self.steps):
                tb.add_row(str(idx + 1), "", item)
        return tb


class JanusReader:
    """Reader of the JANUS Data File

    Args:
        fileName (Path): input filename
        cns (:obj:`Console`,optional): A console instance to capture output. Defaults to None.

    Attributes:
        fileName (Path): input filename
        img (np.array): image data

    Raises:
        NOT_VALID_VICAR_FILE
            The input file ``fileName`` is not ion VICAR format.
    """

    def __init__(
        self,
        fileName: Path,
        console: Console = None,
        debug: bool = False,
        vicar: bool = False,
    ):
        # Check if console exists, if not create one
        global cons  # the variable will be global for the module
        # definition of the dateformat
        self._dateformat = "%Y-%m-%dT%H:%M:%S.%fZ"
        if console is None:
            cons = Console()
        else:
            cons = console
        self.console = cons
        # Check the file type, is str convert to Path
        if type(fileName) is not Path:
            fileName = Path(fileName)
        self.fileName = fileName
        # Check the file extension
        if self.fileName.suffix == ".vic":
            if debug:
                self.console.print(f"{MSG.DEBUG} Input type: Vicar file")
            if not self.fileName.exists():
                raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), self.fileName.name
                )
        elif self.fileName.suffix in [".xml", ".lblx"]:
            if debug:
                self.console.print(f"{MSG.DEBUG} Input type: XML file")
            if "raw" in self.fileName.name:
                self.fileName = self.fileName.with_suffix(".vic")
            elif "cal" in self.fileName.name:
                self.fileName = self.fileName.with_suffix(".dat")
            if not self.fileName.exists():
                raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), self.fileName.name
                )
        elif self.fileName.suffix == ".dat":
            if debug:
                self.console.print(f"{MSG.DEBUG} Input type: Calibrated Data file")
            if not self.fileName.exists():
                raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), self.fileName.name
                )
        # Read the Vicar Header
        if vicar and self.fileName.suffix != ".dat":
            self.vicar = {}
            with open(self.fileName, "rb") as f:
                header_prefix = f.read(40).decode("latin-1")
            if "LBLSIZE" not in header_prefix:
                raise NOT_VALID_VICAR_FILE("File is not a valid VICAR file")
            iblank = header_prefix.index(" ", 8)
            self.label_size = int(header_prefix[8:iblank])
            with open(self.fileName, "rb") as f:
                lbl = str(f.read(self.label_size).decode("latin-1"))
            self.vicar = load_header(lbl)
        elif vicar and self.fileName.suffix == ".dat":
            self.console.print(
                f"{MSG.WARNING} The file is a calibrated data file. VICAR option ignored."
            )

        if self.fileName.suffix == ".dat":
            parts = self.fileName.name.split("_")
            code = parts[-4][1:]
            self.skippedCalibrationSteps = SkippedSteps(code)
        else:
            self.skippedCalibrationSteps = None
        # Read the PDS4 Label
        self.labelFile = self.fileName.with_suffix(".lblx")

        doc = md.parse(self.labelFile.as_posix())
        idArea = getElement(doc, "Identification_Area")
        self.title = getValue(idArea, "title")
        idModification = getElement(idArea, "Modification_Detail", -1)
        self.prodVersion = getValue(idModification, "version_id")
        idObs = getElement(doc, "Observation_Area")
        comments = _get_elements(idObs, "comment")
        self.dataDesc = getValue(idObs, "comment") if comments else None
        timeCoord = getElement(idObs, "Time_Coordinates")

        self.startDT = datetime.strptime(
            getValue(timeCoord, "start_date_time"), self._dateformat
        )
        self.endDT = datetime.strptime(
            getValue(timeCoord, "stop_date_time"), self._dateformat
        )

        primaryRes = getElement(idObs, "Primary_Result_Summary")
        self.level = getValue(primaryRes, "processing_level")

        target = getElement(idObs, "Target_Identification")
        self.target = getValue(target, "name")

        mission = getElement(idObs, "Mission_Area")

        info = getElement(mission, "psa:Mission_Information")
        self.startSC = getValue(mission, "psa:spacecraft_clock_start_count")
        self.endSC = getValue(mission, "psa:spacecraft_clock_stop_count")
        try:
            phase = getElement(info, "psa:Mission_Phase")
        except IndexError:
            self.phaseName = getValue(mission, "psa:mission_phase_name")
            self.phaseID = getValue(mission, "psa:mission_phase_identifier")
        else:
            self.phaseName = getValue(phase, "psa:name")
            self.phaseID = getValue(phase, "psa:id")
        self.startOrbit = getValue(mission, "psa:start_orbit_number")
        self.endOrbit = getValue(mission, "psa:stop_orbit_number")

        context = getElement(idObs, "psa:Observation_Context")
        self.pointingMode = getValue(context, "psa:instrument_pointing_mode")
        self.obsIdentifier = getValue(context, "psa:observation_identifier")

        filter = getElement(idObs, "img:Optical_Filter")
        self.Filter = Filter(filter)

        acqPar = getElement(idObs, "juice_janus:Acquisition_Properties")
        self.AcquisitionParameter = AcquisitionParameter(acqPar)
        obProc = getElement(idObs, "juice_janus:Onboard_Processing")
        self.onBoardProcessing = OnBoardProcessing(obProc)
        grProc = getElement(idObs, "juice_janus:Onground_Processing")
        self.onGroundProcessing = OnGroundProcessing(grProc)
        self.proceesingContext = ProcessingContext(
            getElement(idObs, "psa:Processing_Context")
        )
        self.HK = None
        self.Downsamplig = None
        exp = getElement(doc, "img:Exposure")
        self.Exposure = getValue(exp, "img:exposure_duration")
        self.onBoardCompression = None
        self.subFrame = SubFrame(getElement(doc, "img:Subframe"))
        self.Header = None
        self.instrumentState = InstrumentState(getElement(doc, "img:Instrument_State"))
        # self.image=None
        try:
            distance = getElement(idObs, "geom:Distances")
            self.spacecraftSolarDistance = getValue(distance, "geom:spacecraft_heliocentric_distance")
            self.targetSolarDistance = getValue(distance, "geom:target_heliocentric_distance")
        except IndexError:
            self.spacecraftSolarDistance = None
            self.targetSolarDistance = None
        flObs = getElement(doc, "File_Area_Observational")
        self.creationDate = datetime.strptime(
            getValue(flObs, "creation_date_time").removesuffix("Z"),
            self._dateformat[:-1],
        )
        img = getElement(flObs, "Array_2D_Image")
        self.Offset = int(getValue(img, "offset"))
        elem = _get_elements(img, "Axis_Array")
        self.Samples = int(getValue(elem[1], "elements"))
        self.Lines = int(getValue(elem[0], "elements"))

        # console.print(timeCoord)

        # if self.Format == "HALF":
        if self.level.lower() == "raw":
            with open(self.fileName, "rb") as f:
                f.seek(self.Offset)
                self.image = np.reshape(
                    np.frombuffer(
                        f.read(self.Lines * self.Samples * 2), dtype=np.uint16
                    ),
                    (self.Lines, self.Samples),
                )
        else:
            with open(self.fileName, "rb") as f:
                self.image = np.reshape(
                    np.frombuffer(f.read(), dtype=np.float32),
                    (self.Lines, self.Samples),
                )

    def Show(self, all: bool = False):
        """Print the contents of the VICAR file Label to the console."""
        tb = Table(
            expand=False,
            show_header=False,
            show_lines=False,
            box=box.SIMPLE_HEAD,
            title="General information",
            title_style="italic yellow",
        )
        tb.add_column(style="yellow", justify="left")
        tb.add_column()
        tb.add_column()
        tb.add_row("Title:", "  ", self.title)
        tb.add_row("Data Description", "", self.dataDesc)
        tb.add_row("Processing Level", "", self.level)
        tb.add_section()
        tb.add_row("Start Time", "", str(self.startDT))
        tb.add_row("End Time", "", str(self.endDT))
        tb.add_row("Start Time SC Time", "", self.startSC)
        tb.add_row("End Time SC Time", "", self.endSC)
        tb.add_section()
        tb.add_row("Target Name", "", self.target)
        tb.add_row("Phase Name", "", self.phaseName)
        tb.add_row("Phase ID", "", self.phaseID)
        tb.add_section()
        tb.add_row("Start Orbit", "", str(self.startOrbit))
        tb.add_row("End Orbit", "", str(self.endOrbit))
        tb.add_section()
        tb.add_row("Pointing Mode", "", self.pointingMode)
        tb.add_row("Observation Identifier", "", self.obsIdentifier)
        tb.add_section()
        tb.add_row("HK", "", str(self.HK))
        tb.add_row("Downsampling", "", str(self.Downsamplig))
        tb.add_row("Exposure", "", str(self.Exposure))
        tb.add_row("On Board Compression", "", str(self.onBoardCompression))
        tb.add_row("Header", "", str(self.Header))
        if all:
            elems = [
                tb,
                self.Filter.Show(),
                self.AcquisitionParameter.Show(),
                self.onBoardProcessing.Show(),
                self.subFrame.Show(),
                self.instrumentState.Show(),
                self.onGroundProcessing.Show(),
                self.proceesingContext.Show(),
            ]
            if self.skippedCalibrationSteps:
                elems.append(self.skippedCalibrationSteps.Show())
            col = Columns(
                elems,
                expand=False,
            )
        else:
            col = tb
        self.console.print(
            Panel(
                col,
                title=f"Label for {self.fileName.name}",
                border_style="yellow",
                expand=False,
            )
        )


