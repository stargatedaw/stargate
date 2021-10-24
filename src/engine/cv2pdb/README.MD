
This is the README file for cv2pdb, a 
converter of DMD CodeView/DWARF debug information to PDB files

Copyright (c) 2009-2010 by Rainer Schuetze, All Rights Reserved

The goal of this project is to make debugging of D applications that
were created with the Digital Mars DMD compiler, as seamless as possible 
in current versions of Visual Studio (i.e Visual Studio 2008 and 
VCExpress).
As a side effect, other applications might also benefit from the 
converted debug information, like WinDbg or DMC.

Features
--------
* conversion of DMD CodeView information to PDB file
* conversion of DWARF information to PDB file
* converted line number info allows setting breakpoints
* display of variables, fields and objects in watch, local and auto window and in data tooltips
* generates generic debug info for dynamic arrays, associative arrays and delegates
* autoexp.dat allows convenient display of dynamic and associative arrays in watch windows
* demangles function names for convenient display of callstack 
* also works debugging executables built with the Digital Mars C/C++ compiler DMC

License information
-------------------

This code is distributed under the term of the Artistic License 2.0.
For more details, see the full text of the license in the file LICENSE.

The file demangle.cpp is an adaption of denangle.d to C++ distributed with
the DMD compiler. It is placed into the Public Domain.

The file mscvpdb.h is taken from the WINE-project (http://www.winehq.org)
and is distributed under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
See the file header for more details and 
http://www.gnu.org/licenses/lgpl.html for the full license.

The file dwarf.h is taken from the libdwarf project 
(http://reality.sgiweb.org/davea/dwarf.html)
and is distributed under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
See the file header for more details and 
http://www.gnu.org/licenses/lgpl.html for the full license.

Installation
------------
Sorry, there is no full featured installer available yet, you'll have
to do some simple manual steps to use cv2pdb.

See the file INSTALL for further details.

Usage
-----

Quick start:

Simply run

    cv2pdb debuggee.exe

on your executable to debug and start the debugger, e.g.

    devenv debuggee.exe

or

    vcexpress debuggee.exe

Description:
------------

cv2pdb.exe is a command line tool which outputs its usage information
if run without arguments:

    usage: cv2pdb [-D<version>|-C|-n|-e|-s<C>|-p<embedded-pdb>] <exe-file> [new-exe-file] [pdb-file]

With the `-D` option, you can specify the version of the DMD compiler
you are using. Unfortunately, this information is not embedded into
the debug information. The default is -D2.072. So far, this information 
is only needed to determine whether "char[]" or "const char[]" is 
translated to "string". 

Starting with DMD 2.043, assoiciative arrays have a slightly different
implementation, so debug information needs to be adjusted aswell. This changed
again with DMD 2.068. Version 2.072 started embedding source language 'D' into object files.
Use -D 2.043 or higher to produce the matching debug info.

Option `-C` tells the program, that you want to debug a program compiled
with DMC, the Digital Mars C/C++ compiler. It will disable some of the
D specific functions and will enable adjustment of stack variable names.

With option `-n` demangling of symbols is disabled.

Older versions of the Visual Studio Debugger (up to VS 2012) don't work well if type
and symbol names contain `.`. That's why cv2pdb replaces these characters with '@' by default.
This character can be configured to another character with the `-s`, so `-s.` will
keep symbol names as emitted by the compiler.

The first file name on the command line is expected to be the executable
or dynamic library compiled by the DMD compiler and containing the 
CodeView debug information (-g option used when running dmd).

If no further file name is given, a PDB file will be created with the
same base name as the executable, but with extension "pdb", and the 
executable will be modified to redirect debuggers to this pdb-file instead
of the original debug information.

Example:

    cv2pdb debuggee.exe

In an environment using make-like tools, it is often useful to create
a new file instead of modifying existing files. That way the file 
modification time can be used to continue the build process at the
correct step. 
If another file name is specified, the new executable is written
to this file and leaves the input executable unmodified.. The naming 
of the pdb-file will use the base name of the output file.

Example:

    cv2pdb debuggee.exe debuggee_pdb.exe

Last but not least, the resulting pdb-file can be renamed by specifying
a third file name.

Example:

    cv2pdb debuggee.exe debuggee_pdb.exe debug.pdb

If you plan to move the excutable and PDB file to another computer, it might be helpful
to change the path or file reference that is embedded into the converted binary. `-p` allows
to replace the absolute path of the PDB file with any other file name irrespective of the
actually generated PDB file and without making the file reference absolute.


Changes
-------

For documentation on the changes between this version and
previous versions, please see the file CHANGES.

Feedback
--------
The project home for cv2pdb is here:

    https://github.com/rainers/cv2pdb

There's an issue tracker, where you can leave your comments and suggestions.

Have fun,
Rainer Schuetze
