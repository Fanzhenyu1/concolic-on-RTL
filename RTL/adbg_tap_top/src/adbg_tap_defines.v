//////////////////////////////////////////////////////////////////////
////                                                              ////
////  tap_defines.v                                               ////
////                                                              ////
////                                                              ////
////  This file is part of the JTAG Test Access Port (TAP)        ////
////  http://www.opencores.org/projects/jtag/                     ////
////                                                              ////
////  Author(s):                                                  ////
////       Igor Mohor (igorm@opencores.org)                       ////
////                                                              ////
////                                                              ////
////  All additional information is avaliable in the README.txt   ////
////  file.                                                       ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2000 - 2003 Authors                            ////
////                                                              ////
//// This source file may be used and distributed without         ////
//// restriction provided that this copyright statement is not    ////
//// removed from the file and that any derivative work contains  ////
//// the original copyright notice and the associated disclaimer. ////
////                                                              ////
//// This source file is free software; you can redistribute it   ////
//// and/or modify it under the terms of the GNU Lesser General   ////
//// Public License as published by the Free Software Foundation; ////
//// either version 2.1 of the License, or (at your option) any   ////
//// later version.                                               ////
////                                                              ////
//// This source is distributed in the hope that it will be       ////
//// useful, but WITHOUT ANY WARRANTY; without even the implied   ////
//// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR      ////
//// PURPOSE.  See the GNU Lesser General Public License for more ////
//// details.                                                     ////
////                                                              ////
//// You should have received a copy of the GNU Lesser General    ////
//// Public License along with this source; if not, download it   ////
//// from http://www.opencores.org/lgpl.shtml                     ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
//
// CVS Revision History
//
// $Log: tap_defines.v,v $
// Revision 1.1.1.1  2008-05-14 12:07:33  Nathan
// Original from OpenCores
//
// Revision 1.3  2004/03/02 17:39:45  mohor
// IDCODE_VALUE changed to Flextronics ID.
//
// Revision 1.2  2004/01/27 10:00:33  mohor
// Unused registers removed.
//
// Revision 1.1  2003/12/23 14:52:14  mohor
// Directory structure changed. New version of TAP.
//
//
//


// Define IDCODE Value
`define IDCODE_VALUE  32'h249511c3
// 0001             version
// 0100100101010001 part number (IQ)
// 00011100001      manufacturer id (flextronics)
// 1                required by standard

// Length of the Instruction register
`define	IR_LENGTH	4

// Supported Instructions
`define EXTEST          4'b0000
`define SAMPLE_PRELOAD  4'b0001
`define IDCODE          4'b0010
`define DEBUG           4'b1000
`define MBIST           4'b1001
`define BYPASS          4'b1111

`define STATE_test_logic_reset 4'hF
`define STATE_run_test_idle    4'hC
`define STATE_select_dr_scan   4'h7
`define STATE_capture_dr       4'h6
`define STATE_shift_dr         4'h2
`define STATE_exit1_dr         4'h1
`define STATE_pause_dr         4'h3
`define STATE_exit2_dr         4'h0
`define STATE_update_dr        4'h5
`define STATE_select_ir_scan   4'h4
`define STATE_capture_ir       4'hE
`define STATE_shift_ir         4'hA
`define STATE_exit1_ir         4'h9
`define STATE_pause_ir         4'hB
`define STATE_exit2_ir         4'h8
`define STATE_update_ir        4'hD
