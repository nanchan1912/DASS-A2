# StreetRace Manager Integration Test Cases

This document summarizes the integration test design used for Question 2.2. The executable version of these cases is in `integration/tests/test_integration.py`.

## Main scenarios covered

| ID | Scenario | Modules Involved | Expected Result | Actual Result |
| --- | --- | --- | --- | --- |
| T1 | Assign role before registration | Registration, Crew Management | Error | Passed |
| T2 | Register member then assign role | Registration, Crew Management | Role updates correctly | Passed |
| T3 | Request skill for missing member | Registration, Crew Management | Error | Passed |
| T4 | List crew by role after deactivation | Registration, Crew Management | Inactive member excluded | Passed after fix |
| T5 | Enter mechanic into race | Registration, Inventory, Race Management | Error | Passed |
| T6 | Enter valid driver into race | Registration, Inventory, Race Management | Participant added | Passed |
| T7 | Enter inactive driver into race | Registration, Inventory, Race Management | Error | Passed |
| T8 | Race with damaged vehicle | Registration, Inventory, Race Management | Error | Passed |
| T9 | Repair vehicle after adding parts | Registration, Inventory | Vehicle repaired | Passed |
| T10 | Check mechanic availability for mission | Registration, Mission Planning | Mechanic unavailable | Passed |
| T11 | Transfer race prize to inventory | Registration, Inventory, Race Management, Results | Cash increases | Passed |
| T12 | Start mission without required role | Mission Planning, Registration | Role unavailable | Passed |
| T13 | Start mission with required role available | Registration, Mission Planning | Mission active | Passed |
| T14 | Assign inactive member to mission | Registration, Mission Planning | Error | Passed |
| T15 | Complete race workflow | Registration, Inventory, Race Management, Results, Fuel Management | Race and ranking flow works | Passed |
| T16 | Complete mission workflow | Registration, Mission Planning, Inventory | Reward added to cash | Passed |
| T17 | Gain reputation from race win | Registration, Inventory, Race Management, Reputation System | Reputation increases | Passed |
| T18 | Unlock content from reputation tier | Registration, Reputation System | Content unlocked | Passed |
| T19 | Fuel shortage blocks readiness until refuel | Inventory, Fuel Management | Fuel sufficiency changes correctly | Passed |
| T20 | Refueling deducts cash | Inventory, Fuel Management | Cash decreases | Passed |
| T21 | Fuel action on unknown vehicle | Inventory, Fuel Management | Error | Passed after fix |
| T22 | Invalid role registration | Registration | Error | Passed |
| T23 | Invalid race type | Race Management | Error | Passed |
| T24 | Start race with one participant | Registration, Inventory, Race Management | Error | Passed |
| T25 | Invalid skill level above bound | Registration, Crew Management | Error | Passed |
| T26 | Deduct too much cash | Inventory | Error | Passed |
| T27 | Reputation query for unknown member | Registration, Reputation System | Error | Passed after fix |
| T28 | Manage multiple races together | Registration, Inventory, Race Management | Independent state maintained | Passed |
| T29 | Generate leaderboard from many races | Registration, Inventory, Race Management, Results | Rankings generated correctly | Passed |

## Why these tests were needed

- They cover the required business rules from the assignment prompt.
- They verify data flow between modules, not only isolated functions.
- They include both valid and invalid scenarios.
- They include edge cases such as inactive users, invalid IDs, invalid types, and insufficient cash.
- They include end-to-end workflows for races and missions.

## Errors found during integration testing

- `list_crew_by_role()` returned inactive crew members.
- Fuel operations accepted unknown vehicle IDs.
- Reputation queries accepted unknown member IDs.
- Running `pytest integration/tests` from the repository root failed without path setup.

## Fixes applied

- Added active-member filtering in `crew_management.py`.
- Added vehicle validation in `fuel_management.py`.
- Added member validation in `reputation_system.py`.
- Added `integration/tests/conftest.py` so tests run correctly from the repository root.
