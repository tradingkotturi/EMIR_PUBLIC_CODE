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
#from Voltus_multi_die import Voltus_multi_die
#from Voltus_integem import Voltus_integem
## Class definition for Emir flow
class ChipEmirUtil():
  def __init__(self, flow_, driver_file_, emir_run_dir_):
    """Initialize utility object and execute requested flow.

    Args:
      flow_ (str): Requested flow name.
      driver_file_ (str): Input driver file containing TILE records.
      emir_run_dir_ (str): Output directory for generated Tcl and log files.
    """
    self.flow_ = flow_
    self.dfile_ = driver_file_
    self.emir_h_ = {}
    self.emirtool_h_ = {}
    self.tile_flg_ = False
    self.tile_name_ = None
    self.emir_run_dir_ = emir_run_dir_
    self.power_data_list_elems_ = 2

    # 1) Ensure output location exists.
    self._ensure_run_dir_()
    # 2) Parse input driver file into tile/key/value LUT.
    self._load_driver_file_()
    # 3) Dispatch to the requested flow builder.
    self._dispatch_flow_()

  def _ensure_run_dir_(self):
    """Create output directory if missing."""
    if not isinstance(self.emir_run_dir_, str) or not self.emir_run_dir_.strip():
      raise ValueError("emir_run_dir_ must be a non-empty string")
    if not os.path.exists(self.emir_run_dir_):
      os.makedirs(self.emir_run_dir_)
      print(f"Directory '{self.emir_run_dir_}' does not exist. Created it.")
    else:
      print(f"Directory '{self.emir_run_dir_}' already exists.")

  def _load_driver_file_(self):
    """Parse TILE records from driver file into emir_h_."""
    if not isinstance(self.dfile_, str) or not self.dfile_.strip():
      raise ValueError("driver_file_ must be a non-empty string")

    record_pattern = re.compile(r"^TILE:(\S+)\s+(\S+):(.*)$")
    with open(self.dfile_, "r") as fh_:
      for raw_line_ in fh_:
        line_ = raw_line_.strip()
        # Expected format: TILE:<tile_name> <key>:<value>
        match = record_pattern.match(line_)
        if not match:
          continue
        tile_name_, key_, value_ = match.group(1), match.group(2), match.group(3)
        # Build nested dict: emir_h_[tile_name_][key_] = value_
        self.emir_h_.setdefault(tile_name_, {})[key_] = value_

  def _dispatch_flow_(self):
    """Dispatch requested high-level flow to corresponding builder."""
    flow_handlers = {
      'blk_flow_static': ('blk_flow_', self.build_emir_util_lut_),
      'blk_flow_dynamic': ('blk_flow_', self.build_emir_util_lut_),
      'hview_use_flow': ('hview_use_flow_', self.build_hview_use_emir_util_lut_),
      'top_flat_flow': ('top_flat_flow_', self.build_hview_use_emir_util_lut_),
      'bhview_validate': ('bhview_validate_', self.build_bhview_validate_util_lut_test_),
    }

    mapped = flow_handlers.get(self.flow_)
    if not mapped:
      raise ValueError(f"Unsupported flow '{self.flow_}'")

    # Normalize incoming flow names to legacy/internal names used by ChipEmir.
    normalized_flow_, handler_ = mapped
    self.flow_ = normalized_flow_
    handler_()

  def _split_if_vector_(self, key_, value_):
    """Split scalar string into vector fields for known multi-value keys."""
    vector_keys_ = {
      'lef', 'dotlib', 'pwr_ir_lib', 'vlog_files', 'spef_files', 'def_files', 'arrival_windows',
      'pti_static_files', 'pti_dynamic_files', 'domain_pwr_nets', 'domain_gnd_nets'
    }

    # Keep optional PTI file lists unset when explicitly disabled.
    if key_ in ('pti_static_files', 'pti_dynamic_files') and value_ == 'false':
      return None

    if key_ in vector_keys_:
      return self.splitter_(value_, ' ')
    return value_

  def _update_xpwr_ir_lib_fields_(self, tile_key_, tile_value_):
    """Populate nested xpwr_ir_lib fields from parsed tile data."""
    if 'xpwr_ir_lib' not in self.emirtool_h_:
      self.emirtool_h_['xpwr_ir_lib'] = {}

    if tile_key_ == 'cut_layer':
      self.emirtool_h_['xpwr_ir_lib']['cut_layer'] = tile_value_
    elif tile_key_ in ('exclude_obs_layers', 'pg_pin_layers'):
      self.emirtool_h_['xpwr_ir_lib'][tile_key_] = self.splitter_(tile_value_, ' ')

  def _prepare_tile_lut_(self, tile_name_):
    """Build per-tile Voltus LUT from parsed driver data."""
    tile_data_ = self.emir_h_.get(tile_name_)
    if not isinstance(tile_data_, dict):
      raise ValueError(f"Tile '{tile_name_}' has invalid data")

    self.tile_name_ = tile_name_
    self.emirtool_h_ = {
      'tile_name': tile_name_,
      'xpwr_ir_lib': {'name': tile_name_},
      'hview': {
        'name': tile_name_,
        'pg_pin_layers': [],
        'exclude_obs_layers': [],
      },
      'write_hview_abs_lef': False,
    }

    for key_, value_ in tile_data_.items():
      # Net tables are parsed into dict form required by ChipEmir.
      if key_ in ('pwr_nets', 'gnd_nets'):
        self.make_pg_nets_tbl_(value_, f"{key_}_")
        continue

      # XPGV nested fields are grouped under emirtool_h_['xpwr_ir_lib'].
      if key_ in ('exclude_obs_layers', 'pg_pin_layers', 'cut_layer'):
        self._update_xpwr_ir_lib_fields_(key_, value_)
        if key_ in ('exclude_obs_layers', 'pg_pin_layers'):
          self.emirtool_h_['hview'][key_] = self.splitter_(value_, ' ')
        continue

      mapped_ = self._split_if_vector_(key_, value_)
      if mapped_ is not None:
        self.emirtool_h_[key_] = mapped_

  def _build_tile_command_(self, run_method_name_):
    """Create ChipEmir object and invoke flow method with compatibility fallback."""
    from class_chip_emir import ChipEmir

    chip_obj_ = ChipEmir(self.emirtool_h_, self.flow_, self.dfile_)
    method_ = getattr(chip_obj_, run_method_name_, None)
    if not callable(method_):
      # Compatibility fallback for legacy method names that end with underscore.
      legacy_name_ = run_method_name_ + '_'
      method_ = getattr(chip_obj_, legacy_name_, None)
    if not callable(method_):
      raise AttributeError(f"Method '{run_method_name_}' not found on ChipEmir")
    method_()
    return chip_obj_

  def _write_tile_output_(self, chip_obj_, include_blank_before_exit_=False):
    """Write generated Tcl lines and print Voltus command line."""
    cmd_f_name_ = self.tile_name_ + '.tcl'
    cmd_f_name_path_ = f"{self.emir_run_dir_}/{cmd_f_name_}"
    log_f_name_ = self.tile_name_ + '.tcl.log'
    log_f_name_path_ = f"{self.emir_run_dir_}/{log_f_name_}"

    with open(cmd_f_name_path_, "w") as ofh:
      # Write generated Tcl program lines in order.
      vflow_lines_ = getattr(chip_obj_, 'vflow_', getattr(chip_obj_, 'vflow', []))
      for line_ in vflow_lines_:
        ofh.write(line_ + "\n")
      if include_blank_before_exit_:
        ofh.write("\n")
      # Ensure every generated script exits cleanly.
      ofh.write("exit\n")

    print("voltus", "-stylus", "-file", cmd_f_name_path_, "-log", log_f_name_path_)

  def _finalize_tile_(self):
    """Reset tile-scoped state after output generation."""
    self.tile_name_ = None
    self.emirtool_h_ = {}

  def build_bhview_validate_util_lut_test_(self):
    """Build and emit bhview_validate flow commands for all tiles."""
    if not self.emir_h_:
      return

    self.flow_ = 'bhview_validate_'
    for tile_name_ in self.emir_h_.keys():
      # Build per-tile LUT, generate Tcl, write to disk, then reset state.
      self._prepare_tile_lut_(tile_name_)
      chip_obj_ = self._build_tile_command_('write_tile_bhv')
      self._write_tile_output_(chip_obj_)
      self._finalize_tile_()

  def build_bhview_validate_util_lut_(self):
    """Backward-compatible wrapper for bhview_validate generation."""
    self.build_bhview_validate_util_lut_test_()

  def build_hview_use_emir_util_lut_(self):
    """Build and emit hview_use/top_flat flow commands for all tiles."""
    if not self.emir_h_:
      return

    for tile_name_ in self.emir_h_.keys():
      self._prepare_tile_lut_(tile_name_)
      # top_name is required by downstream top-flat/XM rail flows.
      self.emirtool_h_['top_name'] = tile_name_
      chip_obj_ = self._build_tile_command_('write_blk_pwr_rail_analysis')
      self._write_tile_output_(chip_obj_, include_blank_before_exit_=True)
      self._finalize_tile_()

  def build_emir_util_lut_(self):
    """Build and emit block-flow rail analysis commands for all tiles."""
    if not self.emir_h_:
      return

    self.flow_ = 'blk_flow_'
    for tile_name_ in self.emir_h_.keys():
      self._prepare_tile_lut_(tile_name_)
      self.emirtool_h_['top_name'] = tile_name_
      chip_obj_ = self._build_tile_command_('write_blk_pwr_rail_analysis')
      self._write_tile_output_(chip_obj_)
      self._finalize_tile_()

  def set_current_files_(self, string_):
    """Split power-data string into fixed-width chunks."""
    n_elems_ = self.power_data_list_elems_
    return self.list_maker_(string_, n_elems_)

  def print_emir_lut_(self, tile_name_):
    """Print tile LUT content for debug when key vectors are present."""
    required_keys_ = ('def_files', 'spef_files', 'pwr_ir_lib')
    if all(k_ in self.emirtool_h_ for k_ in required_keys_):
      for tile_attr_ in self.emirtool_h_.keys():
        print(tile_name_, tile_attr_, self.emirtool_h_[tile_attr_])

  def splitter_(self, string_, pattn_):
    """Split input string by provided pattern."""
    if not isinstance(string_, str):
      raise TypeError(f"string_ must be str, got {type(string_).__name__}")
    if not isinstance(pattn_, str):
      raise TypeError(f"pattn_ must be str, got {type(pattn_).__name__}")
    return string_.split(pattn_)

  def make_pg_nets_tbl_(self, string_, net_type_):
    """Build pwr_nets/gnd_nets dictionary from flattened net triple list."""
    nets_ = self.list_maker_(string_, 3)
    if net_type_ == 'pwr_nets_':
      self.emirtool_h_['pwr_nets'] = {}
      for net_triplet_ in nets_:
        # Expected format: <net_name> <voltage> <threshold>
        if len(net_triplet_) >= 3:
          self.emirtool_h_['pwr_nets'][net_triplet_[0]] = net_triplet_[1:]
    elif net_type_ == 'gnd_nets_':
      self.emirtool_h_['gnd_nets'] = {}
      for net_triplet_ in nets_:
        # Expected format: <net_name> <voltage> <threshold>
        if len(net_triplet_) >= 3:
          self.emirtool_h_['gnd_nets'][net_triplet_[0]] = net_triplet_[1:]
    else:
      raise ValueError(f"Unsupported net_type_: {net_type_}")

  def list_maker_(self, string_, n_elems_):
    """Split string into groups with n_elems_ elements each."""
    if not isinstance(string_, str):
      raise TypeError(f"string_ must be str, got {type(string_).__name__}")
    if not isinstance(n_elems_, int) or n_elems_ <= 0:
      raise ValueError("n_elems_ must be a positive integer")

    tokens_ = string_.split()
    return [tokens_[i:i + n_elems_] for i in range(0, len(tokens_), n_elems_)]