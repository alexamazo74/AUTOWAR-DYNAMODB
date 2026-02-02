"""
Example usage of SEC02 services configuration
This module demonstrates how to use the SEC02_BP_SERVICES configuration
"""

from src.config.sec02_services_config import (
    SEC02_BP_SERVICES,
    get_bp_services,
    get_all_services,
    get_bp_checks,
    SEC02_TOTAL_BPS,
    SEC02_TOTAL_SERVICES,
    SEC02_SERVICE_LIST,
)
import json


def print_sec02_overview():
    """Print overview of SEC02 configuration"""
    print("=" * 80)
    print("SEC02: Gestión de Identidad y Acceso - Autenticación")
    print("=" * 80)
    print(f"\nTotal Best Practices: {SEC02_TOTAL_BPS}")
    print(f"Total Services: {SEC02_TOTAL_SERVICES}")
    print(f"\nServices used: {', '.join(SEC02_SERVICE_LIST)}\n")


def print_bp_details(bp_code: str):
    """Print detailed information for a specific BP"""
    bp_data = get_bp_services(bp_code)
    
    if not bp_data:
        print(f"BP {bp_code} not found")
        return
    
    print(f"\n{'=' * 80}")
    print(f"{bp_code}: {bp_data.get('name')}")
    print(f"{'=' * 80}")
    print(f"Description: {bp_data.get('description')}")
    
    print(f"\nServices ({len(bp_data.get('services', []))}): ")
    for service in bp_data.get('services', []):
        print(f"  - {service}")
    
    print(f"\nResources by Service:")
    for service, resources in bp_data.get('resources', {}).items():
        print(f"  {service}:")
        for resource in resources:
            print(f"    - {resource}")
    
    print(f"\nChecks to Perform ({len(bp_data.get('checks', []))}): ")
    for check in bp_data.get('checks', []):
        print(f"  ✓ {check}")


def print_all_bps():
    """Print summary of all SEC02 BPs"""
    print_sec02_overview()
    
    for bp_code in sorted(SEC02_BP_SERVICES.keys()):
        bp_data = SEC02_BP_SERVICES[bp_code]
        print(f"\n{bp_code}: {bp_data['name']}")
        print(f"  Services: {len(bp_data['services'])}")
        print(f"  Checks: {len(bp_data['checks'])}")


def export_config_as_json(output_file: str = "sec02_config.json"):
    """Export SEC02 configuration as JSON"""
    config = {
        "question": "SEC02",
        "title": "Gestión de Identidad y Acceso - Autenticación",
        "total_bps": SEC02_TOTAL_BPS,
        "total_services": SEC02_TOTAL_SERVICES,
        "services_list": SEC02_SERVICE_LIST,
        "best_practices": SEC02_BP_SERVICES,
    }
    
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuration exported to {output_file}")


def get_bp_by_service(service: str) -> list:
    """Get all BPs that use a specific service"""
    matching_bps = []
    
    for bp_code, bp_data in SEC02_BP_SERVICES.items():
        if service in bp_data.get('services', []):
            matching_bps.append({
                'bp': bp_code,
                'name': bp_data['name'],
                'resources_in_service': list(bp_data.get('resources', {}).get(service, []))
            })
    
    return matching_bps


def print_service_coverage():
    """Print coverage of each service across all BPs"""
    print("\n" + "=" * 80)
    print("SERVICE COVERAGE IN SEC02")
    print("=" * 80)
    
    service_bps = {}
    for service in SEC02_SERVICE_LIST:
        bps = get_bp_by_service(service)
        service_bps[service] = bps
        print(f"\n{service.upper()} - Used in {len(bps)} BPs:")
        for bp in bps:
            print(f"  • {bp['bp']}: {bp['name']}")
            if bp['resources_in_service']:
                for resource in bp['resources_in_service'][:3]:  # Show first 3 resources
                    print(f"    - {resource}")
                if len(bp['resources_in_service']) > 3:
                    print(f"    ... and {len(bp['resources_in_service']) - 3} more resources")


def compliance_checklist():
    """Generate a compliance checklist for SEC02"""
    print("\n" + "=" * 80)
    print("SEC02 COMPLIANCE CHECKLIST")
    print("=" * 80)
    
    for bp_code in sorted(SEC02_BP_SERVICES.keys()):
        bp_data = SEC02_BP_SERVICES[bp_code]
        print(f"\n{bp_code}: {bp_data['name']}")
        print(f"{'─' * 76}")
        
        checks = get_bp_checks(bp_code)
        for check in checks:
            print(f"  ☐ {check}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "overview":
            print_sec02_overview()
        elif command == "all":
            print_all_bps()
        elif command == "services":
            print_service_coverage()
        elif command == "checklist":
            compliance_checklist()
        elif command == "export":
            export_config_as_json()
        elif command.startswith("bp:"):
            bp_code = command.split(":")[1]
            print_bp_details(bp_code)
        else:
            print(f"Unknown command: {command}")
            print("\nUsage: python sec02_examples.py [command]")
            print("Commands:")
            print("  overview      - Print SEC02 overview")
            print("  all           - Print all BPs")
            print("  services      - Print service coverage")
            print("  checklist     - Generate compliance checklist")
            print("  export        - Export configuration as JSON")
            print("  bp:CODE       - Print details for specific BP (e.g., bp:SEC02-BP01)")
    else:
        print_all_bps()
        print_service_coverage()
        compliance_checklist()
