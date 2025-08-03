# 🚀 Event Planner App - Deployment Guide

This guide will help you deploy your SMS Event Planner app to a live server so you can use it anytime, anywhere!

## 🎯 Quick Start (Railway - Recommended)

Railway offers the easiest deployment with automatic GitHub integration and a generous free tier.

### Step 1: Prepare Your Code

1. **Push to GitHub** (if you haven't already):
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

### Step 2: Deploy to Railway

1. **Sign up for Railway**: Go to [railway.app](https://railway.app) and sign up with your GitHub account

2. **Create a new project**: 
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your event planner repository

3. **Configure Environment Variables**: In your Railway dashboard, go to your project settings and add these environment variables:
   ```
   FLASK_ENV=production
   SECRET_KEY=your-super-secret-production-key-here
   DATABASE_URL=postgresql://... (Railway will provide this)
   TWILIO_SID=your-twilio-sid
   TWILIO_AUTH=your-twilio-auth-token
   TWILIO_NUMBER=your-twilio-phone-number
   OPENAI_API_KEY=your-openai-api-key
   BASE_URL=https://your-app-name.railway.app
   ```

4. **Deploy**: Railway will automatically deploy your app. You'll get a URL like `https://your-app-name.railway.app`

### Step 3: Update Twilio Webhook

1. **Run the webhook update script**:
   ```bash
   python update_twilio_webhook.py
   ```
   Enter your Railway app URL when prompted.

2. **Test your deployment**: Send an SMS to your Twilio phone number!

---

## 🌐 Alternative Deployment Options

### Option 2: Render (Also Free)

1. **Sign up**: Go to [render.com](https://render.com)
2. **Connect GitHub**: Link your repository
3. **Create Web Service**: 
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app`
4. **Add Environment Variables**: Same as Railway
5. **Deploy**: Get your `.onrender.com` URL

### Option 3: Heroku (Paid)

1. **Install Heroku CLI**: [Download here](https://devcenter.heroku.com/articles/heroku-cli)
2. **Login and Create App**:
   ```bash
   heroku login
   heroku create your-app-name
   ```
3. **Add Environment Variables**:
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-secret-key
   # ... add all other environment variables
   ```
4. **Deploy**:
   ```bash
   git push heroku main
   ```

### Option 4: DigitalOcean App Platform

1. **Sign up**: Go to [digitalocean.com](https://digitalocean.com)
2. **Create App**: Choose GitHub as source
3. **Configure**: Select your repo and branch
4. **Environment Variables**: Add in the app settings
5. **Deploy**: Get your `.ondigitalocean.app` URL

---

## 🔧 Environment Variables Reference

Make sure to set these environment variables in your deployment platform:

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `SECRET_KEY` | Flask secret key | `your-random-secret-key` |
| `DATABASE_URL` | Database connection | Usually auto-provided |
| `TWILIO_SID` | Twilio Account SID | `ACxxxxxxxxxxxxx` |
| `TWILIO_AUTH` | Twilio Auth Token | `your-auth-token` |
| `TWILIO_NUMBER` | Your Twilio phone number | `+1234567890` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-xxxxxxxxxxxxx` |
| `BASE_URL` | Your app's URL | `https://your-app.railway.app` |

---

## 📱 After Deployment Checklist

1. ✅ **App is running**: Visit your deployment URL
2. ✅ **Environment variables set**: Check your platform's settings
3. ✅ **Twilio webhook updated**: Run `python update_twilio_webhook.py`
4. ✅ **Test SMS**: Send a text to your Twilio number
5. ✅ **Database working**: Check that planners and events are being created

---

## 🐛 Troubleshooting

### Common Issues:

**"Internal Server Error"**
- Check your environment variables are set correctly
- Look at the deployment logs for specific error messages

**"SMS not responding"**
- Verify Twilio webhook URL is set to `https://your-app.com/sms/incoming`
- Check that your Twilio credentials are correct

**"Database errors"**
- Make sure `DATABASE_URL` is set (most platforms provide this automatically)
- Check if you need to run database migrations

**"OpenAI errors"**
- Verify your `OPENAI_API_KEY` is valid and has credit

### Getting Logs:

**Railway**: Go to your project → Deployments → View logs

**Render**: Go to your service → Logs tab

**Heroku**: Run `heroku logs --tail`

---

## 🎉 Success!

Once deployed, you can:
- 📱 Text your Twilio number from any phone to start planning events
- 🌍 Access the app from anywhere in the world
- 👥 Invite friends and family to events via SMS
- 📊 Manage multiple events simultaneously

Your SMS Event Planner is now live and ready to help you organize amazing hangouts! 🎊

---

## 💡 Pro Tips

1. **Custom Domain**: Most platforms allow you to add a custom domain (e.g., `events.yourdomain.com`)
2. **Monitoring**: Set up monitoring to get alerts if your app goes down
3. **Backups**: Consider setting up automatic database backups
4. **Scaling**: If you get lots of users, you can easily scale up your deployment

Need help? Check the logs first, then refer to your deployment platform's documentation!
