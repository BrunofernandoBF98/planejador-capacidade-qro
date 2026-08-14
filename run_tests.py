import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from tests.test_etl_and_engine import (
    test_db_master_populated,
    test_control_frame_pools_segregation,
    test_pool_takt_reference_math,
    test_headcount_sanity_real_greater_than_85meta,
    test_unmeasured_operations_scope_honesty,
    test_sanity_check_suite_v10_all_passed,
    test_shift_performance_and_hourly_timeline,
    test_pareto_station_filtering_consistency
)

print("Running test_db_master_populated...")
test_db_master_populated()
print("PASSED!")

print("Running test_control_frame_pools_segregation...")
test_control_frame_pools_segregation()
print("PASSED!")

print("Running test_pool_takt_reference_math...")
test_pool_takt_reference_math()
print("PASSED!")

print("Running test_headcount_sanity_real_greater_than_85meta...")
test_headcount_sanity_real_greater_than_85meta()
print("PASSED!")

print("Running test_unmeasured_operations_scope_honesty...")
test_unmeasured_operations_scope_honesty()
print("PASSED!")

print("Running test_sanity_check_suite_v10_all_passed...")
test_sanity_check_suite_v10_all_passed()
print("PASSED!")

print("Running test_shift_performance_and_hourly_timeline...")
test_shift_performance_and_hourly_timeline()
print("PASSED!")

print("Running test_pareto_station_filtering_consistency...")
test_pareto_station_filtering_consistency()
print("PASSED!")

print("All ADDENDUM v10, Shift Performance & Pareto Filtering tests passed 100% successfully!")
