import asyncio
import random
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

from sqlite import create_profile, create_diary, edit_cmex_id, edit_cmex_iq, get_diary, db_start, get_cmex_id_iq, get_profile_by_username


async def on_startup(_):
    await db_start()


class ProfileStatesGroup(StatesGroup):
    laught_or_not = State()
    voice = State()
    answer = State()
    diary_list_state = State()
    second_voice = State()
    chat = State()


load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

storage = MemoryStorage()
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=storage)

ADMINS_ID = os.getenv('admid')
USERS_ID = os.getenv('usid')
# bot_id = os.getenv('bot_id')
# bot_id = 5894971527
questions_to_send = ['Часто ли Вы смеетесь?', 'Смеетесь ли Вы часто?']


@dp.message_handler(commands=['start'])
async def button_1(message: types.Message):
    markup = InlineKeyboardMarkup()
    await create_profile(message.from_id, message.from_user.username)
    button = InlineKeyboardButton(text='Да \U0001F44D', callback_data='first_question_yes')
    markup.add(button)
    button2 = InlineKeyboardButton(text='Нет \U0001F44E', callback_data='first_question_no')
    markup.add(button2)
    await bot.send_message(message.chat.id, "Посмеемся?", reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data == 'first_question_yes')
async def fqyes(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    await ProfileStatesGroup.voice.set()
    kb = [
        [
            types.KeyboardButton(text="Отмена")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder='Отмена запроса аудио'
    )
    await bot.send_message(call.message.chat.id,
                           'Сейчас проверим. Пришлите аудиозапись, где Вы смеетесь более 10 секунд.',
                           reply_markup=keyboard)


@dp.message_handler(content_types=['voice', 'text'], state=ProfileStatesGroup.voice)
async def load_voice(message: types.Message, state: FSMContext):
    kb = [
        [
            types.KeyboardButton(text="\U0001F606 Профиль"),
            types.KeyboardButton(text="\U0001F4DD Дневник наблюдений")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder='Меню'
    )

    if message.voice:
        async with state.proxy() as data:
            data['voice'] = message.voice.file_id
            if message.voice.duration > 10:
                await edit_cmex_id(user_id=message.from_id)
                await edit_cmex_iq(message.from_id, round(message.voice.duration/10, 2))

                await message.reply("Вы отлично смеетесь! Присоединяйтесь к нашему сообществу, где мы смеемся вместе,"
                                " а также проводим различные конкурсы и делимся наблюдениями."
                                "Ссылка на чат: (скину ниже)", reply_markup=keyboard)
            else:
                await message.reply("Смех не достаточно долгий.", reply_markup=keyboard)
    else:
        await message.reply("Прием аудиозаписи отменен.", reply_markup=keyboard)

    await state.reset_state(with_data=False)


@dp.callback_query_handler(lambda c: c.data == 'first_question_no')
async def fqno(call: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(call.id)
    kb = [
        [
            types.KeyboardButton(text="\U0001F606 Профиль"),
            types.KeyboardButton(text="\U0001F4DD Дневник наблюдений")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder='Меню'
    )

    await bot.send_message(call.message.chat.id, "Главное меню", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "\U0001F606 Профиль")
async def show_profile(message: types.Message):
    cmex_id, cmex_iq = await get_cmex_id_iq(message.from_id)
    await bot.send_message(message.chat.id, "\U0001F606 Ваш профиль \n"
                                            "\n"
                                            f"\U00002B50 Смех ID: {cmex_id[0]}\n"
                                            f"🤓 Смех IQ: {cmex_iq[0]}")


@dp.message_handler(lambda message: message.text == "\U0001F4DD Дневник наблюдений")
async def show_diary(message: types.Message, state: FSMContext):
    await ProfileStatesGroup.diary_list_state.set()
    mes_list = await get_diary(message.from_id)
    if mes_list.fetchall():
        async with state.proxy() as data:
            data['diary_index'] = 0
            data['diary'] = mes_list.fetchall()
            text_to_send = f"{data['diary'][data['diary_index']][1]}\nОтвет: {data['diary'][data['diary_index']][2]}"
        offers_kb = InlineKeyboardMarkup()
        forward = InlineKeyboardButton("Вперед", callback_data="forward_offers")
        middle = InlineKeyboardButton("Отмена", callback_data='cans')
        back = InlineKeyboardButton("Назад", callback_data="back_offers")
        offers_kb.row(back, middle, forward)
        await bot.send_message(message.chat.id, text_to_send, reply_markup=offers_kb)
    else:
        text_to_send = 'В дневнике еще нет записей'
        await bot.send_message(message.chat.id, text_to_send)
        await state.reset_state(with_data=False)


@dp.callback_query_handler(lambda c: c.data == 'forward_offers', state=ProfileStatesGroup.diary_list_state)
async def forward(call: types.callback_query, state: FSMContext):
    async with state.proxy() as data:
        data['diary_index'] += 1
        diary_length = len(data['diary']) - 1
        if diary_length < data['diary_index']:
            data['diary_index'] = 0
        text_to_send = f"{data['diary'][data['diary_index']][1]}\nОтвет: {data['diary'][data['diary_index']][2]}"
    offers_kb = InlineKeyboardMarkup()
    forward = InlineKeyboardButton("Вперед", callback_data="forward_offers")
    middle = InlineKeyboardButton("Отмена", callback_data='cans')
    back = InlineKeyboardButton("Назад", callback_data="back_offers")
    offers_kb.row(back, middle, forward)
    await bot.edit_message_text(text_to_send, call.message.chat.id, call.message.message_id, reply_markup=offers_kb)


@dp.callback_query_handler(lambda c: c.data == 'back_offers', state=ProfileStatesGroup.diary_list_state)
async def prev(call: types.callback_query, state: FSMContext):
    async with state.proxy() as data:
        data['diary_index'] -= 1
        if data['diary_index'] < 0:
            data['diary_index'] = len(data['diary']) - 1
        text_to_send = f"{data['diary'][data['diary_index']][1]}\nОтвет: {data['diary'][data['diary_index']][2]}"
    offers_kb = InlineKeyboardMarkup()
    forward = InlineKeyboardButton("Вперед", callback_data="forward_offers")
    middle = InlineKeyboardButton("Отмена", callback_data='cans')
    back = InlineKeyboardButton("Назад", callback_data="back_offers")
    offers_kb.row(back, middle, forward)
    await bot.edit_message_text(text_to_send, call.message.chat.id, call.message.message_id, reply_markup=offers_kb)


@dp.callback_query_handler(lambda c: c.data == 'cans', state=ProfileStatesGroup.diary_list_state)
async def prev(call: types.callback_query, state: FSMContext):
    await state.reset_state(with_data=False)    # await bot.send_message(message.chat.id, message.text)
    await bot.send_message(call.message.chat.id, 'Вы вышли из дневника наблюдений')


async def for_periodic1(chat_ids):
    while True:
        times_to_repeat = random.randint(1, 2)
        day = 60*60*24
        for i in range(times_to_repeat):
            sleeping_period = random.randint(0, day)
            await asyncio.sleep(sleeping_period)
            day -= sleeping_period
            await periodic1(chat_ids)
            if i == 1:
                await asyncio.sleep(day)


async def periodic1(chat_ids):
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='Да \U0001F44D', callback_data='double_first_question_yes')
    markup.add(button)
    button2 = InlineKeyboardButton(text='Нет \U0001F44E', callback_data='double_first_question_no')
    markup.add(button2)

    for id_u in chat_ids:
        await bot.send_message(id_u, "Посмеемся?", reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data == 'double_first_question_yes')
async def dfqyes(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    await ProfileStatesGroup.second_voice.set()
    kb = [
        [
            types.KeyboardButton(text="Отмена")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder='Отмена запроса аудио'
    )
    await bot.send_message(call.message.chat.id,
                           'Сейчас проверим. Пришлите аудиозапись, где Вы смеетесь более 10 секунд.',
                           reply_markup=keyboard)


@dp.message_handler(content_types=['voice', 'text'], state=ProfileStatesGroup.second_voice)
async def load_voice(message: types.Message, state: FSMContext):
    kb = [
        [
            types.KeyboardButton(text="\U0001F606 Профиль"),
            types.KeyboardButton(text="\U0001F4DD Дневник наблюдений")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder='Меню'
    )

    if message.voice:
        status = await get_cmex_id_iq(message.from_id)
        if status[0] == 'СмехоЖдун':
            await message.reply("Вы отлично смеетесь! Присоединяйтесь к нашему сообществу, где мы смеемся вместе,"
                    " а также проводим различные конкурсы и делимся наблюдениями."
                    "Ссылка на чат: (скину ниже)")

        await edit_cmex_id(user_id=message.from_id)
        await edit_cmex_iq(message.from_id, round(message.voice.duration/10, 2))
        await message.reply(f"Поздравляем! Ваш Смех IQ вырос на {round(message.voice.duration/10, 2)}", reply_markup=keyboard)

    else:
        await message.reply("Прием аудиозаписи отменен", reply_markup=keyboard)

    await state.reset_state(with_data=False)


@dp.callback_query_handler(lambda c: c.data == 'double_first_question_no')
async def dfqno(call: types.callback_query, state: FSMContext):
    await bot.answer_callback_query(call.id)
    kb = [
        [
            types.KeyboardButton(text="\U0001F606 Профиль"),
            types.KeyboardButton(text="\U0001F4DD Дневник наблюдений")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder='Меню'
    )

    await bot.send_message(call.message.chat.id, "Главное меню", reply_markup=keyboard)


async def periodic2(sleep_for, chat_ids, questions):
    i = 0
    while True:
        await asyncio.sleep(sleep_for)
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='Ответить \U0001F60C', callback_data='bot_question2')
        markup.add(button)

        for id in chat_ids:
            await bot.send_message(id, questions[i], reply_markup=markup)
        i += 1
        if len(questions) - 1 < i:
            i = 0


@dp.callback_query_handler(lambda c: c.data == 'bot_question2')
async def quest2(call: types.callback_query, state: FSMContext):
    async with state.proxy() as data:
        data['question_for_diary'] = call.message.text
        data['profile_id'] = call.message.chat.id
    await bot.answer_callback_query(call.id)

    await ProfileStatesGroup.answer.set()
    await bot.send_message(call.message.chat.id, 'Введите, пожалуйста, ответ')


@dp.message_handler(content_types=['text'], state=ProfileStatesGroup.answer)
async def answer2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['answer'] = message.text
        await create_diary(
            question=data['question_for_diary'],
            response=data['answer'],
            profile_id=data['profile_id']
        )
    await state.reset_state(with_data=False)


@dp.message_handler(commands=['ball'])
@dp.message_handler(lambda message: 'Благодарю' in message.text)
async def channel_ball(message: types.Message):
    await ProfileStatesGroup.chat.set()
    await bot.send_message(message.chat.id, 'Введите список юзернеймов через запятую и пробел, без точки в конце')


@dp.message_handler(content_types=['text'], state=ProfileStatesGroup.chat)
async def chat_usernames(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMINS_ID:
        username_list = message.text.split(' ')
        cleaned_list = [i.strip(',') for i in username_list]
        for un in cleaned_list:
            user_id = await get_profile_by_username(un)
            if user_id[0]:
                await edit_cmex_iq(user_id[0], 30)
                await bot.send_message(user_id[0], 'Поздравляем! Ваш Смех IQ вырос на 30')
    await state.finish()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(periodic2(60*60*24, chat_ids=USERS_ID, questions=questions_to_send))
        loop.create_task(for_periodic1(USERS_ID))
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except (KeyboardInterrupt, SystemExit):
        pass
