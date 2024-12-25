import pymorphy3
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='auto', target='en')
morph_analyzer = pymorphy3.MorphAnalyzer()
word_count = {}
word_list = []
final_output = []
count = 0

# Чтение файла диалога
with open('dialog.txt', encoding='utf-8') as file:
    lines = []

    for line in file:
        words_in_line = line.split()
        normalized_words = []
        
        for word in words_in_line:
            parsed_word = morph_analyzer.parse(word)[0]
            normalized_words.append(parsed_word.normal_form)
        lines.append(normalized_words)

# Подсчет слов
for line in lines:
    for word in line:
        if word_count.get(word) is None:
            word_count[word] = 1
        else:
            word_count[word] += 1

# Запись результатов в файл
with open('result.txt', 'w', encoding='utf-8') as output_file:
    output_file.write('Start word | Translate | Number of Mentions')

    for word, count in sorted(word_count.items(), key=lambda item: item[1], reverse=True):
        translated_word = translator.translate(word)
        output_file.write(f'\n{word} | {translated_word} | {count}')
