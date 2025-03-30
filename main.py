import asyncio
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command
from tinydb import TinyDB, Query
import json

def format_database():
    with open("database.json", "r", encoding="utf-8") as file:
        data = json.load(file)  # JSON faylni yuklash

    with open("database.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)  # Chiroyli formatda saqlash

format_database()




TOKEN = "8094890103:AAHdT2MYY1QzJ7GLtm5K7eLNryTjg1vAuQk"
ADMIN_IDS = [5359507225]

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = TinyDB("database.json")
users = db.table("users")


def register_user(user_id, username):
    user = users.get(Query().id == user_id)
    if not user:
        users.insert({"id": user_id, "balance": 3000, "last_bonus": "", "username": username})
        return True
    return False


@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"User-{user_id}"
    user = users.get(Query().id == user_id)

    if not user:
        users.insert({"id": user_id, "balance": 3000, "last_bonus": "", "username": username})
        await message.answer(
            "Xush kelibsiz 😊 \n Sizga boshlang‘ich 3000 coin berildi!")
    else:
        await message.answer("Siz allaqachon ro‘yxatdan o‘tgansiz 😉")


@dp.message(Command("balance"))
async def balance(message: Message):
    user = users.get(Query().id == message.from_user.id)
    if user:
        await message.answer(f"\U0001F4B0 Sizning balansingiz: {user['balance']} ")
    else:
        await message.answer("\U0001F6A8 Siz ro‘yxatdan o‘tmagansiz! \n /start bosib ro'yxatdan o'tishingiz mumkin!")


@dp.message(Command("top"))
async def top(message: Message):
    all_users = users.all()
    total_users = len(all_users)  # Jami foydalanuvchilar soni

    # 1️⃣ Balansi 0 dan katta foydalanuvchilarni tartiblash
    rich_users = sorted(
        [user for user in all_users if user.get('balance', 0) > 0],
        key=lambda x: x['balance'], reverse=True
    )

    # 2️⃣ Agar balansi borlar 10 tadan kam bo‘lsa, 0 balansdagilarni ham qo‘shish
    if len(rich_users) < 10:
        zero_users = sorted(
            [user for user in all_users if user.get('balance', 0) == 0],
            key=lambda x: x['id']
        )
        top_users = rich_users + zero_users[:10 - len(rich_users)]
    else:
        top_users = rich_users[:10]

    # 3️⃣ Ro‘yxatni shakllantirish
    leaderboard = "🏆 TOP 10 o‘yinchilar:\n"
    for i, user in enumerate(top_users, 1):
        username = user.get('username', f"User-{user['id']}")
        balance = user.get('balance', 0)
        leaderboard += f"{i}. {username} - {balance} coin\n"

    # 4️⃣ Jami foydalanuvchilarni ko‘rsatish
    leaderboard += f"\n👥 Jami foydalanuvchilar: {total_users}"

    await message.answer(leaderboard)




@dp.message(Command("daily_bonus"))
async def daily_bonus(message: Message):
    user_id = message.from_user.id
    user = users.get(Query().id == user_id)
    if user:
        last_bonus = user.get('last_bonus', "")
        today = datetime.now().strftime('%Y-%m-%d')
        if last_bonus == today:
            await message.answer("⚠️ Siz bugungi bonusni oldingiz, ertagacha sabr qiling!")
        else:
            bonus = random.randint(3000, 5000)
            users.update({'balance': user['balance'] + bonus, 'last_bonus': today}, Query().id == user_id)
            await message.answer(f"🎉 Kunlik {bonus} bonus oldingiz 😁")
    else:
        await message.answer("🚨 Siz ro‘yxatdan o‘tmagansiz! /start bosib ro'yxatdan o'tishingiz mumkin!")


@dp.message(Command("status"))
async def status(message: Message):
    user_id = message.from_user.id
    user = users.get(Query().id == user_id)

    if user:
        await message.answer(
            f"📊 Sizning ma’lumotlaringiz:\n👤 Username: @{user['username']}\n💰 Balans: {user['balance']} "
        )
    else:
        await message.answer("🚨 Siz ro‘yxatdan o‘tmagansiz! /start bosib ro'yxatdan o'tishingiz mumkin!")


@dp.message(Command("give"))
async def give(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🚫 Sizga bu buyruqni ishlatish huquqi yo‘q!")
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("🚨 Noto'g'ri foydalanish: /give ")
        return

    amount = int(args[1])

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user = users.get(Query().id == user_id)

        if user:
            users.update({'balance': user['balance'] + amount}, Query().id == user_id)
            await message.answer(f"✅ {amount} coin @{message.reply_to_message.from_user.username} foydalanuvchiga berildi!")
        else:
            await message.answer("🚨 Foydalanuvchi bazada topilmadi!")
    else:
        await message.answer("🚨 Iltimos, foydalanuvchini belgilab yuboring!")


@dp.message(Command("delete"))
async def delete(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("🚫 Sizga bu buyruqni ishlatish huquqi berilmagan!")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        users.update({'balance': 0}, Query().id == user_id)
        await message.answer(f"❌ @{message.reply_to_message.from_user.username} ning balansi 0 qilindi!")
    else:
        await message.answer("🚨 Iltimos, foydalanuvchini belgilab yuboring!")


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer("📌 Buyruqlar ro‘yxati:\n\n"
                         "/start - O‘yinni boshlash\n"
                         "/balance - Balansni tekshirish\n"
                         "/top - O'yinchilar reytingi\n"
                         "/daily_bonus - Kunlik bonus olish\n"
                         "/status - Foydalanuvchi ma'lumotlri\n"
                         "/help - Qo‘llanma")

@dp.message()
async def handle_games(message: Message):
    user_id = message.from_user.id
    user = users.get(Query().id == user_id)
    if not user:
        return

    text = message.text.split()
    if len(text) < 2 or not text[1].isdigit():
        return

    bet = int(text[1])
    if bet > user['balance'] or bet <= 0:
        await message.answer("🚨 Sizda yetarli coin yo‘q yoki noto‘g‘ri miqdor!")
        return

    if text[0] == "!b":
        dice_msg = await message.answer_dice(emoji='🏀')
        await asyncio.sleep(3)

        if dice_msg.dice.value in [4, 5]:
            win_amount = bet * random.randint(2, 3)
            users.update({'balance': user['balance'] + win_amount}, Query().id == user_id)
            await message.answer(f"🎉 G‘alaba! Siz {win_amount} coin yutdingiz! ")
        else:
            users.update({'balance': user['balance'] - bet}, Query().id == user_id)
            await message.answer("Yutqazdingiz 😢 \n Omadingizni yana sinab ko‘ring!")





    elif text[0] == "!tqq":
        choices = ["tosh", "qog‘oz", "qaychi"]
        user_choice = random.choice(choices)
        bot_choice = random.choice(choices)
        if user_choice == bot_choice:
            result = "🤝 Durang!"
        elif (user_choice == "tosh" and bot_choice == "qaychi") or \
                (user_choice == "qog‘oz" and bot_choice == "tosh") or \
                (user_choice == "qaychi" and bot_choice == "qog‘oz"):
            users.update({'balance': user['balance'] + bet}, Query().id == user_id)
            result = f"🎉 G‘alaba! Siz {bet} coin yutdingiz!"
        else:
            users.update({'balance': user['balance'] - bet}, Query().id == user_id)
            result = "😢 Yutqazdingiz!"
        await message.answer(f"Siz: {user_choice}, Bot: {bot_choice}\n{result}")





    elif text[0] == "!goal":

        dice_msg = await message.answer_dice(emoji='⚽')  # Futbol animatsiyasi

        await asyncio.sleep(3)

        if dice_msg.dice.value > 3:  # Telegram random qiymat qaytaradi

            users.update({'balance': user['balance'] + bet * 2}, Query().id == user_id)

            await message.answer(f"⚽ G‘alaba! Siz {bet * 2} coin yutdingiz!")

        else:

            users.update({'balance': user['balance'] - bet}, Query().id == user_id)

            await message.answer("😢 Gol ura olmadingiz!")





    elif text[0] == "!survive":

        dice_msg = await message.answer_dice(emoji='🎯')  # Nishonga urish animatsiyasi

        await asyncio.sleep(3)

        if dice_msg.dice.value == 6:  # Agar o‘q markazga tegsa

            users.update({'balance': user['balance'] + int(bet * 2.5)}, Query().id == user_id)

            await message.answer(f"🔫 Siz omon qoldingiz! {int(bet * 2.5)} coin yutdingiz!")

        else:

            users.update({'balance': user['balance'] - bet}, Query().id == user_id)

            await message.answer("💀 Siz yutqazdingiz!")





    elif text[0] == "!slot":

        dice_msg = await message.answer_dice(emoji='🎰')  # Slot animatsiyasi

        await asyncio.sleep(3)

        if dice_msg.dice.value in [64, 1]:  # 64 Jackpot, 1 ham yutuqli kombinatsiya

            win_amount = bet * 5

            users.update({'balance': user['balance'] + win_amount}, Query().id == user_id)

            await message.answer(f"🎰 Jackpot! {win_amount} coin yutdingiz! 🎉")

        elif dice_msg.dice.value in [22, 43]:  # O‘rtacha kombinatsiyalar

            win_amount = bet * 2

            users.update({'balance': user['balance'] + win_amount}, Query().id == user_id)

            await message.answer(f"🎰 O‘rtacha g‘alaba! {win_amount} coin yutdingiz! 😊")

        else:

            users.update({'balance': user['balance'] - bet}, Query().id == user_id)

            await message.answer(f"🎰 😢 Omadsizlik!")



async def main():
    print("🤖 Bot ishga tushdi...")
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        print("❌ Bot to‘xtatildi!")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    import sys

    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())

