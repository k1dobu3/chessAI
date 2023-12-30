# ChessAIBot

[Аттестат](https://drive.google.com/file/d/1_6VoVwtred9De3A24zAupJBmSqADeeXi/view?usp=sharing) по искусственному интеллекту, проект шахматного противника.  
[Отчет](https://docs.google.com/document/d/27cDsaej2ZSlj_91qFLHB_jV84m4JgRdQAc9EgaNVHpw/edit?usp=sharing) 

На основе датасета с более чем 2000 сыграных игр от профессиональных шахматистов с рейтингом 2000+ был обучен ИИ, который и выступает противником во время игры.

В начале использования программы нас встречает простой интерефейс старта с указанием, как начать и чистой шахматной доской:  
  
![Alt-текст](https://sun9-41.userapi.com/impg/uz6qe1c4oM-_s6pWRI7qPwstEzMwyCfYH6hg0A/aEiZ0WBKqds.jpg?size=592x1076&quality=96&sign=fa4201c94e812d5223ad8467d1ae26c5&type=album)

Затем начинается знакомая все игра в шахматы, причем при каждой игре, мы видим, что бот ходит не по шаблону:  
  
![Alt-текст](https://sun9-79.userapi.com/impg/ip4GYeX5zXuKdZgvEh2x7l5PvZk9jZKim8Jeng/lxXwmS57pdQ.jpg?size=520x900&quality=96&sign=3cd1e3215b2f63bcd3f3029943e3ee05&type=album)

Итог работы был достигнут - научили ИИ ходить на основе анализа партий профессионалов.

### Запуск проекта

Необходимо установить следующие библиотеки:
1. numpy
2. chess
3. torch

Перейти в папку проекта через консоль (комманда сd [путь к проекту]).
```
cd chessAI
```

Запустить бота через консоль командой:
```
python main.py
```
