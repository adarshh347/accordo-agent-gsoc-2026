# Example: Simple Loan Agreement

## Natural Language Input

```
I need a model for a simple loan agreement. It should have:
- Borrower's full name
- Lender's full name  
- Loan amount in dollars
- Interest rate as a percentage
- Loan term in months
- Start date of the loan
```

## Expected Structured Intent (from Requirements Agent)

```json
{
  "namespace": "org.example.loan",
  "concepts": [
    {
      "name": "LoanAgreement",
      "decorators": ["@template"],
      "fields": [
        { "name": "borrowerName", "type": "String", "description": "Borrower's full name" },
        { "name": "lenderName", "type": "String", "description": "Lender's full name" },
        { "name": "loanAmount", "type": "Double", "description": "Loan amount in dollars" },
        { "name": "interestRate", "type": "Double", "description": "Interest rate as percentage" },
        { "name": "termMonths", "type": "Integer", "description": "Loan term in months" },
        { "name": "startDate", "type": "DateTime", "description": "Start date of the loan" }
      ]
    }
  ]
}
```

## Expected CTO Output

```cto
namespace org.example.loan

@template
concept LoanAgreement {
  o String borrowerName
  o String lenderName
  o Double loanAmount
  o Double interestRate
  o Integer termMonths
  o DateTime startDate
}
```
