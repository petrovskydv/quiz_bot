from pprint import pprint


def main():
    with open('quiz-questions/1vs1200.txt', 'r', encoding='KOI8-R') as my_file:
        file_contents = my_file.read()
    text = file_contents.split('\n')
    # pprint(faq[:30])
    quiz = {}
    is_question = False
    is_answer = False
    question_text = ''
    answer_text = ''
    for string in text:
        if string.startswith('Вопрос'):
            is_question = True
            continue
        elif len(string) == 0 and is_answer:
            quiz[question_text] = answer_text
            question_text = ''
            answer_text = ''
            is_answer = False
            continue
        elif len(string) == 0:
            is_question = False
            continue
        elif string.startswith('Ответ'):
            is_answer = True
            continue

        if is_question:
            question_text = ' '.join([question_text, string])
        if is_answer:
            answer_text = ' '.join([answer_text, string])

    for question, answer in quiz.items():
        pprint(question)
        pprint(answer)


if __name__ == '__main__':
    main()
