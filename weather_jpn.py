from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://weather.tsukumijima.net/api/forecast"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


@mcp.tool()
async def get_jpn_forecast(city_code: int) -> str:
    """Get weather forecast for a japan location.

    Args:
        city_code: 気象庁の天気情報で使用されている1次細分区の定義表のコード(例: 大阪府は270000) コードはこのURLを参照してください: https://weather.tsukumijima.net/primary_area.xml
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}?city={city_code}"
    forecast_data = await make_nws_request(points_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    description = forecast_data["description"]["text"]
    forecasts = forecast_data["forecasts"]
    forecast_texts = []
    forecast_text = f"""
description: {description}
"""
    forecast_texts.append(forecast_text)
    for forecast in forecasts:  # Only show next 3 forecasts
        forecast_text = f"""
{forecast["date"]}:
weather: {forecast["detail"]["weather"]}
wind: {forecast["detail"]["wind"]}
wave: {forecast["detail"]["wave"]}
temperature: {forecast["temperature"]["min"]["celsius"]}~{forecast["temperature"]["max"]["celsius"]}
"""
        forecast_texts.append(forecast_text)

    return "\n---\n".join(forecast_texts)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
