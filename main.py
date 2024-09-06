TEST_TOKEN = "7373519023:AAGHAMx01azAa4XRtG_QP3JApqLLEcxFsSg"
MAIN_TOKEN = '7129795991:AAHb793O24B1UvI0c-TlGQ-m_e1zDFM0x08'

dp = Dispatcher()


@dp.message(Command('start'))
async def start_command(message: types.Message, state: FSMContext):
    kb = start_logic()
    await message.answer("Выберите действие", reply_markup=kb.as_markup())


@dp.callback_query(F.data == "back", CalculatePrice.start)
async def start_command(callback: CallbackQuery, state: FSMContext):
    kb = start_logic()
    await callback.message.answer("Выберите действие", reply_markup=kb.as_markup())






async def main(token: str) -> None:
    global bot
    if token == "test":
        bot = Bot(TEST_TOKEN)
        await dp.start_polling(bot)
    else:
        bot = Bot(MAIN_TOKEN)
        await dp.start_polling(bot)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <token>")
    else:
        try:
            TOKEN = sys.argv[1]
            asyncio.run(main(TOKEN))
        except Exception as e:
            logging.exception(f"Произошла ошибка: {e}")
            print(f"Произошла ошибка: {e}")