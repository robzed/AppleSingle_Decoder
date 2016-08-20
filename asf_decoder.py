
# AppleSingle Decoder
# written for Python 2
# Run with no arguments for simple help
#
# MIT License
#
# Copyright (c) 2016 Rob Probin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function       # (been writing too much Python 3 to stop)

import sys
import struct
import cStringIO
import os

verbose = False

# As per http://kaiser-edv.de/documents/AppleSingle_AppleDouble.pdf

def read_data(file, message, dlen, type):
    chunk = file.read(dlen)
    if len(chunk) != dlen:
        print("Couldn't read 4 bytes when getting", message)
        sys.exit(1)
    (value,) = struct.unpack(type, chunk)

    if verbose: print(message, "=", hex(value))
    return value

def read_uint(file, message):
    return read_data(file, message, 4, ">I")

def read_ushort(file, message):
    return read_data(file, message, 2, ">H")

def checked_read_uint(file, name, value):
    v = read_uint(file, name)
    if v != value:
        print(name, "not", hex(value))
        sys.exit(1)
    return v

def checked_read_ushort(file, name, value):
    v = read_ushort(file, name)
    if v != value:
        print(name, "not", hex(value))
        sys.exit(1)
    return v

entry_IDs = [
("BAD ENTRY ID", 0),
("Data Fork",  1),
("Resource Fork", 2),
("Real Name", 3), 
("Comment", 4),
("Icon, B&W", 5),
("Icon, Color", 6),
("OBSOLETE v1 FORMAT FILE INFO", 7),
("File Dates Info", 8),
("Finder Info", 9),
("Macintosh File Info", 10),
("ProDOS File Info", 11),
("MS-DOS File Info", 12),
("Short Name", 13),
("AFP File Info", 14),
("Directory ID", 15),

"""Data fork
Resource fork
Files name as created on home file system 
Standard Macintosh comment
Standard Macintosh black and white icon 
Macintosh color icon
File creation date, modification date, and so on 
Standard Macintosh Finder information 
Macintosh file information, attributes, and so on 
ProDOS file information, attributes, and so on 
MS-DOS file information, attributes, and so on AFP short name
AFP file information, attributes, and so on
AFP directory ID"""
]

def convert_one_file (filename, mode, output_f):
    with open(filename, 'rb') as f:
        data = f.read()
      
    f = cStringIO.StringIO(data)
    if True:
    #with open(filename, 'rb') as f:
        magic = checked_read_uint(f, "magic", 0x51600)
        version = checked_read_uint(f, "version", 0x20000)
    
        for i in range(4):
            checked_read_uint(f, "filler", 0)
    
        entries = read_ushort(f, "entries")
        
        max = 0
        entry_id_dict = {}

        for i in range(entries):
            if verbose: print("--------------------------------")
            entry_id = read_uint(f, "entry_id")
            if entry_id == 0:
                print("Entry ID cannot be 0")
                sys.exit(1)
            if entry_id in entry_IDs:
                print("Entry ID not in type table")
                sys.exit(1)
            offset = read_uint(f, "offset")
            length = read_uint(f, "length")
            
            (name, id) = entry_IDs[entry_id]
            if id != entry_id:
                print("Internal error entry ids")
                sys.exit(1) 
                
            if verbose: print("Block Name:", name)
            
            if entry_id in entry_id_dict:
                print("Entry ID already existed in this AppleSingle", entry_id)
                sys.exit(1)
            
            entry_id_dict[entry_id] = (offset, length)
                
            if offset+length > max:
                max = offset+length
            
        if max < len(data):
            print("File not long enough for entries")
            print("File length =", len(data))
            print("Expected =", max)
            sys.exit(1)
    
        print("File seems OK (remember - no checksums!)")
        
        #
        # do extra stuff, if wanted
        #
        if mode == "verify":
            pass
        elif mode == "extract_datafork":
            extract_fork(1, data, output_f, entry_id_dict)
        elif mode == "extract_resfork":
            extract_fork(2, data, output_f, entry_id_dict)
        elif mode == "extract_both_forks":
            extract_fork(1, data, output_f, entry_id_dict)
            extract_fork(2, data, output_f+".resource_fork", entry_id_dict)
            
        else:
            print("Unknown mode:", mode)
            

#
#
#
def file_might_be_AppleSingle(filename):
    with open(filename, 'rb') as f:
        data = f.read(4)
        if len(data) < 4:
            return False
        (magic,) = struct.unpack(">I", data)
        if magic == 0x51600:
            return True
        
    return False


def scan_directory(directory, convert=False):
    for root, dirs, files in os.walk(directory):
        for name in files:
            filepath = os.path.join(root, name)
            if file_might_be_AppleSingle(filepath):
                if convert:
                    print("Converting", filepath)
                    convert_one_file(filepath, "extract_both_forks", filepath)
                else:
                    print(filepath)
    
def extract_fork(element_type, data, output_filename, entry_id_dict):
    
    if element_type not in entry_id_dict:
        print("No fork of that type in this file!")
        sys.exit(1)
    (offset, length) = entry_id_dict[element_type]
    #print(offset, length)
    datafork = data[offset : length+offset]
    if len(datafork) != length:
        print("Internal error - Length of extraction not correct")
        sys.exit(1)
    
    print("Header bytes:")
    (b1, b2, b3, b4, b5, b6, b7, b8) = struct.unpack("BBBBBBBB", datafork[0:8])
    print("  ", hex(b1), hex(b2), hex(b3), hex(b4), hex(b5), hex(b6), hex(b7), hex(b8))
    #print("Len =", len(datafork))
    print("Length =", length)
    
    with open(output_filename, 'wb') as output_f:
        output_f.write(datafork)




def main():
    global verbose
    
    if len(sys.argv) == 4:
        mode = sys.argv[1]
        filename = sys.argv[2]
        out = sys.argv[3]
    elif len(sys.argv) == 3:
        mode = sys.argv[1]
        filename = sys.argv[2]
        if mode == "list":
            print("Files that might be AppleSingle:")
            scan_directory(filename)
            return
        if mode == "batch":
            print("Batch converting directory:")
            scan_directory(filename, convert=True)
            return
        
        if mode != "verbose":
            print("Verbose, list or batch only supported with input filename only")
            sys.exit(1)
        mode = "verify"
        verbose = True
    elif len(sys.argv) == 2: 
        mode = "verify"
        filename = sys.argv[1]
    else:
        print("No filename supplied")
        print("Possible arguments:")
        print("  <filename>")
        print("  verbose <filename>")
        print("  list <path>")
        print("extract_datafork <filename_in> <filename_out>")
        print("extract_resfork <filename_in> <filename_out>")
        print("extract_both_forks <filename_in> <filename_out>   (NOTE: .resource_fork will be appended to filename_out for the resource fork")
        sys.exit(1)
    
    convert_one_file(filename, mode, out)




main()
