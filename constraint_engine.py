import os
import json
from datetime import datetime

# CONFLICT SEVERITY SCALE
SEVERITY = {
    "INCOMPATIBLE": 3,  # Build will literally fail or not fit.
    "WARNING": 2,       # Builds will work, but requires modification (e.g. BIOS update) or near limits.
    "SUBOPTIMAL": 1,    # Building will work fine, but suboptimal (bottlenecks, sync mismatch).
    "OPTIMAL": 0        # No conflicts.
}

class RelationalConstraintEngine:
    """
    RigMaster AI - Advanced Relational Constraint Engine
    Responsible for volumetric, electrical, logical, and healing validation.
    """
    def __init__(self, build_parts):
        """
        build_parts: dictionary of category: document
        """
        self.parts = build_parts
        self.conflicts = []

    def validate_full_build(self):
        """
        Main entry point for re-validation. 
        Calls recursive validation logic for every changed part.
        """
        self.conflicts = []
        
        # 0. BASIC CONSTRAINTS (SOCKET, RAM GEN, FORM FACTOR)
        self._check_basic_constraints()

        # 1. VOLUMETRIC 3D VALIDATION
        self._check_volumetric_clearance()
        
        # 2. ELECTRICAL & TRANSIENT MAPPING
        self._check_electrical_adequacy()
        
        # 3. PIN & HEADER MATRIXING
        self._check_header_connectivity()
        
        # 4. BOTTLENECK & FIRMWARE
        self._check_logical_compatibility()
        
        # 5. ADVANCED HEURISTICS
        self._check_advanced_heuristics()
        
        # 6. PERIPHERALS & ACCESSORIES
        self._check_peripheral_and_accessory_constraints()
        
        # 7. OS
        self._check_os_constraints()
        
        return self.conflicts

    def _check_basic_constraints(self):
        cpu = self.parts.get("cpu")
        mobo = self.parts.get("motherboard")
        ram = self.parts.get("ram")
        case = self.parts.get("case")
        storage = self.parts.get("storage")
        cooler = self.parts.get("cooler")

        # 0.1 CPU vs Motherboard Socket
        if cpu and mobo:
            cpu_socket = cpu.get("logical", {}).get("socket")
            mobo_socket = mobo.get("logical", {}).get("socket")
            if cpu_socket and mobo_socket:
                mobo_sockets = [s.strip() for s in mobo_socket.split('/')]
                if cpu_socket not in mobo_sockets:
                     self._add_conflict("INCOMPATIBLE", f"Socket Mismatch: CPU ({cpu_socket}) does not fit Motherboard ({mobo_socket}).", "motherboard", "socket")

        # 0.2 CPU Cooler Socket
        if cooler and mobo:
            cooler_sockets = cooler.get("logical", {}).get("socket") # it's a list or string of supported
            mobo_socket = mobo.get("logical", {}).get("socket")
            if cooler_sockets and mobo_socket:
                if mobo_socket not in str(cooler_sockets).split(','):
                    self._add_conflict("INCOMPATIBLE", f"Cooler Mounting Mismatch: Cooler does not explicitly support {mobo_socket} socket.", "cooler", "socket")
                    
        # 0.3 RAM Generation & Capacity
        if ram and mobo:
            ram_gen = ram.get("logical", {}).get("ram_gen")
            mobo_ram_gen = mobo.get("logical", {}).get("ram_gen")
            if ram_gen and mobo_ram_gen and ram_gen != mobo_ram_gen:
                self._add_conflict("INCOMPATIBLE", f"RAM Type Mismatch: Motherboard requires {mobo_ram_gen} but RAM is {ram_gen}.", "ram", "ram_gen")
            
            # Slots and Capacity
            sticks = ram.get("logical", {}).get("sticks") or 1
            mobo_slots = mobo.get("logical", {}).get("ram_slots") or 4
            if sticks > mobo_slots:
                self._add_conflict("INCOMPATIBLE", f"Memory Slot Conflict: {sticks} sticks selected but Motherboard only has {mobo_slots} slots.", "ram", "sticks")
                
            ram_cap = ram.get("logical", {}).get("capacity") or 0
            mobo_max = mobo.get("logical", {}).get("max_ram") or 0
            if mobo_max and ram_cap > mobo_max:
                self._add_conflict("INCOMPATIBLE", f"Memory Overload: {ram_cap}GB exceeds {mobo_max}GB max limit of Motherboard.", "ram", "capacity")

        # 0.4 Motherboard Form Factor vs Case
        if mobo and case:
            m_ff = mobo.get("logical", {}).get("form_factor")
            c_ffs = case.get("logical", {}).get("supported_form_factors", [])
            if m_ff and c_ffs and m_ff not in c_ffs:
                self._add_conflict("INCOMPATIBLE", f"Form Factor Mismatch: Motherboard ({m_ff}) is not supported by the Case ({', '.join(c_ffs)}).", "motherboard", "form_factor")

        # 0.5 Storage Ports limits
        if storage and mobo:
            is_m2 = storage.get("logical", {}).get("is_m2", False)
            is_sata = storage.get("logical", {}).get("is_sata", False)
            mobo_m2 = mobo.get("logical", {}).get("m2_slots") or 1
            mobo_sata = mobo.get("logical", {}).get("sata_ports") or 4
            
            # Simple heuristic since rigmaster-ui allows 1 storage item to represent "the storage"
            # It might require > slots if multiple bought. We'll simplify to just checking if mobo has 0
            if is_m2 and mobo_m2 < 1:
                self._add_conflict("INCOMPATIBLE", "M.2 SSD selected, but Motherboard has 0 M.2 slots.", "motherboard", "m2_slots")
            if is_sata and mobo_sata < 1:
                self._add_conflict("INCOMPATIBLE", "SATA Drive selected, but Motherboard has 0 SATA ports.", "motherboard", "sata_ports")

        # 0.6 Essential Component Checklist
        critical_categories = ['cpu', 'motherboard', 'ram', 'psu', 'case', 'storage']
        missing = [cat.upper() for cat in critical_categories if not self.parts.get(cat)]
        
        # Check GPU if CPU has no integrated graphics
        if cpu:
            has_igpu = True
            c_name = str(cpu.get('name', '')).upper()
            if 'INTEL' in c_name and '-F' in c_name: has_igpu = False
            elif 'RYZEN' in c_name and 'G' not in c_name and '7000' not in c_name and '9000' not in c_name: has_igpu = False
            
            if not has_igpu and not self.parts.get("gpu"):
                missing.append("GPU")
                self._add_conflict("INCOMPATIBLE", "CPU lacks integrated graphics. A dedicated GPU is required.", "gpu", "missing")
                
        if missing:
             self._add_conflict("WARNING", f"Incomplete Build Strategy: Missing {', '.join(missing)}.", "assembly", "missing")

    def _check_volumetric_clearance(self):
        case = self.parts.get("case")
        if not case: return

        # 1.1 GPU Effective Space
        # Logic: (Case_Max_GPU_Length) - (Front_Radiator_Thickness + Fan_Thickness) = Effective_GPU_Space.
        gpu = self.parts.get("gpu")
        cooler = self.parts.get("cooler")
        if gpu:
            gpu_len = gpu.get("dimensions", {}).get("length") or 0
            case_gpu_max = case.get("clearances", {}).get("gpu_max_length") or 330
            
            rad_offset = 0
            if cooler and "front" in str(cooler.get("mounting", "")).lower():
                rad_offset = (cooler.get("dimensions", {}).get("thickness") or 27) + \
                             (cooler.get("dimensions", {}).get("fan_thickness") or 25)
            
            effective_gpu_space = case_gpu_max - rad_offset
            if gpu_len > effective_gpu_space:
                self._add_conflict(
                    "INCOMPATIBLE", 
                    f"GPU ({gpu_len}mm) exceeds Effective GPU Space ({effective_gpu_space}mm) "
                    f"due to front radiator thickness ({rad_offset}mm).",
                    "gpu",
                    "length"
                )

        # 1.2 CPU Cooler Height
        # Logic: (Air_Cooler_Height) vs (Case_CPU_Clearance).
        if cooler and "AIR" in str(cooler.get("type", "")).upper():
             cooler_h = cooler.get("dimensions", {}).get("height") or 0
             case_cpu_limit = case.get("clearances", {}).get("cpu_cooler_max_height") or 160
             if cooler_h > case_cpu_limit:
                  self._add_conflict(
                       "INCOMPATIBLE",
                       f"Air Cooler height ({cooler_h}mm) exceeds Case clearance ({case_cpu_limit}mm).",
                       "cooler",
                       "height"
                  )
        
        # 1.3 Top Rad vs VRM/RAM
        # Logic: (Top_Radiator_Thickness) + (Fan_Thickness) vs (Mobo_VRM_Heatsink_Height).
        if cooler and "top" in str(cooler.get("mounting", "")).lower():
            rad_stack = (cooler.get("dimensions", {}).get("thickness") or 27) + \
                        (cooler.get("dimensions", {}).get("fan_thickness") or 25)
            # Maximum allowed stack before hitting standard VRMs in this case
            vrm_clearance = case.get("clearances", {}).get("top_radiator_clearance") or 55
            if rad_stack > vrm_clearance:
                 self._add_conflict(
                    "WARNING",
                    f"Top Radiator stack ({rad_stack}mm) may conflict with Motherboard VRM "
                    f"(Case limit: {vrm_clearance}mm).",
                    "cooler",
                    "thickness"
                )

        # 1.4 PSU Length vs Case max
        psu = self.parts.get("psu")
        if psu:
            psu_len = psu.get("dimensions", {}).get("length") or 0
            case_psu_max = case.get("clearances", {}).get("max_psu_length") or case.get("dimensions", {}).get("length") or 200 # fallback
            # Rigmaster app stores it as parse_dimension_mm(case, ['max_psu_length', 'psu_clearance'])
            # Did I add it in transform_component? I should use 200 if missing.
            # We'll just check if it's there
            if psu_len > case_psu_max:
                self._add_conflict("WARNING", f"PSU ({psu_len}mm) exceeds recommended PSU length for case ({case_psu_max}mm). Ensure sufficient space for cable management.", "psu", "length")


    def _check_electrical_adequacy(self):
        # 2.1 PSU Formula: (Sum of TDP * 1.25) + Peripheral_USB_Draw = Recommended_PSU_Wattage.
        psu = self.parts.get("psu")
        total_tdp = 0
        for cat, part in self.parts.items():
            if part and cat not in ["ups", "monitors", "psu"]:
                total_tdp += part.get("electrical", {}).get("tdp") or 0
        
        peripheral_draw = 25 # Heuristic for USB/RGB/Drives
        rec_wattage = (total_tdp * 1.25) + peripheral_draw
        
        if psu:
            psu_w = psu.get("electrical", {}).get("peak_draw") or psu.get("price") or 0
            if isinstance(psu.get("electrical", {}).get("tdp"), int):
                psu_w = psu.get("electrical", {}).get("tdp") or 0
            
            if psu_w < total_tdp:
                 self._add_conflict("INCOMPATIBLE", f"System requires {total_tdp}W load, PSU only provides {psu_w}W.", "psu", "wattage")
            elif psu_w < rec_wattage:
                 self._add_conflict("WARNING", f"PSU ({psu_w}W) is under the architectural 25% safety margin ({int(rec_wattage)}W target).", "psu", "wattage")

        # 2.2 UPS Logic: (System_Watts + Monitor_Watts) / 0.6 = Required_UPS_VA.
        ups = self.parts.get("ups")
        monitor = self.parts.get("monitors")
        if ups:
            mon_watts = monitor.get("electrical", {}).get("tdp") or 50 if monitor else 50
            required_va = (total_tdp + mon_watts) / 0.6
            ups_va = ups.get("electrical", {}).get("va_rating", 0)
            if ups_va < required_va:
                 self._add_conflict("SUBOPTIMAL", f"UPS ({ups_va}VA) insufficient for safety load. Required: {int(required_va)}VA.", "ups", "va_rating")

    def _check_header_connectivity(self):
        mobo = self.parts.get("motherboard")
        case = self.parts.get("case")
        if not mobo or not case: return

        # Case USB-C requiring Mobo Internal Header
        if "USB-C" in str(case.get("name", "")):
             if mobo.get("headers", {}).get("usb_c", 0) == 0:
                  self._add_conflict("WARNING", "Case has Front-Panel USB-C, but Motherboard lacks a Type-E header.", "motherboard", "usb_c")
        
        # ARGB Device Count vs Headers
        argb_devices = 0
        # Check Fans, Cooler, Case
        if self.parts.get("case_fans"): argb_devices += 3 # example count
        if self.parts.get("cooler") and "RGB" in str(self.parts.get("cooler").get("name")): argb_devices += 1
        
        mobo_argb = mobo.get("headers", {}).get("argb_5v", 1)
        if argb_devices > mobo_argb:
             self._add_conflict("WARNING", f"Build includes {argb_devices} ARGB devices but Mobo only has {mobo_argb} headers. RGB Controller recommended.", "motherboard", "argb_5v")

    def _check_logical_compatibility(self):
        cpu = self.parts.get("cpu")
        mobo = self.parts.get("motherboard")
        if not cpu or not mobo: return

        # BIOS Check: If (CPU_Gen > Mobo_Release_Date)
        # Using string comparison for ISO dates YYYY-MM-DD
        cpu_release = cpu.get("logical", {}).get("release_date")
        mobo_release = mobo.get("logical", {}).get("release_date")
        if cpu_release and mobo_release and cpu_release > mobo_release:
             self._add_conflict("WARNING", "CPU was released after Motherboard. A BIOS Update is likely required to boot.", "motherboard", "release_date")

        # PCIe Lane Sharing
        storage = self.parts.get("storage")
        if storage and storage.get("logical", {}).get("pcie_version", 0) >= 5:
             # Heuristic for Z790/X670 boards often sharing lanes between Gen5 M.2 and GPU
             if "Z790" in str(mobo.get("name")) or "X670" in str(mobo.get("name")):
                  self._add_conflict("SUBOPTIMAL", "Motherboard shares lanes between GPU and PCIe 5.0 SSD. SSD use may reduce GPU to x8 mode.", "motherboard", "pcie_lanes")

    def _check_advanced_heuristics(self):
        cpu = self.parts.get("cpu")
        gpu = self.parts.get("gpu")
        mobo = self.parts.get("motherboard")
        ram = self.parts.get("ram")
        psu = self.parts.get("psu")
        case = self.parts.get("case")
        cooler = self.parts.get("cooler")

        # 1. Thermal/VRM Warnings
        if cpu and mobo:
            cpu_tdp = cpu.get("advanced", {}).get("tdp") or cpu.get("electrical", {}).get("tdp") or 0
            mobo_vrm = mobo.get("advanced", {}).get("vrm_phases") or 0
            if cpu_tdp > 120 and mobo_vrm > 0 and mobo_vrm < 14:
                self._add_conflict("WARNING", f"VRM Warning: {mobo_vrm}-phase VRM may be marginal for {cpu_tdp}W TDP CPU. Consider higher-end boards for stability.", "motherboard", "vrm_phases")

        # 2. Missing Cooling
        if cpu:
            cpu_tdp = cpu.get("advanced", {}).get("tdp") or cpu.get("electrical", {}).get("tdp") or 0
            if cpu_tdp > 105 and not cooler:
                self._add_conflict("INCOMPATIBLE", "High-TDP processor requires aftermarket cooling.", "cooler", "missing")

        # 3. Bottleneck Check
        if cpu and gpu:
            cpu_p = cpu.get("price", 0)
            gpu_p = gpu.get("price", 0)
            if cpu_p > 0 and gpu_p > 0:
                ratio = gpu_p / cpu_p
                if ratio > 3.0:
                    self._add_conflict("SUBOPTIMAL", f"Potential CPU bottleneck. High-end GPU ({gpu.get('name')}) may be restricted by mid-tier CPU.", "cpu", "price")
                elif ratio < 0.8:
                    self._add_conflict("SUBOPTIMAL", f"Potential GPU bottleneck. High-end CPU ({cpu.get('name')}) exceeds GPU performance tier.", "gpu", "price")

        # 4. SFF Cable Management
        if case and psu:
            case_name = str(case.get("name", "")).upper()
            if any(x in case_name for x in ['MINI', 'ITX', 'SMALL', 'SFF']):
                psu_mod = psu.get("advanced", {}).get("modularity", "")
                if 'Modular' not in str(psu_mod):
                    self._add_conflict("WARNING", "Non-modular PSU in small case makes cable management extremely difficult.", "psu", "modularity")

        # 5. ATX 3.0 Readiness
        if gpu and psu:
            gpu_tdp = gpu.get("advanced", {}).get("tdp") or gpu.get("electrical", {}).get("tdp") or 0
            if gpu_tdp > 300:
                psu_conn = str(psu.get("advanced", {}).get("connectors", ""))
                audio_codec = str(mobo.get("advanced", {}).get("audio_codec", "")) if mobo else "Standard"
                if 'ATX 3.0' not in psu_conn and 'High-End' not in audio_codec:  # Proxy for budget build attempting high-end GPU
                    self._add_conflict("WARNING", f"Newer GPUs prefer ATX 3.0 compatible PSUs for transient stability.", "psu", "connectors")

        # 6. RAM Tunings
        if ram and mobo:
            ram_speed = ram.get("advanced", {}).get("speed") or 0
            ram_gen = ram.get("logical", {}).get("ram_gen") or ""
            if ram_speed > 6000 and ram_gen == 'DDR5':
                self._add_conflict("SUBOPTIMAL", f"DDR5 {ram_speed}MHz requires manual BIOS tuning; default profiles may be lower.", "ram", "speed")
            elif ram_speed > 4000 and ram_gen == 'DDR4':
                self._add_conflict("SUBOPTIMAL", f"DDR4 {ram_speed}MHz requires XMP profile in BIOS across most motherboards.", "ram", "speed")

    def _check_peripheral_and_accessory_constraints(self):
        mobo = self.parts.get("motherboard")
        network = self.parts.get("network")
        fans = self.parts.get("fans")
        case = self.parts.get("case")
        ups = self.parts.get("ups")
        cpu = self.parts.get("cpu")
        tools = self.parts.get("tools")
        paste = self.parts.get("thermal_paste")
        
        # 1. USB Count Verification
        usb_total = 0
        peripherals = ['keyboard', 'mouse', 'headset', 'webcam', 'speakers', 'microphone']
        for p_cat in peripherals:
            p = self.parts.get(p_cat)
            if p:
                usb_total += p.get("logical", {}).get("usb_ports_required") or 0
        
        if mobo and usb_total > 0:
            mobo_usb_count = mobo.get("headers", {}).get("usb_3_0", 2) + 2 # Add 2 generic USB 2.0s
            if usb_total > mobo_usb_count:
                self._add_conflict("WARNING", f"Selected peripherals take {usb_total} USB ports, but motherboard may only have ~{mobo_usb_count} Rear I/O ports. A USB hub is likely needed.", "motherboard", "usb_ports")
                
        # 2. Network Redundancy and Expansion
        if network:
            is_wifi_adapter = network.get("advanced", {}).get("is_wifi", False)
            if mobo:
                mobo_name = str(mobo.get("name", "")).upper()
                if is_wifi_adapter and ('WIFI' in mobo_name or 'WI-FI' in mobo_name or 'AX' in mobo_name or 'AC' in mobo_name):
                    self._add_conflict("SUBOPTIMAL", "Motherboard already features built-in Wi-Fi. A discrete Wi-Fi adapter is unnecessary.", "network_adapter", "redundant")
                    
        # 3. Case Fan Slots
        if fans and case:
            f_count = fans.get("logical", {}).get("count") or 1
            # Rough inference based on Form Factor if we don't have exact slots
            case_ffs = case.get("logical", {}).get("supported_form_factors", [])
            max_fans = 6
            if 'Mini ITX' in case_ffs and len(case_ffs) == 1: max_fans = 2
            elif 'Micro ATX' in case_ffs: max_fans = 4
            
            if f_count > max_fans:
                self._add_conflict("WARNING", f"Selected {f_count} case fans, but case structure likely only supports ~{max_fans} fans without modification.", "case_fan", "count")
                
        # 4. UPS Peak VA check
        if ups:
            ups_va = ups.get("electrical", {}).get("va_rating") or 0
            ups_w = ups.get("electrical", {}).get("peak_draw") or 0
            ups_capacity = ups_w if ups_w > 0 else (ups_va * 0.6) # Approx conversion
            
            system_draw = 0
            if cpu: system_draw += cpu.get("electrical", {}).get("tdp") or 65
            gpu = self.parts.get("gpu")
            if gpu: system_draw += gpu.get("electrical", {}).get("peak_draw") or gpu.get("electrical", {}).get("tdp") or 0
            system_draw += 50 # Base system
            
            if ups_capacity > 0 and system_draw > ups_capacity:
                self._add_conflict("WARNING", f"UPS rating (~{int(ups_capacity)}W) is lower than peak system draw (~{int(system_draw)}W). It will overload during game spikes.", "ups", "capacity")

        # 5. Assembly Tools & Paste Advisory
        if cpu:
            cpu_tdp = cpu.get("advanced", {}).get("tdp") or cpu.get("electrical", {}).get("tdp") or 0
            if cpu_tdp > 105 and not paste:
                self._add_conflict("SUBOPTIMAL", "High-TDP processor chosen. Premium thermal paste (rather than pre-applied cooler paste) is recommended.", "thermal_paste", "missing")
        
        if not tools:
             # Just a generic advisory
             pass

    def _check_os_constraints(self):
        os_cfg = self.parts.get("os")
        cpu = self.parts.get("cpu")
        mobo = self.parts.get("motherboard")
        ram = self.parts.get("ram")
        
        if not os_cfg: return
        
        is_win11 = os_cfg.get("logical", {}).get("is_win11", False)
        is_32bit = os_cfg.get("logical", {}).get("is_32bit", False)
        
        if is_win11:
            if cpu:
                cpu_name = str(cpu.get("name", "")).upper()
                c_sock = str(cpu.get("logical", {}).get("socket") or "")
                
                # Check TPM 2.0 / Win 11 Official support heuristics
                if 'LGA1151' in c_sock and not any(x in cpu_name for x in ['8TH', '9TH', '8100', '8400', '8600', '8700', '9100', '9400', '9600', '9700', '9900']):
                    self._add_conflict("WARNING", "Windows 11 natively requires Intel 8th Gen or newer. This CPU may fail official installation requirements.", "os", "version")
                elif 'AM4' in c_sock and ('RYZEN 1' in cpu_name or 'RYZEN 3 1' in cpu_name or 'RYZEN 5 1' in cpu_name or 'RYZEN 7 1' in cpu_name):
                    self._add_conflict("WARNING", "Windows 11 natively requires Ryzen 2000-series or newer. This CPU may fail official installation requirements.", "os", "version")
                elif 'LGA1150' in c_sock or 'LGA1155' in c_sock or 'AM3' in c_sock or 'LGA2011' in c_sock:
                    self._add_conflict("INCOMPATIBLE", "Windows 11 officially unsupported on this architecture (missing TPM 2.0 & Secure Boot).", "os", "version")
                    
        if is_32bit:
            if ram:
                ram_cap = ram.get("logical", {}).get("capacity") or 0
                if ram_cap > 4:
                    self._add_conflict("INCOMPATIBLE", f"A 32-bit Operating System can only address up to 4GB of RAM. Selected {ram_cap}GB will be unusable.", "os", "bits")

    def _add_conflict(self, severity, message, target_category, target_prop):
        # SEARCH FILTER query for Healing Logic
        replacement_parts = self.parts.get(target_category)
        base_price = replacement_parts.get("price") or 0 if replacement_parts else 0
        
        # If part is missing or has no price, provide a broader search range
        if not replacement_parts or base_price == 0:
            min_p = 0
            max_p = 10000 
        else:
            min_p = base_price * 0.9
            max_p = base_price * 1.1
        
        healing_filter = {
            "category": target_category,
            "price_range": [min_p, max_p],
            "exclude_id": replacement_parts.get("id") if replacement_parts else None
        }
        
        self.conflicts.append({
            "severity": severity,
            "severity_value": SEVERITY[severity],
            "message": message,
            "target": target_category,
            "healing_query": healing_filter
        })

# PSEUDO-CODE FOR RECURSIVE RE-VALIDATION
"""
function onPartChanged(newPart, currentBuild):
    // 1. Update the state
    currentBuild[newPart.category] = newPart
    
    // 2. Clear old caches
    invalidatePerformanceEstimates()
    
    // 3. Initiate Engine (RECURSIVE RE-VALIDATION)
    engine = new RelationalConstraintEngine(currentBuild)
    conflicts = engine.validate_full_build()
    
    // 4. Update UI
    displayConflicts(conflicts)
    
    // 5. Check if further recursive resolution needed
    if any(conflicts.severity == "INCOMPATIBLE"):
        triggerBuildLock(true)
        showHealingSuggestions(conflicts.top_priority_healing_query)
        
    return conflicts
"""

if __name__ == "__main__":
    # Test architectural sample
    mock_build = {
        "case": {"name": "SFF Case", "clearances": {"gpu_max_length": 300, "cpu_cooler_max_height": 130, "top_radiator_clearance": 40}, "price": 100},
        "gpu": {"name": "RTX 4090", "dimensions": {"length": 336}, "price": 1600, "electrical": {"tdp": 450}},
        "cpu": {"name": "i9-14900K", "electrical": {"tdp": 125}, "logical": {"release_date": "2023-10-17"}},
        "motherboard": {"name": "Z690 Board", "logical": {"release_date": "2021-11-04"}, "headers": {"usb_c": 0}, "price": 200},
        "psu": {"name": "750W Gold", "electrical": {"peak_draw": 750}, "price": 120}
    }
    
    engine = RelationalConstraintEngine(mock_build)
    results = engine.validate_full_build()
    print(json.dumps(results, indent=2))
