# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
import random

async def execute_multiplication(dut, val_a, val_b):
    """Helper to shift 16-bit inputs in, calculate, and mux 32-bit output out."""
    
    # 1. Shift in 16-bit Operand A (Upper byte, then lower byte)
    dut.ui_in.value = (val_a >> 8) & 0xFF
    dut.uio_in.value = 1  # bit 0: load_a = 1
    await ClockCycles(dut.clk, 1)
    
    dut.ui_in.value = val_a & 0xFF
    dut.uio_in.value = 1  
    await ClockCycles(dut.clk, 1)

    # 2. Shift in 16-bit Operand B
    dut.ui_in.value = (val_b >> 8) & 0xFF
    dut.uio_in.value = 2  # bit 1: load_b = 1
    await ClockCycles(dut.clk, 1)
    
    dut.ui_in.value = val_b & 0xFF
    dut.uio_in.value = 2  
    await ClockCycles(dut.clk, 1)

    # 3. Latch the combinational output into the result register
    dut.uio_in.value = 4  # bit 2: latch_res = 1
    await ClockCycles(dut.clk, 1)

    # 4. Mux the 32-bit result out in four 8-bit chunks
    dut.uio_in.value = 0  # bits 4:3: out_sel = 00
    await ClockCycles(dut.clk, 1)
    byte0 = int(dut.uo_out.value)

    dut.uio_in.value = 8  # bits 4:3: out_sel = 01
    await ClockCycles(dut.clk, 1)
    byte1 = int(dut.uo_out.value)

    dut.uio_in.value = 16 # bits 4:3: out_sel = 10
    await ClockCycles(dut.clk, 1)
    byte2 = int(dut.uo_out.value)

    dut.uio_in.value = 24 # bits 4:3: out_sel = 11
    await ClockCycles(dut.clk, 1)
    byte3 = int(dut.uo_out.value)

    # Reconstruct the 32-bit integer
    return (byte3 << 24) | (byte2 << 16) | (byte1 << 8) | byte0


@cocotb.test()
async def test_multiplier(dut):
    dut._log.info("Start Multiplier Test")

    # Set clock to 20ns (50MHz) to accurately test your STA constraint
    clock = Clock(dut.clk, 20, unit="ns")
    cocotb.start_soon(clock.start())

    # Initialize and Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test edge cases")
    
    # Test maximum 16-bit values (65535 * 65535)
    max_val = 65535
    result = await execute_multiplication(dut, max_val, max_val)
    expected = max_val * max_val
    assert result == expected, f"Max value failed! Expected {expected}, got {result}"

    dut._log.info("Run randomized fuzz testing")

    # Loop through 50 random 16x16 multiplications
    for i in range(50):
        val_a = random.randint(0, 65535)
        val_b = random.randint(0, 65535)

        actual_val = await execute_multiplication(dut, val_a, val_b)
        expected_val = val_a * val_b

        assert actual_val == expected_val, \
            f"Failed on {val_a} * {val_b}: Expected {expected_val}, got {actual_val}"

    dut._log.info("All multiplier tests passed!")
