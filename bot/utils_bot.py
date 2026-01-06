def check_answer_logic(answer, target_translation, buttons_word, practice_word):
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
    if message.content_type == 'text':
        return True, message.text.strip().lower()
    else:
        return False, None


