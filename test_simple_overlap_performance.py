#!/usr/bin/env python3
"""Simple performance test using existing logic"""

import time
from app.services.availability_service import AvailabilityService

def test_simple_overlap_calculation():
    """Test the time calculation logic directly"""
    
    service = AvailabilityService()
    
    # Test data - simulate guests available at different times
    guest_availabilities = [
        {
            'guest_name': 'Alice',
            'start_time': time.strptime('14:00', '%H:%M'),
            'end_time': time.strptime('18:00', '%H:%M'),
            'all_day': False
        },
        {
            'guest_name': 'Bob', 
            'start_time': time.strptime('15:00', '%H:%M'),
            'end_time': time.strptime('19:00', '%H:%M'),
            'all_day': False
        },
        {
            'guest_name': 'Charlie',
            'start_time': time.strptime('13:00', '%H:%M'),
            'end_time': time.strptime('17:00', '%H:%M'),
            'all_day': False
        }
    ]
    
    # Convert to datetime.time objects
    from datetime import time as dt_time
    for guest in guest_availabilities:
        start_struct = guest['start_time']
        end_struct = guest['end_time']
        guest['start_time'] = dt_time(start_struct.tm_hour, start_struct.tm_min)
        guest['end_time'] = dt_time(end_struct.tm_hour, end_struct.tm_min)
    
    print("=== Testing Time Overlap Calculation Performance ===\n")
    print("Guest availability:")
    for guest in guest_availabilities:
        print(f"  {guest['guest_name']}: {guest['start_time']} - {guest['end_time']}")
    
    # Time multiple runs
    times = []
    for i in range(1000):  # 1000 iterations
        start_time = time.time()
        overlap = service._calculate_time_overlap(guest_availabilities)
        end_time = time.time()
        times.append(end_time - start_time)
    
    # Calculate stats
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    total_time = sum(times)
    
    print(f"\nPerformance Results (1000 iterations):")
    print(f"Total time: {total_time:.4f}s")
    print(f"Average per calculation: {avg_time*1000:.4f}ms")
    print(f"Min: {min_time*1000:.4f}ms")
    print(f"Max: {max_time*1000:.4f}ms")
    
    print(f"\nCalculated overlap: {overlap}")
    
    # Performance assessment
    if avg_time < 0.001:  # 1ms
        print("✅ EXCELLENT: Sub-1ms performance")
    elif avg_time < 0.01:  # 10ms
        print("✅ GOOD: Sub-10ms performance")
    elif avg_time < 0.1:  # 100ms
        print("⚠️  OK: Sub-100ms performance")
    else:
        print("❌ SLOW: Over 100ms per calculation")
    
    # Estimate real-world performance
    estimated_db_time = 0.05  # 50ms for database query
    estimated_total = estimated_db_time + avg_time
    print(f"\nEstimated real-world time (with DB): {estimated_total*1000:.1f}ms")

if __name__ == "__main__":
    test_simple_overlap_calculation()
