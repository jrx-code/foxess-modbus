"""The H3 fault words (31044, 31045, 31047-31051), bit by bit."""

from __future__ import annotations

# One tuple per fault word, least significant bit first. None is a reserved bit.
FAULT_BITS: tuple[tuple[str | None, ...], ...] = (
    (
        "Grid Lost Fault",
        "Grid Voltage Fault",
        "Grid Frequency Fault",
        "Grid 10min Voltage Fault",
        "EPS Voltage Fault",
        "Software Inverter Over-current Fault",
        "DCI Fault",
        None,
        "Hardware Inverter Over-current Fault",
        "Software Bus Voltage Fault",
        "Battery Voltage Fault",
        "Software Battery Over-current Fault",
        "Isolation Fault",
        "Residual Over-current Fault",
        "PV Voltage Fault",
        "Software PV Over-current Fault",
    ),
    (
        "Inverter Temperature Fault",
        "Ground Connection Fault",
        "Inverter Overload Fault",
        "EPS Overload Fault",
        "Battery Power Low Fault",
        "Hardware Bus Voltage Fault",
        "Hardware PV Over-current Fault",
        "Hardware Battery Over-current Fault",
        "SCI Fault",
        "Master SPI Fault",
        "BMS Lost Fault",
    ),
    (
        "Master Sample Detection Fault",
        "Residual Current Detection Fault",
        "Inverter EEPROM Fault",
        "PV Connection Direction Fault",
        "Battery Relay Open",
        "Battery Relay Short Circuit",
        "Battery Buck Fault",
        "Battery Boost Fault",
        "EPS Relay Fault",
        "Short EPS Load Fault",
        "Battery Connection Direction Fault",
        "Main Relay Open",
        "S1 Close Fault",
        "S2 Close Fault",
        "M1 Close Fault",
        "M2 Close Fault",
    ),
    (
        "Grid Voltage Consistency Fault",
        "Grid Frequency Consistency Fault",
        "DCI Consistency Fault",
        "Residual Current Consistency Fault",
        None,
        None,
        "Slave SPI Fault",
        "Slave Sample Fault",
        "RDSP SPI Fault",
        "RDSP Sample Fault",
    ),
    (
        "ARM EEPROM Fault",
        "Meter Lost Fault",
    ),
    (
        "BMS External Fault",
        "BMS Internal Fault",
        "Battery Over-voltage",
        "Battery under-voltage",
        "BMS Charge Over-current",
        "BMS Discharge Over-current",
        "BMS Over-temperature",
        "BMS Under-temperature",
        "BMS Cell Imbalance",
        "BMS Hardware Protection Fault",
        "BMS Circuit Fault",
        "BMS Insulation Fault",
        "BMS Voltage Sensor Fault",
        "BMS Temperature Sensor Fault",
        "BMS Current Sensor Fault",
        "BMS Relay Fault",
    ),
    (
        "BMS Type Mismatch",
        "BMS Version Mismatch",
        "BMS Manufacturer Mismatch",
        "BMS Software/Hardware Mismatch",
        "BMS Master/Slave Mismatch",
        "BMS Charge Request Not Acknowledged",
        "BMS Supply Fault",
        None,
        "BMS Self Check Fault",
        "BMS Cell Temperature Difference Fault",
        "BMS Cell Voltage Break Line Fault",
        "BMS Self Check Voltage Mismatch Fault",
        "BMS Precharge Fault",
        "BMS Self Check HVB Fault",
        "BMS Self Check Pack Current Fault",
        "BMS Self Check Sys Mismatch Fault",
    ),
)


def active_faults(words: list[int]) -> list[str]:
    """The names of the set bits across the fault words.

    A set bit with no known name reads as ``Unknown fault <word>.<bit>``.
    """
    faults: list[str] = []
    for index, (word, names) in enumerate(zip(words, FAULT_BITS, strict=True)):
        for bit in range(16):
            if not word & (1 << bit):
                continue
            name = names[bit] if bit < len(names) else None
            faults.append(name or f"Unknown fault {index + 1}.{bit}")
    return faults
