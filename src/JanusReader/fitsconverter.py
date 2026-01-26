import copy
from astropy.io import fits
import pathlib
import datetime
import pandas as pd
import os

def explode_janusreader_class(levels,results,obj,text=None,name=[]):
    
    for attr, value in obj.__dict__.items():
        if attr != "image" and attr != "_dateformat":
            #print(attr,value)
            name_local = copy.deepcopy(name)
            name_local.append(attr)
            if not isinstance(value,list):
                value = [value]
            
            for x in value:
                try:
                    _,_,name_local = explode_janusreader_class(levels,results,x,attr,name_local)

                except:
                    #print(text,attr,x,name_local)
                    levels.append(name_local)
                    results.append(x)
            name_local = []
    
    return levels,results,name


def exploded2list(levels,results,dateformat):
    count = 0
    calstep = []
    calinputfile = []
    fits_name = []
    fits_value = []
    for lv,rslt in zip(levels,results):
        #print("")
        #print(lv,rslt)
        
        if len(lv) == 1:
            name = lv[0]
            if isinstance(rslt, pathlib.PurePath):
                rslt = rslt.name
            if isinstance(rslt,datetime.datetime):
                rslt = rslt.strftime(dateformat)
            value = rslt
            fits_name.append(name)
            fits_value.append(value)
        elif lv[0] == "Filter" or lv[0] == "AcquisitionParameter" or lv[0] == "onBoardProcessing" or lv[0] == "onGroundProcessing" or lv[0] == "subFrame":
            
            name = lv[-1]
            value = rslt
            fits_name.append(name)
            fits_value.append(value)
        elif lv[0] == 'proceesingContext':
            if lv[-1] == 'processingInputFile':
                calinputfile.append(rslt)
            else:
                pass
        elif lv[0] == "instrumentState":
            if count == 0:
                a = rslt
                count = 1
            elif count == 1:
                b = rslt
                count = 2
                
                name = a
                value = float(b)
                fits_name.append(name)
                fits_value.append(value)
            elif count == 2:
                count = 0
                pass
            else:
                fits_name.append(name)
                fits_value.append(value)
                continue
        elif lv[0] == 'skippedCalibrationSteps':
            if lv[1] == 'code':
                name = 'calcode'
                value = rslt
                fits_name.append(name)
                fits_value.append(value)
            else:
                calstep.append(rslt)
            
        else:
            print("boh",lv,rslt)

    name = 'skipstep'
    value = calstep
    
    fits_name.append(name)
    fits_value.append(value)
    name = 'califile'
    value = calinputfile
    fits_name.append(name)
    fits_value.append(value)

    return fits_name,fits_value


def lblxname2fitsname(lblx,path):
    fits_naming_convention = pd.read_csv(path,header=None)
    fits_naming_convention.columns = ["lblx","fits"]

    fitsname = []
    for x in lblx:
        #print(x)
        tmp = fits_naming_convention.loc[fits_naming_convention['lblx']==x,"fits"]
        if pd.isna(tmp).item():
            fitsname.append(x)
        else:
            fitsname.append(tmp.item())

    return fitsname



def to_fits(box,folder,dictionary):

    levels = []
    results = []
    levels,results,_ = explode_janusreader_class(levels,results,box)
    fits_name_raw,fits_results = exploded2list(levels,results,box._dateformat)
    fits_name = lblxname2fitsname(fits_name_raw,dictionary)

    ####################################
    hdu = fits.PrimaryHDU(data=box.image)
    hdr = hdu.header

    for x,y in zip(fits_name,fits_results):
        if isinstance(y,list):
            rslt = f"[{','.join([str(s) for s in y])}]"
        else:
            rslt = y
        #print(x, rslt)
        hdr[x] = rslt
    
    basename = pathlib.Path(box.fileName).stem

    hdu.writeto(os.path.join(folder,f'{basename}.fits'),overwrite=True)

    return