from flask import Blueprint, render_template, request, jsonify
from app.models import Planner, Event, Guest
from app.services.event_service import EventService
from app.services.guest_service import GuestService

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """
    Main dashboard page.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Event Planner Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                margin-bottom: 40px;
            }
            .feature {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .feature h3 {
                color: #667eea;
                margin-top: 0;
            }
            .instructions {
                background: #f8f9fa;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
            }
            .code {
                background: #f1f3f4;
                padding: 15px;
                border-radius: 5px;
                font-family: monospace;
                margin: 10px 0;
            }
            .webhook-url {
                background: #e8f5e8;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
                word-break: break-all;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎉 Event Planner SMS App</h1>
            <p>Intelligent event planning through simple text messages</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="planner-count">-</div>
                <div>Active Planners</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="event-count">-</div>
                <div>Total Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="guest-count">-</div>
                <div>Total Guests</div>
            </div>
        </div>

        <div class="instructions">
            <h2>🚀 Setup Instructions</h2>
            <p>To connect your Twilio account, set up the webhook URL:</p>
            <div class="webhook-url">
                <strong>Webhook URL:</strong> https://your-domain.com/sms/incoming
            </div>
            <p>Make sure to configure these environment variables:</p>
            <div class="code">
TWILIO_SID=your_twilio_account_sid<br>
TWILIO_AUTH=your_twilio_auth_token<br>
TWILIO_NUMBER=your_twilio_phone_number<br>
OPENAI_API_KEY=your_openai_api_key
            </div>
        </div>

        <div class="features">
            <div class="feature">
                <h3>📱 SMS-Driven Interface</h3>
                <p>Users interact with the system entirely through text messages. No app downloads or complex interfaces required.</p>
                <ul>
                    <li>Natural language processing</li>
                    <li>Intelligent conversation flows</li>
                    <li>Context-aware responses</li>
                </ul>
            </div>

            <div class="feature">
                <h3>🤖 AI-Powered Parsing</h3>
                <p>Advanced AI understands natural language to extract event details and availability information.</p>
                <ul>
                    <li>Event detail extraction</li>
                    <li>Availability parsing</li>
                    <li>Venue suggestions</li>
                </ul>
            </div>

            <div class="feature">
                <h3>👥 Smart Guest Management</h3>
                <p>Automatically collect availability from guests and find optimal meeting times.</p>
                <ul>
                    <li>Contact management</li>
                    <li>Availability collection</li>
                    <li>RSVP tracking</li>
                </ul>
            </div>

            <div class="feature">
                <h3>📅 Intelligent Scheduling</h3>
                <p>Find overlapping availability and suggest optimal times for events.</p>
                <ul>
                    <li>Overlap detection</li>
                    <li>Time optimization</li>
                    <li>Scheduling suggestions</li>
                </ul>
            </div>
        </div>

        <div class="instructions">
            <h2>💬 How to Use</h2>
            <p><strong>For Event Planners:</strong></p>
            <div class="code">
"Plan a birthday party for 10 people next Saturday"<br>
"Add John (555-123-4567) and Sarah (555-987-6543)"<br>
"Status" - Check event progress<br>
"Help" - Show available commands
            </div>
            
            <p><strong>For Guests:</strong></p>
            <div class="code">
"I'm free Monday 2-5pm and Wednesday evening"<br>
"Yes" - Confirm attendance<br>
"No" - Decline invitation<br>
"Maybe" - Tentative response
            </div>
        </div>

        <script>
            // Load stats
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('planner-count').textContent = data.planners || 0;
                    document.getElementById('event-count').textContent = data.events || 0;
                    document.getElementById('guest-count').textContent = data.guests || 0;
                })
                .catch(error => console.log('Stats loading error:', error));
        </script>
    </body>
    </html>
    """


@dashboard_bp.route("/api/stats")
def get_stats():
    """
    Get application statistics.
    """
    try:
        planner_count = Planner.query.count()
        event_count = Event.query.count()
        guest_count = Guest.query.count()
        
        return jsonify({
            'planners': planner_count,
            'events': event_count,
            'guests': guest_count
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'planners': 0,
            'events': 0,
            'guests': 0
        })


@dashboard_bp.route("/health")
def health_check():
    """
    Health check endpoint.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'event-planner',
        'version': '1.0.0'
    })
