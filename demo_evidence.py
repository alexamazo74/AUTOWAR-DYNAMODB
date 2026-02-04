"""Demo script showing how the new evidence messages work"""

# Simulating the error scenarios from the logs
errors = {
    "SEC01-BP03": "'ConfigService' object has no attribute 'describe_config_recorders'",
    "SEC01-BP04": "'ConfigService' object has no attribute 'describe_config_recorders'",
    "SEC01-BP06": "'ConfigService' object has no attribute 'describe_config_recorders'",
    "SEC01-BP08": "'ConfigService' object has no attribute 'describe_config_recorders'",
}

def create_evidence_message(error_msg):
    """Simulate the new evidence logic"""
    if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
        return f"Access denied - insufficient IAM permissions: {error_msg[:100]}"
    elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
        return f"Request timeout while querying AWS services: {error_msg[:100]}"
    else:
        return f"Error querying services: {error_msg[:150]}"

print("\n" + "="*80)
print("✅ DEMOSTRACIÓN: Nuevos mensajes de evidencia para BPs en PENDING_REVIEW")
print("="*80)

print("\n📋 Antes (campo evidence era siempre):")
print("   Evidence: N/D")

print("\n📋 Ahora (campo evidence muestra la razón específica):")
print("-"*80)

for bp, error in errors.items():
    evidence = create_evidence_message(error)
    print(f"\n🔸 {bp}")
    print(f"   Status: PENDING_REVIEW")
    print(f"   Finding: Unable to verify...")
    print(f"   Evidence: {evidence}")

print("\n" + "="*80)
print("📝 Tipos de errores detectados:")
print("="*80)
print("1. ✅ AccessDenied / UnauthorizedOperation")
print("   → Muestra: 'Access denied - insufficient IAM permissions...'")
print("\n2. ✅ Timeout errors")
print("   → Muestra: 'Request timeout while querying AWS services...'")
print("\n3. ✅ Otros errores (como el ConfigService)")
print("   → Muestra: 'Error querying services: [mensaje completo]'")

print("\n" + "="*80)
print("🎯 Ejemplo real de los logs del backend:")
print("="*80)
print("\nError en logs:")
print("   Error checking SEC01-BP03: 'ConfigService' object has no attribute 'describe_config_recorders'")
print("\nEvidencia que aparecerá en la UI:")
print("   Error querying services: 'ConfigService' object has no attribute 'describe_config_recorders'")

print("\n✨ Los cambios YA están activos en el backend local (auto-reload)")
print("🚫 No se ha hecho push a git todavía\n")
