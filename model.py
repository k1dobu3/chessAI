import re

import torch

#from evaluation import evaluation
import chess.pgn
import numpy as np
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import torch.nn.functional as F
import os

# board format
# r n b q k b n r
# p p p p p p p p
# . . . . . . . .
# . . . . . . . .
# . . . . . . . .
# . . . . . . . .
# P P P P P P P P
# R N B Q K B N R

data = open('2000gamesDATA.pgn')
data = data.read()
data = data.split('\n\n')
data = [x for x in data if not x.startswith('[')]

game = chess.Board()

for i in range(len(data)):
    data[i] = re.sub('{.*}', '', data[i])

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

num_2_letter = {
    0: 'a',
    1: "b",
    2: "c",
    3: "d",
    4: "e",
    5: "f",
    6: "g",
    7: "h"
}


# Создание матрицы, представляющей доску с учетом типа фигур (pieceType)
# Замена символов на числа: pieceType и его верхнего регистра представляются как -1 и 1, прочие символы - 0
# Возвращается двумерный массив (матрица) для доски
def create_rep_layer(board, pieceType):
    s = str(board)
    s = re.sub(f'[^{pieceType}{pieceType.upper()} \n]', '.', s)
    s = re.sub(f'{pieceType}', '-1', s)
    s = re.sub(f'{pieceType.upper()}', '1', s)
    s = re.sub(f'\.', '0', s)

    board_mat = []

    for row in s.split('\n'):
        row = row.split(' ')
        row = [int(x) for x in row]
        board_mat.append(row)
    return np.array(board_mat)

def board_to_rep(board):
    pieces = ['p', 'r', 'n', 'b', 'q', 'k']
    layers = []
    for piece in pieces:
        layers.append(create_rep_layer(board, piece))
    board_rep = np.stack(layers)
    return board_rep


# Преобразование доски в набор матриц, представляющих разные типы фигур
# Для каждого типа фигуры вызывается create_rep_layer, и результаты объединяются в трехмерный массив
def move_rep(move, board):
    board.push_san(move).uci()
    move = str(board.pop())

    from_output_layer = np.zeros((8, 8))
    from_row = 8 - int(move[1])
    from_column = letter_2_num[move[0]]
    from_output_layer[from_row, from_column] = 1

    to_output_layer = np.zeros((8, 8))
    to_row = 8 - int(move[3])
    to_column = letter_2_num[move[2]]
    to_output_layer[to_row, to_column] = 1

    return np.stack([from_output_layer, to_output_layer])


# Создание списка ходов из текстового представления партии (s)
# Извлекаются ходы и удаляется номер хода, если он присутствует
def create_move_list(s):
    moves = re.sub('\d*\. ', '', s).split(' ')[:-1]
    return list(filter(lambda x: x != '', moves))


# Класс для создания набора данных для обучения
# Принимает массив шахматных партий и предоставляет методы для извлечения обучающих примеров
class ChessDataset(Dataset):
    def __init__(self, games):
        super(ChessDataset, self).__init__()
        self.games = np.array(games)

    def __len__(self):
        return 2000

    def __getitem__(self, index):
        while True:
            game_i = np.random.randint(self.games.shape[0])
            random_game = data[game_i]
            moves = create_move_list(random_game)
            if moves:
                break

        if len(moves) <= 1:
            return self.__getitem__(index)
        game_state_i = np.random.randint(len(moves) - 1)

        next_move = moves[game_state_i]
        moves = moves[:game_state_i]

        board = chess.Board()

        for move in moves:
            board.push_san(move)

        x = board_to_rep(board)
        y = move_rep(next_move, board)
        if game_state_i % 2 == 1:
            x *= 1
        return x, y


data_train = ChessDataset(data)
data_train_loader = DataLoader(data_train, batch_size=32, shuffle=True, drop_last=True)


# Включает в себя два сверточных слоя, слои нормализации и активации
class Module(nn.Module):

    def __init__(self, hidden_size):
        super(Module, self).__init__()
        self.conv1 = nn.Conv2d(hidden_size, hidden_size, 3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(hidden_size, hidden_size, 3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(hidden_size)
        self.bn2 = nn.BatchNorm2d(hidden_size)
        self.activation1 = nn.SELU()
        self.activation2 = nn.SELU()

    def forward(self, x):
        x_input = torch.clone(x)
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.activation1(x)
        x = self.conv2(x)
        x = self.bn2(x)
        x = x + x_input
        x = self.activation2(x)
        return x


# Определение нейронной сети для обучения на шахматных данных
# Состоит из входного слоя, нескольких блоков Module и выходного сверточного слоя
class ChessNetwork(nn.Module):

    def __init__(self, hidden_layers=4, hidden_size=200):
        super(ChessNetwork, self).__init__()
        self.hidden_layers = hidden_layers
        self.input_layer = nn.Conv2d(6, hidden_size, 3, stride=1, padding=1)
        self.module_list = nn.ModuleList([Module(hidden_size) for i in range(hidden_layers)])
        self.output_layer = nn.Conv2d(hidden_size, 2, 3, stride=1, padding=1)

    def forward(self, x):

        x = x.float()
        x = self.input_layer(x)
        x = F.relu(x)

        for i in range(self.hidden_layers):
            x = self.module_list[i](x)

        x = self.output_layer(x)

        return x


# Определение функций потерь для задач предсказания начальной и конечной позиции хода
metric_from = nn.CrossEntropyLoss()
metric_to = nn.CrossEntropyLoss()

model = ChessNetwork()

# Оптимизатор
# Определение оптимизатора (Adam) для обучения модели
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)


if not os.path.exists('TrainedModel'):
    os.mkdir('TrainedModel')

model_path = os.path.join('TrainedModel', 'model.pt')
torch.save(model.state_dict(), model_path)