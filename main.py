import telebot
import time
import decimal
import copy
import json
import os
from telebot import types
from collections import defaultdict

token = ''
bot = telebot.TeleBot(token)
price = defaultdict(list)
debt_book = defaultdict(dict)
keys_names = defaultdict(dict)
changer = defaultdict(list)
name = {}
equals = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_sticker(message.chat.id, open(r"C:\Users\HONOR\PycharmProjects\Bot-schitovod\sticker.webp", 'rb'))
    bot.send_message(message.chat.id,
                     f'Привет, {message.from_user.first_name}, я помогу тебе вытрясти все с твоего товарища💸'
                     f'А так же буду вести твою долговую книжку 📕!',
                     reply_markup=keyboard())


@bot.message_handler(content_types=['text'])
def counting(message):
    command = message.text
    if message.text == '💰 Посчитать чек':
        debtor = bot.send_message(message.chat.id, 'Введи имя того с кем будет вестись расчет.')
        bot.register_next_step_handler(debtor, note, command)

    elif message.text == 'Список 📃' or message.text == '✏ Изменить запись':
        answer = ''
        if len(debt_book[message.from_user.id]) == 0:
            bot.send_message(message.chat.id, '(Список пуст)')
        for key_name in debt_book[message.from_user.id]:
            result = 0
            show_list = debt_book[message.from_user.id][key_name].copy()
            for i in range(len(show_list)):
                if i == 0:
                    answer += key_name.title() + '\n'
                answer += f'{i + 1}) {(beautiful(show_list[i][0]))}{show_list[i][2]:^20}{show_list[i][1]}\n'
                result += show_list[i][0]
            answer += f'Итог: {beautiful(result)}\n\n'
        bot.send_message(message.chat.id, answer)
        if message.text == '✏ Изменить запись':
            redact = bot.send_message(message.chat.id, 'Введите имя, номер записи, сумму и коментарий через пробел:')
            bot.register_next_step_handler(redact, note_change)

    elif message.text == 'Объеденить список 🔗':
        name_comp = bot.send_message(message.chat.id, f'Введите имя с кем хотите объеденить список:')
        bot.register_next_step_handler(name_comp, note, command)

    elif message.text == 'Очистить список 🧨':
        if len(debt_book[message.from_user.id]) == 0:
            bot.send_message(message.chat.id, '(Список пуст)')
        else:
            names = []
            [names.append(x.title()) for x in debt_book[message.from_user.id].keys()]
            name_del = bot.send_message(message.chat.id, f'Введите имя с кем вы хотите удалить список\n{names}')
            bot.register_next_step_handler(name_del, note, command)

    elif message.text == '🆘 Help':
        bot.send_message(message.chat.id, '''
        Этот бот помогает вести долговую книжу, а также расчитывать чеки и делится списком записей с друзьями.
         Каждая запись включает в себя сумму, коментарий и дату внесения записи.

        Для внесения новой записи достаточно лишь отправить сообщение с 3мя состовляющими (Имя, сумма, коментарий) 
        через пробел. При вашей задолженности используйте '-' перед суммой.

        Примеры ввода:
        Иван 500 такси
        Иван 300 шаурма
        Иван -800 возврат долга

        Список 📃:
        Иван
        1) 500.0               такси          21:51(МСК)   31.01.2023
        2) 300.0              шаурма          21:51(МСК)   31.01.2023
        3) -800.0          возврат долга      21:52(МСК)   31.01.2023
        Итог: 0.0

        Хранить список с нулевым значением не имеет смысла по этому можно использовать функцию "Очистить список 🧨"

        (💰 Посчитать чек)            
        Помогает высчитать задолженность при совместном походе в магазин и покупке общих продуктов вместе с
        личными или при походе в ресторан.Общие затраты расчитываются поровну, личные записываются на счет владельца.

        (Список 📃)
        Отображает имеющиеся записи по именам.

        (Очистить список 🧨)
        Очищает нужный нам список

        (Объеденить список 🔗)
        Позволяет объеденить список с определнным пользователем, для совместного ведения списка.

        (✏ Изменить запись)
        Меняет запись. Ответ ожидается в формате:
        (Иван 2 2000 до зарплаты) без скобочек
        ''')

    elif len(message.text.split()) >= 3:
        notes = message.text.split()
        value = notes[1].replace(',', '.')
        seconds = time.time() + 10800
        name[message.from_user.id] = notes[0].lower()
        tform = time.strftime('%H:%M(МСК)  %d.%m', time.localtime(seconds))
        if value.replace('.', '').isdigit() or value[1:].replace('.', '').isdigit():
            if message.from_user.id not in debt_book:
                debt_book[message.from_user.id] = {}
            if name[message.from_user.id] not in debt_book[message.from_user.id]:
                debt_book[message.from_user.id][notes[0].lower()] = []
            debt_book[message.from_user.id][notes[0].lower()].append([float(value), tform, ' '.join(notes[2:])])
            bot.send_message(message.chat.id, 'Запись сохранена.')
            save_to_file()
        else:
            bot.send_message(message.chat.id, 'Сумма не корректна.')
        check_keys(message)
    else:
        bot.send_message(message.chat.id, 'Команда не распознана.')


def note(message, command):
    name[message.from_user.id] = message.text.lower()
    if message.from_user.id not in debt_book:
        debt_book[message.from_user.id] = defaultdict(list)

    if command == '💰 Посчитать чек':
        price[message.from_user.id].clear()
        check = bot.send_message(message.chat.id, 'Введи сумму чека🧾, который нужно посчитать.')
        bot.register_next_step_handler(check, his_purch)

    elif command == 'Очистить список 🧨':
        keypad = types.InlineKeyboardMarkup()
        keypad.add(types.InlineKeyboardButton('Да', callback_data='delete'))
        bot.send_message(message.chat.id, 'Вы уверены, что хотите очистить список ?', reply_markup=keypad)

    elif command == 'Объеденить список 🔗':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Принимаю', callback_data='take'),
                   types.InlineKeyboardButton('Отправляю', callback_data='send'))
        bot.send_message(message.from_user.id, 'Вы принимаете запрос на объединение или отправляете?',
                         reply_markup=markup)


def his_purch(message):  # Получаем список со стоимостью его покупок.
    bill = message.text
    if ',' in message.text:
        bill = bill.replace(',', '.')
    if bill.replace('.', '').isdigit():
        price[message.from_user.id].append(float(bill))  # Отправляем чек в список
        his_purchases = bot.send_message(message.chat.id,
                                         f'Введи через пробел стоимость позиций, которые купил(а) {name[message.from_user.id]}:')
        bot.register_next_step_handler(his_purchases, my_purch)
    elif message.text.lower() == 'выход':
        bot.send_message(message.chat.id, 'Понял-принял.')
    else:
        check = bot.send_message(message.chat.id,
                                 'Ожидается число. Для выхода из цикла введите "выход"')
        bot.register_next_step_handler(check, his_purch)


def my_purch(message):  # Получаем список моих покупок
    first = []
    if message.text.lower() == 'выход':
        bot.send_message(message.chat.id, 'Понял-принял.')
    else:
        for el in message.text.split():
            if ',' in el:
                el = el.replace(',', '.')
            if el.replace('.', '').isdigit() is False:
                bot.send_message(message.chat.id,
                                 'Какое-то из твоих чисел не удалось распознать, придется начать сначала.\n Если не хочешь введи "выход"')
                time.sleep(2)
                his_purchases = bot.send_message(message.chat.id,
                                                 f'Введи через пробел стоимость позиций, которые купил(а) {name[message.from_user.id]}:')
                bot.register_next_step_handler(his_purchases, my_purch)
            first.append(float(el))

        price[message.from_user.id].append(sum(first))  # [1] Сумма его покупок
        my_purchases = bot.send_message(message.chat.id, 'Сколько сам потратил? Введи через пробел')
        bot.register_next_step_handler(my_purchases, who_pays)


def who_pays(message):  # Определяем кто платит
    second = []
    if message.text.lower() == 'выход':
        bot.send_message(message.chat.id, 'Понял-принял.')
    else:
        for el in message.text.split():
            if ',' in el:
                el = el.replace(',', '.')
            if el.replace('.', '').isdigit() is False:
                bot.send_message(message.chat.id,
                                 'Какое-то из твоих чисел не удалось распознать, придется начать сначала.'
                                 'Если не хочешь введи "выход"')
                time.sleep(2)
                my_purchases = bot.send_message(message.chat.id, 'Введи через пробел стоимость покупок.')
                bot.register_next_step_handler(my_purchases, who_pays)
            second.append(float(el))
        price[message.from_user.id].append(sum(second))
        if len(price[message.from_user.id]) == 1:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('✡  Я', callback_data='am'),
                       types.InlineKeyboardButton(f'{name[message.from_user.id].title()} 🐀', callback_data='he'))
            bot.send_message(message.from_user.id, 'Кто оплачивал❓', reply_markup=markup)
        elif price[message.from_user.id][0] >= price[message.from_user.id][1] + price[message.from_user.id][2]:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('✡  Я', callback_data='am'),
                       types.InlineKeyboardButton(f'{name[message.from_user.id].title()} 🐀', callback_data='he'))
            bot.send_message(message.from_user.id, 'Кто оплачивал❓', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, 'Стоимость ваших покупок не может превышать сумму чека.')


@bot.callback_query_handler(func=lambda call: call.data == 'am')
def i_paid(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Считаю...')
    send = bot.send_animation(call.from_user.id,
                              open(r"C:\Users\HONOR\PycharmProjects\Bot-schitovod\courir-counting-courir-stock.mp4",
                                   'rb'))
    time.sleep(7)
    bot.delete_message(call.from_user.id, send.id)
    keypad = types.InlineKeyboardMarkup()
    keypad.add(types.InlineKeyboardButton('💾 Сохранить ?', callback_data='save'))
    if len(price[call.from_user.id]) == 1:
        equals[call.from_user.id] = price[call.from_user.id][0]
    else:
        equals[call.from_user.id] = (price[call.from_user.id][0] - price[call.from_user.id][2]) / 2 + \
                                    price[call.from_user.id][1] / 2
    bot.send_message(call.from_user.id, f'Тебе должны {beautiful(equals[call.from_user.id])} тенге',
                     reply_markup=keypad)


@bot.callback_query_handler(func=lambda call: call.data == 'he')
def he_paid(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Считаю...')
    send = bot.send_animation(call.from_user.id,
                              open(r"C:\Users\HONOR\PycharmProjects\Bot-schitovod\courir-counting-courir-stock.mp4",
                                   'rb'))
    time.sleep(7)
    bot.delete_message(call.from_user.id, send.id)
    keypad = types.InlineKeyboardMarkup()
    keypad.add(types.InlineKeyboardButton('💾 Сохранить ?', callback_data='save'))
    if len(price[call.from_user.id]) == 1:
        equals[call.from_user.id] = -(price[call.from_user.id][0])
    else:
        equals[call.from_user.id] = -(
                    (price[call.from_user.id][0] - price[call.from_user.id][1]) / 2 + price[call.from_user.id][2] / 2)
    bot.send_message(call.from_user.id, f'Ты должен(а) {beautiful(equals[call.from_user.id])[1:]} тенге',
                     reply_markup=keypad)


@bot.callback_query_handler(func=lambda call: call.data == 'delete')
def delete_step_two(call):
    debt_book[call.from_user.id].pop(name[call.from_user.id], None)
    bot.answer_callback_query(callback_query_id=call.id, text='Список очищен ✅')
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Очищено.')
    if name[call.from_user.id] in keys_names[call.from_user.id]:
        he_id = keys_names[call.from_user.id][name[call.from_user.id]][0]
        he_name = keys_names[call.from_user.id][name[call.from_user.id]][1]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Да', callback_data='yes'),
                   types.InlineKeyboardButton('Нет', callback_data='no'))
        bot.send_message(he_id, f'{he_name} очистил ваш список, подтверждаете действие?',
                         reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'save')
def saving(call):
    seconds = time.time() + 10800
    tform = time.strftime('%H:%M(МСК)  %d.%m', time.localtime(seconds))
    bot.answer_callback_query(callback_query_id=call.id, text='Сохранено ✅')
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='Сохранено.')
    result = [equals[call.from_user.id], tform]
    if name[call.from_user.id] not in debt_book[call.from_user.id]:
        debt_book[call.from_user.id][name[call.from_user.id]] = []
    debt_book[call.from_user.id][name[call.from_user.id]].append(result)
    comm = bot.send_message(call.from_user.id, 'Оставь коментарий к этой записи')
    bot.register_next_step_handler(comm, comment)


@bot.callback_query_handler(func=lambda call: call.data == 'send')
def compound(call):
    bot.send_message(call.from_user.id, f'{call.from_user.id} {name[call.from_user.id]}')
    bot.send_message(call.from_user.id, '''
    Отправте этот ключ тому, с кем хотите объеденить список.
    Для объединения второму пользователю потребуется ввести это сообщение,
    после нажатия кнопки принять в разделе объеденить список.''')


@bot.callback_query_handler(func=lambda call: call.data == 'take')
def take_dict(call):
    code = bot.send_message(call.from_user.id, 'Введите ключ второго пользователя:')
    bot.register_next_step_handler(code, take_dict2)


@bot.callback_query_handler(func=lambda call: call.data == 'yes')
def yes(call):
    command = 'Очистить список 🧨'
    names = []
    [names.append(x.title()) for x in debt_book[call.from_user.id].keys()]
    name_del = bot.send_message(call.from_user.id, f'Введите имя с кем вы хотите удалить список\n{names}')
    bot.register_next_step_handler(name_del, note, command)


@bot.callback_query_handler(func=lambda call: call.data == 'yes_change')
def change_two(call):
    flag = False
    changer_name = changer[call.from_user.id][2]
    before = changer[call.from_user.id][0]
    before[0] = -before[0]
    after = changer[call.from_user.id][1]
    after[0] = -after[0]
    for i in range(0, len(debt_book[call.from_user.id][changer_name])):
        if debt_book[call.from_user.id][changer_name][i] == before:
            debt_book[call.from_user.id][changer_name][i] = after
            bot.send_message(call.from_user.id, 'Запись успешно заменена.')
            flag = True

    if flag is False:
        bot.send_message(call.from_user.id, 'Что-то пошло не так.')


@bot.callback_query_handler(func=lambda call: call.data == 'no')
def no(call):
    bot.send_message(call.from_user.id, 'Принял, данные сохранены.')


def save_to_file():
    seconds = time.time() + 10800
    tform = time.strftime('_%d-%m-%Y', time.localtime(seconds))
    with open(os.path.join('save', f'debt_book{tform}.json'), 'w', encoding='utf-8') as file:
        json.dump(debt_book, file, indent=4, ensure_ascii=False)


def take_dict2(message):
    comp_key = int(message.text.split()[0])  # Его ключ
    comp_name = message.text.split()[1]  # Мое имя
    if comp_key not in debt_book:  # Если нет ни одной записи, создается словарь с айди
        debt_book[comp_key] = {}
    if comp_name not in debt_book[comp_key]:  # Если нет ни одной записи на имя друга
        debt_book[comp_key][comp_name] = []
    keys_names[message.from_user.id][name[message.from_user.id]] = [comp_key,
                                                                    comp_name]  # В словарь ключей вводим адрес его словаря
    keys_names[comp_key][comp_name] = [message.from_user.id,
                                       name[message.from_user.id]]  # В его словарь ключей вводим свои данные
    rev_my = revers(copy.deepcopy(debt_book[message.from_user.id][name[message.from_user.id]]))
    rev_he = revers(copy.deepcopy(debt_book[comp_key][comp_name]))
    debt_book[message.from_user.id][name[message.from_user.id]].extend(rev_he)
    debt_book[comp_key][comp_name].extend(rev_my)
    bot.send_message(message.from_user.id, 'Списки объединены')
    bot.send_message(comp_key, f'{comp_name.title()} подключился к вашему списку')


def revers(rev_list):
    for el in rev_list:
        el[0] = -el[0]
    return rev_list


def comment(message):
    debt_book[message.from_user.id][name[message.from_user.id]][-1].append(message.text)
    time.sleep(1)
    bot.send_message(message.from_user.id, 'Записал')
    check_keys(message)
    save_to_file()


def check_keys(message):
    if name[message.from_user.id] in keys_names[message.from_user.id]:
        he_id = keys_names[message.from_user.id][name[message.from_user.id]][0]
        my_name = keys_names[message.from_user.id][name[message.from_user.id]][1]
        midle = debt_book[message.from_user.id][name[message.from_user.id]][-1].copy()
        midle[0] = -midle[0]
        if my_name in debt_book[he_id]:
            debt_book[he_id][my_name].extend([midle])
        else:
            debt_book[he_id][my_name] = [midle]
        bot.send_message(he_id, f'{my_name} внес новую запись\n {midle}')


def note_change(message):
    name_changer = message.text.split()[0].lower()
    index = int(message.text.split()[1]) - 1
    if len(message.text.split()) >= 4:
        if index + 1 <= len(debt_book[message.from_user.id][name_changer]):
            if name_changer in debt_book[message.from_user.id]:
                try:
                    summ = float(message.text.split()[2])
                    midle = copy.deepcopy(debt_book[message.from_user.id][name_changer][index])
                    debt_book[message.from_user.id][name_changer][index][0] = summ
                    debt_book[message.from_user.id][name_changer][index][2] = ' '.join(message.text.split()[3:])
                    bot.send_message(message.from_user.id, 'Запись изменена.')
                    changed = copy.deepcopy(debt_book[message.from_user.id][name_changer][index])
                    if name_changer in keys_names[message.from_user.id]:
                        he_id = keys_names[message.from_user.id][name_changer][0]
                        my_name = keys_names[message.from_user.id][name_changer][1]
                        changer[he_id] = [midle, changed, my_name]
                        markup = types.InlineKeyboardMarkup()
                        markup.add(types.InlineKeyboardButton('Да', callback_data='yes_change'),
                                   types.InlineKeyboardButton('Нет', callback_data='no'))
                        bot.send_message(he_id, f'''{my_name} изменил(а) запись \n {midle}
                                            на {changed}. Внести изменения в ваш список?''', reply_markup=markup)
                    save_to_file()

                except:
                    bot.send_message(message.from_user.id,
                                     'Сумма не распознана')
            else:
                bot.send_message(message.from_user.id,
                                 'Такого имени нет в записях.')
        else:
            bot.send_message(message.from_user.id,
                             'Ошибка в индексе записи')
    else:
        bot.send_message(message.from_user.id,
                         'Ожидается 4 значения через пробел(Имя, номер записи, сумма, коментарий)')


def beautiful(number):
    result = decimal.Decimal(str(number))
    result = '{0:,}'.format(result).replace(',', ' ')
    return result


def keyboard():
    but = types.KeyboardButton
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    markup.add(but('💰 Посчитать чек'), but('Список 📃'), but('✏ Изменить запись'), but('Объеденить список 🔗'),
               but('🆘 Help'), but('Очистить список 🧨'))
    return markup


if __name__ == "__main__":
    bot.infinity_polling()
