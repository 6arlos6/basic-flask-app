"""Writing docstrings

There are several different docstring formats which one can use in order to enable Sphinx's
autodoc extension to automatically generate documentation. For this tutorial we will use
the Sphinx format, since, as the name suggests, it is the standard format used with Sphinx.
Other formats include Google (see here) and NumPy (see here), but they require the use of 
Sphinx's napoleon extension, which is beyond the scope of this tutorial."""

import gspread
import os

def my_worksheet(rol, documento, hoja, row = None, col = None):
    """Returns a list of :class:`bluepy.blte.Service` objects representing
    the services offered by the device. This will perform Bluetooth service
    discovery if this has not already been done; otherwise it will return a
    cached list of services immediately..

    :param uuids: A list of string service UUIDs to be discovered,
        defaults to None
    :type uuids: list, optional
    :return: A list of the discovered :class:`bluepy.blte.Service` objects,
        which match the provided ``uuids``
    :rtype: list On Python 3.x, this returns a dictionary view object,
        not a list
    """
    # src/reportes/security/update_google_sheet.py
    if rol == 'servicio':
        if row == None:
            PATH_PRINCIPAL = os.path.join("src","reportes","security","dama-datos.json")
            sa = gspread.service_account(filename=PATH_PRINCIPAL)
            sh = sa.open(documento)
            w = sh.worksheet(hoja)
        else:
            PATH_PRINCIPAL = os.path.join("src","reportes","security","dama-datos.json")
            sa = gspread.service_account(filename=PATH_PRINCIPAL)
            sh = sa.open(documento)
            w = sh.add_worksheet(title=hoja,rows=f"{row}", cols=f"{col}")
        return w
    elif rol == 'sia':
        if row == None:
            PATH_PRINCIPAL = os.path.join("src","reportes","security","dama-datos.json")
            sa = gspread.service_account(filename=PATH_PRINCIPAL)
            sh = sa.open(documento)
            w = sh.worksheet(hoja)
        else:
            PATH_PRINCIPAL = os.path.join("src","reportes","security","dama-datos.json")
            sa = gspread.service_account(filename=PATH_PRINCIPAL)
            sh = sa.open(documento)
            w = sh.add_worksheet(title=hoja,rows=f"{row}", cols=f"{col}")
        return w
    else:
        return -1
