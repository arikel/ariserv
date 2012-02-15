#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from xml.dom import minidom, Node
import base64
import gzip
import StringIO
import os.path
import pygame

#-------------------------------------------------------------------------------
def decode_base64(in_str):
	return base64.decodestring(in_str)

def encode_base64(in_str):
	return base64.encodestring(in_str)
	
def decompress_gzip(in_str):
	compressed_stream = StringIO.StringIO(in_str)
	gzipper = gzip.GzipFile(fileobj=compressed_stream)
	return gzipper.read()
	
def compress_gzip(in_str):
	compressed_stream = StringIO.StringIO()
	gzipper = gzip.GzipFile(fileobj=compressed_stream, mode="wb")
	gzipper.write(in_str)
	gzipper.close()
	return compressed_stream.getvalue()
	
def getCode(val):
	code = chr(int(val & 255))
	code = code + chr(int((val>>8) & 255))
	code = code + chr(int((val>>16) & 255))
	code = code + chr(int((val>>24) & 255))
	return code
	
def decode(encoded_content):
	s = encoded_content
	if encoded_content:
		s = decode_base64(s)
		s = decompress_gzip(s)
	#print "Content after decode and decompress : %s" % (s)
	decoded_content = []
	for idx in xrange(0, len(s), 4):
		val = ord(str(s[idx])) | (ord(str(s[idx + 1])) << 8) | \
			 (ord(str(s[idx + 2])) << 16) | (ord(str(s[idx + 3])) << 24)
		decoded_content.append(val)
	return decoded_content
	
def encode(content_list):
	"Encodes an array of ints corresponding to tiles id"
	coded_content = ""
	for n in content_list:
		coded_content = coded_content + getCode(n)
	coded_content = compress_gzip(coded_content)
	coded_content = encode_base64(coded_content)
	return coded_content
	


