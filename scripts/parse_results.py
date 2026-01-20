#!/usr/bin/env python3
"""
Parses Conftest JSON output and generates GitHub Action outputs.
"""
import os
import json


def main():
    terraform_dir = os.environ.get('TERRAFORM_DIR', '.')
    soft_fail = os.environ.get('SOFT_FAIL', 'false').lower() == 'true'
    github_output = os.environ.get('GITHUB_OUTPUT', '')
    
    results_path = os.path.join(terraform_dir, 'conftest_results.json')
    
    violations = []
    
    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        # Parse Conftest output format
        for result in results:
            for failure in result.get('failures', []):
                violations.append({
                    'message': failure.get('msg', 'Unknown violation')
                })
            for warning in result.get('warnings', []):
                violations.append({
                    'message': warning.get('msg', 'Unknown warning'),
                    'type': 'warning'
                })
    except FileNotFoundError:
        print(f"⚠️  Results file not found: {results_path}")
    except json.JSONDecodeError as e:
        print(f"⚠️  Could not parse results: {e}")
    except Exception as e:
        print(f"⚠️  Error reading results: {e}")
    
    # Build summary
    violations_count = len(violations)
    passed = violations_count == 0
    
    summary_lines = []
    if passed:
        summary_lines.append("✅ **All resources have required tags**")
    else:
        summary_lines.append(f"❌ **Found {violations_count} tag violation(s)**\n")
        for v in violations:
            prefix = "⚠️" if v.get('type') == 'warning' else "❌"
            summary_lines.append(f"- {prefix} {v['message']}")
    
    summary = '\n'.join(summary_lines)
    
    # Print results
    print(f"\n📊 Violations: {violations_count}")
    print(summary)
    
    # Write outputs
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"violations_count={violations_count}\n")
            f.write(f"passed={str(passed).lower()}\n")
            f.write(f"violations_summary<<EOF\n{summary}\nEOF\n")
    
    # Exit code
    if not passed and not soft_fail:
        exit(1)


if __name__ == '__main__':
    main()
