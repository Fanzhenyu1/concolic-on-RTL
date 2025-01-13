module case1_tb();

    // Generated top module signals
    reg  clk;
    reg  rst;
    reg  [7:0]in = 8'b0;


    wire [7:0]out;

    // Generated top module instance
    case1 _conc_top_inst(
            .clk     ( clk ),
            .rst     ( rst ),
            .in     ( in ),

            .out     ( out ));

    // Generated clk pulse
    always begin
        #5 clk = ~clk;
    end
    integer i, seed;
    // Generated initial block
    initial begin
        clk = 1'b0;
        rst = 1'b0;
        in = 8'b0;


        #2 clk = 1'b1;
        rst = 1'b1;
        #5 rst = 1'b0;

        #1 in = 8'h26;
        #9;
        $display("Period 0: in = %b, out = %b", in, out);

        #1 in = 8'hf5;
        #9;
        $display("Period 1: in = %b, out = %b", in, out);

        #1 in = 8'h6e;
        #9;
        $display("Period 2: in = %b, out = %b", in, out);        

        for(i= 3; i<20; i++) begin
            #1;
            in = $random(seed);

            #9;
            $display("Period %d: in = %b, out = %b", i, in, out);
        end


        $finish;
    end

    initial
    begin            
        $dumpfile("wave.vcd");        //生成的vcd文件名称
        $dumpvars(0, case1_tb);    //tb模块名称
    end 
endmodule