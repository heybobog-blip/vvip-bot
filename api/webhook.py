import os
import json
import asyncio
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from http.server import BaseHTTPRequestHandler
import nest_asyncio

# =================ตั้งค่าข้อมูลระบบ=================
TOKEN = "8456991861:AAHHFhU2hP7ftrm_s_hYi2VhchnN9zG0KUw"
ADMIN_GROUP_ID = -1003548598788
LIVE_ROOM_ID = -1003600215785
ADMIN_CONTACT_1 = "https://t.me/Zienramok"
ADMIN_CONTACT_2 = "https://t.me/ZeinJojackpod"

# ลิ้งค์รูปภาพหน้าแรก
WELCOME_IMAGE = "https://img2.pic.in.th/Gemini_Generated_Image_ltb4kiltb4kiltb4-copy.jpg"

# ลิ้งค์เว็บฝากเงิน
WEB_LINK = "https://huayok.com/r/tvsxrm"

# =================ส่วนการทำงานของบอท=================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ข้อความต้อนรับ
    caption_text = f"""
✨ **ขั้นตอนเข้ากลุ่ม VIP LIVE ขงเบ้งนำทัพ** ✨
━━━━━━━━━━━━━━━━━━
📢 **กติกาและวิธีการเข้ากลุ่ม**

1️⃣ **สมัคร/ฝากเงิน** กับเว็บ HuayOK
👉 (กดปุ่ม "💰 สมัครสมาชิก / ฝากเงิน" ด้านล่าง)

2️⃣ **ทำรายการฝากเงิน** ให้เรียบร้อย
👉 ยอดฝากขั้นต่ำ 100 บาทขึ้นไป

3️⃣ **ส่งรูปสลิป** หรือหลักฐานการโอน
👉 ส่งเข้ามาในแชทนี้ได้เลย

4️⃣ **รอแอดมินตรวจสอบ**
👉 เมื่ออนุมัติแล้ว บอทจะส่ง **"ปุ่มกดเข้ากลุ่ม"** ให้ทันที!

👇 **เริ่มรายการกดปุ่มด้านล่าง** 👇 (เข้ากลุ่มไปแล้วจะอยู่ได้ 24 ชม. นะครับ)
"""
    keyboard = [
        [InlineKeyboardButton("💰 สมัครสมาชิก / ฝากเงิน (กดเลย)", url=WEB_LINK)],
        [InlineKeyboardButton("👤 ติดต่อแอดมิน 1", url=ADMIN_CONTACT_1), InlineKeyboardButton("👤 ติดต่อแอดมิน 2", url=ADMIN_CONTACT_2)]
    ]
    
    await context.bot.send_photo(
        chat_id=update.effective_chat.id, 
        photo=WELCOME_IMAGE,
        caption=caption_text, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

async def handle_slip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not update.message.photo:
        return

    photo = update.message.photo[-1].file_id
    caption = update.message.caption if update.message.caption else "-"
    
    # ดึงเวลาปัจจุบัน (ไทย)
    tz = pytz.timezone('Asia/Bangkok')
    now_str = datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S')

    # ข้อมูลลูกค้าเพิ่มเติม
    username = f"@{user.username}" if user.username else "ไม่มี Username"
    language = user.language_code if user.language_code else "ไม่ระบุ"
    is_premium = "⭐️ Yes" if user.is_premium else "No"
    
    user_info = (
        f"📅 <b>เวลาส่ง:</b> {now_str}\n"
        f"👤 <b>ชื่อ:</b> {user.first_name} {user.last_name or ''}\n"
        f"🔗 <b>User:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"🌐 <b>ภาษา:</b> {language} | 💎 <b>Premium:</b> {is_premium}\n"
        f"📝 <b>ข้อความแนบ:</b> {caption}"
    )

    admin_keyboard = [
        [
            InlineKeyboardButton("✅ อนุมัติ (ส่งลิ้งค์)", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ ปฏิเสธ", callback_data=f"reject_{user.id}")
        ]
    ]

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_GROUP_ID,
            photo=photo,
            caption=f"📩 <b>ได้รับสลิปใหม่!</b>\n━━━━━━━━━━━━\n{user_info}",
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode='HTML'
        )
        await update.message.reply_text("📥 <b>ได้รับสลิปแล้วครับ</b>\n⏳ กรุณารอสักครู่ แอดมินกำลังตรวจสอบ...", parse_mode='HTML')
    except Exception as e:
        print(f"Error sending to admin: {e}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    action, target_user_id = data.split("_")
    target_user_id = int(target_user_id)

    if action == "approve":
        try:
            # สร้างลิ้งค์
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=LIVE_ROOM_ID, 
                member_limit=1,
                name=f"User_{target_user_id}"
            )

            user_kb = [
                [InlineKeyboardButton("🔥 เข้ากลุ่ม VIP ขงเบ้ง (กดได้ครั้งเดียว) 🔥", url=invite_link.invite_link)]
            ]

            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ <b>ตรวจสอบเรียบร้อย!</b>\n\nยินดีด้วยครับ คุณได้รับสิทธิ์เข้ากลุ่ม 👑\nกรุณากดปุ่มด้านล่างเพื่อเข้ากลุ่มทันทีครับ 👇",
                reply_markup=InlineKeyboardMarkup(user_kb),
                parse_mode='HTML'
            )

            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n✅ <b>อนุมัติเรียบร้อยโดย:</b> {query.from_user.first_name}",
                parse_mode='HTML'
            )

        except Exception as e:
            await query.message.reply_text(f"⚠️ เกิดข้อผิดพลาด: {e}")

    elif action == "reject":
        try:
            # 🔥🔥🔥 เพิ่มปุ่มติดต่อแอดมินตรงนี้ครับ 🔥🔥🔥
            reject_kb = [
                [InlineKeyboardButton("👤 ติดต่อแอดมิน 1", url=ADMIN_CONTACT_1)],
                [InlineKeyboardButton("👤 ติดต่อแอดมิน 2", url=ADMIN_CONTACT_2)]
            ]

            await context.bot.send_message(
                chat_id=target_user_id,
                text="❌ <b>สลิปไม่ผ่านการอนุมัติ</b>\nโปรดติดต่อแอดมินเพื่อตรวจสอบข้อมูลเพิ่มเติมครับ",
                reply_markup=InlineKeyboardMarkup(reject_kb), # ใส่ปุ่มเข้าไป
                parse_mode='HTML'
            )

            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n❌ <b>ปฏิเสธโดย:</b> {query.from_user.first_name}",
                parse_mode='HTML'
            )
        except:
            await query.message.reply_text("⚠️ แจ้งเตือนลูกค้าไม่ได้")

# =================ส่วนเชื่อมต่อ Vercel=================
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len)
        
        try:
            json_string = post_body.decode('utf-8')
            update_data = json.loads(json_string)
        except:
            self.send_response(500)
            self.end_headers()
            return

        async def main():
            app = ApplicationBuilder().token(TOKEN).build()
            app.add_handler(CommandHandler('start', start))
            app.add_handler(MessageHandler(filters.PHOTO, handle_slip))
            app.add_handler(CallbackQueryHandler(button_click))
            
            await app.initialize()
            await app.process_update(Update.de_json(update_data, app.bot))
            await app.shutdown()

        nest_asyncio.apply()
        
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Main Error: {e}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running via Webhook! (Reject Button Update)")
