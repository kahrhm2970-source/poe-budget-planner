# Manual review before a real deployment

This checklist is outside the automated arithmetic checks.

1. Identify the exact switch model, installed PSU configuration and available PoE output budget.
2. Confirm each selected port's PoE standard, class/type, power pairs and individual limit.
3. Obtain a suitable worst-case PSE allocation for every device, including startup modes and cable-loss allowance. Record the vendor reference privately.
4. Verify cabling, length, connectors and environmental limits under the manufacturer's requirements.
5. Decide whether a reserve policy is appropriate; document why that percentage was chosen.
6. Check behavior during PSU failure, reduced power, negotiation and priority changes.
7. On authorized hardware, compare allocation readings with the plan and document any difference. Do not assume a pass in this tool proves operational readiness.
8. Publish only sanitized synthetic data. Keep customer inventories and hardware identifiers private.
