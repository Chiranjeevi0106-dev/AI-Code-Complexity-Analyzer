import lizard

# Detect language using keywords
def detect_language(code):
    code = code.lower()

    # Python
    if (
        "def " in code or
        "import " in code or
        "print(" in code or
        "range(" in code or
        "elif " in code or
        "except:" in code or
        "lambda " in code
    ):
        return "Python"

    # Java
    elif (
        "public static void main" in code or
        "system.out.println" in code or
        "class " in code
    ):
        return "Java"

    # C / C++
    elif (
        "#include" in code or
        "cout<<" in code or
        "printf(" in code or
        "int main(" in code
    ):
        return "C/C++"

    # JavaScript
    elif (
        "function " in code or
        "console.log(" in code or
        "let " in code or
        "const " in code
    ):
        return "JavaScript"

    else:
        return "Unknown"

# Map language to file extension
def get_extension(lang):
    extensions = {
        "Python": ".py",
        "Java": ".java",
        "C++": ".cpp",
        "JavaScript": ".js",
        "Unknown": ".txt"
    }
    return extensions.get(lang, ".txt")


# Main analyzer
def analyze_code(code):
    lang = detect_language(code)
    filename = "temp" + get_extension(lang)

    result = lizard.analyze_file.analyze_source_code(filename, code)

    loc = result.nloc
    functions = len(result.function_list)

    if functions > 0:
        complexity = result.function_list[0].cyclomatic_complexity
    else:
        complexity = 1

    loops = code.count("for") + code.count("while")
    conditions = code.count("if")

    features = [loc, loops, conditions, complexity]

    return features, lang