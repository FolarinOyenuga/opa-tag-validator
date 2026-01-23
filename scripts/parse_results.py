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
    
    error_occurred = False
    error_message = ""
    
    try:
        with open(results_path, 'r') as f:
            content = f.read()
            
        # Check if content looks like an error (not valid JSON array)
        if not content.strip().startswith('['):
            error_occurred = True
            error_message = f"Conftest error: {content[:500]}"
            print(f"⚠️  Conftest output is not valid JSON: {content[:200]}")
        else:
            results = json.loads(content)
            
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
        error_occurred = True
        error_message = f"Results file not found: {results_path}"
        print(f"⚠️  {error_message}")
    except json.JSONDecodeError as e:
        error_occurred = True
        error_message = f"Could not parse results: {e}"
        print(f"⚠️  {error_message}")
    except Exception as e:
        error_occurred = True
        error_message = f"Error reading results: {e}"
        print(f"⚠️  {error_message}")
    
    # Build summary
    violations_count = len(violations)
    passed = violations_count == 0 and not error_occurred
    
    summary_lines = []
    if error_occurred:
        summary_lines.append(f"⚠️ **Error during validation**\n\n{error_message}")
    elif passed:
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
