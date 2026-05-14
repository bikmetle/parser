from collections import defaultdict
import json


with open('ozon.ru.har', 'r') as f:
    har = json.load(f)


product_question = defaultdict(list)

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'widgetStateId=webListQuestions' in url:
        content = json.loads(entry['response']['content']['text'])
        for question_data in content['state']['questions'].values():
            product_url = question_data['sharing']['url'].split("/questions")[0]
            content = question_data['content']
            product_question[product_url].append(content)

with open('product_questions.txt', 'w', encoding='utf-8') as f:
    for product_url, questions in product_question.items():
        f.write(f"{product_url}\n")
        for i, question in enumerate(questions, 1):
            f.write(f"  {i}. {question}\n")
        f.write("\n")
