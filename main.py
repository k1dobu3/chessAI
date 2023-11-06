import telebot
import chess
import config
import moves

bot = telebot.TeleBot(config.bot_token)

# Отслеживание состояния пользователя
user_states = {}


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Этот бот играет в шахматы. Используй команду /move, чтобы сделать ход.")
    bot.send_message(message.chat.id, "Шахматная доска:\n"
                                      " 8 ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜\n"
                                      " 7 ☗ ☗ ☗ ☗ ☗ ☗ ☗ ☗\n"
                                      " 6 ☐ ☐ ☐ ☐ ☐ ☐ ☐ ☐\n"
                                      " 5 ☐ ☐ ☐ ☐ ☐ ☐ ☐ ☐\n"
                                      " 4 ☐ ☐ ☐ ☐ ☐ ☐ ☐ ☐\n"
                                      " 2 ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙\n"
                                      " 1 ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖\n"
                                      "  🄰 🄱 🄲 🄳 🄴 🄵 🄶 🄷")


@bot.message_handler(commands=['move'])
def send_move(message):
    user_states[message.chat.id] = "waiting_for_move"
    bot.send_message(message.chat.id, "Введите ваш ход:")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_move")
def process_move(message):
    global gameBoard, player, color

    player_move = message.text
    # Здесь вы можете обработать ход пользователя
    bot.send_message(message.chat.id, f"Вы ввели ход: {player_move}")
    if gameBoard.turn == player:
        if len(player_move) == 4:
            gameBoard.push_uci(player_move)
            engine_move = moves.choose_move(gameBoard, player, color)
            gameBoard.push_uci(engine_move.uci())
            bot.reply_to(message, f"Ход бота: {engine_move.uci()}")
            bot.reply_to(message, moves.display_board(gameBoard), parse_mode='html')
        else:
            bot.reply_to(message, "Некорректный ход. Введите ход в формате 'e2e4'.")
    else:
        return 0

    user_states[message.chat.id] = "waiting_for_command"


if __name__ == '__main__':
    gameBoard = chess.Board()
    player = chess.WHITE
    color = chess.BLACK

    bot.polling()
