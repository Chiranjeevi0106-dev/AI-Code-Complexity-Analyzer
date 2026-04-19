import ast

def ai_debug(code, lang="Unknown"):

    # Python Debugging
    if lang == "Python":
        try:
            ast.parse(code)
            return "No major issues found. Python syntax looks correct."

        except SyntaxError as e:
            return f"Line {e.lineno}: Syntax error - {e.msg}"

    # C / C++
    elif lang == "C/C++":
        issues = []

        if "#include" not in code:
            issues.append("Missing header file (#include).")

        if "main(" not in code:
            issues.append("Missing main() function.")

        if ";" not in code:
            issues.append("Possible missing semicolon.")

        if not issues:
            return "No major issues found in C/C++ code."

        return "\n".join(issues)

    # Java
    elif lang == "Java":
        issues = []

        if "class " not in code:
            issues.append("Missing class declaration.")

        if "main(" not in code:
            issues.append("Missing main method.")

        if ";" not in code:
            issues.append("Possible missing semicolon.")

        if not issues:
            return "No major issues found in Java code."

        return "\n".join(issues)

    else:
        if not code.strip():
            return "No code provided for debugging."
        return "Language-specific debugging not available for this code. Please provide Python, C/C++, Java, or JavaScript code."

