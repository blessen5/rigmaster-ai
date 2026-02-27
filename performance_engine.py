
import re

class PerformanceEngine:
    def __init__(self, db):
        self.db = db
        
    def _get_gpu_score(self, gpu_name):
        """Returns a heuristic performance score (0-100) for a GPU"""
        name = gpu_name.lower()
        if '4090' in name: return 100
        if '4080' in name: return 90
        if '7900 xtx' in name: return 92
        if '4070 ti' in name: return 82
        if '7900 xt' in name: return 85
        if '4070' in name: return 75
        if '7800 xt' in name: return 72
        if '4060 ti' in name: return 60
        if '4060' in name: return 50
        if '3060' in name: return 45
        if '7600' in name: return 48
        # Default fallback
        return 50

    def _get_cpu_score(self, cpu_name):
        """Returns a heuristic performance score (0-100) for a CPU"""
        name = cpu_name.lower()
        if '14900' in name or '7950' in name: return 100
        if '14700' in name or '7900' in name: return 90
        if '7800x3d' in name: return 95 # Gaming king
        if '14600' in name or '7700' in name: return 80
        if '13600' in name or '7600' in name: return 75
        if '12600' in name or '5800' in name: return 65
        if '12400' in name or '5600' in name: return 55
        return 50

    def calculate_bottleneck(self, cpu_score, gpu_score):
        """
        Calculates bottleneck percentage.
        Positive = GPU Bottleneck (Good for gaming)
        Negative = CPU Bottleneck (Bad for gaming)
        """
        # A balanced build has GPU slightly stronger than CPU for gaming
        ratio = gpu_score / cpu_score
        
        if 0.9 <= ratio <= 1.1:
            return 0, "Perfect Match"
        elif ratio > 1.1:
            # GPU is much stronger -> CPU bottleneck
            bn = min((ratio - 1.1) * 50, 100)
            return -int(bn), "CPU Bottleneck"
        else:
            # CPU is much stronger -> GPU bottleneck (acceptable)
            bn = min((0.9 - ratio) * 50, 100)
            return int(bn), "GPU Limit"

    def predict_fps(self, gpu_score, cpu_score):
        """Predicts FPS for standard games at 1440p High"""
        # Base FPS roughly based on score (100 score = ~140 FPS in Cyberpunk at 1440p DLSS)
        base_power = (gpu_score * 0.7) + (cpu_score * 0.3)
        
        games = {
            "Cyberpunk 2077 (Ultra)": int(base_power * 1.2),
            "Call of Duty: MW3": int(base_power * 1.8),
            "Fortnite (Pro Settings)": int(base_power * 3.5),
            "Counter-Strike 2": int(base_power * 4.0)
        }
        return games

    def analyze_build(self, build_doc):
        """Main entry point for analysis"""
        if not build_doc:
            return {"error": "No build provided"}

        # Fetch names directly if IDs provided, or assuming names are in build_doc for simplicity
        # Check if we need to resolve IDs
        cpu_name = "Unknown CPU"
        gpu_name = "Unknown GPU"
        
        # Determine component names
        # Assuming database access or passed names. 
        # For this engine, we'll try to resolve if IDs are present, else look for names
        
        try:
            from bson.objectid import ObjectId
            if 'cpu_id' in build_doc and build_doc['cpu_id']: 
                cid = build_doc['cpu_id']
                if isinstance(cid, str): cid = ObjectId(cid)
                # Look in components table
                c = self.db.components.find_one({'_id': cid})
                if c: cpu_name = c['name']
            if 'gpu_id' in build_doc and build_doc['gpu_id']:
                gid = build_doc['gpu_id']
                if isinstance(gid, str): gid = ObjectId(gid)
                # Look in components table
                g = self.db.components.find_one({'_id': gid})
                if g: gpu_name = g['name']
        except:
             # Fallback
             pass

        cpu_s = self._get_cpu_score(cpu_name)
        gpu_s = self._get_gpu_score(gpu_name)
        
        bn_val, bn_type = self.calculate_bottleneck(cpu_s, gpu_s)
        fps = self.predict_fps(gpu_s, cpu_s)
        
        # Personality
        vibe = "Balanced All-Rounder"
        if gpu_s > 90 and cpu_s > 90: vibe = "God-Tier Monster"
        elif gpu_s > 80 and cpu_s < 70: vibe = "Graphics Pursist"
        elif cpu_s > 80 and gpu_s < 60: vibe = "Workstation Workhorse"
        elif gpu_s < 50 and cpu_s < 50: vibe = "Budget Starter"
        
        return {
            "scores": {
                "cpu": cpu_s,
                "gpu": gpu_s,
                "overall": int((cpu_s + gpu_s)/2)
            },
            "bottleneck": {
                "percentage": abs(bn_val),
                "type": bn_type,
                "verdict": "Ideally, we want the GPU to be the limit (95-99% usage). Your configuration is " + ("well balanced." if abs(bn_val) < 10 else f"limited by the {bn_type.split()[0]}.")
            },
            "gaming_performance": fps,
            "vibe": vibe
        }
