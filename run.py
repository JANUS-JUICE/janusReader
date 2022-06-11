#! /usr/bin/env python3

from pathlib import Path
from matplotlib import pyplot as plt
from JanusReader import JanusReader
from rich import inspect, print
from rich.console import Console
from bitstring import BitStream, BitArray
from SCOS.SCOS import SCOS
from CCSDS import CCSDS
from datetime import datetime
from rich.panel import Panel

# cns=Console(record=True)


# testFile=Path('../../DATA/SVT-1a/raw/janus_raw_sc_1_0734009714_000_13.vic')
# a= JanusReader(testFile)
# inspect(a)

# a.Show()
# cns.save_text('out.txt')
# print(testFile.stat())
# print(a.image.shape)
# plt.imshow(a.image, interpolation='nearest')
# plt.show()


tlm=Path('../../DATA/SVT-1a/tlm/JAN1_1_2022.116.17.39.00.000')

with open(tlm, 'rb') as f:
    l=f.read(76)
a=BitArray(l)
# hx=a.hex
p=CCSDS('juice',a.hex)
p.Show()