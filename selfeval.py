# SelfEval module

import ast
import re
import tokenize
from io import BytesIO

# Language quality criteria
CRITERIA_DESCRIPTIONS = {
    "correctness": "Code is free from syntax errors and logical bugs.",
    "efficiency": "Code uses efficient algorithms and data structures.",
    "readability": "Code is easy to read and understand.",
    "maintainability": "Code is easy to maintain and extend.",
    "documentation": "Code is well-documented with clear explanations.",
    "testability": "Code is designed to be easily testable.",
    "error_handling": "Code handles errors and edge cases appropriately.",
    "security": "Code is secure and protects against common vulnerabilities.",
    "modularity": "Code is organized into reusable, well-defined modules.",
    "best_practices": "Code follows language-specific best practices."
}

# Default criteria to evaluate if none specified
DEFAULT_CRITERIA = [
    "correctness",
    "efficiency",
    "readability",
    "documentation",
    "best_practices"
]

def count_lines(code):
    """Count non-empty, non-comment lines of code"""
    lines = code.strip().split("\n")
    count = 0
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            count += 1
    return count

def evaluate_syntactic_correctness(code):
    """Check if code has syntax errors"""
    try:
        ast.parse(code)
        return 10, "No syntax errors detected."
    except SyntaxError as e:
        return 0, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return 2, f"Error parsing code: {str(e)}"

def evaluate_documentation(code):
    """Evaluate code documentation quality"""
    # Count docstrings and comments
    docstring_pattern = r'"""[^"]*"""'
    docstrings = re.findall(docstring_pattern, code, re.DOTALL)
    
    # Count non-empty comment lines
    comment_count = 0
    code_lines = 0
    for line in code.split("\n"):
        line = line.strip()
        if line and not line.startswith('"""'): 
            if line.startswith("#"):
                comment_count += 1
            elif not line.endswith('"""'):
                code_lines += 1
    
    # Evaluate documentation ratio
    doc_ratio = (len(docstrings) + comment_count) / max(1, code_lines)
    
    if doc_ratio >= 0.3 and len(docstrings) > 0:
        return 9, "Code is well-documented with clear explanations."
    elif doc_ratio >= 0.15:
        return 6, "Code has adequate documentation but could be improved."
    else:
        return 3, "Code lacks sufficient documentation."

def evaluate_efficiency(code):
    """Basic evaluation of code efficiency (limited static analysis)"""
    score = 7  # Start with an average score
    issues = []
    
    # Look for potentially inefficient patterns
    if "+= 1" in code and "counter" not in code.lower():
        issues.append("Consider using more efficient increment methods where applicable")
        score -= 1
    
    if re.search(r"for\s+\w+\s+in\s+range\(len\(", code):
        issues.append("Using range(len()) is less readable than direct iteration")
        score -= 1
    
    # Check for nested loops (potential O(n²) complexity)
    nested_loop_count = len(re.findall(r"for\s+\w+\s+in[^:]+:[^\n]*\n[^\n]*\s+for\s+\w+\s+in", code))
    if nested_loop_count > 1:
        issues.append(f"Found {nested_loop_count} nested loops; consider optimizing if processing large data")
        score -= min(nested_loop_count, 3)  # Deduct up to 3 points
    
    # Look for list comprehensions (efficient)
    comprehensions = len(re.findall(r"\[[^\]\[]+for\s+\w+\s+in[^\]\[]+\]", code))
    if comprehensions > 0:
        score += min(comprehensions, 2)  # Add up to 2 points
    
    if score >= 8:
        return score, "Code appears to be efficient with good algorithmic choices."
    elif score >= 5:
        msg = "Code has reasonable efficiency but could be improved. " + ("\n".join(issues) if issues else "")
        return score, msg
    else:
        msg = "Code has potential efficiency issues: " + ("\n".join(issues) if issues else "")
        return score, msg

def evaluate_readability(code):
    """Evaluate code readability"""
    score = 7  # Start with an average score
    issues = []
    
    # Check line length
    long_lines = 0
    for line in code.split("\n"):
        if len(line.strip()) > 100:  # PEP 8 recommends 79, but 100 is more lenient
            long_lines += 1
    
    if long_lines > 0:
        issues.append(f"Found {long_lines} lines exceeding recommended length")
        score -= min(long_lines, 3)  # Deduct up to 3 points
    
    # Check variable naming
    variable_pattern = r"\b([a-z_][a-z0-9_]*) *=[^=]"
    variables = re.findall(variable_pattern, code)
    short_vars = [var for var in variables if len(var) < 3 and var not in ['i', 'j', 'k', 'x', 'y', 'z']]
    
    if short_vars:
        issues.append(f"Found {len(short_vars)} variables with overly short names")
        score -= min(len(short_vars), 2)
    
    # Check function naming
    func_pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    funcs = re.findall(func_pattern, code)
    non_snake_case = [f for f in funcs if not re.match(r"^[a-z][a-z0-9_]*$", f)]
    
    if non_snake_case:
        issues.append(f"Found {len(non_snake_case)} function names not using snake_case")
        score -= min(len(non_snake_case), 2)
    
    # Check whitespace and indentation consistency
    inconsistent_indent = False
    indent_pattern = re.compile(r"^( *)\S")
    indents = [len(m.group(1)) for m in indent_pattern.finditer(code, re.MULTILINE) if m.group(1)]
    if indents and any(i % 4 != 0 for i in indents):
        inconsistent_indent = True
        score -= 2
    
    if score >= 8:
        return score, "Code is very readable with good naming and formatting."
    elif score >= 5:
        msg = "Code has reasonable readability but could be improved. " + ("\n".join(issues) if issues else "")
        return score, msg
    else:
        msg = "Code has readability issues: " + ("\n".join(issues) if issues else "")
        return score, msg

def evaluate_best_practices(code):
    """Evaluate adherence to best practices"""
    score = 7  # Start with an average score
    issues = []
    positives = []
    
    # Check for global variables
    global_vars = re.findall(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=[^=]", code, re.MULTILINE)
    if len(global_vars) > 3:  # Some globals are okay
        issues.append(f"Uses {len(global_vars)} global variables")
        score -= min(len(global_vars) - 3, 2)
    
    # Check for magic numbers
    # Ignore 0, 1, -1 as common values
    magic_numbers = re.findall(r"[^\w\d\.]([2-9]|[1-9]\d+)(?![\d\.])", code)
    if len(magic_numbers) > 5:
        issues.append(f"Contains {len(magic_numbers)} magic numbers that should be constants")
        score -= min(len(magic_numbers) // 5, 2)
    
    # Check for exception handling
    try_blocks = code.count("try:")
    except_blocks = code.count("except")
    if try_blocks > 0 and try_blocks == except_blocks and "except:" not in code:  # Good practice
        positives.append("Uses proper exception handling")
        score += 1
    elif "except:" in code:  # Bare except is bad practice
        issues.append("Uses bare except clauses without specifying exception types")
        score -= 1
    
    # Check for context managers (with statements)
    with_count = code.count("with")
    if with_count > 0:
        positives.append(f"Uses context managers ({with_count} with statements)")
        score += min(with_count, 2)
    
    if score >= 8:
        return score, "Code follows best practices well. " + ", ".join(positives)
    elif score >= 5:
        msg = "Code follows most best practices but has some issues. " + ", ".join(issues)
        return score, msg
    else:
        msg = "Code has several best practice issues: " + ", ".join(issues)
        return score, msg

def evaluate_code(code, criteria=None):
    """Evaluate code against specified criteria"""
    if not criteria:
        criteria = DEFAULT_CRITERIA
    
    results = {}
    total_score = 0
    max_possible = 0
    
    # Ensure all criteria are valid
    valid_criteria = [c for c in criteria if c in CRITERIA_DESCRIPTIONS]
    
    # Always check correctness first
    if "correctness" in valid_criteria:
        score, message = evaluate_syntactic_correctness(code)
        results["correctness"] = {
            "score": score,
            "max_score": 10,
            "message": message
        }
        total_score += score
        max_possible += 10
        
        # If code has syntax errors, other evaluations may not be meaningful
        if score < 3:
            for c in valid_criteria:
                if c != "correctness" and c not in results:
                    results[c] = {
                        "score": 0,
                        "max_score": 10,
                        "message": "Not evaluated due to syntax errors"
                    }
            return {
                "total_score": total_score,
                "max_score": len(valid_criteria) * 10,
                "percentage": (total_score / max_possible) * 100 if max_possible > 0 else 0,
                "criteria_results": results,
                "summary": "Code has syntax errors that need to be fixed before other aspects can be evaluated."
            }
    
    # Process other criteria
    for criterion in valid_criteria:
        if criterion == "correctness" and "correctness" in results:
            continue  # Already evaluated
            
        if criterion == "documentation":
            score, message = evaluate_documentation(code)
        elif criterion == "efficiency":
            score, message = evaluate_efficiency(code)
        elif criterion == "readability":
            score, message = evaluate_readability(code)
        elif criterion == "best_practices":
            score, message = evaluate_best_practices(code)
        else:
            # For criteria we don't have specific evaluators yet,
            # provide a placeholder message
            score = 5  # Neutral score
            message = f"Basic {criterion} check - detailed evaluation not implemented yet."
        
        results[criterion] = {
            "score": score,
            "max_score": 10,
            "message": message
        }
        
        total_score += score
        max_possible += 10
    
    # Calculate overall quality score
    percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0
    
    # Generate summary
    if percentage >= 80:
        summary = "High-quality code that follows good practices in most areas."
    elif percentage >= 60:
        summary = "Solid code with some areas for improvement."
    elif percentage >= 40:
        summary = "Code needs improvement in several key areas."
    else:
        summary = "Code has significant issues that should be addressed."
    
    return {
        "total_score": total_score,
        "max_score": max_possible,
        "percentage": percentage,
        "criteria_results": results,
        "summary": summary
    }

def run(params):
    """Main function for the SelfEval tool"""
    code = params.get("code", "")
    criteria = params.get("criteria", None)  # Optional parameter
    
    if not code:
        return {
            "error": "Missing code parameter",
            "status": "failed"
        }
    
    # Evaluate the code
    evaluation = evaluate_code(code, criteria)
    
    return {
        "evaluation": evaluation,
        "status": "success"
    }