import errno
import os
import xml.dom.minidom as md
from pathlib import Path

import numpy as np
from rich import box, print
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from JanusReader.exceptions import NOT_VALID_VICAR_FILE
from JanusReader.vicar_head import load_header


__version__ = "0.9.0"


class MSG:
    """Data class for the message labelling
    """
    DEBUG = "[blue][DEBUG][/blue]"
    WARNING = "[yellow][WARNING][/yellow]"
    ERROR = "[red][ERROR][/red]"


def getValue(nodeList: md.Element, label: str) -> str:
    """Get the value from a tag

    Args:
        nodelist: The xml block to evaluate
        label: The name of the tag to extract
        type: The type of the value to return (will be casted if type is not None)

    Returns:
         The value of the tag, appropriately casted if type is not None

    """
    # for item in nodeList:
    #     print(item)
    elem = nodeList.getElementsByTagName(label)

    if len(elem) == 0:
        cons.print(
            f"{MSG.WARNING} Missing label {label}. The label might have been removed or renamed.")
        return None

    elif len(elem) > 1:
        cons.print(
            f"{MSG.WARNING} More than one label {label}. The label might have been duplicated. This should never happen.")

    data = elem[0].firstChild.data
    #
    # Auto identification
    #
    if data.isdigit():
        data = int(data)
    elif data.replace('.', '', 1).isdigit() and data.count('.') < 2:
        data = float(data)
    #
    # if type:
    #     return type(data)

    return data


def getElement(doc, label, el=0) -> md.Element:
    """Get a Block of a dom

    Args:
        doc (xml.dom): The full Object

        label (str): The name of the tag to extract

    Returns:
        (xml.dom) The node tree extracted

    Todo:
        * implement OnBoard processing class
    """
    elem = doc.getElementsByTagName(label)
    return elem[el]


class State:
    def __init__(self, item):
        self.name = getValue(item, 'img:device_name').lower()
        self.value = getValue(item, 'img:temperature_value')

        self.unit = getElement(
            item, 'img:temperature_value').getAttribute('unit')


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
        tb = Table(expand=False, show_header=False,
                   show_lines=False, box=box.SIMPLE_HEAD,
                   title="Instrument State", title_style="italic yellow")
        tb.add_column(style='yellow', justify='left')
        tb.add_column()
        tb.add_column()
        for item in self.states:
            tb.add_row(' '.join(item.name.split('_')).title(),
                       '', f"{item.value} {item.unit}")
        return tb


class AcquisitionParameter:
    def __init__(self, acq):
        self.frontDoor = getValue(acq, "juice_janus:front_door_status")
        self.instMode = getValue(acq, "juice_janus:instrument_mode")
        self.sessID = getValue(acq, "juice_janus:image_session_id")
        self.imgNum = getValue(acq, 'juice_janus:image_number')
        self.filtNumber = getValue(acq, "juice_janus:filter_number")
        self.filterName = getValue(acq, "juice_janus:filter_name")
        self.filWheelDir = getValue(acq, "juice_janus:filter_wheel_direction")
        self.filSnapin = getValue(acq, "juice_janus:filter_snapin")
        self.multifilter = None
        pass

    def Show(self):
        tb = Table(expand=False, show_header=False,
                   show_lines=False, box=box.SIMPLE_HEAD,
                   title="Acquisition Parameters", title_style="italic yellow")
        tb.add_column(style='yellow', justify='left')
        tb.add_column()
        tb.add_column()
        tb.add_row("Front Door Status", "", self.frontDoor)
        tb.add_row("Instrument Mode", "", self.instMode)
        tb.add_row("Image Session ID", "", self.sessID)
        tb.add_row("Image Number", "", str(self.imgNum))
        tb.add_row("Filter Number", "", str(self.filtNumber))
        tb.add_row("Filter Name", "", self.filterName)
        tb.add_row("Filter Wheel Direction", "", self.filWheelDir)
        tb.add_row("Filter Snapin", "", self.filSnapin)
        tb.add_row("Multifilter", "", str(self.multifilter))
        return tb


class SubFrame:
    def __init__(self, proc) -> None:
        self.firstLine = getValue(proc, 'img:first_line')
        self.firstSample = getValue(proc, 'img:first_sample')
        self.lines = getValue(proc, 'img:lines')
        self.samples = getValue(proc, 'img:samples')
        self.subFrameType = getValue(proc, 'img:subframe_type')

    def Show(self):
        tb = Table(expand=False, show_header=False,
                   show_lines=False, box=box.SIMPLE_HEAD,
                   title="SubFrame Parameters", title_style="italic yellow")
        tb.add_column(style='yellow', justify='left')
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
        self.badPixelCorrection = getValue(
            proc, 'juice_janus:bad_pixel_correction')
        self.badPixelMapName = getValue(
            proc, 'juice_janus:bad_pixel_map_name')
        self.badPixelCount = getValue(proc, 'juice_janus:bad_pixel_count')
        self.fpnCorrection = getValue(proc, 'juice_janus:fpn_correction')
        self.fpnMapName = getValue(proc, 'juice_janus:fpn_map_name')
        self.spikeMaximumValue = getValue(
            proc, 'juice_janus:spike_maximum_value')
        self.spikeDistance = getValue(proc, 'juice_janus:spike_distance')
        self.spikeCount = getValue(proc, 'juice_janus:spike_count')
        self.spikeCorrection = getValue(proc, 'juice_janus:spike_correction')

    def Show(self):
        tb = Table(expand=False, show_header=False,
                   show_lines=False, box=box.SIMPLE_HEAD,
                   title="Onboard Processing", title_style="italic yellow")
        tb.add_column(style='yellow', justify='left')
        tb.add_column()
        tb.add_column()
        tb.add_row("Bad Pixels Correction", "", str(self.badPixelCorrection))
        tb.add_row("Bad Pixel Map Name", "", self.badPixelMapName)
        tb.add_row("Bad Pixel Count", "", str(self.badPixelCount))
        tb.add_section()
        tb.add_row("FPN Correction", "", str(self.fpnCorrection))
        tb.add_row("FPN Map Name", "", self.fpnMapName)
        tb.add_section()
        tb.add_row("Spike Maximum Value", "", str(self.spikeMaximumValue))
        tb.add_row("Spike Distance", "", str(self.spikeDistance))
        tb.add_row("Spike Distance", "", str(self.spikeDistance))
        tb.add_row("Spike Correction", "", str(self.spikeCorrection))
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

    def __init__(self, fileName: Path, console: Console = None, debug: bool = False, vicar: bool = False):
        # Check if console exists, if not create one
        global cons  # the variable will be global for the module
        if console is None:
            cons = Console()
        else:
            cons = console
        self.console = console
        # Check the file type, is str convert to Path
        if type(fileName) is not Path:
            fileName = Path(fileName)
        self.fileName = fileName
        # Check the file extension
        if self.fileName.suffix == '.vic':
            if debug:
                self.console.print(f"{MSG.DEBUG} Input type: Vicar file")
            if not self.fileName.exists():
                raise FileNotFoundError(errno.ENOENT, os.strerror(
                    errno.ENOENT), self.fileName.name)
        elif self.fileName.suffix == '.xml':
            if debug:
                self.console.print(f"{MSG.DEBUG} Input type: XML file")
            self.fileName = self.fileName.with_suffix('.vic')
            if not self.fileName.exists():
                raise FileNotFoundError(errno.ENOENT, os.strerror(
                    errno.ENOENT), self.fileName.name)
        # Read the Vicar Header
        if vicar:
            self.vicar = {}
            with open(self.fileName, 'rb') as f:
                l = str(f.read(40).decode('latin-1'))
            # self.txt=l
            if 'LBLSIZE' not in l:
                raise NOT_VALID_VICAR_FILE('File is not a valid VICAR file')
            iblank = l.index(" ", 8)
            self.label_size = int(l[8:iblank])
            with open(self.fileName, 'rb') as f:
                lbl = str(f.read(self.label_size).decode('latin-1'))

            self.vicar=load_header(lbl)

            if self.vicar.get("EOL", False):
                # we need to repeat label reading as above after computing the offset
                # as this duplicates code we should refactor this to a single function.
                cons.print(f"{MSG.DEBUG} The vicar file has labels at the end of the file.")
                next_labels_offset = (self.vicar["LBLSIZE"] +
                                      self.vicar["RECSIZE"] *
                                      self.vicar["NLB"] +
                                      self.vicar["RECSIZE"] *
                                      self.vicar["N2"] *
                                      self.vicar["N3"])
                                        
                with open(self.fileName, 'rb') as f:
                    f.seek(next_labels_offset)
                    l=str(f.read(40).decode('latin-1'))
                    
                if 'LBLSIZE' not in l:
                    cons.print(f"{MSG.ERROR} Expected lables at end of file "
                               "but could not find LBLSIZE. "
                               "vicar labels might be incomplete.")
                else:
                    iblank = l.index(" ", 8)
                    self.eol_label_size = int(l[8:iblank])
                    with open(self.fileName, 'rb') as f:
                        f.seek(next_labels_offset)
                        lbl = str(f.read(self.label_size).decode('latin-1'))
                        
                    self.vicar.update(load_header(lbl))

        # Read the PDS4 Label
        self.labelFile = self.fileName.with_suffix('.xml')

        doc = md.parse(self.labelFile.as_posix())
        idArea = getElement(doc, 'pds:Identification_Area')
        self.title = getValue(idArea, 'pds:title')
        idModification = getElement(idArea, 'pds:Modification_Detail', -1)
        self.prodVersion = getValue(idModification, 'pds:version_id')
        idObs = getElement(doc, 'pds:Observation_Area')
        if idObs.childNodes[1].nodeName == 'pds:comment':
            self.dataDesc = idObs.childNodes[1].firstChild.nodeValue
        timeCoord = getElement(idObs, 'pds:Time_Coordinates')

        self.startDT = getValue(timeCoord, 'pds:start_date_time')
        self.endDT = getValue(timeCoord, 'pds:stop_date_time')

        primaryRes = getElement(idObs, 'pds:Primary_Result_Summary')
        self.level = getValue(primaryRes, 'pds:processing_level')

        target = getElement(idObs, 'pds:Target_Identification')
        self.target = getValue(target, 'pds:name')

        mission = getElement(idObs, 'pds:Mission_Area')

        info = getElement(mission, 'psa:Mission_Information')
        self.startSC = getValue(mission, 'psa:spacecraft_clock_start_count')
        self.endSC = getValue(mission, 'psa:spacecraft_clock_stop_count')
        self.phaseName = getValue(mission, 'psa:mission_phase_name')
        self.phaseID = getValue(mission, 'psa:mission_phase_identifier')
        self.startOrbit = getValue(mission, 'psa:start_orbit_number')
        self.endOrbit = getValue(mission, 'psa:stop_orbit_number')

        context = getElement(idObs, 'psa:Observation_Context')
        self.pointingMode = getValue(context, 'psa:instrument_pointing_mode')
        self.obsIdentifier = getValue(context, 'psa:observation_identifier')

        acqPar = getElement(idObs, "juice_janus:Acquisition_Properties")
        self.AcquisitionParameter = AcquisitionParameter(acqPar)
        obProc = getElement(idObs, "juice_janus:Onboard_Processing")
        self.onBoardProcessing = OnBoardProcessing(obProc)
        self.onGroundProcessing = None
        self.HK = None
        self.Downsamplig = None
        exp = getElement(doc, 'img:Exposure')
        self.Exposure = getValue(exp, 'img:exposure_duration')
        self.onBoardCompression = None
        self.subFrame = SubFrame(getElement(doc, 'img:Subframe'))
        self.Header = None
        self.instrumentState = InstrumentState(
            getElement(doc, 'img:Instrument_State'))
        # self.image=None
        flObs = getElement(doc, 'pds:File_Area_Observational')
        self.creationDate = getValue(flObs, 'pds:creation_date_time')
        img = getElement(flObs, "pds:Array_2D_Image")
        self.Offset = getValue(img, "pds:offset")
        elem = img.getElementsByTagName("pds:Axis_Array")
        self.Samples = getValue(elem[1], "pds:elements")
        self.Lines = getValue(elem[0], "pds:elements")
        # console.print(timeCoord)

        # if self.Format == "HALF":
        if self.level.lower() == 'raw':
            with open(self.fileName, 'rb') as f:
                f.seek(self.Offset)
                self.image = np.reshape(np.frombuffer(f.read(
                    self.Lines * self.Samples * 2), dtype=np.uint16), (self.Lines, self.Samples))
        else:
            with open(self.fileName, 'rb') as f:
                self.image = np.reshape(np.frombuffer(
                    f.read(), dtype=np.float32), (self.Lines, self.Samples))

    def Show(self, all: bool = False):
        """Print the contents of the VICAR file Label to the console.
        """
        tb = Table(expand=False, show_header=False, show_lines=False, box=box.SIMPLE_HEAD,
                   title="General information", title_style="italic yellow")
        tb.add_column(style='yellow', justify='left')
        tb.add_column()
        tb.add_column()
        tb.add_row("Title:", '  ', self.title)
        tb.add_row("Data Description", '', self.dataDesc)
        tb.add_row("Processing Level", '', self.level)
        tb.add_section()
        tb.add_row("Start Time", '', self.startDT)
        tb.add_row("End Time", '', self.endDT)
        tb.add_row("Start Time SC Time", '', self.startSC)
        tb.add_row("End Time SC Time", '', self.endSC)
        tb.add_section()
        tb.add_row("Target Name", '', self.target)
        tb.add_row("Phase Name", '', self.phaseName)
        tb.add_row("Phase ID", '', self.phaseID)
        tb.add_section()
        tb.add_row("Start Orbit", "", self.startOrbit)
        tb.add_row("End Orbit", "", self.endOrbit)
        tb.add_section()
        tb.add_row("Pointing Mode", "", self.pointingMode)
        tb.add_row("Observation Identifier", "", self.obsIdentifier)
        tb.add_section()
        tb.add_row("On Ground Processing", "", str(self.onGroundProcessing))
        tb.add_row("HK", "", str(self.HK))
        tb.add_row("Downsampling", "", str(self.Downsamplig))
        tb.add_row("Exposure", "", str(self.Exposure))
        tb.add_row("On Board Compression", "", str(self.onBoardCompression))
        tb.add_row("Header", "", str(self.Header))
        if all:
            col = Columns([tb, self.AcquisitionParameter.Show(), self.onBoardProcessing.Show(
            ), self.subFrame.Show(), self.instrumentState.Show()], expand=False)
        else:
            col = tb
        self.console.print(Panel(
            col, title=f"Label for {self.fileName.name}", border_style='yellow', expand=False))
