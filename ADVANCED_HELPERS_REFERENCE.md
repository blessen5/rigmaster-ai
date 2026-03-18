# Advanced Compatibility Analysis - Quick Reference Guide

## Quick Function Reference

### Numeric Extraction
```python
extract_numeric_value(text, pattern=r'(\d+(?:\.\d+)?)')
# Returns first number found in text, default 0
# Usage: extract_numeric_value("RTX 4090 12GB") → 4090 (first number found)
```

## CPU Analysis Functions

```python
infer_cpu_tdp(doc) → float
# Returns TDP in watts
# Example: infer_cpu_tdp(cpu_doc) → 140

infer_cpu_voltage(doc) → float | None  
# Returns core voltage (e.g., 1.35V)
# Example: infer_cpu_voltage(cpu_doc) → 1.35

infer_cpu_base_clock(doc) → float
# Returns base frequency in GHz
# Example: infer_cpu_base_clock(cpu_doc) → 3.4

infer_cpu_boost_clock(doc) → float
# Returns maximum turbo frequency in GHz
# Example: infer_cpu_boost_clock(cpu_doc) → 5.6

infer_cpu_core_count(doc) → int
# Returns number of cores
# Example: infer_cpu_core_count(cpu_doc) → 12
```

## GPU Analysis Functions

```python
infer_gpu_vram(doc) → float
# Returns VRAM in GB
# Example: infer_gpu_vram(gpu_doc) → 12

infer_gpu_bus_width(doc) → int
# Returns memory bus width in bits
# Example: infer_gpu_bus_width(gpu_doc) → 192

infer_gpu_tdp(doc) → float
# Returns GPU power consumption in watts
# Example: infer_gpu_tdp(gpu_doc) → 320
```

## RAM Analysis Functions

```python
infer_ram_voltage(doc) → float | None
# Returns operating voltage (e.g., 1.25V)
# Example: infer_ram_voltage(ram_doc) → 1.25

infer_ram_speed(doc) → float
# Returns frequency in MHz
# Example: infer_ram_speed(ram_doc) → 6000

infer_ram_timing(doc) → int
# Returns CAS latency (CL value)
# Example: infer_ram_timing(ram_doc) → 30
```

## Motherboard Analysis Functions

```python
infer_mobo_vrm_phases(doc) → int
# Estimates VRM phase count (for power delivery assessment)
# Range: 8-24 phases typical
# Example: infer_mobo_vrm_phases(mobo_doc) → 18

infer_mobo_pcie_lanes(doc) → int
# Calculates estimated available PCIe lanes
# Typical: 16-28 lanes
# Example: infer_mobo_pcie_lanes(mobo_doc) → 24

extract_usb_ports(doc) → dict
# Returns USB port configuration
# Returns: {'usb2': int, 'usb3': int, 'usb3_1': int, 'usb3_2': int, 'type_c': int}
# Example: extract_usb_ports(mobo_doc) → 
#   {'usb2': 2, 'usb3': 4, 'usb3_1': 0, 'usb3_2': 2, 'type_c': 2}

infer_audio_codec(doc) → str
# Returns audio quality descriptor
# Returns: 'High-End', 'Realtek Standard', 'Standard'
# Example: infer_audio_codec(mobo_doc) → 'Realtek Standard'
```

## Storage Analysis Functions

```python
infer_storage_interface(doc) → str
# Returns storage type
# Returns: 'NVMe', 'SATA', 'HDD', 'UNKNOWN'
# Example: infer_storage_interface(storage_doc) → 'NVMe'

infer_storage_protocol(doc) → str | None
# Returns protocol with PCIe generation
# Returns: 'NVMe PCIe 5.0', 'NVMe PCIe 4.0', 'SATA', None
# Example: infer_storage_protocol(storage_doc) → 'NVMe PCIe 4.0'

infer_storage_raid_support(doc) → bool
# Checks if drive supports RAID configurations
# Example: infer_storage_raid_support(storage_doc) → True
```

## Power Supply Analysis Functions

```python
infer_psu_efficiency_rating(doc) → str
# Returns efficiency rating
# Returns: 'Titanium', 'Platinum', 'Gold', 'Silver', '80+'
# Example: infer_psu_efficiency_rating(psu_doc) → 'Gold'

infer_psu_modularity(doc) → str
# Returns modularity type
# Returns: 'Fully Modular', 'Semi-Modular', 'Non-Modular'
# Example: infer_psu_modularity(psu_doc) → 'Fully Modular'

infer_psu_connector_support(doc) → str
# Returns connector type support
# Returns: 'ATX 3.0 Ready (12V-2x6)', '12VAUX'
# Example: infer_psu_connector_support(psu_doc) → 'ATX 3.0 Ready (12V-2x6)'
```

## Case & Thermal Functions

```python
infer_case_airflow_design(doc) → str
# Returns case cooling design type
# Returns: 'Open-Frame', 'Optimized Flow', 'Standard'
# Example: infer_case_airflow_design(case_doc) → 'Optimized Flow'

infer_os_compatibility(cpu_doc, mobo_doc, ram_doc) → list
# Returns list of OS compatibility issue strings
# Example: infer_os_compatibility(cpu, mobo, ram) → 
#   ['OS Compat: AM4 Ryzen may need BIOS update for Win11 TPM support.']
```

## Usage Examples

### Example 1: Comprehensive CPU Assessment
```python
if cpu:
    tdp = infer_cpu_tdp(cpu)
    voltage = infer_cpu_voltage(cpu)
    cores = infer_cpu_core_count(cpu)
    base_clock = infer_cpu_base_clock(cpu)
    boost_clock = infer_cpu_boost_clock(cpu)
    
    print(f"CPU: {tdp}W TDP, {cores} cores, {base_clock:.1f}-{boost_clock:.1f}GHz, {voltage}V")
    # Output: CPU: 140W TDP, 12 cores, 3.4-5.6GHz, 1.35V
```

### Example 2: GPU-Mobo Compatibility Check
```python
if gpu and mobo:
    gpu_vram = infer_gpu_vram(gpu)
    mobo_lanes = infer_mobo_pcie_lanes(mobo)
    
    if gpu_vram > 12 and mobo_lanes < 16:
        messages.append(f"GPU Performance: {gpu_vram}GB GPU on {mobo_lanes} lanes will bottleneck")
```

### Example 3: RAM Stability Assessment
```python
if ram and mobo:
    speed = infer_ram_speed(ram)
    voltage = infer_ram_voltage(ram)
    timing = infer_ram_timing(ram)
    
    if voltage > 1.25:
        messages.append(f"RAM Tuning: {speed}MHz @ {voltage}V requires BIOS XMP profile")
```

### Example 4: Thermal Analysis
```python
if cpu and cooler and case:
    cpu_tdp = infer_cpu_tdp(cpu)
    cooler_height = parse_dimension_mm(cooler, ['height'])
    case_max = parse_dimension_mm(case, ['max_cpucooler_height'])
    
    percent_free = ((case_max - cooler_height) / case_max) * 100
    if percent_free < 10:
        messages.append(f"Thermal Alert: Only {percent_free:.0f}% cooler clearance!")
```

## Important Notes

- All functions gracefully handle `None` and missing data
- Numeric values default to `0` when not found
- String comparisons use `normalize()` for case-insensitive matching
- Functions prioritize explicit fields, then use heuristics from component names
- Most functions have fallback/default values for incomplete data

## Integration with Validation Logic

These functions are automatically called in `run_validation_logic()` sections 11-20:

| Section | Functions | Purpose |
|---------|-----------|---------|
| 11 | CPU helpers | Power delivery, voltage, clock analysis |
| 12 | GPU helpers | VRAM, bandwidth, power requirements |
| 13 | RAM helpers | Voltage, speed, timing verification |
| 14 | Mobo helpers | PCIe, USB, audio analysis |
| 15 | Storage helpers | Protocol, RAID capability |
| 16 | PSU helpers | Efficiency, modularity, connectors |
| 17 | Thermal helpers | Cooler/case clearance, airflow |
| 18 | Connectivity helpers | USB port assessment |
| 19 | OS helpers | Platform compatibility |

---

**File Modified:** `app.py`  
**Functions Added:** 25+ new helper functions  
**Lines of Code:** ~400 new lines of validation logic  
**Backward Compatible:** Yes - all original checks retained
