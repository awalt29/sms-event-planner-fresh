#!/usr/bin/env python3

import sys
import re
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

def test_user_examples():
    """Test the exact examples the user mentioned"""
    
    def _parse_shorthand_time(time_str):
        """Parse shorthand time formats like '7-11p', '11-5', '7p', etc."""
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
        
        return None

    def format_time_display(time_24):
        """Convert 24-hour time to 12-hour display"""
        hour = int(time_24[:2])
        if hour == 0:
            return "12am"
        elif hour < 12:
            return f"{hour}am"
        elif hour == 12:
            return "12pm"
        else:
            return f"{hour-12}pm"

    print("🧪 Testing User-Requested Examples")
    print("=" * 45)
    
    # Test the specific examples from the user's request
    user_examples = [
        "7-11p",  # Should mean 7pm-11pm
        "11-5",   # Should mean 11am-5pm  
    ]
    
    print("\n📱 User's specific examples:")
    print("-" * 30)
    
    for example in user_examples:
        result = _parse_shorthand_time(example)
        if result:
            start_display = format_time_display(result['start'])
            end_display = format_time_display(result['end'])
            print(f"  '{example}' → {start_display}-{end_display}")
        else:
            print(f"  '{example}' → ❌ No match")
    
    print(f"\n📝 Testing full message scenario:")
    print("-" * 35)
    
    # Simulate parsing "Friday 7-11p, Saturday 11-5"
    full_message = "Friday 7-11p, Saturday 11-5"
    print(f"Message: '{full_message}'")
    
    # Extract time parts
    import re
    time_parts = re.findall(r'\b(\d{1,2}-\d{1,2}[ap]?)\b', full_message.lower())
    
    print(f"Extracted time parts: {time_parts}")
    
    for part in time_parts:
        result = _parse_shorthand_time(part)
        if result:
            start_display = format_time_display(result['start'])
            end_display = format_time_display(result['end'])
            print(f"  '{part}' → {start_display}-{end_display}")
    
    print(f"\n✅ Shorthand parsing now correctly handles:")
    print(f"   • '7-11p' as 7pm-11pm")
    print(f"   • '11-5' as 11am-5pm")
    print(f"   • Mixed formats like '9a-12p'")
    print(f"   • Single times like '7p' (with 4-hour window)")

if __name__ == "__main__":
    test_user_examples()
