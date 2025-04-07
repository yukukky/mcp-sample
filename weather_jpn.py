from typing import Any, Dict, List
import httpx
import xml.etree.ElementTree as ET
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://weather.tsukumijima.net/api/forecast"
AREA_XML_URL = "https://weather.tsukumijima.net/primary_area.xml"
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
async def get_city_codes() -> str:
    """Get available city codes from Japan Meteorological Agency.

    Returns a formatted list of city codes and their corresponding names.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(AREA_XML_URL, timeout=30.0)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.text)
            areas = []

            # RSS形式のXMLから都道府県と都市の情報を抽出
            for pref in root.findall(".//pref"):
                pref_title = pref.get("title")
                for city in pref.findall(".//city"):
                    city_title = city.get("title")
                    city_id = city.get("id")
                    areas.append(f"{pref_title} - {city_title}: {city_id}")

            if not areas:
                return "エリア情報が見つかりませんでした。"

            return "\n".join(areas)
        except httpx.HTTPStatusError as e:
            return f"HTTPエラー: ステータスコード {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"リクエストエラー: {str(e)}"
        except ET.ParseError as e:
            return f"XMLパースエラー: {str(e)}"
        except Exception as e:
            return f"エラーが発生しました: {str(e)}"


@mcp.tool()
async def get_jpn_forecast(city_code: str) -> str:
    """Get weather forecast for a japan location.

    Args:
        city_code: 気象庁の天気情報で使用されている1次細分区のコード (例: 大阪府は270000)
                  コード一覧を取得するには get_city_codes ツールを使用してください
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
