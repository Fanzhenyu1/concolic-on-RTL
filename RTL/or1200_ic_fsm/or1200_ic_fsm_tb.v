`timescale 1ns/1ps
module or1200_ic_fsm_tb();
reg clk;
reg rst;
reg ic_en;
reg icqmem_cycstb_i;
reg icqmem_ci_i;
reg tagcomp_miss;
reg biudata_valid;
reg biudata_error;
reg [31:0] start_addr;
wire [31:0] saved_addr;
wire [3:0] icram_we;
wire biu_read;
wire first_hit_ack;
wire first_miss_ack;
wire first_miss_err;
wire burst;
wire tag_we;

// 实例化待测模块
or1200_ic_fsm uut (
    .clk(clk),
    .rst(rst),
    .ic_en(ic_en),
    .icqmem_cycstb_i(icqmem_cycstb_i),
    .icqmem_ci_i(icqmem_ci_i),
    .tagcomp_miss(tagcomp_miss),
    .biudata_valid(biudata_valid),
    .biudata_error(biudata_error),
    .start_addr(start_addr),
    .saved_addr(saved_addr),
    .icram_we(icram_we),
    .biu_read(biu_read),
    .first_hit_ack(first_hit_ack),
    .first_miss_ack(first_miss_ack),
    .first_miss_err(first_miss_err),
    .burst(burst),
    .tag_we(tag_we)
    );

// 时钟激励
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

// 复位激励
initial begin
    rst = 1;
    #10;
    rst = 0;
end

integer i;
initial begin
    ic_en = 0;
    icqmem_cycstb_i = 0;
    icqmem_ci_i = 0;
    tagcomp_miss = 0;
    biudata_valid = 0;
    biudata_error = 0;
    start_addr = 0;
    #10;
    for(i = 0; i < 100; i = i + 1) begin
        $display("********Period %d********", i);
        ic_en = $random & 1'd1;
        icqmem_cycstb_i = $random & 1'd1;
        icqmem_ci_i = $random & 1'd1;
        tagcomp_miss = $random & 1'd1;
        biudata_valid = $random & 1'd1;
        biudata_error = $random & 1'd1;
        start_addr = $random;
        if(i == 13) begin ic_en = 1; tagcomp_miss = 1; biudata_valid = 1; biudata_error = 0; icqmem_cycstb_i = 1; icqmem_ci_i = 0; end

        if(i == 15) begin ic_en = 1; biudata_valid = 1; end
        if(i == 16) begin ic_en = 1; biudata_valid = 1; end

        // if(i == 50) begin ic_en = 1; icqmem_cycstb_i = 0; tagcomp_miss = 0; biudata_error = 0; biudata_valid = 0; end

        #10;        
    end
    $finish;
end
initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, or1200_ic_fsm_tb);
end

endmodule
