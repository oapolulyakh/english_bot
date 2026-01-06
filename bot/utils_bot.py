def check_answer_logic(answer, target_translation, buttons_word, practice_word):
    """
    Проверяет правильность ответа пользователя на вопрос в режиме тренировки.

    Сравнивает ответ пользователя с правильным переводом и определяет результат проверки.
    Если ответ правильный, возвращает код 1 и сообщение об успехе. Если ответ неправильный,
    в зависимости от количества оставшихся вариантов возвращает код 2 (возможность
    повторной попытки) или код 3 (показ правильного ответа).

    При неправильном ответе удаляет выбранный вариант из списка возможных ответов.

    :param answer: Ответ пользователя
    :type answer: str
    :param target_translation: Правильный перевод слова
    :type target_translation: str
    :param buttons_word: Список вариантов переводов (может изменяться)
    :type buttons_word: list[str]
    :param practice_word: Слово на английском языке, перевод которого угадывается
    :type practice_word: str
    :return: Кортеж из кода результата (1, 2 или 3) и текстового сообщения
    :rtype: tuple[int, str]
    """
    if answer != target_translation:
        if len(buttons_word) <= 2:
            return 3, f'Было близко! Правильный ответ: \n{practice_word} -> {target_translation}'

        else:
            if answer in buttons_word:
                buttons_word.remove(answer)
            return 2, f'Неверно, попробуй еще раз'
    else:
        return 1, f'Верно! ✅\n{practice_word} -> {target_translation}'

def check_text(message):
    """
    Проверяет, является ли сообщение текстовым, и возвращает его содержимое.

    Проверяет тип содержимого сообщения. Если сообщение содержит текст,
    возвращает True и обработанный текст (убраны пробелы по краям, приведен к нижнему регистру).
    Если сообщение не является текстовым, возвращает False и None.

    :param message: Объект сообщения от Telegram Bot API
    :type message: telebot.types.Message
    :return: Кортеж из флага успешной проверки и текста сообщения (или None)
    :rtype: tuple[bool, str | None]
    """
    if message.content_type == 'text':
        return True, message.text.strip().lower()
    else:
        return False, None


