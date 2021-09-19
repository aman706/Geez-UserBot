import logging

from Ironx import BOT_USERNAME
from Ironx.events import register

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.WARNING)


@register(outgoing=True, pattern=r"^\.helpme")
async def yardim(event):
    try:
        tgbotusername = BOT_USERNAME
        if tgbotusername is not None:
            results = await event.client.inline_query(tgbotusername, "@Geez-Project")
            await results[0].click(
                event.chat_id, reply_to=event.reply_to_msg_id, hide_via=True
            )
            await event.delete()
        else:
            await event.edit(
                "`The bot is not working! Please set Bot Token and Username correctly. The module has been discontinued.`"
            )
    except Exception:
        return await event.edit(
            "`You cannot send inline results in this chat (caused by SendInlineBotResultRequest)`"
        )
