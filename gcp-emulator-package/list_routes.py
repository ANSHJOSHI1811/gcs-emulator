#!/usr/bin/env python3
"""List all Flask routes in the application."""
from app.factory import create_app

app = create_app()
print("\n=== All Compute/VPC Routes ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
    rule_str = str(rule)
    if 'compute' in rule_str.lower() or 'vpc' in rule_str.lower():
        print(f"{rule.methods} {rule_str}")

print("\n=== All Routes (first 20) ===")
for i, rule in enumerate(sorted(app.url_map.iter_rules(), key=lambda r: str(r))):
    if i >= 20:
        print("...")
        break
    print(f"{rule.methods} {rule}")
