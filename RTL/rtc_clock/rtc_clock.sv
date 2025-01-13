
module	rtc_clock(
	input  logic        clk_i,
	input  logic        rstn_i,

	input  logic        clock_update_i,
	output logic [21:0] clock_o,
	input  logic [21:0] clock_i,

	input  logic  [14:0] init_sec_cnt_i,

	output logic        update_day_o
);

	logic [7:0] r_seconds;
	logic [7:0] r_minutes;
	logic [6:0] r_hours;

	logic [7:0] s_seconds;
	logic [7:0] s_minutes;
	logic [6:0] s_hours;

	logic [14:0] r_sec_counter;

	logic s_update_seconds;
	logic s_update_minutes;
	logic s_update_hours;

	assign s_seconds = clock_i[7:0];
	assign s_minutes = clock_i[15:8];
	assign s_hours   = clock_i[21:16];

	assign s_update_seconds = r_sec_counter == 15'h7FFF;
	assign s_update_minutes = s_update_seconds & (r_seconds == 8'h59);
	assign s_update_hours   = s_update_minutes & (r_minutes == 8'h59);

	assign update_day_o   = s_update_hours & (r_hours == 6'h23);
	assign clock_o        = {r_hours,r_minutes,r_seconds};


    always @ (posedge clk_i or negedge rstn_i)
    begin
        if(~rstn_i)
            r_sec_counter <= 'h0;
        else
        begin
        	if (clock_update_i)
        		r_sec_counter <= init_sec_cnt_i;
        	else
            	r_sec_counter <= r_sec_counter + 1;
        end
    end

	always @(posedge clk_i or negedge rstn_i) begin
		if(~rstn_i)
			r_seconds <= 0;
		else begin
			if (clock_update_i)
				r_seconds <= s_seconds;
			else if (s_update_seconds) begin // advance the seconds
					if (r_seconds[7:4] <= 4'h4 && r_seconds[3:0] == 4'h9) begin
						r_seconds[7:4] <= r_seconds[7:4] + 4'h1;
						r_seconds[3:0] <= 4'h0;
					end	else if (r_seconds[7:4] ==4'h5 && r_seconds[3:0] == 4'h9) begin
						r_seconds[7:4] <= 4'h0;
						r_seconds[3:0] <= 4'h0;
					end else
						r_seconds <= r_seconds + 8'h1;
				end
		end
	end

	always @(posedge clk_i or negedge rstn_i) begin
		if(~rstn_i)
			r_minutes <= 0;
		else begin
			if (clock_update_i)
				r_minutes <= s_minutes;
			else if (s_update_minutes) begin // advance the minutes
					if (r_minutes[7:4] <= 4'h4 && r_minutes[3:0] == 4'h9) begin
						r_minutes[7:4] <= r_minutes[7:4] + 4'h1;
						r_minutes[3:0] <= 4'h0;
					end	else if (r_minutes[7:4] ==4'h5 && r_minutes[3:0] == 4'h9) begin
						r_minutes[7:4] <= 4'h0;
						r_minutes[3:0] <= 4'h0;
					end else
						r_minutes <= r_minutes + 8'h1;
				end
		end
	end

	always @(posedge clk_i or negedge rstn_i) begin
		if(~rstn_i)
			r_hours <= 0;
		else begin
			if (clock_update_i)
				r_hours <= s_hours;
			else if (s_update_hours) begin // advance the hours
					if (r_hours[5:4] <= 2'h1 && r_hours[3:0] == 4'h9) begin
						r_hours[5:4] <= r_hours[5:4] + 2'h1;
						r_hours[3:0] <= 4'h0;
					end else if (r_hours[5:0] == 6'h24) begin
						r_hours <= 6'h00;
					end else
						r_hours <= r_hours + 6'h1;
				end
		end
	end

// property clock_max;
// 	@(posedge clk_i) disable iff (!rstn_i) (clock_o <= 22'h235959);
// endproperty

// property update_day_flag;
// 	@(posedge clk_i) disable iff (!rstn_i) (clock_o == 22'h235959 && s_update_seconds && ~clock_update_i)|-> update_day_o;
// endproperty

// assert property (clock_max);
// assert property (update_day_flag);
endmodule
