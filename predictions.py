import chess
import numpy as np
import torch
from model import ChessNetwork, board_to_rep
import chess.svg

letter_2_num = {
    'a': 0,
    'b': 1,
    'c': 2,
    'd': 3,
    'e': 4,
    'f': 5,
    'g': 6,
    'h': 7
}

piece_symbols_white = {
    chess.PAWN: "♙",
    chess.KNIGHT: "♘",
    chess.BISHOP: "♗",
    chess.ROOK: "♖",
    chess.QUEEN: "♕",
    chess.KING: "♔",
}

piece_symbols_black = {
    chess.PAWN: "☗",
    chess.KNIGHT: "♞",
    chess.BISHOP: "♝",
    chess.ROOK: "♜",
    chess.QUEEN: "♛",
    chess.KING: "♚",
}

piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

model = ChessNetwork()
model.load_state_dict(torch.load('TrainedModel/model.pt'))
model.eval()


def distribution_over_moves(vals):
    probs = np.array(vals)
    probs = np.exp(probs)
    probs = probs / probs.sum()
    probs = probs ** 3
    probs = probs / probs.sum()
    return probs


def eval_board(board):
    score = 0

    # Суммируйте оценку
    for piece_type, value in piece_values.items():
        score += value * len(board.pieces(piece_type, chess.WHITE))
        score -= value * len(board.pieces(piece_type, chess.BLACK))

    # Проверьте, сдвинулась ли пешка h или a
    has_h_pawn_moved = any(move.from_square == chess.H2 or move.to_square == chess.H2 for move in board.move_stack)
    has_a_pawn_moved = any(move.from_square == chess.A2 or move.to_square == chess.A2 for move in board.move_stack)

    # Наказывать за то, что начинаешь с пешек h или a
    if not has_h_pawn_moved:
        score -= 0.2
    if not has_a_pawn_moved:
        score -= 0.2

    # Наказывать за висячие предметы (в центре доски в виде «острова» из двух пеше)
    for square, piece in board.piece_map().items():
        if piece.color == board.turn:
            attackers = [attacker for attacker in board.attackers(not piece.color, square)]
            try:
                attackers = [attacker for attacker in attackers
                             if piece_values.get(attacker.piece_type, 0) >= piece_values.get(piece.piece_type, 0)]
            except AttributeError:
                print()

            if not attackers and piece_values.get(piece.piece_type, 0) > 1:
                score -= piece_values.get(piece.piece_type, 0) / 2

    # Добавление бонуса за управление центром
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    king_square = board.king(board.turn)

    for square in center_squares:
        piece = board.piece_at(square)
        if piece is not None and piece.color == board.turn:
            score += 0.4 * piece_values.get(piece.piece_type, 0)

    # Добавление бонуса за более активную позицию
    for piece in board.piece_map().values():
        if isinstance(piece, chess.Piece) and piece.color == board.turn:
            try:
                mobility = len(board.attacks(piece.square))
                score += 0.5 * piece_values.get(piece.piece_type, 0) * mobility
            except AttributeError:
                print()
    for square in center_squares:
        if board.is_attacked_by(chess.WHITE, square) and chess.square_distance(square, king_square) <= 4:
            score += 0.1

        # Добавление бонуса за подвижность фигуры рядом с королем
    for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        for piece in board.pieces(piece_type, board.turn):
            if chess.square_distance(piece, king_square) <= 4:
                mobility = len(board.attacks(piece))
                score += 0.2 * piece_values.get(piece_type, 0) * mobility

    #print("Очки: {}".format(score))
    return score


def choose_move(board, player, color):
    legal_moves = list(board.legal_moves)
    best_move = None
    best_score = float('-inf') if player == chess.WHITE else float('inf')
    for move in legal_moves:
        # проверяет, не приводит ли перемещение к подвешиванию фигуры
        if board.is_capture(move):
            piece_captured = board.piece_at(move.to_square)
            if piece_captured is not None:
                eval_board_after_move = eval_board(board)
                board.push(move)
                if board.is_check():
                    eval_board_after_move -= 1.0 * piece_values[piece_captured.piece_type]
                if eval_board_after_move < eval_board(board):
                    board.pop()
                    continue
                # проверяет, имеет ли захваченный фрагмент равное или меньшее значение по сравнению с захваченным фрагментом
                piece_capturing = board.piece_at(move.from_square)
                if piece_capturing is not None and piece_values.get(piece_capturing.piece_type, 0) <= piece_values.get(piece_captured.piece_type, 0):
                    best_score += 0.5 * piece_values[piece_captured.piece_type]  # добавляет фиксированный бонус к счету
                board.pop()

        x = torch.Tensor(board_to_rep(board)).float()
        if color == chess.BLACK:
            x *= -1
        x = x.unsqueeze(0)
        output = model(x)  # форма: 1, 2, 8, 8
        score = output[0][0][move.to_square // 8][move.to_square % 8].item()  # извлекает оценку из тензора и преобразует в скаляр
        if player == chess.BLACK:
            score = -score
        if player == chess.WHITE and score > best_score:
            best_move = move
            best_score = score
        elif player == chess.BLACK and score < best_score:
            best_move = move
            best_score = score
    return best_move


def display_board(board):
    empty_square = '☐'  # символ для пустых клеток
    board_str = "Шахматная доска:\n"
    for rank in range(7, -1, -1):
        board_str += "{:2d} ".format(rank + 1)
        for file in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            if piece is not None:
                if piece.color == chess.WHITE:
                    board_str += "{:2}".format(piece_symbols_white[piece.piece_type])
                else:
                    board_str += "{:2}".format(piece_symbols_black[piece.piece_type])
            else:
                board_str += "{:2}".format(empty_square)
        board_str += "\n"
    board_str += "   🄰 🄱 🄲 🄳 🄴 🄵 🄶 🄷\n"
    return board_str


gameBoard = chess.Board()
player = chess.WHITE
color = chess.BLACK