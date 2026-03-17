#!/usr/bin/env tclsh
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
# Program Name: rcGraphView.tcl 
# Last Major Change: Sun Nov 09 20:20:20 PST 2025
# Disclaimer: This program is not fully tested. I make no guarantees that this
#   program works in all scenarios. Use it at your own risk.                     
##
global nameMapH
global graphH

set ::DOT_BIN "C:/Program Files/Graphviz/bin/dot.exe"

# ---------------------------------------------------------------------------
# normalizeNode -- convert a raw SPEF node token to a DOT-safe identifier
# ---------------------------------------------------------------------------
proc normalizeNode {raw} {
    regsub -all {\*} $raw  "N"     out
    regsub -all {:}  $out "_HSP_"  out
    return $out
}

# ---------------------------------------------------------------------------
# nodeAttrs -- return DOT attribute string for a node, coloured by pin direction.
#   displayName : normalized node name used as the DOT identifier/label
#   origName    : raw SPEF name used as connH key
#   connH       : dict mapping raw SPEF node -> pin direction (I/O/B)
# ---------------------------------------------------------------------------
proc nodeAttrs {displayName origName connH} {
    if {[dict exists $connH $origName]} {
        set dir   [dict get $connH $origName]
        set label "${displayName}($dir)"
        switch -- $dir {
            I { return "\[label=\"$label\", style=filled, color=limegreen\]" }
            B { return "\[label=\"$label\", style=filled, color=yellow\]"    }
            O { return "\[label=\"$label\", style=filled, color=cyan\]"      }
        }
    }
    return "\[label=\"$displayName\"\]"
}

# ---------------------------------------------------------------------------
# parseConnSection -- extract CONN entries into a connH dict.
#   Writes comment lines to fileId so the .dot file retains them.
# ---------------------------------------------------------------------------
proc parseConnSection {fileId connTypeDict} {
    set connH [dict create]
    dict for {connLine _} $connTypeDict {
        puts $fileId "// $connLine"
        if {[regexp {^\s*\S+\s+(\S+)\s+(\S+)} $connLine -> node dir]} {
            dict set connH $node $dir
        }
    }
    return $connH
}

# ---------------------------------------------------------------------------
# renderDotOutputs -- invoke Graphviz dot to produce PostScript and PDF outputs.
# ---------------------------------------------------------------------------
proc renderDotOutputs {dotFile} {
    if {![file exists $dotFile]} { return }
    set psFile "${dotFile}.ps"
    set pdfFile "${dotFile}.pdf"
    puts "Rendering $dotFile -> $psFile"
    if {[catch {exec $::DOT_BIN -Tps $dotFile -o $psFile} err] && $err ne ""} {
        puts stderr "dot error: $err"
    }
    puts "Rendering $dotFile -> $pdfFile"
    if {[catch {exec $::DOT_BIN -Tpdf $dotFile -o $pdfFile} err] && $err ne ""} {
        puts stderr "dot error: $err"
    }
}

# ---------------------------------------------------------------------------
# renderElementGraph -- core writer for a single element-type .dot file.
#   idx       : SPEF net index (e.g. *42)
#   elemType  : CCAP | CGCAP | RES
#   edgeLabel : edge label prefix  (CC / GC / R)
#   edgeColor : Graphviz colour for edges
#   suffix    : output filename suffix  (_cc / _cg / _res)
# ---------------------------------------------------------------------------
proc renderElementGraph {idx elemType edgeLabel edgeColor suffix} {
    global graphH

    regsub {^\s*\*} $idx "N" base
    set fileNm "${base}${suffix}.dot"
    set fileId [open $fileNm w]
    set nodeLinesH [dict create]

    puts $fileId "graph G \{"

    if {![dict exists $graphH $idx]} {
        puts stderr "renderElementGraph: net '$idx' not found in graph"
        puts $fileId "\}"
        close $fileId
        return
    }

    puts $fileId "  DeenKotturi \[shape=box\];"
    set idGraphH [dict get $graphH $idx]

    set connH [dict create]
    if {[dict exists $idGraphH CONN]} {
        set connH [parseConnSection $fileId [dict get $idGraphH CONN]]
    }

    if {[dict exists $idGraphH $elemType]} {
        dict for {leftNode rightNodeSub} [dict get $idGraphH $elemType] {
            dict for {rightNode value} $rightNodeSub {
                set lNew [normalizeNode $leftNode]
                set rNew [normalizeNode $rightNode]
                puts $fileId "// $leftNode  [getNetName $leftNode]"
                puts $fileId "// $rightNode [getNetName $rightNode]"
                dict set nodeLinesH $lNew [nodeAttrs $lNew $leftNode  $connH]
                dict set nodeLinesH $rNew [nodeAttrs $rNew $rightNode $connH]
                puts $fileId "  \"$lNew\"--\"$rNew\" \[label=\"${edgeLabel}:$value\", color=$edgeColor\];"
                puts $fileId "  // ======================="
            }
        }
    }

    dict for {node attrs} $nodeLinesH {
        puts $fileId "  $node $attrs"
    }
    puts $fileId "\}"
    close $fileId
    renderDotOutputs $fileNm
}

# ---------------------------------------------------------------------------
# Public single-type graph procs (thin wrappers around renderElementGraph)
# ---------------------------------------------------------------------------
proc printIdxCcGraph  {idx} { renderElementGraph $idx CCAP  CC green _cc  }
proc printIdxCgGraph  {idx} { renderElementGraph $idx CGCAP GC blue  _cg  }
proc printIdxResGraph {idx} { renderElementGraph $idx RES   R  red   _res }

# ---------------------------------------------------------------------------
# printIdxGraph -- combined undirected graph: CCAP + CGCAP + RES in one file.
# ---------------------------------------------------------------------------
proc printIdxGraph {idx} {
    global graphH

    regsub {^\s*\*} $idx "N" base
    set fileNm "${base}.dot"
    set fileId [open $fileNm w]
    set nodeLinesH [dict create]

    puts $fileId "graph G \{"

    if {![dict exists $graphH $idx]} {
        puts stderr "printIdxGraph: net '$idx' not found in graph"
        puts $fileId "\}"
        close $fileId
        return
    }

    puts $fileId "  DeenKotturi \[shape=box\];"
    set idGraphH [dict get $graphH $idx]

    set connH [dict create]
    if {[dict exists $idGraphH CONN]} {
        set connH [parseConnSection $fileId [dict get $idGraphH CONN]]
    }

    foreach {elemType edgeLabel edgeColor} {
        CCAP  CC  green
        CGCAP GC  blue
        RES   R   red
    } {
        if {![dict exists $idGraphH $elemType]} { continue }
        dict for {leftNode rightNodeSub} [dict get $idGraphH $elemType] {
            dict for {rightNode value} $rightNodeSub {
                set lNew [normalizeNode $leftNode]
                set rNew [normalizeNode $rightNode]
                puts $fileId "// $leftNode  [getNetName $leftNode]"
                puts $fileId "// $rightNode [getNetName $rightNode]"
                dict set nodeLinesH $lNew [nodeAttrs $lNew $leftNode  $connH]
                dict set nodeLinesH $rNew [nodeAttrs $rNew $rightNode $connH]
                puts $fileId "  \"$lNew\"--\"$rNew\" \[label=\"${edgeLabel}:$value\", color=$edgeColor\];"
                puts $fileId "  // ======================="
            }
        }
    }

    dict for {node attrs} $nodeLinesH {
        puts $fileId "  $node $attrs"
    }
    puts $fileId "\}"
    close $fileId
    renderDotOutputs $fileNm
}

# ---------------------------------------------------------------------------
# getNetName -- resolve a SPEF node token to its mapped hierarchical net name.
# ---------------------------------------------------------------------------
proc getNetName {spefNode} {
    global nameMapH
    if {[regexp {^(\S+):(\S+)$} $spefNode -> netIdx fracture]} {
        if {[dict exists $nameMapH $netIdx]} {
            return "[dict get $nameMapH $netIdx]:$fracture"
        }
    } elseif {[regexp {^(\S+)$} $spefNode -> netIdx]} {
        if {[dict exists $nameMapH $netIdx]} {
            return [dict get $nameMapH $netIdx]
        }
    }
    return $spefNode
}

# ---------------------------------------------------------------------------
# getNetFromIdx / getIdxFromNet -- bidirectional name-map lookups
# ---------------------------------------------------------------------------
proc getNetFromIdx {idx} {
    global nameMapH
    if {[dict exists $nameMapH $idx]} { return [dict get $nameMapH $idx] }
    return ""
}

proc getIdxFromNet {net} {
    global nameMapH
    return [dict keys [dict filter $nameMapH value $net]]
}

# ---------------------------------------------------------------------------
# createGraph -- parse a SPEF file into nameMapH and graphH.
#   Supports plain and gzip-compressed (.gz) SPEF files.
# ---------------------------------------------------------------------------
proc createGraph {spef} {
    global nameMapH graphH

    set nameMapH [dict create]
    set graphH   [dict create]

    if {![file exists $spef]} {
        error "SPEF file not found: $spef"
    }

    set fileNm [file normalize $spef]
    if {[regexp {\.gz$} $fileNm]} {
        set fId [open "|zcat $fileNm"]
    } else {
        set fId [open $fileNm r]
    }

    set inNameMap 0
    set inDNet    0
    set inConn    0
    set inCap     0
    set inRes     0
    set netIdx    ""

    while {[gets $fId line] >= 0} {

        # ---- NAME_MAP section ----------------------------------------
        if {[regexp {^\s*\*NAME_MAP\s*$} $line]} {
            set inNameMap 1
            continue
        }
        if {$inNameMap} {
            if {[regexp {^\s*\*PORTS\s*$} $line]} {
                set inNameMap 0
            } elseif {[regexp {^\s*(\S+)\s+(\S+)\s*$} $line -> idx nm]} {
                dict set nameMapH $idx $nm
            }
            continue
        }

        # ---- D_NET header --------------------------------------------
        if {[regexp {^\s*\*D_NET\s+(\S+)\s+(\S+)\s*$} $line -> ni tcap]} {
            set netIdx $ni
            set inDNet 1
            dict set graphH $netIdx TCAP $tcap
            continue
        }

        if {!$inDNet} { continue }

        # ---- Section-transition keywords -----------------------------
        if {[regexp {^\s*\*CONN\s*$} $line]} { set inConn 1 ; continue }
        if {[regexp {^\s*\*CAP\s*$}  $line]} { set inConn 0 ; set inCap 1 ; continue }
        if {[regexp {^\s*\*RES\s*$}  $line]} { set inCap  0 ; set inRes 1 ; continue }
        if {[regexp {^\s*\*END\s*$}  $line]} {
            set inDNet 0 ; set inConn 0 ; set inCap 0 ; set inRes 0
            continue
        }

        if {[regexp {^\s*$} $line]} { continue }

        # ---- Data lines ----------------------------------------------
        if {$inConn} {
            dict set graphH $netIdx CONN $line 1

        } elseif {$inCap} {
            # 4-token: coupling cap  (element# leftNode rightNode value)
            if {[regexp {^\s*\S+\s+(\S+)\s+(\S+)\s+(\S+)\s*$} $line -> lNode rNode val]} {
                dict set graphH $netIdx CCAP  $lNode $rNode $val
            # 3-token: cap to ground (element# node value)
            } elseif {[regexp {^\s*\S+\s+(\S+)\s+(\S+)\s*$} $line -> lNode val]} {
                dict set graphH $netIdx CGCAP $lNode GND    $val
            }

        } elseif {$inRes} {
            if {[regexp {^\s*\S+\s+(\S+)\s+(\S+)\s+(\S+)\s*$} $line -> lNode rNode val]} {
                dict set graphH $netIdx RES $lNode $rNode $val
            }
        }
    }
    close $fId
}
