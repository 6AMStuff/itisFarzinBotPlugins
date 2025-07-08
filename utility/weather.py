import httpx
from bot import Bot
from pyrogram import filters
from pyrogram.types import Message

from config import Config


async def get_weather(location: str):
    async with httpx.AsyncClient(proxy=Config.PROXY) as client:
        data = (
            await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params=dict(name=location, count=1),
            )
        ).json()

        if not data.get("results"):
            return {
                "status": False,
                "result": "Couldn't find the country/region/state.",
            }

        data = data["results"][0]
        params = {
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "current": ["temperature_2m"],
            "timezone": "auto",
        }

        weather = (
            await client.get(
                "https://api.open-meteo.com/v1/forecast", params=params
            )
        ).json()

        return {
            "status": True,
            "result": {
                "country": data.get("country"),
                "country_code": data.get("country_code"),
                "region": data.get("admin1"),
                "subregion": data.get("admin2"),
                "population": data.get("population"),
                "timezone": weather["timezone"],
                "temperature": (
                    str(weather["current"]["temperature_2m"])
                    + weather["current_units"]["temperature_2m"]
                ),
            },
        }


@Bot.on_message(
    Config.IS_ADMIN & filters.command(["weather"], Config.CMD_PREFIXES)
)
async def weather(_: Bot, message: Message):
    action = message.command[0]
    if len(message.command) < 2:
        await message.reply(f"{Config.CMD_PREFIXES[0]}{action} [location]")
        return

    location = " ".join(message.command[1:])
    result = await get_weather(location=location)
    text = ""
    if not result["status"]:
        text = result["result"]
    else:
        data = result["result"]

        if country := data.get("country"):
            code = f" ({code})" if (code := data.get("country_code")) else ""
            text += f"Country: {country}{code}\n"

        if region := data.get("region"):
            text += f"Region: {region}\n"

        if sub := data.get("subregion"):
            text += f"District: {sub}\n"

        if pop := data.get("population"):
            text += f"Population: {pop:,}\n"

        text += "Timezone: {}\nTemperature: {}\n".format(
            data["timezone"], data["temperature"]
        )

    await message.reply(text)


__all__ = ["weather"]
__plugin__ = True
__bot_only__ = False
