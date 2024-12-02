module case2_tb();

    // Generated top module signals
    reg  clock;
    reg  reset;
    reg  input_a = 1'b0;
    reg  input_b = 1'b0;
    reg  input_c = 1'b0;
    reg  input_d = 1'b0;
    wire [3:0]ooo;
    wire [3:0]out;

    // Generated top module instance
    case2 _conc_top_inst(
            .clk     ( clock ),
            .reset     ( reset ),
            .input_a     ( input_a ),
            .input_b     ( input_b ),
            .input_c     ( input_c ),
            .input_d     ( input_d ),
            .ooo     ( ooo ),
            .out     ( out ));

    // Generated internal use signals
    reg  [31:0] _conc_pc;
    reg  [3:0] _conc_opcode;
    reg  [3:0] _conc_ram[0:10];


    // Generated clock pulse
    always begin
        #5 clock = ~clock;
    end

    // Generated program counter
    always @(posedge clock) begin
        _conc_opcode = _conc_ram[_conc_pc];
        input_a <= #1 _conc_opcode[3];
        input_b <= #1 _conc_opcode[2];
        input_c <= #1 _conc_opcode[1];
        input_d <= #1 _conc_opcode[0];
        $strobe(";_C %d", _conc_pc);
        _conc_pc <= #2 _conc_pc + 32'b1;
    end

    // Generated initial block
    initial begin
        clock = 1'b0;
        reset = 1'b0;
        _conc_pc = 32'b0;
        $readmemb("data.mem", _conc_ram);
        #2 clock = 1'b1;
        reset = 1'b1;
        #5 reset = 1'b0;
        #100 $finish;
    end

    initial
    begin            
        $dumpfile("wave.vcd");        //生成的vcd文件名称
        $dumpvars(0, case2_tb);    //tb模块名称
    end 
endmodule