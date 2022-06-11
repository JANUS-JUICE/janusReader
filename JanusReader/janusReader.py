from pathlib import Path
from rich.table import Table
from rich import print
from rich.panel import Panel
import numpy as np
from rich.console import Console
from JanusReader.exceptions import NOT_VALID_VICAR_FILE


def strfy(text:str)->str:
    """Return a string with spaces replaced by underscores and title-cased.

    Args:
        text (str): Input string.

    Returns:
        str: Modified string
    """
    return text.replace('_', ' ').title()

class JanusReader:
    """Reader of the JANUS Data File

        Args:
            fileName (Path): input filename
            cns (Console, optional): A console instance to capture output. Defaults to None.
        
        Attributes:
            fileName (Path): input filename
            img (np.array): image data

        Raises:
            NOT_VALID_VICAR_FILE
                The input file ``fileName`` is not ion VICAR format.
        """
    def __init__(self, fileName:Path, cns:Console=None):
        
        if cns is None:
            cns=Console()
        self.console=cns
        if type(fileName) is not Path:
            fileName=Path(fileName)
        self.fileName=fileName
        with open(self.fileName, 'rb') as f:
            l=str(f.read(40).decode('latin-1'))
        # self.txt=l
        if 'LBLSIZE' not in l:
            raise NOT_VALID_VICAR_FILE('File is not a valid VICAR file')
        iblank = l.index(" ", 8)
        self.label_size = int(l[8:iblank])
        with open(self.fileName, 'rb') as f:
            lbl = str(f.read(self.label_size).decode('latin-1'))
        # print(lbl)
        parts=[ x for x in lbl.split('  ') if x]
        if '\x00' in parts[-1]:
            parts.pop(-1)
        for item in parts[1:]:
            pt=item.split('=')
            if pt[-1].isnumeric():
                val=int(pt[-1])
            elif pt[-1].isdecimal():
                val = float(pt[-1])
            else:
                val=pt[-1][1:-1]    
            setattr(self, pt[0].title(), val)
        if self.Format == "HALF":
            with open(self.fileName, 'rb') as f:
                f.seek(self.label_size)
                self.image=np.reshape(np.frombuffer(f.read(), dtype=np.uint16),(self.Nl,self.Ns))
        # np.reshape(self.image,(self.Nl,self.Ns))
        
        
        
    def Show(self):
        """Print the contents of the VICAR file Label to the console.
        """
        tb=Table.grid(expand=False)
        tb.add_column(style='yellow', justify='left')
        tb.add_column()
        tb.add_column()
        for item in self.__dict__:
            if item in ['fileName', 'image', 'console']:
                continue
            if not item.startswith('_'):
                tb.add_row(strfy(item), '  ', str(self.__dict__[item]))
        self.console.print(Panel(tb,title=f"Label for {self.fileName.name}", border_style='yellow', expand=False))
