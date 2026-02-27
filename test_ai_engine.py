"""
Test script for AI Engine
Tests all AI providers and functionality
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import AI engine
from ai_engine import get_ai_engine

def test_ai_recommendation():
    """Test AI PC recommendation"""
    print("=" * 60)
    print("Testing AI PC Recommendation")
    print("=" * 60)
    
    ai_engine = get_ai_engine()
    
    # Test case 1: Gaming build
    print("\n1. Testing Gaming Build Recommendation...")
    try:
        result = ai_engine.get_pc_recommendation(
            budget="$1500",
            use_case="Gaming and Streaming",
            preferences={
                "brand_preference": "AMD for CPU, NVIDIA for GPU",
                "form_factor": "ATX"
            }
        )
        print(f"✓ Success! Provider used: {result.get('provider_used', 'unknown')}")
        print(f"  CPU: {result.get('cpu', 'N/A')}")
        print(f"  GPU: {result.get('gpu', 'N/A')}")
        print(f"  Motherboard: {result.get('motherboard', 'N/A')}")
        print(f"  RAM: {result.get('ram', 'N/A')}")
        print(f"  Reasoning: {result.get('reasoning', 'N/A')[:100]}...")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test case 2: Budget build
    print("\n2. Testing Budget Build Recommendation...")
    try:
        result = ai_engine.get_pc_recommendation(
            budget="$700",
            use_case="1080p Gaming",
            preferences={}
        )
        print(f"✓ Success! Provider used: {result.get('provider_used', 'unknown')}")
        print(f"  CPU: {result.get('cpu', 'N/A')}")
        print(f"  GPU: {result.get('gpu', 'N/A')}")
        print(f"  Estimated Total: {result.get('estimated_total', 'N/A')}")
    except Exception as e:
        print(f"✗ Failed: {e}")

def test_compatibility_check():
    """Test AI compatibility analysis"""
    print("\n" + "=" * 60)
    print("Testing AI Compatibility Check")
    print("=" * 60)
    
    ai_engine = get_ai_engine()
    
    print("\n1. Testing Compatible Build...")
    try:
        result = ai_engine.analyze_compatibility(
            cpu_name="AMD Ryzen 5 7600X",
            motherboard_name="ASUS ROG STRIX B650-A",
            ram_name="Corsair Vengeance DDR5-6000 32GB",
            other_components={
                "GPU": "NVIDIA RTX 4070",
                "PSU": "Corsair RM850x 850W"
            }
        )
        print(f"✓ Success!")
        print(f"  Compatible: {result.get('compatible', 'N/A')}")
        print(f"  Issues: {result.get('issues', [])}")
        print(f"  Confidence: {result.get('confidence', 'N/A')}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n2. Testing Incompatible Build...")
    try:
        result = ai_engine.analyze_compatibility(
            cpu_name="Intel Core i9-14900K",
            motherboard_name="ASUS ROG STRIX B450-F",  # Wrong socket
            ram_name="G.Skill Trident Z DDR4-3200 32GB",  # Wrong RAM type
        )
        print(f"✓ Success!")
        print(f"  Compatible: {result.get('compatible', 'N/A')}")
        print(f"  Issues: {result.get('issues', [])}")
    except Exception as e:
        print(f"✗ Failed: {e}")

def test_performance_estimate():
    """Test AI performance estimation"""
    print("\n" + "=" * 60)
    print("Testing AI Performance Estimation")
    print("=" * 60)
    
    ai_engine = get_ai_engine()
    
    print("\n1. Testing High-End Build Performance...")
    try:
        result = ai_engine.estimate_performance(
            cpu_name="AMD Ryzen 7 7800X3D",
            gpu_name="NVIDIA RTX 4080",
            ram_name="32GB DDR5-6000",
            games=["Cyberpunk 2077", "Valorant", "Elden Ring"]
        )
        print(f"✓ Success!")
        print(f"  Bottleneck: {result.get('bottleneck', 'N/A')}")
        print(f"  Bottleneck Severity: {result.get('bottleneck_severity', 'N/A')}")
        if 'benchmarks' in result:
            print("  Benchmarks:")
            for bench in result['benchmarks'][:3]:
                print(f"    - {bench.get('game', 'N/A')}: 1080p={bench.get('1080p', 'N/A')} | 1440p={bench.get('1440p', 'N/A')} | 4K={bench.get('4k', 'N/A')}")
    except Exception as e:
        print(f"✗ Failed: {e}")

def test_provider_availability():
    """Test which AI providers are available"""
    print("\n" + "=" * 60)
    print("Testing AI Provider Availability")
    print("=" * 60)
    
    ai_engine = get_ai_engine()
    
    print(f"\nConfigured Providers: {ai_engine.providers}")
    print(f"\nAPI Keys Status:")
    print(f"  Groq: {'✓ Set' if ai_engine.groq_key else '✗ Not Set'}")
    print(f"  Mistral: {'✓ Set' if ai_engine.mistral_key else '✗ Not Set'}")
    print(f"  Gemini: {'✓ Set' if ai_engine.gemini_key else '✗ Not Set'}")
    print(f"  Ollama URL: {ai_engine.ollama_url}")

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "AI ENGINE TEST SUITE" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Test provider availability first
    test_provider_availability()
    
    # Test AI recommendation
    test_ai_recommendation()
    
    # Test compatibility check
    test_compatibility_check()
    
    # Test performance estimation
    test_performance_estimate()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60 + "\n")
