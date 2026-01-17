import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from http.server import BaseHTTPRequestHandler

# =================ตั้งค่าข้อมูลระบบ=================
# ใส่ Token ที่คุณให้มา
TOKEN = "8456991861:AAHHFhU2hP7ftrm_s_hYi2VhchnN9zG0KUw"

# ห้องแอดมิน (สำหรับส่งสลิปไปให้ตรวจ)
ADMIN_GROUP_ID = -1003548598788

# ห้องไลฟ์สด (ที่จะเจนลิ้งค์ให้ลูกค้า)
LIVE_ROOM_ID = -1003600215785

# ข้อมูลติดต่อแอดมิน
ADMIN_CONTACT_1 = "https://t.me/Zienramok"
ADMIN_CONTACT_2 = "https://t.me/ZeinJojackpod"

# =================ส่วนการทำงานของบอท=================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
✨ **ยินดีต้อนรับสู่ระบบรับเข้ากลุ่ม VVIP** ✨
━━━━━━━━━━━━━━━━━━
📢 **กติกาการใช้งาน**
1. โอนเงินตามยอดที่ตกลง
2. **ส่งรูปสลิปการโอนเงิน** เข้ามาในแชทนี้
3. รอแอดมินตรวจสอบและกดอนุมัติ
4. เมื่ออนุมัติแล้ว บอทจะส่งลิ้งค์เข้ากลุ่มให้ทันที!

💬 **มีปัญหาติดต่อแอดมิน**
👇 กดปุ่มด้านล่าง
"""
    keyboard = [
        [InlineKeyboardButton("👤 ติดต่อแอดมิน 1", url=ADMIN_CONTACT_1)],
        [InlineKeyboardButton("👤 ติดต่อแอดมิน 2", url=ADMIN_CONTACT_2)]
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=text, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

async def handle_slip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ลูกค้าส่งรูปมา
    user = update.message.from_user
    photo = update.message.photo[-1].file_id # เอาความละเอียดสูงสุด
    caption = update.message.caption if update.message.caption else "-"
    
    user_info = f"👤 <b>ลูกค้า:</b> {user.first_name} {user.last_name or ''}\n🆔 <b>ID:</b> <code>{user.id}</code>\n📝 <b>ข้อความ:</b> {caption}"

    # สร้างปุ่มให้แอดมินตัดสินใจ
    admin_keyboard = [
        [
            InlineKeyboardButton("✅ อนุมัติ (ส่งลิ้งค์)", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ ปฏิเสธ", callback_data=f"reject_{user.id}")
        ]
    ]

    # ส่งสลิปไปห้องแอดมิน
    await context.bot.send_photo(
        chat_id=ADMIN_GROUP_ID,
        photo=photo,
        caption=f"📩 <b>ได้รับสลิปใหม่!</b>\n\n{user_info}",
        reply_markup=InlineKeyboardMarkup(admin_keyboard),
        parse_mode='HTML'
    )

    # ตอบกลับลูกค้าว่าได้รับแล้ว
    await update.message.reply_text("📥 <b>ได้รับสลิปแล้วครับ</b>\n⏳ กรุณารอสักครู่ แอดมินกำลังตรวจสอบ...", parse_mode='HTML')

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # แยกคำสั่งกับ ID ลูกค้า (เช่น approve_123456)
    action, target_user_id = data.split("_")
    target_user_id = int(target_user_id)

    if action == "approve":
        try:
            # 1. สร้างลิ้งค์เข้าห้อง LIVE (กดได้ 1 ครั้ง)
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=LIVE_ROOM_ID, 
                member_limit=1,
                name=f"User_{target_user_id}"
            )

            # 2. ส่งลิ้งค์ให้ลูกค้าทาง Inbox
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ <b>ตรวจสอบเรียบร้อย!</b>\n\nยินดีด้วยครับ คุณได้รับสิทธิ์เข้ากลุ่ม 👑\n👇 <b>กดเข้ากลุ่มได้ที่นี่ (ลิ้งค์กดได้ครั้งเดียว):</b>\n{invite_link.invite_link}",
                parse_mode='HTML'
            )

            # 3. อัพเดทข้อความในห้องแอดมิน
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n✅ <b>อนุมัติเรียบร้อยโดย:</b> {query.from_user.first_name}",
                parse_mode='HTML'
            )

        except Exception as e:
            await query.message.reply_text(f"⚠️ เกิดข้อผิดพลาด: {e}\n(ลูกค้าอาจบล็อกบอท หรือบอทไม่ได้เป็นแอดมินในกลุ่มเป้าหมาย)")

    elif action == "reject":
        try:
            # 1. แจ้งเตือนลูกค้า
            await context.bot.send_message(
                chat_id=target_user_id,
                text="❌ <b>สลิปไม่ผ่านการอนุมัติ</b>\nโปรดติดต่อแอดมินเพื่อตรวจสอบข้อมูลเพิ่มเติมครับ",
                parse_mode='HTML'
            )

            # 2. อัพเดทข้อความในห้องแอดมิน
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n❌ <b>ปฏิเสธโดย:</b> {query.from_user.first_name}",
                parse_mode='HTML'
            )
        except:
            await query.message.reply_text("⚠️ แจ้งเตือนลูกค้าไม่ได้ (อาจบล็อกบอท)")

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
            
            # Process update
            await app.process_update(Update.de_json(update_data, app.bot))

        # รัน Async Loop
        import nest_asyncio
        nest_asyncio.apply()
        
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Error: {e}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running via Webhook!")
