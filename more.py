from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()


def getresponse (inputtext):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    with open ("previd.txt") as p:
        previd=p.read()
    if previd:
        response = client.responses.create(
            model="gpt-4.1-mini",
            previous_response_id=previd,
            input=inputtext
        )
    else:
        response = client.responses.create(
            model="gpt-4.1-mini",
            previous_response_id="resp_6892cce26ec0819c9e3cfe6759c09c460fff2002fe985129",
            input=inputtext
        )
    with open ("previd.txt", "w") as p:
        p.write(response.id)
    answer=response.output_text
    answer=answer.replace("\n"," ")
    line=inputtext+"%"+answer+"\n"
    with open("chathistory.txt", "a") as f:
        f.write(line)

def createlog(previd):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.responses.create(
            model="gpt-4.1-mini",
            previous_response_id=previd,
            input="Ты — эмоционально поддерживающий ИИ, который ведёт краткий лог взаимодействия с пользователем. Ты должен составить краткий, но информативный лог, отражающий следующее:\n\n1. Основные трудности или переживания, с которыми обратился пользователь (например, тревога, одиночество, выгорание, утрата, неуверенность и т.д.).\n2. Какие шаги ты предпринял для оказания эмоциональной поддержки (например, выслушал, дал возможность выразить чувства, помог переосмыслить ситуацию, напомнил о ресурсе, порекомендовал обратиться к специалисту и т.д.).\n3. Возможный эффект взаимодействия на пользователя, если он был выражен или замечен (например, \"пользователь стал спокойнее\", \"выразил благодарность\", \"сказал, что почувствовал облегчение\" и т.д.).\n\nНе выдумывай информацию — лог должен быть основан только на реальном содержании диалога. Стиль лога — нейтрально-доброжелательный, без оценок, коротко и по делу. Не используй конкретные имена, просто 'пользователь'.\n\nПример:\n— Пользователь обратился с чувством тревоги, вызванной профессиональной неуверенностью. ИИ выслушал, помог нормализовать чувства и предложил фокусироваться на маленьких шагах. В ходе беседы пользователь сказал, что чувствует себя спокойнее и благодарен за поддержку. Приступай")
    answer=response.output_text
    with open("journal.txt", "a") as f:
        f.write(answer)


if __name__ == "__main__":
    print('more - first AI psychologist in Azerbaijan')
    text=input("Enter text...")
    response=getresponse(inputtext=text)
    print(response)