import telebot
import psycopg2

username = "thzrixmbpxycue"
password = "7184838441baf33aa0986afeca61e726ab610163a77c357087e3e826fc71fc5c"
host = "ec2-54-210-128-153.compute-1.amazonaws.com"
database = "d7tofl99vg7pq2"
port = 5432


bot = telebot.TeleBot("5571503607:AAHvem3lFbtFpSG7AV6OEKslPDROhA64wpw")


# Filter for words
def words_filter(msg, words):
    if not msg.text:
        return False
    for word in words:
        if word in msg.text:
            return True
    return False


@bot.message_handler(commands=['start'])
def welcome(message):
    if message.chat.type == 'private':
        chat_id = str(message.from_user.id)
        bot.send_message(message.from_user.id, "Assalomu alaykum." + chat_id ,parse_mode='html')


@bot.message_handler(commands=['dellall'])
def delete_all(message):
    connection = psycopg2.connect(host=host, database=database, user=username, password=password, port=port)
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE grs")
    connection.close()


@bot.message_handler(commands=['getall'])
def getall(message):
    get_data(message)


@bot.message_handler(content_types=['text'])
def lalala(message):
    if message.chat.type == 'supergroup':
        if '/set' in message.text:
            channel = message.text.replace('/set ', '').split()[0]
            is_admin = bot.get_chat_member(chat_id=str(channel), user_id=message.from_user.id).can_delete_messages
            if is_admin:
                new_channel(message, channel)
            else:
                bot.send_message(message.chat.id, "Botni kanalga admin qilmadingiz.")
        else:
            pass


def check(message):
    connection = psycopg2.connect(host=host, database=database, user=username, password=password, port=port)
    with connection.cursor() as cursor:
        cursor.execute("SELECT kanal FROM grs WHERE grid = %s", message.chat.id)
    result = cursor.fetchone()
    connection.close()
    if result is None:
        return False
    return True


def get_data(message):
    chat_id = message.chat.id
    msg = ""
    connection = psycopg2.connect(host=host, database=database, user=username, password=password, port=port)
    with connection.cursor() as cursor:
        cursor.execute("SELECT kanal FROM grs WHERE grid = %s", chat_id)
        result = cursor.fetchall()

    for x in result:
        msg += "{}\n".format(x)
    if msg is None:
        bot.send_message(message.chat.id, "Hech narsa yoq")
    else:
        bot.send_message(message.chat.id, msg)
    connection.close()


def new_channel(message, chan):
    connection = psycopg2.connect(host=host, database=database, user=username, password=password, port=port)
    channel = str(chan)
    with connection.cursor() as cursor:
        sql_select_query = "SELECT kanal FROM grs WHERE grid = %s"
        cursor.execute(sql_select_query, message.chat.id)
        record = cursor.fetchone()
    msg = str(record)
    if channel not in record:
        sql_update_query = "INSERT INTO grs(grid, userid, kanal) VALUES (%s, %s, %s)"
        with connection.cursor() as cursor:
            cursor.execute(sql_update_query, (message.chat.id, message.from_user.id, channel))
        bot.send_message(message.chat.id, "Guruhingiz kanalingizga ulandi." + msg)
        connection.close()
    else:
        sql_update_query = "Update grs SET kanal = %s where grid = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql_update_query, (channel, message.chat.id))
        bot.send_message(message.chat.id, "Guruhingiz kanalingizga qayta ulandi." + msg)
        connection.close()


bot.polling(none_stop=True)
