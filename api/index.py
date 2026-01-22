from datetime import datetime, timedelta
from vvspy import get_trip
from vvspy.models import Trip
import logging
import os
import google.genai as genai
from http.server import BaseHTTPRequestHandler
import json

gemini_api_key = os.getenv("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vvspy")
logger.setLevel(logging.DEBUG)

PROMPT_TEMPLATE = """Analyze this Stuttgart trip data and give a brief route recommendation.

PREFERENCES:
1. U6 from Pragfriedhof to Feuerbach, then S-Bahn from Feuerbach to Weilimdorf
2. If Feuerbach has issues: U-Bahn to Hauptbahnhof, then train to Weilimdorf

IMPORTANT DECISION RULES:
- First look for trips matching preference 1 with NO issues or delays
- If preference 1 trips exist but have delays, recommend them and state the delay amount
- Only suggest alternatives if preference 1 trips are canceled or unavailable

TRIP DATA:
{trip_data}

Give a 2-3 sentence response that includes:
- Which route to take with departure time from the initial station
- Total time and any delays in minutes
- Any cancellations or service alerts
- Alternative if primary route unavailable

Keep it extremely concise for voice assistant output."""


def get_commute_data():
    """Fetch and analyze commute data from 7:00 to 8:30"""
    output = []

    today = datetime.now().date()
    # Generate departure times from 7:00 to 8:30, every 5 minutes
    departure_times = [datetime.combine(today, datetime.strptime("07:00", "%H:%M").time(
    )) + timedelta(minutes=i*5) for i in range(int((8*60 + 30 - 7*60) / 5) + 1)]

    for dep_time in departure_times:
        try:
            trip: Trip = get_trip('de:08111:115', 'de:08111:2270', check_time=dep_time)
            output.append(f"Departure at {dep_time.strftime('%H:%M')} - Duration: {trip.duration / 60} minutes\n")
            for i, connection in enumerate(trip.connections):
                output.append(f"\n  Connection {i + 1}:\n")
                output.append(f"    Duration: {connection.duration / 60} minutes\n")
                output.append(f"    Realtime Controlled: {connection.is_realtime_controlled}\n")
                output.append(f"    Origin:\n")
                output.append(f"      Name: {connection.origin.name}\n")
                output.append(f"      Departure Time: {connection.origin.departure_time_estimated}\n")
                output.append(f"      Delay: {connection.origin.delay}\n")
                output.append(f"    Destination:\n")
                output.append(f"      Name: {connection.destination.name}\n")
                output.append(f"      Arrival Time: {connection.destination.arrival_time_estimated}\n")
                output.append(f"      Delay: {connection.destination.delay}\n")
                output.append(f"    Transportation: {connection.transportation.disassembled_name}\n")

                if connection.infos:
                    output.append(f"    Infos:\n")
                    for info in connection.infos:
                        output.append(f"      Type: {info.get('type')}\n")
                        output.append(f"      Title: {info.get('title')}\n")
                        output.append(f"      Subtitle: {info.get('subtitle')}\n")
                        if info.get('content'):
                            output.append(f"      Message Content:\n")
                            output.append(f"        {info.get('content')}\n")
                else:
                    output.append(f"    Infos: None\n")
                output.append(f"    Path Description: {connection.path_description}\n")

        except (IndexError, TypeError) as e:
            output.append(
                f"Departure at {dep_time.strftime('%H:%M')} - No trips found: {e}\n")

    unified_output = "".join(output)

    if not unified_output or "No trips found" in unified_output:
        raise Exception("No trips available in the next 30 minutes")

    return unified_output


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY not configured")

            trip_data = get_commute_data()

            client = genai.Client(api_key=gemini_api_key)
            prompt = PROMPT_TEMPLATE.format(trip_data=trip_data)
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "trip_data": trip_data,
                "recommendation": response.text
            }).encode())

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Sorry, something went wrong with the transit data service. Please try again later.",
                "details": str(e)
            }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()