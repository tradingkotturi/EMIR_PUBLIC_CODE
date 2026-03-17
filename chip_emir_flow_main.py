#!/usr/bin/env python3
#***********************************************************************************#
#*                                 MIT License                                     *#
#*                                                                                 *#
#*         Copyright (c) [2025] [Deen Kotturi deen_kotturi@sloan.mit.edu]          *#
#*                                                                                 *#
#* Permission is hereby granted, free of charge, to any person obtaining a copy    *#
#* of this software and associated documentation files (the "Software"), to deal   *#
#* in the Software without restriction, including without limitation the rights    *# 
#* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       *#  
#* copies of the Software, and to permit persons to whom the Software is           *#
#* furnished to do so, subject to the following conditions:                        *#
#*                                                                                 *# 
#* The above copyright notice and this permission notice shall be included in all  *#
#* copies or substantial portions of the Software.                                 *#
#*                                                                                 *#
#* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      *#
#* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        *#
#* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     *#
#* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          *#
#* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   *#
#* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   *#
#* SOFTWARE.                                                                       *#
#***********************************************************************************#
#
# Author: Deen Kotturi
# Email : deen_kotturi@sloan.mit.edu
# Program Name: class_chip_emir.py
# Last Major Change: Sun Nov 09 20:20:20 PST 2025
# Disclaimer: This program is not fully tested. I make no guarantees that this
#   program works in all scenarios. Use it at your own risk.                     
##
from class_chip_emir_utils import ChipEmirUtil
from class_chip_3dic import Emir3DIC
from class_chip_em import Voltus_integem
import argparse as ap


BLOCK_FLOWS = {
  'blk_flow_dynamic',
  'blk_flow_static',
  'hview_use_flow',
  'bhview_validate',
  'top_flat_flow',
}

THREED_FLOWS = {
  '3d_static_pwr_only',
  '3d_static_rail_only',
  '3d_dynamic_pwr_only',
  '3d_dynamic_rail_only',
}


def _resolve_integem_template(args):
  return args.em_template_file if args.em_template_file else args.template_file


def _validate_args(parser, args):
  if not args.flow_type:
    parser.error('Missing required argument: -f/--flow_type')

  if args.flow_type in BLOCK_FLOWS and not args.template_file:
    parser.error(f"Flow '{args.flow_type}' requires -t/--template_file")

  if args.flow_type in THREED_FLOWS and not args.template_file:
    parser.error(f"Flow '{args.flow_type}' requires -t/--template_file")

  if args.flow_type == 'integem':
    if not _resolve_integem_template(args):
      parser.error("Flow 'integem' requires -t/--template_file or -e/--em_template_file")
    if not args.output_file:
      parser.error("Flow 'integem' requires -o/--output_file")

  if args.flow_type == 'multi_die':
    if not args.multi_die_template_file:
      parser.error("Flow 'multi_die' requires -m/--multi_die_template_file")
    if not args.output_file:
      parser.error("Flow 'multi_die' requires -o/--output_file")


def _run_flow(args):
  if args.flow_type in BLOCK_FLOWS:
    ChipEmirUtil(args.flow_type, args.template_file, 'EMIR_RUN_DIR')
    return

  if args.flow_type in THREED_FLOWS:
    Emir3DIC(args.flow_type, args.template_file, '3D_EMIR_RUN_DIR')
    return

  if args.flow_type == 'integem':
    template = _resolve_integem_template(args)
    obj = Voltus_integem(template, args.output_file)
    obj.read_template_file()
    obj.print_lines()
    return

  if args.flow_type == 'multi_die':
    print('Note: Voltus_multi_die class is not yet available. Skipping multi_die flow.')
    return

  print("Incorrect Usage. Execute the script with -h option")


def main():
  parser = ap.ArgumentParser()
  """User Interface"""
  parser.add_argument('-f', '--flow_type', help='Flow type is any of these values: blk_flow_dynamic, blk_flow_static, hview_use_flow, bhview_validate, top_flat_flow, 3d_static_pwr_only, 3d_static_rail_only, 3d_dynamic_pwr_only, 3d_dynamic_rail_only integem multi_die')
  parser.add_argument('-t', '--template_file', help='Template file to use with blk_template_flow, multi_die, or integrated_em as flow_type')
  parser.add_argument('-e', '--em_template_file', help='EM Template file to use with integrated_em as flow_type')
  parser.add_argument('-m', '--multi_die_template_file', help='EM Template file to use with multi_die (3dic) as flow_type')
  parser.add_argument('-o', '--output_file', help='output file to use with multi_die or integrated EM as flow_type')
  args = parser.parse_args()
  _validate_args(parser, args)
  _run_flow(args)

if __name__=='__main__':
  main()




