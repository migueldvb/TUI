#!/usr/bin/env python
r"""
Interface for viewing images with the ds9 image viewer.
Loosely based on XPA, by Andrew Williams.

Before trying to use this, please carefully ready
the Requirements section below.

Here is a basic summary for use:
    import RO.DS9
    import numarray
    ds9Win = RO.DS9.DS9Win()
    # show a FITS file in frame 1
    ds9Win. showFITSFile("foo/test.fits")
    # show an array in frame 2
    ds9Win.xpaset("frame 2")
    myArray = numarray.arange(10000, shape=[100,100])
    ds9Win.showArray(myArray)

For more information, see the XPA Access Points section
of the ds9 reference manual (under Help in ds9). Then experiment.

Extra Keyword Arguments:
Many commands take additional keywords as arguments. These are sent
as separate commands after the main command is executed.
Useful keywords for viewing images include: scale, orient and zoom.
Note that the value of each keyword is sent as an unquoted string.
If you want the value quoted, provide the quotes yourself, e.g.:
    foo='"quoted value"'

Template Argument:
The template argument allows you to specify which instance of ds9
you wish to command via xpa.
One common use is control more than one ds9 window.
Since ds9 can only have one window, you must launch
multiple instances of ds9 using the -title command-line
option to specify a different window title for each.
Then specify the window title as the template to RO.DS9.
See the XPA documentation for other uses for template,
such as talking to ds9 on a remote host.

For a list of local servers try % xpaget xpans

WARNING: ds9 3.0.3 and xpa 2.1.5 have several nasty bugs.
One I have not figured out to work around is that on Windows
showArray fails because the data undergoes newline translation.
See <http://www.astro.washington.edu/rowen/ds9andxpa.html>
for more information.

Requirements:

* Unix Requirements
- ds9 and xpa must be installed somewhere on your $PATH

* MacOS X Requirements
- The MacOS X version must be called "ds9.app".
  "SAOImageDS9.app" or "SAOImage DS9.app"
  (one of these should be the default for your version)
  and must be in one of the two *standard* locations applications
  (e.g. ~/Applications or /Applications on English systems).
  AND/OR:
- xpa for darwin installed somewhere on your $PATH
- ds9 for darwin installed somewhere on your $PATH

  Note: as I write this, ds9 4.0b9 is out and the MacOS X application
  does not include xpa. They may fix this, but if your application
  does not include xpa then you MUST install darwin xpa.
  (xpa is part of the 3.0.3 MacOS X version of ds9).

* Windows Requirements
- Mark Hammond's pywin32 package: <http://sourceforge.net/projects/pywin32/>
- ds9 installed in the default directory (C:\Program Files\ds9\
  on English systems)
- xpa executables installed in the default directory (C:\Program Files\xpa\)
  or in the same directory as ds9.exe. Why might you choose the latter?
  Because (at least for ds9 3.0.3) to use ds9 with xpa from the command line,
  the xpa executables should be in with ds9.exe. Otherwise ds9 can't find
  xpans when it starts up and so fails to register itself.

History:
2004-04-15 ROwen    First release.
2004-04-20 ROwen    showarry improvements:
                    - Accepts any array whose values can be represented as signed ints.
                    - Bug fix: x and y dimensions were swapped (#@$@# numarray)
2004-04-29 ROwen    Added xpaset function.
2004-05-05 ROwen    Added DS9Win class and moved the showXXX functions to it.
                    Added function xpaget.
                    Added template argument to xpaset.
2004-10-15 ROwen    Bug fix: could only communicate with one ds9;
                    fixed by specifying port=0 when opening ds9.
2004-11-02 ROwen    Improved Mac compatibility (now looks in [~]/Applications).
                    Made compatible with Windows, except showArray is broken;
                    this appears to be a bug in ds9 3.0.3.
                    loadFITSFile no longer tests the file name's extension.
                    showArray now handles most array types without converting the data.
                    Eliminated showBinFile because I could not get it to work;
                    this seems to be an bug or documentation bug in ds9.
                    Changed order of indices for 3-d images from (y,x,z) to (z,y,x).
2004-11-17 ROwen    Corrected a bug in the subprocess version of xpaget.
                    Updated header comments for big-fixed version of subprocess.
2004-12-01 ROwen    Bug fix in xpaset: terminate data with \n if not already done.
                    Modified to use subprocess module (imported from RO.Future
                    if Python is old enough not to include it).
                    Added __all__.
2004-12-13 ROwen    Bug fix in DS9Win; the previous version was missing
                    the code that waited for DS9 to launch.
2005-05-16 ROwen    Added doRaise argument to xpaget, xpaset and DS9Win;
                    the default is False so the default behavior has changed.
2005-09-23 ROwen    Bug fix: used the warnings module without importing it.
2005-09-27 ROwen    Added function setup.
                    Checks for xpa and ds9. If not found at import
                    then raise a warning make DS9Win. xpaset and xpaget
                    retry the check and raise RuntimeError on failure
                    (so you can install xpa and ds9 and run without reloading).
                    MacOS X: modified to launch X11 if not already running.
2005-09-30 ROwen    Windwows: only look for xpa in ds9's directory
                    (since ds9 can't find it in the default location);
                    updated the installation instructions accordingly.
2005-10-05 ROwen    Bug fix: Windows path joining via string concatenation was broken;
                    switched to os.path.join for all path joining.
                    Bug fix: Windows search for xpa was broken ("break" only breaks one level).
2005-10-11 ROwen    MacOS X: add /usr/local/bin to env var PATH and set env var DISPLAY, if necessary
                    (because apps do not see the user's shell modifications to env variables).
2005-10-13 ROwen    MacOS X and Windows: add ds9 and xpa to the PATH if found
                    MacOS X: look for xpaget in <applications>/ds9.app as well as on the PATH
                    Windows: look for xpaget in <program files>\xpa\ as well as ...\ds9\
2005-10-31 ROwen    Bug fix: showArray mis-handled byteswapped arrays.
2005-11-02 ROwen    Improved fix for byteswapped arrays that avoids copying the array
                    (based on code by Tim Axelrod).
2005-11-04 ROwen    Simplified byte order test as suggested by Rick White.
2006-07-11 ROwen    Modified to handle version 4.0b9 of ds9 on Mac, which is now named "SAOImage DS9.app".
2006-10-23 ROwen    Modified to handle version 4.0b10 of ds9 on Mac (SAO keeps renaming the Mac application).
2007-01-22 ROwen    Bug fix: _findUnixApp's "not found" exception was not created correctly.
2007-01-24 ROwen    Improved the documentation and test case.
"""
__all__ = ["setup", "xpaget", "xpaset", "DS9Win"]

import numarray as num
import os
import socket
import time
import warnings
import RO.OS
try:
    import subprocess
except ImportError:
    import RO.Future.subprocess as subprocess


def _addToPATH(newPath):
    """Add newPath to the PATH environment variable.
    Do nothing if newPath already in PATH.
    """
    if RO.OS.PlatformName == "win":
        pathSep = ";"
    else:
        pathSep = ":"
    pathStr = os.environ.get("PATH", "")
    if newPath in pathStr:
        return

    if pathStr:
        pathStr = pathStr + pathSep + newPath
    else:
        pathStr = newPath
    os.environ["PATH"] = pathStr


def _findApp(appName, subDirs = None, doRaise = True):
    """Find a Mac or Windows application by expicitly looking for
    the in the standard application directories.
    If found, add directory to the PATH (if necessary).
    
    Inputs:
    - appName   name of application, with .exe or .app extension
    - subDirs   subdirectories of the main application directories;
                specify None if no subdirs
    - doRaise   raise RuntimeError if not found?
    
    Returns a path to the application's directory.
    Return None or raise RuntimeError if not found.
    """
    appDirs = RO.OS.getAppDirs()
    if subDirs == None:
        subDirs = []
    dirTrials = []
    for appDir in appDirs:
        for subDir in subDirs:
            if subDir:
                trialDir = os.path.join(appDir, subDir)
            else:
                trialDir = appDir
            dirTrials.append(trialDir)
            if os.path.exists(os.path.join(trialDir, appName)):
                _addToPATH(trialDir)
                return trialDir
    if doRaise:
        raise RuntimeError("Could not find %s in %s" % (appName, dirTrials,))
    return None
    

def _findUnixApp(appName):
    """Use the unix "which" command to find the application on the PATH
    Return the path if found.
    Raise RuntimeError if not found.
    """
    p = subprocess.Popen(
        args = ("which", appName),
        shell = False,
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
    )
    try:
        p.stdin.close()
        errMsg = p.stderr.read()
        if errMsg:
            fullErrMsg = "'which %s' failed: %s" % (appName, errMsg)
            raise RuntimeError(fullErrMsg)
        appPath = p.stdout.read()
        if not appPath.startswith("/"):
            raise RuntimeError("Could not find %s on your PATH" % (appName,))
    finally:
        p.stdout.close()
        p.stderr.close()

    return appPath

def _findDS9AndXPA():
    """Locate ds9 and xpa, and add to PATH if not already there.
    
    Returns:
    - ds9Dir    directory containing ds9 executable
    - xpaDir    directory containing xpaget and (presumably)
                the other xpa executables
    
    Sets global variable _DirFromWhichToRunDS9
    to xpaDir if the platform is Windows, else to None
    This is a hack to make sure that ds9 on Windows can find xpans
    and register itself with xpa when it starts up.
                
    Raise RuntimeError if ds9 or xpa are not found.
    """
    global _DirFromWhichToRunDS9
    _DirFromWhichToRunDS9 = None
    if RO.OS.PlatformName == "mac":
        # ds9 and xpa may be in any of:
        # - ~/Applications/ds9.app
        # - /Applications.ds9.app
        # - on the PATH (adding /usr/local/bin if necessary)
        
        # add DISPLAY envinronment variable, if necessary
        # (since ds9 is an X11 application and environment
        os.environ.setdefault("DISPLAY", "localhost:0")

        # look for ds9 and xpa inside of "ds9.app" or "SAOImage DS9.app"
        # in the standard application locations
        ds9Dir = _findApp("ds9", ["ds9.app", "SAOImageDS9.app", "SAOImage DS9.app"], doRaise=False)
        foundDS9 = (ds9Dir != None)
        foundXPA = False
        if ds9Dir and os.path.exists(os.path.join(ds9Dir, "xpaget")):
            xpaDir = ds9Dir
            foundXPA = True

        # for anything not found, look on the PATH
        # after making sure /usr/local/bin is on the PATH
        if not (foundDS9 and foundXPA):
            # make sure /usr/local/bin is on the PATH
            # (if PATH isn't being set in ~/.MacOSX.environment.plist
            # then the bundled Mac app will only see the standard default PATH).
            _addToPATH("/usr/local/bin")

            if not foundDS9:
                ds9Dir = _findUnixApp("ds9")
    
            if not foundXPA:
                xpaDir = _findUnixApp("xpaget")
    
    elif RO.OS.PlatformName == "win":
        ds9Dir = _findApp("ds9.exe", ["ds9"], doRaise=True)
        xpaDir = _findApp("xpaget.exe", ["xpa", "ds9"], doRaise=True)
        _DirFromWhichToRunDS9 = xpaDir
    
    else:
        # unix
        ds9Dir = _findUnixApp("ds9")
        xpaDir = _findUnixApp("xpaget")
    
    return (ds9Dir, xpaDir)
    

def setup(doRaise=False, debug=False):
    """Search for xpa and ds9 and set globals accordingly.
    Return None if all is well, else return an error string.
    The return value is also saved in global variable _SetupError.
    
    Sets globals:
    - _SetupError   same value as returned
    - _Popen        subprocess.Popen, if ds9 and xpa found,
                    else a variant that searches for ds9 and xpa
                    first and then runs subprocess.Popen if found
                    else raises an exception
                    This permits the user to install ds9 and xpa
                    and use this module without reloading it
    """
    global _SetupError, _Popen
    _SetupError = None
    try:
        ds9Dir, xpaDir = _findDS9AndXPA()
        if debug:
            print "ds9Dir=%r\npaDir=%r" % (ds9Dir, xpaDir)
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception, e:
        _SetupError = "RO.DS9 unusable: %s" % (e,)
        ds9Dir = xpaDir = None
    
    if _SetupError:
        class _Popen(subprocess.Popen):
            def __init__(self, *args, **kargs):
                setup(doRaise=True)
                subprocess.Popen.__init__(self, *args, **kargs)
        
        if doRaise:
            raise RuntimeError(_SetupError)
    else:
        _Popen = subprocess.Popen
    return _SetupError


errStr = setup(doRaise=False, debug=False)
if errStr:
    warnings.warn(errStr)

_ArrayKeys = ("dim", "dims", "xdim", "ydim", "zdim", "bitpix", "skip", "arch")
_DefTemplate = "ds9"

_OpenCheckInterval = 0.2 # seconds
_MaxOpenTime = 10.0 # seconds

def xpaget(cmd, template=_DefTemplate, doRaise = False):
    """Executes a simple xpaget command:
        xpaset -p <template> <cmd>
    returning the reply.
    
    Inputs:
    - cmd       command to execute; may be a string or a list
    - template  xpa template; can be the ds9 window title
                (as specified in the -title command-line option)
                host:port, etc.
    - doRaise   if True, raise RuntimeError if there is a communications error,
                else issue a UserWarning warning

    Raises RuntimeError or issues a warning (depending on doRaise)
    if anything is written to stderr.
    """
    fullCmd = 'xpaget %s %s' % (template, cmd,)
#   print fullCmd

    p = _Popen(
        args = fullCmd,
        shell = True,
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
    )
    try:
        p.stdin.close()
        errMsg = p.stderr.read()
        if errMsg:
            fullErrMsg = "%r failed: %s" % (fullCmd, errMsg)
            if doRaise:
                raise RuntimeError(fullErrMsg)
            else:
                warnings.warn(fullErrMsg)
        return p.stdout.read()
    finally:
        p.stdout.close()
        p.stderr.close()


def xpaset(cmd, data=None, dataFunc=None, template=_DefTemplate, doRaise = False):
    """Executes a simple xpaset command:
        xpaset -p <template> <cmd>
    or else feeds data to:
        xpaset <template> <cmd>
        
    The command must not return any output for normal completion.
    
    Inputs:
    - cmd       command to execute
    - data      data to write to xpaset's stdin; ignored if dataFunc specified.
                If data[-1] is not \n then a final \n is appended.
    - dataFunc  a function that takes one argument, a file-like object,
                and writes data to that file. If specified, data is ignored.
                Warning: if a final \n is needed, dataFunc must supply it.
    - template  xpa template; can be the ds9 window title
                (as specified in the -title command-line option)
                host:port, etc.
    - doRaise   if True, raise RuntimeError if there is a communications error,
                else issue a UserWarning warning
    
    Raises RuntimeError or issues a warning (depending on doRaise)
    if anything is written to stdout or stderr.
    """
    if data or dataFunc:
        fullCmd = 'xpaset %s %s' % (template, cmd)
    else:
        fullCmd = 'xpaset -p %s %s' % (template, cmd)
#   print fullCmd

    p = _Popen(
        args = fullCmd,
        shell = True,
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
    )
    try:
        if dataFunc:
            dataFunc(p.stdin)
        elif data:
            p.stdin.write(data)
            if data[-1] != '\n':
                p.stdin.write('\n')
        p.stdin.close()
        reply = p.stdout.read()
        if reply:
            fullErrMsg = "%r failed: %s" % (fullCmd, reply.strip())
            if doRaise:
                raise RuntimeError(fullErrMsg)
            else:
                warnings.warn(fullErrMsg)
    finally:
        p.stdin.close() # redundant
        p.stdout.close()


def _computeCnvDict():
    """Compute array type conversion dict.
    Each item is: unsupported type: type to which to convert.
    
    ds9 supports UInt8, Int16, Int32, Float32 and Float64.
    """
    
    cnvDict = {
        num.Int8: num.Int16,
        num.UInt16: num.Int32,
        num.UInt32: num.Float32,    # ds9 can't handle 64 bit integer data
        num.Int64: num.Float64,
    }

    if hasattr(num, "UInt64="):
        cnvDict[num.UInt64] = num.Float64

    return cnvDict

_CnvDict = _computeCnvDict()
_FloatTypes = (num.Float32, num.Float64)
_ComplexTypes = (num.Complex32, num.Complex64)


def _expandPath(fname, extraArgs=""):
    """Expand a file path and protect it such that spaces are allowed.
    Inputs:
    - fname     file path to expand
    - extraArgs extra arguments that are to be appended
                to the file path
    """
    filepath = os.path.abspath(os.path.expanduser(fname))
    # if windows, change \ to / to work around a bug in ds9
    filepath = filepath.replace("\\", "/")
    # quote with "{...}" to allow ds9 to handle spaces in the file path
    return "{%s%s}" % (filepath, extraArgs)


def _formatOptions(kargs):
    """Returns a string: "key1=val1,key2=val2,..."
    (where keyx and valx are string representations)
    """
    arglist = ["%s=%s" % keyVal for keyVal in kargs.iteritems()]
    return '%s' % (','.join(arglist))


def _splitDict(inDict, keys):
    """Splits a dictionary into two parts:
    - outDict contains any keys listed in "keys";
      this is returned by the function
    - inDict has those keys removed (this is the dictionary passed in;
      it is modified by this call)
    """
    outDict = {}
    for key in keys:
        if inDict.has_key(key):
            outDict[key] = inDict.pop(key)
    return outDict  


class DS9Win:
    """An object that talks to a particular window on ds9
    
    Inputs:
    - template: window name (see ds9 docs for talking to a remote ds9)
    - doOpen: open ds9 using the desired template, if not already open;
            MacOS X warning: opening ds9 requires ds9 to be on your PATH;
            this may not be true by default;
            see the module documentation above for workarounds.
    - doRaise   if True, raise RuntimeError if there is a communications error,
            else issue a UserWarning warning.
            Note: doOpen always raises RuntimeError on failure!
    """
    def __init__(self,
        template=_DefTemplate,
        doOpen = True,
        doRaise = False,
    ):
        self.template = str(template)
        self.doRaise = bool(doRaise)
        if doOpen:
            self.doOpen()
    
    def doOpen(self):
        """Open the ds9 window (if necessary).
        
        Raise OSError or RuntimeError on failure, even if doRaise is False.
        """
        if self.isOpen():
            return
        
        if RO.OS.PlatformName == "mac":
            # make sure X11 is running
            p = _Popen(
                args = ("open", "-a", "X11"),
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
            )
            try:
                p.stdin.close()
                errMsg = p.stdout.read()
                if errMsg:
                    raise RuntimeError("Could not launch X11: %s" % (errMsg,))
            finally:
                p.stdout.close()

        global _DirFromWhichToRunDS9
        _Popen(
            args = ('ds9', '-title', self.template, '-port', "0"),
            cwd = _DirFromWhichToRunDS9, 
        )

        startTime = time.time()
        while True:
            time.sleep(_OpenCheckInterval)
            if self.isOpen():
                return
            if time.time() - startTime > _MaxOpenTime:
                raise RuntimeError('Could not open ds9 window %r; timeout' % (self.template,))

    def isOpen(self):
        """Return True if this ds9 window is open
        and available for communication, False otherwise.
        """
        try:
            xpaget('mode', template=self.template, doRaise=True)
            return True
        except RuntimeError:
            return False

    def showArray(self, arr, **kargs):
        """Display a 2-d or 3-d grayscale integer numarray arrays.
        3-d images are displayed as data cubes, meaning one can
        view a single z at a time or play through them as a movie,
        that sort of thing.
        
        Inputs:
        - arr: a numarray array; must be 2-d or 3-d:
            2-d arrays have index order (y, x)
            3-d arrays are loaded as a data cube index order (z, y, x)
        kargs: see Extra Keyword Arguments in the module doc string for information.
        Keywords that specify array info (see doc for showBinFile for the list)
        are ignored, because array info is determined from the array itself.
        
        Data types:
        - UInt8, Int16, Int32 and floating point types sent unmodified.
        - All other integer types are converted before transmission.
        - Complex types are rejected.
    
        Raises ValueError if arr's elements are not some kind of integer.
        Raises RuntimeError if ds9 is not running or returns an error message.
        """
        if not hasattr(arr, "type") or not hasattr(arr, "astype"):
            arr = num.array(arr)
        
        if arr.type() in _ComplexTypes:
            raise TypeError("ds9 cannot handle complex data")

        ndim = arr.getrank()
        if ndim not in (2, 3):
            raise RuntimeError("can only display 2d and 3d arrays")
        dimNames = ["z", "y", "x"][3-ndim:]

        # if necessary, convert array type
        cnvType = _CnvDict.get(arr.type())
        if cnvType:
#           print "converting array from %s to %s" % (arr.type(), cnvType)
            arr = arr.astype(cnvType)

        # determine byte order of array
        isBigendian = (arr.isbyteswapped() != num.isBigEndian)
        
        # compute bits/pix; ds9 uses negative values for floating values
        bitsPerPix = arr.itemsize() * 8
        if arr.type() in _FloatTypes:
            # array is float; use negative value
            bitsPerPix = -bitsPerPix
    
        # remove array info keywords from kargs; we compute all that
        _splitDict(kargs, _ArrayKeys)

        # generate array info keywords; note that numarray
        # 2-d images are in order [y, x]
        # 3-d images are in order [z, y, x]
        arryDict = {}
        for axis, size in zip(dimNames, arr.getshape()):
            arryDict["%sdim" % axis] = size
        
        arryDict["bitpix"] = bitsPerPix
        if (isBigendian):
            arryDict["arch"] = 'bigendian'
        else:
            arryDict["arch"] = 'littleendian'
            
        self.xpaset(
            cmd = 'array [%s]' % (_formatOptions(arryDict),),
            dataFunc = arr.tofile,
        )
        
        for keyValue in kargs.iteritems():
            self.xpaset(cmd=' '.join(keyValue))

# showBinFile is commented out because it is broken with ds9 3.0.3
# (apparently due to a bug in ds9) and because it wasn't very useful
#   def showBinFile(self, fname, **kargs):
#       """Display a binary file in ds9.
#       
#       The following keyword arguments are used to specify the array:
#       - xdim      # of points along x
#       - ydim      # of points along y
#       - dim       # of points along x = along y (only use for a square array)
#       - zdim      # of points along z
#       - bitpix    number of bits/pixel; negative if floating
#       - arch  one of bigendian or littleendian (intel)
#       
#       The remaining keywords are extras treated as described
#       in the module comment.
#
#       Note: integer data must be UInt8, Int16 or Int32
#       (i.e. the formats supported by FITS).
#       """
#       arryDict = _splitDict(kargs, _ArrayKeys)
#       if not arryDict:
#           raise RuntimeError("must specify dim (or xdim and ydim) and bitpix")
#
#       arrInfo = "[%s]" % (_formatOptions(arryDict),)
#       filePathPlusInfo = _expandPath(fname, arrInfo)
#
#       self.xpaset(cmd='file array "%s"' % (filePathPlusInfo,))
#       
#       for keyValue in kargs.iteritems():
#           self.xpaset(cmd=' '.join(keyValue))
    
    def showFITSFile(self, fname, **kargs):
        """Display a fits file in ds9.
        
        Inputs:
        - fname name of file (including path information, if necessary)
        kargs: see Extra Keyword Arguments in the module doc string for information.
        Keywords that specify array info (see doc for showBinFile for the list)
        must NOT be included.
        """
        filepath = _expandPath(fname)
        self.xpaset(cmd='file "%s"' % filepath)

        # remove array info keywords from kargs; we compute all that
        arrKeys = _splitDict(kargs, _ArrayKeys)
        if arrKeys:
            raise RuntimeError("Array info not allowed; rejected keywords: %s" % arrKeys.keys())
        
        for keyValue in kargs.iteritems():
            self.xpaset(cmd=' '.join(keyValue))

    def xpaget(self, cmd):
        """Execute a simple xpaget command and return the reply.
        
        The command is of the form:
            xpaset -p <template> <cmd>
        
        Inputs:
        - cmd       command to execute
    
        Raises RuntimeError if anything is written to stderr.
        """
        return xpaget(
            cmd = cmd,
            template = self.template,
            doRaise = self.doRaise,
        )
    

    def xpaset(self, cmd, data=None, dataFunc=None):
        """Executes a simple xpaset command:
            xpaset -p <template> <cmd>
        or else feeds data to:
            xpaset <template> <cmd>
            
        The command must not return any output for normal completion.
        
        Inputs:
        - cmd       command to execute
        - data      data to write to xpaset's stdin; ignored if dataFunc specified
        - dataFunc  a function that takes one argument, a file-like object,
                    and writes data to that file. If specified, data is ignored.
        
        Raises RuntimeError if anything is written to stdout or stderr.
        """
        return xpaset(
            cmd = cmd,
            data = data,
            dataFunc = dataFunc,
            template = self.template,
            doRaise = self.doRaise,
        )

if __name__ == "__main__":
    myArray = num.arange(10000, shape=[100,100])
    ds9Win = DS9Win("DS9Test")
    ds9Win.showArray(myArray)

