#!/usr/bin/env -S  python  #
# -*- coding: utf-8 -*-
# ===============================================================================
# Author: Dr. Samuel Louviot, PhD
# Institution: Nathan Kline Institute
#              Child Mind Institute
# Address: 140 Old Orangeburg Rd, Orangeburg, NY 10962, USA
#          215 E 50th St, New York, NY 10022
# Date: 
# email: samuel DOT louviot AT nki DOT rfmh DOT org
# ===============================================================================
# LICENCE INFORMATION HERE
# ===============================================================================

"""
GENERAL DOCUMENTATION HERE
"""

# standard-library imports
import os
import re
import ast
import sys
import glob
import argparse

# before we do any third-party imports, parse command-line arguments
if __name__ == '__main__':   # (if this was a package rather than a single-file module, we would just cut this code out and put it in WhateverThePackageIsCalled/__main__.py (without the if statement)
	import ast, argparse
	
	def OneOrTwoNumbers( s ): # custom argument "type"
		seq = ast.literal_eval( s.strip( ' [](),' ) + ',' )
		try: x, = seq
		except: x = a, b = seq
		return x
		
	def TwoNumbers( s ):
		seq = ast.literal_eval( s )
		x = a, b = [ float(element) for element in seq ] # will throw an exception if there aren't exactly two elements, both interpretable as floats
		return x
		
	class HelpFormatter( argparse.RawDescriptionHelpFormatter ): pass
	#class HelpFormatter( argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter ): pass
	parser = argparse.ArgumentParser( description=__doc__, formatter_class=HelpFormatter, )#   prog='python -m RecruitmentCurveFitting', )
	parser.add_argument(       "filenames",         metavar='FILENAME',    nargs='*', help='one or more text files to load (use a dash to denote stdin)' )
	parser.add_argument(       "--help-module",     action='store_true',   help='display the docstring for the main package (Python API)' )
	parser.add_argument(       "--unpack-examples", action='store_true',   help='write example files to the current directory (do not overwrite) and quit' )
	parser.add_argument( "-p", "--plot",            action='store_true',   help='whether to show figures on-screen' )
	parser.add_argument( "-g", "--grid",            action='store_true',   help='whether to use a grid for the plots' )
	parser.add_argument( "-x", "--xlabel",          metavar='XLABEL',      default='Stimulation Intensity (mA)', help='x-axis label text for the plots' )
	parser.add_argument( "-y", "--ylabel",          metavar='YLABEL',      default='Response ($\\mu$V)', help='y-axis label text for the plots' )
	parser.add_argument( "-t", "--title",           metavar='TITLE',       default=None, help='override automatically-generated plot titles' )
	parser.add_argument(       "--xlim",            metavar='XMIN,XMAX',   default=None, type=OneOrTwoNumbers, help='x-axis limits for the plots' )
	parser.add_argument(       "--ylim",            metavar='YMIN,YMAX',   default=None, type=TwoNumbers, help='y-axis limits for the plots' )
	parser.add_argument(       "--mark-mmax",       action='store_true',   help='whether to mark M_max on plots' )
	parser.add_argument(       "--mark-hmax",       action='store_true',   help='whether to mark H_max on plots' )
	parser.add_argument(       "--threshold",       metavar='MTHRESHOLD',  default=0, type=float, help='unscaled proportion of Mmax (between 0 and 1) to mark as "threshold" for the M-wave curve (set to 0 to leave it unmarked)' )
	parser.add_argument( "-s", "--saveas",          metavar='PDFFILENAME', default='', help='name of pdf file in which to save figures (one per page)' )
	OPTS = parser.parse_args()

# third-party imports (and comments indicating how to install them)
#import matplotlib    # python -m conda install matplotlib          or    python -m pip install matplotlib
#import mne           # python -m conda install -c whatever mne     or    python -m pip install mne
#import audiomath     # python -m pip install audiomath

# import our own modules
from SomeOtherPackageWeWrote import This

# function and class definitions for this module

__all__ = [ # symbols listed here will be the ones the user gets when they `import *` from here
	'Main',
	'EndUserError',
	'This',   # NB: imported from SomeOtherPackageWeWrote
	'That',
	'TheOther',
]

class EndUserError( Exception ): pass

class That:
	pass
	
def TheOther( x ):
	pass
	
def Main( plot=False, xlim=None, ylim=None, threshold=0.0, **kwargs ):
	if threshold < 0.0: raise EndUserError( 'cannot have a negative threshold' ) # we will catch this an re-frame it as SystemExit, which means it won't look scary to the end-user
	a = 1 / threshold # if threshold is zero, this will raise an exception but we're not catching that, so it will be delivered with a scary backtrace. That's OK, because this is an actual bug.


# "Main" block for this file (if this was a package rather than a single-file module, we would just cut this code out and put it in WhateverThePackageIsCalled/__main__.py (without the if statement)
if __name__ == '__main__':
	print(OPTS)
	This( OPTS.xlim ) # this is how you would dereference an individual option
	try:
		result = Main( **OPTS.__dict__ )  # this is how you just pass them wholesale to a function
	except EndUserError as error:
		raise SystemExit( error )
