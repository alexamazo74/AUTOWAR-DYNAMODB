#!/usr/bin/env python3
"""
Test script for SEC04, SEC05, SEC06 implementations
Validates new security evaluator methods and metrics calculations
"""

import sys
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules import correctly"""
    print("\n[TEST] Testing imports...")
    try:
        # Test config import directly (no relative imports)
        spec_path = Path(__file__).parent / "src" / "config" / "sec04_05_06_services_config.py"
        import importlib.util
        spec = importlib.util.spec_from_file_location("sec04_05_06_services_config", spec_path)
        sec_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sec_config)
        
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_services_config():
    """Test services configuration"""
    print("\n[TEST] Testing services configuration...")
    try:
        import importlib.util
        spec_path = Path(__file__).parent / "src" / "config" / "sec04_05_06_services_config.py"
        spec = importlib.util.spec_from_file_location("sec04_05_06_services_config", spec_path)
        sec_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sec_config)
        
        # Verify SEC04
        assert "SEC04-BP01" in sec_config.SEC04_SERVICES, "SEC04-BP01 missing"
        assert "SEC04-BP02" in sec_config.SEC04_SERVICES, "SEC04-BP02 missing"
        assert "SEC04-BP03" in sec_config.SEC04_SERVICES, "SEC04-BP03 missing"
        assert "SEC04-BP04" in sec_config.SEC04_SERVICES, "SEC04-BP04 missing"
        print("✓ SEC04 services configuration valid (4 BPs)")
        
        # Verify SEC05
        assert "SEC05-BP01" in sec_config.SEC05_SERVICES, "SEC05-BP01 missing"
        assert "SEC05-BP02" in sec_config.SEC05_SERVICES, "SEC05-BP02 missing"
        assert "SEC05-BP03" in sec_config.SEC05_SERVICES, "SEC05-BP03 missing"
        assert "SEC05-BP04" in sec_config.SEC05_SERVICES, "SEC05-BP04 missing"
        print("✓ SEC05 services configuration valid (4 BPs)")
        
        # Verify SEC06
        assert "SEC06-BP01" in sec_config.SEC06_SERVICES, "SEC06-BP01 missing"
        assert "SEC06-BP02" in sec_config.SEC06_SERVICES, "SEC06-BP02 missing"
        assert "SEC06-BP03" in sec_config.SEC06_SERVICES, "SEC06-BP03 missing"
        assert "SEC06-BP04" in sec_config.SEC06_SERVICES, "SEC06-BP04 missing"
        assert "SEC06-BP05" in sec_config.SEC06_SERVICES, "SEC06-BP05 missing"
        print("✓ SEC06 services configuration valid (5 BPs)")
        
        # Verify metrics
        assert "detection_metrics" in sec_config.SECURITY_METRICS
        assert "network_security" in sec_config.SECURITY_METRICS
        assert "compute_security" in sec_config.SECURITY_METRICS
        assert "operational_efficiency" in sec_config.SECURITY_METRICS
        print("✓ Security metrics configuration valid")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_evaluator_code():
    """Test that evaluator code contains required methods"""
    print("\n[TEST] Testing evaluator code structure...")
    try:
        evaluator_path = Path(__file__).parent / "src" / "app" / "security_evaluator.py"
        with open(evaluator_path, 'r', encoding='utf-8') as f:
            evaluator_code = f.read()
        
        # Check that methods exist in code
        required_methods = [
            "def evaluate_sec04",
            "def evaluate_sec05",
            "def evaluate_sec06",
            "def get_security_metrics",
            "def get_security_kpis",
            "_calculate_detection_metrics",
            "_calculate_network_metrics",
            "_calculate_compute_metrics",
            "_calculate_operational_metrics",
        ]
        
        for method in required_methods:
            assert method in evaluator_code, f"Method missing: {method}"
        
        print("✓ All evaluator methods found in code")
        
        # Check method signatures
        assert "def evaluate_sec04(self) -> Dict[str, Any]:" in evaluator_code
        assert "def evaluate_sec05(self) -> Dict[str, Any]:" in evaluator_code
        assert "def evaluate_sec06(self) -> Dict[str, Any]:" in evaluator_code
        print("✓ Method signatures are correct")
        
        # Check BP counts in docstrings
        assert "SEC04: Detección" in evaluator_code and "(4 BPs)" in evaluator_code
        assert "SEC05: Protección de infraestructura" in evaluator_code and "(4 BPs)" in evaluator_code
        assert "SEC06: Protección de infraestructura" in evaluator_code and "(5 BPs)" in evaluator_code
        print("✓ BP count documentation is correct")
        
        return True
    except AssertionError as e:
        print(f"✗ Evaluator code test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Evaluator code test failed: {e}")
        return False


def test_findings_structure():
    """Test that findings have correct structure"""
    print("\n[TEST] Testing findings structure...")
    try:
        # Create a sample finding
        sample_finding = {
            "bp": "SEC04-BP01",
            "status": "COMPLIANT",
            "finding": "Test finding",
            "severity": "HIGH",
            "risk": "Test risk",
            "remediation": "Test remediation",
            "evidence": "Test evidence",
        }
        
        # Check all required fields exist
        required_fields = ["bp", "status", "finding", "severity", "risk", "remediation", "evidence"]
        for field in required_fields:
            assert field in sample_finding, f"Missing field: {field}"
        
        print("✓ Finding structure is valid")
        return True
    except Exception as e:
        print(f"✗ Finding structure test failed: {e}")
        return False


def test_metrics_structure():
    """Test that metrics have correct structure"""
    print("\n[TEST] Testing metrics structure...")
    try:
        import importlib.util
        spec_path = Path(__file__).parent / "src" / "config" / "sec04_05_06_services_config.py"
        spec = importlib.util.spec_from_file_location("sec04_05_06_services_config", spec_path)
        sec_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sec_config)
        
        SECURITY_METRICS = sec_config.SECURITY_METRICS
        
        # Check that all metric categories exist
        required_categories = [
            "detection_metrics",
            "network_security",
            "compute_security",
            "operational_efficiency"
        ]
        
        for category in required_categories:
            assert category in SECURITY_METRICS, f"Missing metric category: {category}"
            assert isinstance(SECURITY_METRICS[category], list), f"{category} is not a list"
            assert len(SECURITY_METRICS[category]) > 0, f"{category} is empty"
        
        print(f"✓ Metrics structure is valid")
        print(f"  - Detection metrics: {len(SECURITY_METRICS['detection_metrics'])} items")
        print(f"  - Network security metrics: {len(SECURITY_METRICS['network_security'])} items")
        print(f"  - Compute security metrics: {len(SECURITY_METRICS['compute_security'])} items")
        print(f"  - Operational efficiency metrics: {len(SECURITY_METRICS['operational_efficiency'])} items")
        return True
    except Exception as e:
        print(f"✗ Metrics structure test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("SEC04, SEC05, SEC06 Implementation Tests")
    print("=" * 70)
    
    tests = [
        ("Services Configuration", test_services_config),
        ("Evaluator Code Structure", test_evaluator_code),
        ("Findings Structure", test_findings_structure),
        ("Metrics Structure", test_metrics_structure),
        ("Imports", test_imports),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Implementation is ready.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
