module b11_tb();

    // Generated top module signals
    reg  clock;
    reg  reset;
    reg  [5:0]x_in = 6'b0;
    reg  stbi = 1'b0;

    wire [5:0]x_out;
    wire [8:0]s_xout;
    // assign s_xout = 9'sb111111;
    // Generated top module instance
    b11 _conc_top_inst(
            .clock     ( clock ),
            .reset     ( reset ),
            .x_in     ( x_in ),
            .stbi     ( stbi ),
            .x_out     ( x_out ));

    // Generated clock pulse
    always begin
        #5 clock = ~clock;
    end
    integer i, seed;
    // Generated initial block
    initial begin
        clock = 1'b0;
        reset = 1'b0;
        x_in = 6'b0;
        stbi = 1'b0;

        #2 clock = 1'b1;
        reset = 1'b1;
        #5 reset = 1'b0;

        for(i= 0; i<1; i++) begin
            #1;
            x_in = $random(seed);
            stbi = $random(seed);
            #9;
            $display("Period %d: x_in = %b, stbi = %b, x_out = %b", i, x_in, stbi, x_out);
        end

        #1;
        x_in = 6'b000010;
        stbi = 1'b0;
        #9;
        $display("x_in = %b, stbi = %b, x_out = %b", x_in, stbi, x_out);

        seed = $time;
        for(i= 2; i<12; i++) begin
            #1;
            x_in = $random(seed);
            stbi = $random(seed);
            #9;
            $display("Period %d: x_in = %b, stbi = %b, x_out = %b", i, x_in, stbi, x_out);
        end        

        $finish;
    end

    initial
    begin            
        $dumpfile("wave.vcd");        //生成的vcd文件名称
        $dumpvars(0, b11_tb);    //tb模块名称
    end 
endmodule