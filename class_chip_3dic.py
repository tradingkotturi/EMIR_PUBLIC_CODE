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
import argparse as ap
import re
import os
class Emir3DIC:
  def __init__(self, flow_, driver_file_, emir_run_dir_):
    self.flow_ = flow_
    self.emir_run_dir_ = emir_run_dir_ 
    self.dfile_ = driver_file_
    self.stacked_die_mapping_file_ = str
    self.ir_additional_settings_file_ = None
    self.md_fabric_flow_ = str
    self.pkg_ = str
    self.emir_h_ = {}
    self.emirtool_h_ = {}
    self.bool_tbl_ = {}
    self.ir_additional_settings_ = {}
    self.vflow_ = []
    self.multi_die_pwr_nets_ = []
    self.multi_die_gnd_nets_ = [] 
    self.out_file_name_ = str
    self.out_dir_ = str
    self.line_ = str
  
    if not os.path.exists(self.emir_run_dir_): 
      os.makedirs(self.emir_run_dir_)
      print(f"Directory '{self.emir_run_dir_}' does not exist. Created it.")
    else:
      print(f"Directory '{self.emir_run_dir_}' already exists.")
    self.power_data_list_elems_ = 2 
    with open(self.dfile_, "r") as fh_:
      for line_ in fh_:
        line_ = line_.strip()
        match = re.match(r"^DIE:(\S+)\s+(\S+):(.*)$", line_)
        if match:
          if match.group(1) in self.emir_h_:
            self.emir_h_[match.group(1)][match.group(2)] = match.group(3)
          else: 
            self.emir_h_[match.group(1)] = {} 
            self.emir_h_[match.group(1)][match.group(2)] = match.group(3)
        match = re.match(r"^3DFABRIC:(\S+)\s+(\S+):(.*)$", line_)
        if match:
          self.md_fabric_flow_ = match.group(1)
          attr_name_ = match.group(2) 
          attr_val_ = match.group(3) 
          if attr_name_ == 'mapping_file':
            self.stacked_die_mapping_file_ = attr_val_
          if attr_name_ == 'ir_additional_settingsude':
            self.ir_additional_settings_file_ = attr_val_
          if attr_name_ == 'pkg_netlist':
            self.pkg_ = attr_val_
    fh_.close()

    if self.flow_ == '3d_static_pwr_only':
      self.flow_ = 'static_pwr_only_'
      self.out_file_name_ = '3d_'+ 'static_pwr_only.tcl'
      self.out_dir_ = '3D_RUN_STATIC_PWR'
      self.build_static_pwr_only_()
    elif self.flow_ == '3d_static_rail_only':
      self.flow_ = 'static_rail_only'
      self.out_file_name_ = '3d_'+ 'static_rail_only.tcl'
      self.out_dir_ = '3D_RUN_STATIC_RAIL'
      self.build_static_rail_only_()
    elif self.flow_ == '3d_dynamic_pwr_only':
      self.flow_ = 'dynamic_pwr_only'
      self.out_file_name_ = '3d_'+ 'dynamic_pwr_only.tcl'
      self.out_dir_ = '3D_RUN_DYNAMIC_PWR'
      self.build_dynamic_pwr_only_()
    elif self.flow_ == '3d_dynamic_rail_only':
      self.flow_ = 'dynamic_rail_only'
      self.out_file_name_ = '3d_'+ 'dynamic_rail_only.tcl'
      self.out_dir_ = '3D_RUN_DYNAMIC_RAIL'
      self.build_dynamic_rail_only_()

  def lsf_settings_file_(self):
     if 'lsf_cmds_file' in self.emir_h_[self.die_] and 'lsf_cmds_file' not in self.bool_tbl_:
       self.bool_tbl_['lsf_cmds_file'] = 1
       self.line_ = 'source' + ' ' + self.emir_h_[self.die_]['lsf_cmds_file']
       self.line_ = self.line_ + '\n'
       self.vflow_.append(self.line_)
       self.line_ = str
  
  def specify_liberty_(self):
    if 'dotlib' in self.emir_h_[self.die_]:
      self.line_ = 'specify_lib -die_instance_name {' + self.die_ +'} {' + self.emir_h_[self.die_]['dotlib'] + '}'
      self.line_ = self.line_ + '\n'
      self.vflow_.append(self.line_)
      self.line_ = str

  def specify_lef_(self):
    if 'lef' in self.emir_h_[self.die_]:
      self.line_ = 'specify_lib -die_instance_name {' + self.die_ +'} -lef {' + self.emir_h_[self.die_]['lef'] + '}'
      self.line_ = self.line_ + '\n'
      self.vflow_.append(self.line_)
      self.line_ = str

  def specify_def_(self):
    if 'def_files' in self.emir_h_[self.die_]:
      self.line_ = 'specify_def {' + self.emir_h_[self.die_]['def_files'] + '} -die_instance_name ' + self.die_
      self.line_ = self.line_ + '\n'
      self.vflow_.append(self.line_)
      self.line_ = str

  def specify_spef_(self):
    if 'spef_files' in self.emir_h_[self.die_]:
      self.line_ = 'specify_spef {' + self.emir_h_[self.die_]['spef_files'] + '} -die_instance_name ' + self.die_
      self.line_ = self.line_ + '\n'
      self.vflow_.append(self.line_)
      self.line_ = str

  def read_arrival_window_(self):
    if 'arrival_windows' in self.emir_h_[self.die_]:
      self.line_ = 'read_arrival_window {' + self.emir_h_[self.die_]['arrival_windows'] + '} -die_instance_name ' + self.die_
      self.line_ = self.line_ + '\n'
      self.vflow_.append(self.line_)
      self.line_ = str
  
  ## Important: You have to pass the value of self.flow_ based on what user has chosen
  def set_power_analysis_mode_(self):
    self.line_ = 'set_power_analysis_mode \\\n'
    self.line_ = self.line_ + '\t' + '-die_instance_name ' + self.die_ + '\\\n'    
    if self.flow_ == 'static_pwr_only_':
      self.line_ = self.line_ + '\t' + '-method ' + 'static' + '\\\n'    
    elif self.flow_ == 'dynamic_pwr_only_':
      self.line_ = self.line_ + '\t' + '-method ' + 'dynamic_stochastic_with_sta' + '\\\n'    
    self.line_ = self.line_ + '\t' + '-pwr_ir_libraries ' + '{' + self.emir_h_[self.die_]['pwr_ir_lib'] + '}\\\n'    
    self.line_ = self.line_ + '...' + '\n'
    self.vflow_.append(self.line_)
    self.line_ = str

  def set_default_switching_activity_(self):
    self.line_ = 'default_switching_activity' + '\\\n'
    self.line_ = self.line_ + '...' + '\n'
    self.vflow_.append(self.line_)
    self.line_ = str

  def set_power_(self):
    self.line_ = 'set_power ' + self.emir_h_[self.die_]['set_power'] + ' -die_instance_name ' + self.die_
    self.line_ = self.line_ + '\n'
    self.vflow_.append(self.line_)
    self.line_ = str
    
  def print_lines_(self):
    for line_ in self.vflow_:
      print(line_)

  def build_static_pwr_only_(self): 
    for die_ in self.emir_h_:
      self.die_ = die_
      if 'is_interposer' not in self.emir_h_[self.die_]:
        self.lsf_settings_file_()
        self.specify_liberty_() 
        self.specify_lef_() 
        self.specify_def_()
        self.specify_spef_()
    for die_ in self.emir_h_:
      self.die_ = die_
      if 'is_interposer' not in self.emir_h_[self.die_]:
        self.read_arrival_window_()
    for die_ in self.emir_h_:
      self.die_ = die_
      if 'is_interposer' not in self.emir_h_[self.die_]:
        self.set_power_analysis_mode_()
    for die_ in self.emir_h_:
      self.die_ = die_
      if 'is_interposer' not in self.emir_h_[self.die_]:
        self.set_default_switching_activity_()
        self.set_power_()
    self.line_ = 'set_power_output_dir ' + self.out_dir_ + '\n\n'
    self.line_ = self.line_ + 'write_pwr_rpt' + '\n\n'
    self.line_ = self.line_ + 'exit' + '\n'
    self.vflow_.append(self.line_)
    self.line_ = str
    self.print_lines_()

  def set_dynamic_power_simulation_(self, die_):
    self.die_ = die_
    self.line_ = 'set_pwr_simulation ' + '...'
    self.vflow_.append(self.line_)
    self.line_ = str
    
  def build_dynamic_pwr_only_(self): 
    for die_ in self.emir_h_:
      self.die_ = die_
      if 'is_interposer' not in self.emir_h_[self.die_]:
        self.lsf_settings_file_()
        self.specify_liberty_() 
        self.specify_lef_() 
        self.specify_def_()
        self.specify_spef_()
    for die_ in self.emir_h_:
      self.die_ = die_
      if 'is_interposer' not in self.emir_h_[self.die_]:
        self.read_arrival_window_()
    for die_ in self.emir_h_:
      self.die_ = die_
      if 'is_interposer' not in self.emir_h_[self.die_]:
        self.set_power_analysis_mode_()
    for die_ in self.emir_h_:
      self.die_ = die_
      if 'is_interposer' not in self.emir_h_[self.die_]:
        self.set_default_switching_activity_()
        self.set_power_()
    for die_ in self.emir_h_:
      self.die_ = die_
      if 'is_interposer' not in self.emir_h_[self.die_]:
        self.set_dynamic_power_simulation_(die_)
    self.line_ = 'set_power_output_dir ' + self.out_dir_ + '\n\n'
    self.line_ = self.line_ + 'write_pwr_rpt' + '\n\n'
    self.line_ = self.line_ + 'exit' + '\n'
    self.vflow_.append(self.line_)
    self.line_ = str
    self.print_lines_()

  def set_rail_analysis_mode_(self, die_):
    self.die_ = die_
    tmp_dir_name_ = 'tmp_dir_' + self.die_
    self.line_ = 'rail_analysis_mode\\\n'
    if self.flow_ == 'static_rail_only_':
      self.line_ = self.line_ + '\t' + '-method ' + 'static'+ '\\\n'    
      self.line_ = self.line_ + '...' + '\n'    
      self.line_ = self.line_ + '\t' + '-report_vv_layers ' + self.emir_h_[self.die_]['report_vv_layers'] + '\\\n'
      self.line_ = self.line_ + '...' + '\n'
      self.vflow_.append(self.line_)
      self.line_ = str
    if self.flow_ == 'dynamic_rail_only_':
      self.line_ = self.line_ + '\t' + '-method ' + 'dynamic'+ '\\\n'    
      self.line_ = self.line_ + '...' + '\n'
      self.vflow_.append(self.line_)
      self.line_ = str

  def ploc_xy_file_(self, die_):
    self.die_ = die_
    self.line_ = 'ploc_xy_file -format xy' + ' -net ALL' + ' -file ' + self.emir_h_[self.die_]['ploc'] + ' -die_instance_name ' + self.die_ + '\n'
    self.vflow_.append(self.line_)
    self.line_ = str

  def set_static_power_data_(self):
    self.line_ = 'set_current_files -reset' + '\n'
    for die_ in self.emir_h_:
      self.die_ = die_
      if 'pti_static_files' in self.emir_h_[self.die_] and self.emir_h_[self.die_] != 'false': 
        self.line_ = self.line_ + 'set_current_files ' + '-format ' + 'current {' + self.emir_h_[self.die_]['pti_static_files'] + '} -die_instance_name ' + self.die_ + '\n'
    self.vflow_.append(self.line_)
    self.line_ = str 

  def set_dynamic_power_data_(self):
    self.set_static_power_data_()

  def set_pkg_(self):
    if self.pkg_ != None:
      self.line_ = 'set_package -spice ' + self.pkg_ + '\n'
      self.vflow_.append(self.line_)
      self.line_ = str

  def make_pg_nets_tbl_(self, string_, net_type_):
    nets_ = self.list_maker_(string_, 3)
    #print("Line 620:", nets_)
    if net_type_ == 'pwr_nets_':
      self.emir__h_['pwr_nets'] = {}
      for i in nets_:
        self.emir_h_['pwr_nets'][i[0]] =i[1:]
    if net_type_ == 'gnd_nets_':
      self.emir_h_['gnd_nets'] = {}
      for i in nets_:
        self.emir_h_['gnd_nets'][i[0]] =i[1:]

  def list_maker_(self, string_, n_elems_):
    list_ = string_.split()
    output_list_ = []
    for i in range(0, len(list_), n_elems_):
      output_list_.append(list_[i:i+n_elems_])
    return output_list_

  def set_pg_nets_(self, die_):
    self.line_ = '' 
    self.die_ = die_
    if 'pwr_nets' in self.emir_h_[self.die_]:  
      list_ = self.emir_h_[self.die_]['pwr_nets'].split() 
      for net_ in range(0, len(list_), 3):
        pwr_net_ = list_[net_:net_+3]
        self.line_ = self.line_ + 'pg_nets ...' + '\n'
        self.multi_die_pwr_nets_.append(die_ + '/' + pwr_net_[0])
    if 'gnd_nets' in self.emir_h_[self.die_]:  
      list_ = self.emir_h_[self.die_]['pwr_nets'].split() 
      for net_ in range(0, len(list_), 3):
        gnd_net_ = list_[net_:net_+3]
        self.line_ = self.line_ + 'set_pg_nets ...' + '\n'
        self.multi_die_gnd_nets_.append(die_ + '/' + gnd_net_[0])
    self.vflow_.append(self.line_)
    self.line_ = str

  def set_multi_die_analysis_mode_(self):
    self.line_ = 'set_multi_die_analysis_mode\\\n' 
    self.line_ = self.line_ + '...' + '\n'
    self.vflow_.append(self.line_)
    self.line = str
 
  def select_analysis_domain_(self):
    self.line_ = 'select_analysis_domain ...' 
    self.vflow_.append(self.line_)
    self.line_ = str
  
  def set_ir_additional_settings_(self):
    if isinstance(self.ir_additional_settings_file_, str) and self.ir_additional_settings_file_.strip():
      self.line_ = 'set_ir_additional_settings ' + self.ir_additional_settings_file_ + '\n'
      self.vflow_.append(self.line_)
      self.line_ = str
  def analyze_rail_(self):
    self.line_ = 'run_rail ...' + '\n'
    self.vflow_.append(self.line_)
    self.line_ = str

  def create_die_model_(self):
    self.line_ = 'create_die_model\\\n'
    self.line_ = self.line_ + '...' + '\n'
    self.vflow_.append(self.line_)
    self.line_ = str

  def build_static_rail_only_(self): 
    for die_ in self.emir_h_:
      self.die_ = die_
      self.lsf_settings_file_()
      self.specify_lef_() 
      self.specify_def_()
      self.specify_spef_()
    for die_ in self.emir_h_:
      self.set_rail_analysis_mode_(die_)
    self.set_static_power_data_()
    for die_ in self.emir_h_:
      self.set_pg_nets_(die_)
    self.set_multi_die_analysis_mode_()
    self.select_analysis_domain_()
    self.set_ir_additional_settings_()
    self.analyze_rail_()
    self.create_die_model_()
    self.print_lines_()

  def build_dynamic_rail_only_(self): 
    for die_ in self.emir_h_:
      self.die_ = die_
      self.lsf_settings_file_()
      self.specify_lef_() 
      self.specify_def_()
      self.specify_spef_()
    for die_ in self.emir_h_:
      self.set_rail_analysis_mode_(die_)
    self.set_dynamic_power_data_()
    for die_ in self.emir_h_:
      self.set_pg_nets_(die_)
    self.set_multi_die_analysis_mode_()
    self.select_analysis_domain_()
    self.set_pkg_()
    self.set_ir_additional_settings_()
    self.analyze_rail_()
    self.create_die_model_()
    self.print_lines_()
