"""VICAR utilities
"""

def load_header(header:str)->dict:
    """Creates a list of (keyword,value) pairs and saves them inside a dictionary.
    
        Args:
            header (str): header of the image
        
        Returns:
            dict: header intrepretated
    """

    # Internal method to parse one item starting at index i
    def _parse_single(i):
        while header[i] == " ":
                i += 1

        if header[i] == "'":
            i += 1
            j = i
            while header[j] != "'":
                    j += 1

            value = header[i:j]
            j += 1
        else:
            j = i
            is_float = False
            while True:

                if header[j] in ",) ":
                    if is_float:
                        # Note use of decimal storage, so that printing a
                        # value afterward looks normal.
                        value =float(header[i:j])
                    else:
                        value = int(header[i:j])
                    break

                if header[j] in ".Ee":
                    is_float = True
                j += 1

        return (value, j)

    # Internal method to parse one item starting at index i
    def _parse_group(i):
        value = []
        i += 1
        while 1:
            (nextval, i) = _parse_single(i)

            value.append(nextval)

            while header[i] == " ":
                i += 1

            if header[i] == ")":
                return (value, i+1)

            if header[i] == ",":
                i += 1

    # Execution begins here

    ikey = 0
    dat={}
    while True:

        # Extract the keyword
        jkey = header[ikey:].find("=") + ikey
        if jkey < ikey:
            break

        keyword = header[ikey:jkey].strip()

        # non-ASCII text indicates end of header
        if keyword[0] < " " or keyword[0] > "~":
            return

        # Look for beginning of value
        ivalue = jkey + 1
        while header[ivalue] == " ":
            ivalue = ivalue + 1

        # Interpret value
        if header[ivalue] == "(":
            (value, jvalue) = _parse_group(ivalue)
        else:
            (value, jvalue) = _parse_single(ivalue)

        dat[keyword]=value

        ikey = jvalue
    return dat
