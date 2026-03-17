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
import os
import sys
import re
import argparse as ap

'''Voltus_integem class for integrated EM flow (PG EM + Sig EM + SEB)'''
class Voltus_integem:
  TEMPLATE_KEYS = (
    'ictem', 'lef', 'lib', 'ccs', 'ccsp', 'pwr_ir_lib', 'pgv', 't_lef', 'ndr_lef', 'verilog',
  )

  def __init__(self, input_tmplt, out_file):
    self.tmplt_in = input_tmplt
    self.out_file = out_file
    self.line_ = ""
    self.lines_ = []
    self.tmplt_h = {}
    self.runtime_h = {}
    self.var_map = {}  # Maps Tcl variable names to their expanded values

  def _append_line(self, line):
    self.lines_.append(line)

  def _append_multiline(self, lines):
    self.lines_.append('\n'.join(lines))
  
  def _build_variable_map(self):
    """Build a map of Tcl variables to their concrete values for expansion."""
    self.var_map = {}

    template_var_map = {'sebtable': 'sebtable'}
  
  def _expand_variables(self):
    """Expand Tcl variable references ($VAR and ${VAR}) in generated output lines."""
    token_regex = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)')

    def resolve_var(var_name):
      if var_name in self.var_map:
        return self.var_map[var_name]
      upper_name = var_name.upper()
      if upper_name in self.var_map:
        return self.var_map[upper_name]
      lower_name = var_name.lower()
      if lower_name in self.var_map:
        return self.var_map[lower_name]
      return None

    def expand_line(line):
      expanded = line
      max_passes = 8
      for _ in range(max_passes):
        changed = False

        def replacer(match):
          nonlocal changed
          var_name = match.group(1) if match.group(1) is not None else match.group(2)
          resolved = resolve_var(var_name)
          if resolved is None:
            return match.group(0)
          changed = True
          return resolved

        updated = token_regex.sub(replacer, expanded)
        expanded = updated
        if not changed:
          break
      return expanded

    expanded_lines = []
    for line in self.lines_:
      expanded_lines.append(expand_line(line))
    self.lines_ = expanded_lines

  def _require_keys(self, keys, context):
    missing = [key for key in keys if key not in self.tmplt_h]
    if missing:
      raise ValueError(f"Missing required template keys for {context}: {', '.join(missing)}")

  def _parse_voltage_entries(self, key_name):
    if key_name not in self.tmplt_h:
      raise ValueError(f"{key_name} not found in template")

    entries = []
    for item in self.tmplt_h[key_name].split(','):
      fields = item.strip().split()
      if len(fields) != 3:
        raise ValueError(f"Invalid {key_name} entry '{item.strip()}'. Expected: <NET> <VOLTAGE> <THRESHOLD>")
      entries.append(tuple(fields))
    return entries

  def _append_pg_nets_from_template(self):
    pass

  def _parse_domain(self):
    if 'domain' not in self.tmplt_h:
      raise ValueError("domain not found in template")
    fields = [field.strip() for field in self.tmplt_h['domain'].split(',')]
    if len(fields) != 3:
      raise ValueError("Invalid domain format. Expected: <domain>,<pwr_nets>,<gnd_nets>")
    return fields[0], fields[1], fields[2]

  def _create_flow(self):
    self.write_var_settings()
    self.set_design_related_settings()
    self.set_pre_timing_settings()
    self.read_design_data()
    self.create_mmmc()
    self.set_post_timing_settings()
    self.set_design_mode_and_delay_cal_mode()
    self.create_power_analysis_flow()
    self.set_rail_analysis_flow_settings()
    self.create_rail_analysis_flow()
    self.create_signal_em_analysis_flow()
    self.create_analyze_self_heat_flow()
    self.create_final_pg_seb_flow()
    self.create_final_signal_seb_flow()

  def read_template_file(self):
    if not os.path.exists(self.tmplt_in):
      raise FileNotFoundError(f"Template file not found: {self.tmplt_in}")

    real_file = os.path.realpath(self.tmplt_in)
    key_pattern = '|'.join(self.TEMPLATE_KEYS)
    template_regex = re.compile(rf"^({key_pattern}):\s*(.*)$", re.IGNORECASE)

    with open(real_file, "r") as fh:
      for raw_line in fh:
        match = template_regex.match(raw_line)
        if match:
          self.tmplt_h[match.group(1).lower()] = match.group(2)

    if 'pwr_ir_lib' not in self.tmplt_h and 'pgv' in self.tmplt_h:
      self.tmplt_h['pwr_ir_lib'] = self.tmplt_h['pgv']

    self._create_flow()

  def print_lines(self):
    """Build variable map and expand all Tcl variables before writing output."""
    self._build_variable_map()
    self._expand_variables()
    with open(self.out_file, "w") as fh:
      for line in self.lines_:
        fh.write(line + '\n')

  def write_var_settings(self):
    pass

  def set_design_related_settings(self):
    pass

  def set_pre_timing_settings(self):
    pass

  def read_design_data(self):
    pass

  def create_mmmc(self):
    pass

  def set_post_timing_settings(self):
    pass

  def set_design_mode_and_delay_cal_mode(self):
    pass

  def create_power_analysis_flow(self):
    pass
  
  def set_rail_analysis_flow_settings(self):
    pass
  
  def create_rail_analysis_flow(self):
    pass

  def create_signal_em_analysis_flow(self):
    pass

  def create_analyze_self_heat_flow(self):
    pass

  def create_final_pg_seb_flow(self):
    pass

  def create_final_signal_seb_flow(self):
    pass