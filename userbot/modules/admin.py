
from asyncio import sleep
from os import remove

from telethon.errors import (
    BadRequestError,
    ChatAdminRequiredError,
    ImageProcessFailedError,
    PhotoCropSizeSmallError,
    UserAdminInvalidError,
)
from telethon.errors.rpcerrorlist import MessageTooLongError, UserIdInvalidError
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
    EditPhotoRequest,
)
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from telethon.tl.types import (
    ChannelParticipantsAdmins,
    ChannelParticipantsBots,
    ChatAdminRights,
    ChatBannedRights,
    MessageEntityMentionName,
    MessageMediaPhoto,
    PeerChat,
)

from Ironx import BOTLOG, BOTLOG_CHATID, CMD_HELP
from Ironx.events import register

# =================== CONSTANT ===================
PP_TOO_SMOL = "`Image Too Small`"
PP_ERROR = "`Image Processing Failed`"
NO_ADMIN = "`Sorry You Are Not Admin:)`"
NO_PERM = "`Sorry You Don't Have Permission!`"
NO_SQL = "`Running In Non-SQL Mode`"

CHAT_PP_CHANGED = "`Successfully Changed Group Profile`"
CHAT_PP_ERROR = (
   "` There is a Problem With Updating Photos, `"
     "` Maybe Because You're Not an Admin, `"
     "` Or Don't Have Permission.` "
)
INVALID_MEDIA = "`Media Tidak Valid`"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)

UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)
# ================================================


@register(outgoing=True, pattern=r"^\.setgpic$")
async def set_group_photo(gpic):
    if not gpic.is_group:
        await gpic.edit("`Please Perform This Command In The Group.`")
        return
    replymsg = await gpic.get_reply_message()
    chat = await gpic.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
    photo = None

    if not admin and not creator:
        return await gpic.edit(NO_ADMIN)

    if replymsg and replymsg.media:
        await gpic.edit("`Mengubah Profil Grup`")
        if isinstance(replymsg.media, MessageMediaPhoto):
            photo = await gpic.client.download_media(message=replymsg.photo)
        elif "image" in replymsg.media.document.mime_type.split("/"):
            photo = await gpic.client.download_file(replymsg.media.document)
        else:
            await gpic.edit(INVALID_MEDIA)

    if photo:
        try:
            await gpic.client(
                EditPhotoRequest(gpic.chat_id, await gpic.client.upload_file(photo))
            )
            await gpic.edit(CHAT_PP_CHANGED)

        except PhotoCropSizeSmallError:
            await gpic.edit(PP_TOO_SMOL)
        except ImageProcessFailedError:
            await gpic.edit(PP_ERROR)


@register(outgoing=True, pattern=r"^\.promote(?: |$)(.*)")
async def promote(promt):
    # Get targeted chat
    chat = await promt.get_chat()
    # Grab admin status or creator in a chat
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, also return
    if not admin and not creator:
        return await promt.edit(NO_ADMIN)

    new_rights = ChatAdminRights(
        add_admins=False,
        invite_users=True,
        change_info=False,
        ban_users=True,
        delete_messages=True,
        pin_messages=True,
    )

    await promt.edit("`Promote User As Admin... Please Wait`")
    user, rank = await get_user_from_event(promt)
    if not rank:
        rank = "Admin"  # Just in case.
    if not user:
        return

    # Try to promote if current user is admin or creator
    try:
        await promt.client(EditAdminRequest(promt.chat_id, user.id, new_rights, rank))
        await promt.edit("`Successfully Promoted This User As Admin!`")
        await sleep(5)
        await promt.delete()

    # If Telethon spit BadRequestError, assume
    # we don't have Promote permission
    except BadRequestError:
        return await promt.edit(NO_PERM)

    # Announce to the logging group if we have promoted successfully
    if BOTLOG:
        await promt.client.send_message(
            BOTLOG_CHATID,
            "#PROMOSI\n"
            f"PENGGUNA: [{user.first_name}](tg://user?id={user.id})\n"
            f"GRUP: {promt.chat.title}(`{promt.chat_id}`)",
        )


@register(outgoing=True, pattern=r"^\.demote(?: |$)(.*)")
async def demote(dmod):
    # Admin right check
    chat = await dmod.get_chat()
