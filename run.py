#! /usr/bin/env python3

from pathlib import Path
import sys

from JanusReader import JanusReader as jr
from JanusReader import MSG
from rich.console import Console
from rich import inspect
import traceback



console=Console(record=True)
# fileName='../../DATA2/03_-_SVT-1a/raw/janus_raw_sc_0734009714_000_13_1_0734009720_0000.vic'
fileName = '/Users/romolo.politi/Documents/Progetti/JANUS/Software/janus-raw2cal/input/janus_raw_sc_0773586170_0180_01_20240706T131128_0000__1_0.vic'
#fileName = '/Users/romolo.politi/Documents/Progetti/JANUS/Software/janus-raw2cal/OUTPUT/janus_cal_sc_0773586170_0181_01_20240706T131130_0000__1_0.dat'

try:
    data = jr(Path(fileName),console=console, debug=True,vicar=True)
except FileNotFoundError as e:
    console.print(f"{MSG.ERROR} {e.strerror} ({e.filename})")
    sys.exit(e.strerror)
except Exception as e:
    console.print(e.args[0])
    console.print(traceback.format_exc())
    sys.exit()
    
# console.print(data.vicar)
data.Show(all=True)

# testFile=Path('../../DATA/SVT-1a/raw/janus_raw_sc_1_0734009714_000_13.vic')
# a= JanusReader(testFile)
# inspect(a)

# a.Show()
# cns.save_text('out.txt')
# print(testFile.stat())
# print(a.image.shape)
# plt.imshow(a.image, interpolation='nearest')
# plt.show()


# tlm=Path('../../DATA/SVT-1a/tlm/JAN1_1_2022.116.17.39.00.000')

# with open(tlm, 'rb') as f:
#     l=f.read(76)
# a=BitArray(l)
# # hx=a.hex
# p=CCSDS('juice',a.hex)
# p.Show()