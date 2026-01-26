# @using annotation run-down
## Rules
1. If the function contains tokenRemaining with selfAddress!() as parameter, it MUST have @using(assetsInContract = true) annotation.
2. If the function contains transferTokenFromSelf!, it MUST have @using(assetsInContract = true) annotation.
3. If the function contains transferTokenToSelf!, it MUST have @using(preapprovedAssets = true) annotation.
4. If the function assigns to a mutable field (`mut`), it must have @using(updateFields = true) annotation (regardless of scope). For mappings, updateFields is only required when the assignment is **at the main scope** (not inside if/else or other nested blocks).
5. If the function has assetsInContract = true or updateFields = true or preapprovedAssets = true and doesn't contain checkCaller! statement it MUST have checkExternalCaller = false.
6. If the function is private it must not use checkExternalCaller = false.
7. If the function uses insert! it must have preapprovedAssets = true annotation.
8. <map>.insert! doesn't use curly brackets syntax, if there is code like insert!{...}(...) it must be changed to insert!(...).
9. If preapprovedAssets = true is used but not assetsInContract = true AND there is a transferTokenToSelf!, payToContractOnly = true must be added.