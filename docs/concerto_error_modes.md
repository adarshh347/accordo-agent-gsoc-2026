# Concerto CLI Error Modes Documentation

This document outlines the error patterns from `@accordproject/concerto-cli` that our wrapper handles.

## Overview

The concerto-cli can produce different types of errors during parsing and validation. Understanding these patterns is crucial for the agent's retry logic.

## Error Types

### 1. Syntax Errors (Parsing Phase)

**When:** Malformed CTO syntax - missing braces, keywords, etc.

**CLI Command:** `concerto parse --model file.cto`

**Example Error:**
```
4:04:39 PM - error: Expected "-->", "@", "default", "o", "optional", "range", "}", comment, end of line, or whitespace but end of input found.
```

**Pattern to Match:**
- Contains `error:` and `expected`
- Usually mentions what tokens were expected

**Fix Suggestions:**
- Check for missing closing braces `}`
- Verify all declarations are complete
- Ensure proper keyword usage

---

### 2. Type Errors (Compilation Phase)

**When:** References to undefined types

**CLI Command:** `concerto compile --model file.cto --target JSONSchema`

**Example Error:**
```
4:06:43 PM - error: Undeclared type "FakeType" in "property org.example.badtype@1.0.0.BadTypeModel.value". File 'examples/invalid_model_type.cto':
```

**Pattern to Match:**
- Contains `Undeclared type`
- Includes the offending type name in quotes
- Includes the property path

**Fix Suggestions:**
- Use primitive types: `String`, `Integer`, `Double`, `Boolean`, `DateTime`, `Long`
- Define custom types before using them
- Import external types if needed

---

### 3. Import Errors

**When:** Failed to resolve imported namespaces

**Example Error:**
```
error: Unable to resolve type "org.external@1.0.0.SomeType"
```

**Pattern to Match:**
- Contains `Unable to resolve`
- Mentions the full qualified type name

**Fix Suggestions:**
- Check import URL is accessible
- Verify the namespace/version is correct
- Consider using `--offline` flag if working locally

---

## CLI Exit Codes

**Important:** The concerto-cli often returns exit code 0 even on errors. We must parse the output text to detect errors.

| Scenario | Exit Code | Contains |
|----------|-----------|----------|
| Success | 0 | `info: Compiled to...` or valid JSON |
| Syntax Error | 0 | `error: Expected...` |
| Type Error | 0 | `error: Undeclared type...` |
| File Not Found | 1 | Error message |

## Validation Strategy

1. **Parse first** - Catches syntax errors
2. **Compile second** - Catches type/semantic errors
3. **Check output** - Look for `error:` pattern regardless of exit code
4. **Extract details** - Parse error messages for actionable information

## Wrapper API

Our Python wrapper provides:

```python
from src.tools.concerto_tools import validate_model

result = validate_model(cto_content)
# Returns:
# {
#     "valid": bool,
#     "status": "success" | "syntax_error" | "type_error" | "unknown_error",
#     "error": str | None,
#     "details": str | None,
#     "suggestion": str | None
# }
```

## Common Primitive Types

| Type | Description | Example |
|------|-------------|---------|
| `String` | Text | `o String name` |
| `Integer` | Whole number | `o Integer count` |
| `Long` | Large whole number | `o Long bigNumber` |
| `Double` | Decimal number | `o Double price` |
| `Boolean` | True/false | `o Boolean active` |
| `DateTime` | Date and time | `o DateTime created` |

## Optional/Array Modifiers

```cto
o String name                    // Required field
o String nickname optional       // Optional field
o String[] tags                  // Array of strings
o String[] aliases optional      // Optional array
```
