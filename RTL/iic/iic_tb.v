`timescale 1ns/1ps
module iic_tb();
reg wb_clk_i;
reg rst_i;
reg [2:0] wb_adr_i;
reg [7:0] wb_dat_i;
wire [7:0] wb_dat_o;
reg wb_we_i;
reg wb_stb_i;
reg wb_cyc_i;
wire wb_ack_o;
wire wb_inta_o;
reg scl_pad_i;
wire scl_pad_o;
wire scl_padoen_o;
reg sda_pad_i;
wire sda_pad_o;
wire sda_padoen_o;

// 实例化待测模块
i2c_master_top uut (
    .wb_clk_i(wb_clk_i),
    .rst_i(rst_i),
    .wb_adr_i(wb_adr_i),
    .wb_dat_i(wb_dat_i),
    .wb_dat_o(wb_dat_o),
    .wb_we_i(wb_we_i),
    .wb_stb_i(wb_stb_i),
    .wb_cyc_i(wb_cyc_i),
    .wb_ack_o(wb_ack_o),
    .wb_inta_o(wb_inta_o),
    .scl_pad_i(scl_pad_i),
    .scl_pad_o(scl_pad_o),
    .scl_padoen_o(scl_padoen_o),
    .sda_pad_i(sda_pad_i),
    .sda_pad_o(sda_pad_o),
    .sda_padoen_o(sda_padoen_o)
    );

// 时钟激励
initial begin
    wb_clk_i = 0;
    forever #5 wb_clk_i = ~wb_clk_i;
end

// 复位激励
initial begin
    rst_i = 0;
    #10;
    rst_i = 1;
end

integer i;
initial begin
    wb_adr_i = 0;
    wb_dat_i = 0;
    wb_we_i = 0;
    wb_stb_i = 0;
    wb_cyc_i = 0;
    scl_pad_i = 0;
    sda_pad_i = 0;
    #10;
    for(i = 0; i < 1000; i = i + 1) begin
        $display("********Period %d********", i);
        wb_adr_i = $random & 3'd7;
        wb_dat_i = $random & 8'd255;
        wb_we_i = $random & 1'd1;
        wb_stb_i = $random & 1'd1;
        wb_cyc_i = $random & 1'd1;
        scl_pad_i = $random & 1'd1;
        sda_pad_i = $random & 1'd1;
        if (i == 141) begin wb_dat_i[7:4] = 4'b0100;  end

        if (i >= 754 && i < 850) begin sda_pad_i = 1'b1;  end
        if (i == 776) begin wb_dat_i[7] = 1'b0;  end
        if (i == 777) begin wb_dat_i[7] = 1'b0;  end

        if (i == 817) begin wb_adr_i = 3'b010; wb_dat_i[7] = 1'b1;  end
        if (i == 821) begin wb_adr_i = 3'b100; wb_dat_i[6] = 1'b1; end
        if (i == 831) begin wb_dat_i[7] = 1'b0; wb_adr_i = 3'b010;  end

        if (i >= 855 && i < 925) begin sda_pad_i = 1'b1;  end

        #10;
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, iic_tb);
end

endmodule
