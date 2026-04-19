
def get_suggestions(features):
    loc = features[0]
    loops = features[1]
    conditions = features[2]
    complexity = features[3]

    tips = []

    if loc > 40:
        tips.append("Split large code into smaller functions.")

    if loops > 2:
        tips.append("Reduce loops or use simpler logic where possible.")

    if conditions > 3:
        tips.append("Too many conditions detected. Consider simplifying if-else blocks.")

    if complexity > 8:
        tips.append("High cyclomatic complexity. Break code into modules/functions.")

    if loops == 0 and conditions == 0:
        tips.append("Code is already simple and clean.")

    if not tips:
        tips.append("Minor improvements only. Code complexity is manageable.")

    return tips

