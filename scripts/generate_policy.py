#!/usr/bin/env python3
"""
Generates OPA/Rego policy based on required tags input.
"""
import os


def parse_required_tags(tags_input: str) -> list:
    """Parse required tags from input (comma-separated or newline-separated)."""
    if ',' in tags_input:
        return [t.strip() for t in tags_input.split(',') if t.strip()]
    return [t.strip() for t in tags_input.split('\n') if t.strip()]


def generate_rego_policy(tags: list) -> str:
    """Generate Rego policy for required tags (OPA 1.0+ compatible syntax)."""
    tags_list = ', '.join(f'"{tag}"' for tag in tags)
    
    return f'''package main

import rego.v1

required_tags := [{tags_list}]

# Deny resources missing required tags
deny contains msg if {{
    resource := input.resource_changes[_]
    
    # Skip deleted resources
    resource.change.actions[_] != "delete"
    
    # Get tags (prefer tags_all for AWS provider v3.38.0+)
    after := resource.change.after
    tags := get_tags(after)
    
    # Check for missing tags
    missing := required_tags[_]
    not tags[missing]
    
    msg := sprintf("Resource '%s' is missing required tag: %s", [resource.address, missing])
}}

# Deny resources with empty tag values
deny contains msg if {{
    resource := input.resource_changes[_]
    
    resource.change.actions[_] != "delete"
    
    after := resource.change.after
    tags := get_tags(after)
    
    tag := required_tags[_]
    tags[tag] == ""
    
    msg := sprintf("Resource '%s' has empty value for required tag: %s", [resource.address, tag])
}}

# Helper to get tags (prefers tags_all over tags)
get_tags(after) := after.tags_all if {{
    after.tags_all
}}

get_tags(after) := after.tags if {{
    not after.tags_all
    after.tags
}}

get_tags(after) := {{}} if {{
    not after.tags_all
    not after.tags
}}
'''


def main():
    required_tags = os.environ.get('REQUIRED_TAGS', '')
    action_path = os.environ.get('ACTION_PATH', '.')
    tags = parse_required_tags(required_tags)
    
    if not tags:
        print("⚠️  No required tags specified")
        return
    
    print(f"📋 Required tags: {', '.join(tags)}")
    
    policy = generate_rego_policy(tags)
    
    policy_path = os.path.join(action_path, 'policies', 'tags.rego')
    os.makedirs(os.path.dirname(policy_path), exist_ok=True)
    
    with open(policy_path, 'w') as f:
        f.write(policy)
    
    print(f"✅ Generated policy at {policy_path}")


if __name__ == '__main__':
    main()
