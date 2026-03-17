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
class ChipEmir:
  def __init__(self, lut, flow, template_file):
    self.lut_ = lut
    self.flow_ = flow 
    self.tf_ = template_file 
    self.dotlib_ = False
    self.lef_ = False
    self.lef_dotlib_ = False
    self.pwr_def_files_ = False
    self.vlog = True
    self.vflow_ = []
    self.pwr_set_ = []
  
  def print_lines_(self):
    for l in self.vflow_:
      print(l)

  def emirtool_internal_env_settings_(self):
    self.vflow_.append('setenv SOME_ENV_VAR 0') 

  def lsf_settings_file_(self):
    if self.lut_['lsf_cmds_file']:
      self.vflow_.append('source' + ' ' + self.lut_['lsf_cmds_file'])

  def lef_list_(self):
    if self.lut_['lef']:
      self.vflow_.append('set lef_list [list]')
      for i in self.lut_['lef']:
        self.vflow_.append('lappend lef_list' + ' ' + i)
        self.lef_ = True

  def dotlib_list_(self):
    if self.lut_['dotlib']:
      self.vflow_.append('set liberty_files [list]')
      for i in self.lut_['dotlib']:
        self.vflow_.append('lappend liberty_files' + ' ' + i)
        self.dotlib_ = True

  def read_lef_dotlib_(self):
    if self.lef_ and self.dotlib_:
      self.vflow_.append('read_liberty_files' + ' ' + '$liberty_files')
      self.vflow_.append('read_lef_files' + ' ' + '$lef_list')
      self.lef_dotlib_ = True 

  def set_layout_files_(self):
    if self.lut_['def_files']:
      self.vflow_.append('set_layout_files' + ' ' + '"' + ' '.join(self.lut_['def_files']) + '"')
      self.pwr_def_files_ = True 

  def set_parasitic_files_(self):
    if self.lut_['spef_files']:
      self.vflow_.append('set_parasitic_files' + ' ' + '"' + ' '.join(self.lut_['spef_files']) + '"')
      self.pwr_spef_files_ = True

  def read_vlog_files_(self): 
    if self.lut_['vlog_files']:
      self.vflow_.append('read_logical_netlist_files' + ' -top ' + self.lut_['top_name'] + ' ' + '"' + ' '.join(self.lut_['vlog_files']) + '"')
      self.vlog = True

  def read_layout_files_(self): 
    if self.lut_['def_files']:
      self.vflow_.append('read_layout' + ' "' + ' '.join(self.lut_['def_files']) + '"')

  def read_rc_netlist_files_(self): 
    if self.lut_['spef_files']:
      self.vflow_.append('read_rc_netlist_files' + ' "' + ' '.join(self.lut_['spef_files']) + '"')

  def init_design_(self):
    if self.lef_dotlib_: 
      self.vflow_.append('init_design')

  def read_arrival_windows_(self): 
    if 'arrival_windows' in self.lut_ and self.lut_['arrival_windows'][0] != 'none':
      print("DBG 92", self.lut_['arrival_windows'][0])
      self.vflow_.append('read_arrival_window' + ' ' + ' '.join(self.lut_['arrival_windows']))
    elif 'block_arrival_windows' in self.lut_ and self.lut_['block_arrival_windows'] != 'none':
      blks_ = self.list_maker_(self.lut_['block_arrival_windows'], 2)
      for i in blks_:
        self.vflow_.append('read_arrival_window' + ' -cell ' + i[0] + ' ' + i[1])
  
  def power_set_db_(self):
    if 'rctechfile' in self.lut_:
      self.pwr_set_.append('pwr_extraction_tech_file' + ' ' + self.lut_['rctechfile'])
    else:
      print("Info:POWER rctechfile not provided. Please set power_extraction_tech_file.")
      #self.pwr_set_.append('pwr_extraction_tech_file' + ' ' + self.lut_['rctechfile'])

  def power_sim_(self):
    if self.lut_['pwr_incl']:
      self.pwr_set_.append('set_power_include_file' + ' ' + self.lut_['pwr_incl']) 

  def write_hview_config_(self):
    f = open("hview.config", "w")
    # generate the HView file
    f.write(line_)
    f.close()
    #self.vflow_.append(line_)

  def write_abstract_lef_(self):
    if self.lut_['hview']['pg_pin_layers'] and self.lut_['hview']['exclude_obs_layers'] and self.lut_['write_hview_abs_lef']:
      cmd_str_ = 'generate_abstract' + ' ' + self.lut_['hview']['name'] + '.lef.gz' + ' ' + '-stripe_pins' + ' ' + '-pg_pin_layers {' + ' '.join(self.lut_['hview']['pg_pin_layers']) + '} ' + '-exclude_obs_layers {' + ' '.join(self.lut_['hview']['exclude_obs_layers']) + '}'
      self.hview_lef_ = self.lut_['hview']['name']+ '.lef.gz'
      self.vflow_.append(cmd_str_)
      self.write_hview_config_()

  def write_flow_tmpl_blk_hview_lef_config_(self):
    self.emirtool_internal_env_settings_()
    self.lsf_settings_file_()
    self.lef_list_()
    self.dotlib_list_()
    self.read_lef_dotlib_()
    #self.set_layout_files_()
    #self.set_parasitic_files_()
    self.read_vlog_files_()
    self.init_design_()
    self.read_layout_files_()
    self.read_rc_netlist_files_()
    self.read_arrival_windows_()
    if self.lut_['hview'] and self.lut_['hview']['name']:
      self.write_abstract_lef_()
    self.print_lines_()

  def write_flow_tmpl_blk_pwr_(self):
    self.emirtool_internal_env_settings_()
    self.lsf_settings_file_()
    self.lef_list_()
    self.dotlib_list_()
    self.read_lef_dotlib_()
    self.read_vlog_files_()
    self.init_design_()
    self.read_layout_files_()
    self.read_rc_netlist_files_()
    self.read_arrival_windows_()
    self.power_set_db_()
    self.power_sim_()
    self.vflow_.extend(self.pwr_set_)
    if self.flow_ == 'blk_pwr':
      line_ = 'write_pwr_rpt -instances ...' 
      self.vflow_.append(line_)
      self.print_lines_()

  def make_power_data(self):
    set_current_data_lines_ = ''
    with open(self.lut_['set_current_data']) as fh:
      for pti_line_ in fh:
        pti_line_ = pti_line_.strip()
        match = re.match(r"(\S+)\s+(.*)", pti_line_)
        if match:
          set_current_data_lines_ = set_current_data_lines_ + 'set_current_data ' + '-instance_name ' + match.group(1) + ' -format current ' + '[list ' + match.group(2) + ']' + '\n'
    return set_current_data_lines_
    
  def write_hview_use_pwr_rail_analysis_(self):
    line_ = ''
    #print(self.lut_)
    self.lut_['write_pwr_rpt_in_parallel'] = 'false'
    self.emirtool_internal_env_settings_()
    self.lsf_settings_file_()
    self.lef_list_()
    self.dotlib_list_()
    self.read_lef_dotlib_()
    self.set_layout_files_()
    self.set_parasitic_files_()
    line_ = line_ + 'rail_analysis_preconditioning\\' + '\n'
    line_ = line_ + '\t' + '-preconditioner ' + self.lut_['hview_use_flow_preconditioner'] + '\\' + '\n' + '...' + '\n'

  def list_maker_(self, string_, n_elems_):
    list_ = string_.split()
    output_list_ = []
    for i in range(0, len(list_), n_elems_):
      output_list_.append(list_[i:i+n_elems_])
    return output_list_

  def make_hview_config(self):
    line_ = 'hview config ...' + '\n'
    return line_

  def make_rail_config(self):
    self.line_ = self.line_ + 'rail_analysis_preconditioning\\' + '\n' + '...' + '\n'

  def write_tile_bhv_(self):
    self.line_ = ''
    self.emirtool_internal_env_settings_()
    self.lsf_settings_file_()
    self.lef_list_()
    self.dotlib_list_()
    self.read_lef_dotlib_()
    self.set_layout_files_()
    self.set_parasitic_files_()
    self.lut_['write_pwr_rpt_in_parallel'] = 'false'
    self.make_rail_config()
    self.vflow_.append(self.line_)

  def write_blk_pwr_rail_analysis_(self):
    self.line_ = ''
    self.emirtool_internal_env_settings_()
    self.lsf_settings_file_()
    self.lef_list_()
    self.dotlib_list_()
    self.read_lef_dotlib_()
    if self.flow_ == 'hview_use_flow_':
      self.set_layout_files_()
      self.set_parasitic_files_()
      self.lut_['write_pwr_rpt_in_parallel'] = 'false'
    elif self.flow_ == 'top_flat_flow_':
      self.set_layout_files_()
      self.set_parasitic_files_()
      #self.lut_['write_pwr_rpt_in_parallel'] = 'true'
      self.read_arrival_windows_()
      self.power_set_db_()
      self.power_sim_()
      self.vflow_.extend(self.pwr_set_)
    elif self.flow_ == 'blk_flow_':
      self.read_vlog_files_()
      self.init_design_()
      self.read_layout_files_()
      self.read_rc_netlist_files_()
      self.power_set_db_()
      self.power_sim_()
      self.read_arrival_windows_()
      self.write_abstract_lef_()
      self.vflow_.extend(self.pwr_set_)
      self.hview_lef_ = self.lut_['top_name']+ '.lef.gz'
      self.line_ = self.make_hview_config() 
      #self.print_lines_()
    self.make_rail_config()
    self.vflow_.append(self.line_)
    #self.print_lines_()

  def write_rail_analysis_(self):
    self.write_flow_tmpl_blk_pwr_()
    if self.flow_ == 'top_flat':
      self.set_layout_files_()
      self.set_parasitic_files_()
    line_ = 'rail_analysis_preconditioning\\' + '\n' + '...' + '\n'
    self.vflow_.append(line_)
    self.print_lines_()

  def write_blk_pwr_rail_hview(self):
    pass
    
  def output_template_file_(self):
    if self.flow_ == 'hview_lef_config':
      self.write_flow_tmpl_blk_hview_lef_config_()
    elif self.flow_ == 'blk_pwr':
      self.write_flow_tmpl_blk_pwr_()
    elif self.flow_ == 'blk_pwr_rail_only':
      self.write_rail_analysis_()
    elif self.flow_ == 'dyn_blk_pwr_ir':
      self.write_blk_pwr_rail_analysis_()
    elif self.flow_ == 'top_flat':
      self.write_rail_analysis_()
    else:
      exit("None of the options matched. Please execute vapi.py -h")
