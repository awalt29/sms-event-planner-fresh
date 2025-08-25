#!/usr/bin/env python3

import sys
import re
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

def test_shorthand_time_parsing():
    """Test the shorthand time parsing method directly"""
    
    def _parse_shorthand_time(time_str):
        """
        Parse shorthand time formats like '7-11p', '11-5', '7p', etc.
        Returns dict with start and end times in 24-hour format
        """
        import re
        
        if not time_str:
            return None
            
        time_str = time_str.strip().lower()
        
        # Pattern 1: Mixed am/pm ranges like "9a-12p" (9am to 12pm)
        mixed_pattern = r'(\d{1,2})\s*([ap])\s*-\s*(\d{1,2})\s*([ap])'
        mixed_match = re.search(mixed_pattern, time_str)
        
        if mixed_match:
            start_num = int(mixed_match.group(1))
            start_period = mixed_match.group(2)
            end_num = int(mixed_match.group(3))
            end_period = mixed_match.group(4)
            
            # Convert to 24-hour
            if start_period == 'p':
                start_hour = 12 if start_num == 12 else start_num + 12
            else:  # 'a'
                start_hour = 0 if start_num == 12 else start_num
                
            if end_period == 'p':
                end_hour = 12 if end_num == 12 else end_num + 12
            else:  # 'a'
                end_hour = 0 if end_num == 12 else end_num
            
            if 0 <= start_hour <= 23 and 0 <= end_hour <= 23 and start_hour < end_hour:
                return {
                    'start': f"{start_hour:02d}:00",
                    'end': f"{end_hour:02d}:00"
                }
        
        # Pattern 2: Ranges with single am/pm: 7-11p, 2-6pm, 11-5
        range_pattern = r'(\d{1,2})\s*-\s*(\d{1,2})\s*([ap]m?)?'
        range_match = re.search(range_pattern, time_str)
        
        if range_match:
            start_num = int(range_match.group(1))
            end_num = int(range_match.group(2))
            suffix = range_match.group(3)
            
            # Determine AM/PM for times
            if suffix and 'p' in suffix:
                # Both times are PM
                start_hour = 12 if start_num == 12 else start_num + 12
                end_hour = 12 if end_num == 12 else end_num + 12
            elif suffix and 'a' in suffix:
                # Both times are AM
                start_hour = 0 if start_num == 12 else start_num
                end_hour = 0 if end_num == 12 else end_num
            else:
                # No suffix - use smart defaults
                if start_num >= 7 and end_num <= 11 and start_num < end_num:
                    # Evening: 7-11 → 7pm-11pm
                    start_hour = start_num + 12
                    end_hour = end_num + 12
                elif start_num >= 11 and end_num <= 6:
                    # Day span: 11-5 → 11am-5pm
                    start_hour = start_num
                    end_hour = end_num + 12
                elif start_num >= 9 and end_num == 12:
                    # Morning: 9-12 → 9am-12pm
                    start_hour = start_num
                    end_hour = 12
                elif start_num >= 1 and start_num <= 6 and end_num > start_num:
                    # Afternoon: 1-6 → 1pm-6pm
                    start_hour = start_num + 12
                    end_hour = end_num + 12
                else:
                    # Default - assume PM if late hours
                    if start_num >= 6:
                        start_hour = start_num + 12
                        end_hour = end_num + 12
                    else:
                        start_hour = start_num
                        end_hour = end_num
            
            # Validate range
            if 0 <= start_hour <= 23 and 0 <= end_hour <= 23 and start_hour < end_hour:
                return {
                    'start': f"{start_hour:02d}:00",
                    'end': f"{end_hour:02d}:00"
                }
        
        # Pattern 3: Single times with am/pm: 7p, 11a, 2pm
        single_pattern = r'(\d{1,2})\s*([ap]m?)'
        single_match = re.search(single_pattern, time_str)
        
        if single_match:
            time_num = int(single_match.group(1))
            suffix = single_match.group(2)
            
            if 'p' in suffix:
                hour = 12 if time_num == 12 else time_num + 12
            else:  # 'a' in suffix
                hour = 0 if time_num == 12 else time_num
            
            # For single times, assume 4-hour availability
            end_hour = min(23, hour + 4)
            
            if 0 <= hour <= 23:
                return {
                    'start': f"{hour:02d}:00",
                    'end': f"{end_hour:02d}:00"
                }
        
        return None

    def _smart_time_defaults(start_hour, end_hour):
        """Apply smart defaults for ambiguous time ranges"""
        # Common patterns:
        # 7-11 -> 7pm-11pm (evening)
        # 11-5 -> 11am-5pm (day span)
        # 9-12 -> 9am-12pm (morning)
        # 1-6 -> 1pm-6pm (afternoon)
        
        if start_hour >= 7 and end_hour <= 11 and start_hour < end_hour:
            # Evening range: 7-11 -> 7pm-11pm
            return start_hour + 12, end_hour + 12
        elif start_hour >= 9 and end_hour <= 12:
            # Morning range: 9-12 -> 9am-12pm
            return start_hour, end_hour
        elif start_hour >= 11 and end_hour <= 6:
            # Day span: 11-5 -> 11am-5pm
            return start_hour, end_hour + 12
        elif start_hour >= 1 and start_hour <= 6 and end_hour > start_hour and end_hour <= 11:
            # Afternoon: 1-6 -> 1pm-6pm
            return start_hour + 12, end_hour + 12
        else:
            # Default case - assume PM for start time if it's reasonable
            if start_hour >= 6:
                return start_hour + 12, end_hour + 12
            else:
                return start_hour, end_hour

    print("🧪 Testing Shorthand Time Parsing")
    print("=" * 40)
    
    test_cases = [
        ("7-11p", "7pm-11pm"),
        ("11-5", "11am-5pm"),
        ("2-6pm", "2pm-6pm"),
        ("9a-12p", "9am-12pm"),
        ("7p", "7pm (4-hour window)"),
        ("11a", "11am (4-hour window)"),
        ("1-6", "1pm-6pm"),
        ("9-12", "9am-12pm"),
    ]
    
    for test_input, expected_desc in test_cases:
        result = _parse_shorthand_time(test_input)
        print(f"\n📝 Testing: '{test_input}' (expecting {expected_desc})")
        if result:
            if result['start'] == result['end']:
                print(f"  ✅ Single time: {result['start']}")
            else:
                start_hour = int(result['start'][:2])
                end_hour = int(result['end'][:2])
                start_display = f"{start_hour if start_hour <= 12 else start_hour-12}{'am' if start_hour < 12 else 'pm'}"
                end_display = f"{end_hour if end_hour <= 12 else end_hour-12}{'am' if end_hour < 12 else 'pm'}"
                print(f"  ✅ Range: {start_display}-{end_display} (24h: {result['start']}-{result['end']})")
        else:
            print(f"  ❌ No match")

if __name__ == "__main__":
    test_shorthand_time_parsing()
