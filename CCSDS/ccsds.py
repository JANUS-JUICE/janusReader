#! /usr/bin/env python3
from bitstring import BitStream
import spiceypy as spice
from datetime import datetime, timedelta
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print

class Proto:
    def Show(self):
        tb = Table.grid()
        tb.add_column('Field', justify='right', style='yellow')
        tb.add_column()
        tb.add_column('Value', justify='left')
        for item in self.__dict__:
            if item.startswith('_'):
                continue
            else:
                if type(self.__dict__[item]) is str:
                    var = f"[green]'{self.__dict__[item]}'[/green]"
                elif type(self.__dict__[item]) is bool:
                    var = f"[red]'{self.__dict__[item]}'[/red]"
                else:
                    var = f"[cyan]{self.__dict__[item]}[/cyan]"
                tb.add_row(item, ' = ', var)
        return Panel(tb, title=f"{self.__class__.__name__}", border_style='yellow', expand=False)

class PacketId(Proto):
    def __init__(self,data):
        pID = BitStream(hex=data).unpack('uint: 3, 2*bin: 1, bits: 11')
        self.VersionNum = pID[0]
        self.packetType = pID[1]
        self.dataFieldHeaderFlag = pID[2]
        self.Apid = pID[3].uint
        self.Pid = pID[3][0:7].uint
        self.Pcat = pID[3][7:].uint
        pass
    
    def serialize(self):
        return [self.VersionNum, self.packetType, self.dataFieldHeaderFlag,
                self.Apid, self.Pid, self.Pcat]

class SeqControl(Proto):
    def __init__(self,data):
        sq = BitStream(hex=data).unpack('bin:2,uint:14')
        self.SegmentationFlag = sq[0]
        self.SSC = sq[1]

    def serialize(self):
        return [self.SegmentationFlag, self.SSC]

class SourcePacketHeader:
    def __init__(self,data):
        # Read the Source Packet Header(48 bits)
        # - Packet ID (16 bits)
        self.packetId = PacketId(data[0:4])
        # - Packet Sequence Control (16 bits)
        self.sequeceControl = SeqControl(data[4:8])
        """ 
        - Packet Length (16 bits)
        In the packet is stored Packet length is an unsigned word 
        expressing “Number of octects contained in Packet Data Field” minus 1.
        """
        self.packetLength = BitStream(hex=data[8:12]).unpack('uint:16')[0]+1
        # Based on BepiColombo SIMBIO-SYS
        # ref: BC-SIM-GAF-IC-002 pag. 48
    def serialize(self):
        return [*self.packetId.serialize(), *self.sequeceControl.serialize(), self.packetLength]

class DataFieldHeader(Proto):
    def __init__(self,data,missionID,t0):
        # Read The Data Field Header (80 bit)
        dfhData = BitStream(hex=data).unpack('bin:1,uint:3,bin:4,3*uint:8,uint:1,uint:31,uint:16')
        self.pusVersion = dfhData[1]
        self.ServiceType = dfhData[3]
        self.ServiceSubType = dfhData[4]
        self.DestinationId = dfhData[5]
        self.Synchronization = dfhData[6]
        self.CorseTime = dfhData[7]
        self.FineTime = dfhData[8]
        self.SCET = "1/%s:%s" % (self.CorseTime, self.FineTime)
        if self.Synchronization == 0:
            self.UTCTime = self.scet2UTC(missionID,t0)
        else:
            self.UTCTime = '1970-01-01T00:00:00.00000Z'
        pass

    def serialize(self):
        return [self.pusVersion, self.ServiceType, self.ServiceSubType,
                self.DestinationId, self.SCET, self.UTCTime]

    def scet2UTC(self,missionID,t0):
        if t0 == None:
            et = spice.scs2e(missionID, "{}.{}".format(self.CorseTime, self.FineTime))
            ScTime = spice.et2utc(et, 'ISOC', 5)
        else:
            dateFormat = "%Y-%m-%dT%H:%M:%S.%f"
            dt=datetime.strptime(t0,dateFormat)
            sc = self.CorseTime + self.FineTime*(2**(-16))
            f=dt+timedelta(seconds=sc)
            ScTime=f.strftime(dateFormat)
        return ScTime+'Z'
    
    
        

class PackeDataField:
    def __init__(self,data, missionID,t0):
        # Data Field Header
        self.DFHeader = DataFieldHeader(data[0:20],missionID,t0)
        # Data
        self.Data = data[20:]
        pass  

class CCSDS:
    """ Reader for the CCSDS header """
    """     Main Class   """

    def __init__(self, missionID, data,t0= None):
        if type(missionID) is str:
            if missionID.lower() == 'bepicolombo':
                missionID=-121
            else:
                if t0 == None:
                    print("WARNING: the Mission name is not valid. time converte setted to 1970-01-01 00:00:00")
                    t0 = "1970-01-01T00:00:00.000"
        # Source Packet Header
        self.SPH = SourcePacketHeader(data[0:12])
        # Packet Data Field
        self.PDF = PackeDataField(data[12:],missionID,t0)
        self.Data=self.PDF.Data

    def Show(self):
        elements=[
            self.SPH.packetId.Show(),
            self.SPH.sequeceControl.Show(),
            self.PDF.DFHeader.Show(),
        ]
        col=Columns(elements)
        print(col)