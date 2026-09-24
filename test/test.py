# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
import random

@cocotb.test()
async def test_multiplier(dut):
    dut._log.info("Start Multiplier Test")

    # Set the clock period to 20 ns (50 MHz) to match your timing constraint
    clock = Clock(dut.clk, 20, unit="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test edge cases")
    
    # Optional: Test specifically for max values (255 * 255 = 65025)
    dut.ui_in.value = 255
    dut.uio_in.value = 255
    await ClockCycles(dut.clk, 1) # Combinational logic takes 1 clock cycle to register out
    
    actual_val = (int(dut.uio_out.value) << 8) | int(dut.uo_out.value)
    assert actual_val == 65025, f"Max value failed! Expected 65025, got {actual_val}"

    dut._log.info("Run randomized fuzz testing")

    # Loop through 100 random multiplications
    for i in range(100):
        val_a = random.randint(0, 255)
        val_b = random.randint(0, 255)

        # Drive inputs
        dut.ui_in.value = val_a
        dut.uio_in.value = val_b

        # Wait one cycle for the combinational path to resolve and register
        await ClockCycles(dut.clk, 1)

        # Read output pins and combine the two 8-bit ports into a 16-bit integer
        expected_val = val_a * val_b
        actual_val = (int(dut.uio_out.value) << 8) | int(dut.uo_out.value)

        # Assert halts the testbench and throws an error if timing/logic is wrong
        assert actual_val == expected_val, \
            f"Failed on {val_a} * {val_b}: Expected {expected_val}, got {actual_val}"

    dut._log.info("All multiplier tests passed perfectly!")
