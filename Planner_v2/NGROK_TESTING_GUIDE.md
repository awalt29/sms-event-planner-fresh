🧪 **SMS Preferences Feature Testing Guide**

## Setup Complete ✅
- **Server**: Running at http://localhost:8000
- **Ngrok URL**: https://b073d12be702.ngrok-free.app
- **Database**: Preferences columns added successfully
- **Feature**: Complete 7-step preferences collection workflow

## Testing the Complete Preferences Workflow

### **Step 1: Update Twilio Webhook**
Update your Twilio phone number webhook URL to:
```
https://b073d12be702.ngrok-free.app/sms
```

### **Step 2: Create Event (Text from your planner phone)**
Text: `Let's hang out. Friday, Saturday`

Expected response: Bot will ask about the activity.

### **Step 3: Set Activity**
Text: `Dinner`

Expected response: Bot will ask for guest list.

### **Step 4: Add Guest with Phone**
Text: `Sarah 1234567890`

Expected response: Bot will ask for availability request confirmation.

### **Step 5: Send Availability Request**
Text: `Yes send`

Expected response: Bot confirms availability request was sent to Sarah.

### **Step 6: Test Complete 7-Step Guest Workflow (From Sarah's phone)**

**6a. Guest receives availability request:**
Expected message format:
```
Hi Sarah! [Planner] wants to hang out on one of these days:

- Friday, August 30
- Saturday, August 31

Reply with your availability and we'll find common times!🗓️ 

You can say things like:

- 'Friday 2-6pm, Saturday after 4pm'
- 'Friday all day, Saturday evening'  
- 'Friday after 3pm'
- 'Busy' (if you're not available any of these days)
```

**6b. Guest provides availability:**
From Sarah's phone, text: `Friday 7-11pm, Saturday 6-10pm`

Expected response:
```
Great! I have you available:
- Friday 7:00 PM-11:00 PM
- Saturday 6:00 PM-10:00 PM

Does this look right?

1️⃣ Yes, that's correct
2️⃣ Let me change my times
```

**6c. Guest confirms availability:**
Text: `1`

Expected response:
```
Perfect! Now, do you have any preferences for this dinner? (dietary restrictions, location preferences, etc.)

📝 Share any preferences, or text 'none' if you don't have any.
```

**6d. Guest provides preferences:**
Text: `I'm vegetarian and prefer quieter restaurants`

Expected response:
```
Got it! Let me confirm everything:

📅 Your availability:
- Friday 7:00 PM-11:00 PM
- Saturday 6:00 PM-10:00 PM

📝 Your preferences: I'm vegetarian and prefer quieter restaurants

Is this all correct?

1️⃣ Yes, send to planner
2️⃣ Change my availability  
3️⃣ Change my preferences
```

**6e. Guest final confirmation:**
Text: `1`

Expected response:
```
Perfect! I've sent your availability and preferences to [Planner]. They'll let everyone know once they pick the final time! 🎉
```

### **Step 7: Verify Enhanced Planner Notification**

The planner should receive an enhanced notification like:
```
📅 Sarah has responded:
- Friday 7:00 PM-11:00 PM
- Saturday 6:00 PM-10:00 PM
📝 Preferences: I'm vegetarian and prefer quieter restaurants

💬 Reply 'menu' for options
```

## Test Variations

### **Alternative Guest Responses:**
- **No preferences**: Text `none` in step 6d
- **Change availability**: Text `2` in step 6c or `2` in step 6e  
- **Change preferences**: Text `3` in step 6e
- **Different availability formats**: Try `Friday all day`, `Saturday evening`, etc.

### **Expected Behavior:**
- ✅ All availability displays now include preferences when provided
- ✅ Preferences are optional - guests can skip them
- ✅ Multi-step confirmation process with change options
- ✅ Enhanced planner notifications with both availability AND preferences
- ✅ State cleanup after each response (users return to planner mode)

## Debugging Commands

If you need to check the application state during testing:

```bash
# Check guest states
python -c "
from app import create_app, db
from app.models.guest_state import GuestState
app = create_app()
with app.app_context():
    states = GuestState.query.all()
    for s in states:
        print(f'{s.phone_number}: {s.current_state}')
"

# Check guests and preferences
python -c "
from app import create_app, db  
from app.models.guest import Guest
app = create_app()
with app.app_context():
    guests = Guest.query.all()
    for g in guests:
        print(f'{g.name}: {g.rsvp_status}, prefs: {g.preferences}')
"
```

## Success Criteria ✅
- [ ] Guest receives formatted availability request
- [ ] 7-step preferences workflow completes successfully
- [ ] Planner receives availability AND preferences in notification
- [ ] State management works correctly (no stuck states)
- [ ] Preferences are optional and handled gracefully
- [ ] Change options work for both availability and preferences

🎯 **Ready to test!** Start with Step 1 and follow the complete workflow.
