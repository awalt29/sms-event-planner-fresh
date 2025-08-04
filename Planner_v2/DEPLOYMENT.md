# SMS Event Planner - Railway Deployment Guide

## Quick Deploy to Railway

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app) and sign up
   - Connect your GitHub account

2. **Deploy the App**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select this repository
   - Railway will auto-detect the Python app and deploy

3. **Configure Environment Variables**
   In the Railway dashboard, add these environment variables:

   ```
   SECRET_KEY=your-secret-key-here
   TWILIO_SID=your-twilio-account-sid
   TWILIO_AUTH=your-twilio-auth-token  
   TWILIO_NUMBER=+1234567890
   OPENAI_API_KEY=your-openai-api-key (optional)
   ```

4. **Set up Database**
   - Railway will automatically provision a PostgreSQL database
   - The DATABASE_URL will be automatically set

5. **Configure Twilio Webhook**
   - Get your Railway app URL (e.g., `https://your-app-name.railway.app`)
   - In Twilio Console → Phone Numbers → Manage → Active numbers
   - Click your phone number
   - Set Webhook URL to: `https://your-app-name.railway.app/sms/webhook`
   - Set HTTP method to POST

## Testing the Deployment

1. **Test API Health**
   ```bash
   curl https://your-app-name.railway.app/health
   ```

2. **Test SMS Endpoint**
   ```bash
   curl -X POST https://your-app-name.railway.app/sms/test \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "1234567890", "message": "Hello"}'
   ```

3. **Test Real SMS**
   - Send a text message to your Twilio number
   - The app should respond with the name collection prompt

## Twilio Setup

1. **Get a Twilio Account**
   - Sign up at [twilio.com](https://twilio.com)
   - Get your Account SID and Auth Token from the dashboard

2. **Buy a Phone Number**
   - Go to Phone Numbers → Manage → Buy a number
   - Choose a number that supports SMS

3. **Configure Webhook**
   - Set webhook URL to: `https://your-app-name.railway.app/sms/webhook`
   - Method: POST

## Complete Workflow Test

Once deployed, text your Twilio number:

1. **"John Smith"** → Name collection
2. **"Alice Johnson, 555-123-4567"** → Guest addition  
3. **"done"** → Move to date collection
4. **"8/20"** → Set event date
5. **"1"** → Request availability
6. Continue through location, activity, and venue selection

## Features Included

✅ Complete 9-stage workflow
✅ Venue suggestions with Google Maps
✅ AI-powered natural language processing
✅ Guest availability tracking
✅ RSVP management
✅ Contact memory across events
✅ PostgreSQL database
✅ Production-ready deployment

## Architecture

- **9 Workflow Handlers**: Focused 50-100 line handlers
- **6 Service Classes**: Clean business logic separation  
- **Real SMS Integration**: Twilio webhook support
- **Database Persistence**: PostgreSQL with migrations
- **Health Monitoring**: Built-in health check endpoints
