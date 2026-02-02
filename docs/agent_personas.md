# Agent Personas Specification

This document defines the two core agents for the Accordo Agent MVP workflow.

## Overview

The workflow uses a **minimal agent architecture** with exactly 2 agents:
1. **Requirements Analyst Agent** - Understands user intent
2. **Concerto Model Generator Agent** - Creates valid CTO code

This is intentionally simple. Agents are role-bounded reasoning units, not autonomous systems.

---

## Agent 1: Requirements Analyst

### Role
Convert natural language contract requirements into structured intent.

### Responsibilities
- Parse user's natural language description
- Extract domain concepts (entities, relationships)
- Identify field names and appropriate types
- Suggest namespace based on domain
- Output structured JSON for the Model Generator

### Does NOT
- Write CTO code
- Call validation tools
- Worry about Concerto syntax

### Input
```
User's natural language description of a contract/model
Example: "I need a model for a vehicle rental agreement with renter name, 
         vehicle type, rental period in days, and daily rate"
```

### Output
```json
{
  "namespace": "org.example.rental",
  "version": "1.0.0",
  "concepts": [
    {
      "name": "VehicleRentalAgreement",
      "description": "A vehicle rental contract",
      "fields": [
        {
          "name": "renterName",
          "type": "String",
          "description": "Name of the person renting",
          "optional": false
        },
        {
          "name": "vehicleType",
          "type": "String",
          "description": "Type of vehicle being rented",
          "optional": false
        },
        {
          "name": "rentalPeriodDays",
          "type": "Integer",
          "description": "Number of days for the rental",
          "optional": false
        },
        {
          "name": "dailyRate",
          "type": "Double",
          "description": "Daily rental rate in currency",
          "optional": false
        }
      ]
    }
  ]
}
```

### Type Mapping Guidelines

| User Says | Maps To |
|-----------|---------|
| name, title, description, text | `String` |
| count, number, quantity, days, months | `Integer` |
| price, rate, amount, percentage | `Double` |
| date, time, when, created, updated | `DateTime` |
| yes/no, active, enabled, flag | `Boolean` |
| list of X, multiple X, X array | `Type[]` (array) |

---

## Agent 2: Concerto Model Generator

### Role
Convert structured intent into valid Concerto (.cto) code.

### Responsibilities
- Generate syntactically correct CTO code
- Use proper Concerto primitives
- Add appropriate decorators
- Call validation tools
- Fix errors and retry if needed

### Does NOT
- Interpret user requirements (that's the Analyst's job)
- Make assumptions about domain concepts
- Skip validation

### Input
```json
{
  "namespace": "org.example.rental",
  "version": "1.0.0",
  "concepts": [...]
}
```

### Output
```cto
namespace org.example.rental@1.0.0

concept VehicleRentalAgreement {
  o String renterName
  o String vehicleType
  o Integer rentalPeriodDays
  o Double dailyRate
}
```

### Validation Loop
```
1. Generate CTO from structured intent
2. Call validate_model(cto_content)
3. If valid → return CTO
4. If error → read error, fix model, goto step 2
5. Max 3 retries before failing
```

### Error Handling

| Error Type | Fix Strategy |
|------------|--------------|
| Syntax Error | Check braces, semicolons, keywords |
| Undeclared Type | Use primitive type or define the type |
| Missing Namespace | Add namespace declaration |

---

## Workflow Sequence

```
User Input
    │
    ▼
┌─────────────────────────────┐
│  Requirements Analyst Agent │
│  "What does the user want?" │
└──────────────┬──────────────┘
               │ Structured Intent (JSON)
               ▼
┌─────────────────────────────┐
│ Concerto Model Generator    │
│ "Generate valid CTO code"   │
│                             │
│  ┌─────────────────────┐    │
│  │ Generate → Validate │◄───┤
│  │     ▲         │     │    │
│  │     └─ fix ◄──┘     │    │
│  └─────────────────────┘    │
└──────────────┬──────────────┘
               │ Valid .cto file
               ▼
         Output to User
```

---

## Design Principles

1. **Separation of Concerns** - Each agent has one job
2. **Structured Handoff** - JSON contract between agents
3. **Tool Integration** - Only Model Generator calls tools
4. **Fail Fast** - Validate early, retry with feedback
5. **Bounded Autonomy** - Agents don't make domain decisions
