from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import os
load_dotenv()


def getresponse(inputtext, user_id=None, conversation_history=None, db_session=None):
    """
    Get AI response with conversation context using database-driven approach.
    
    Args:
        inputtext: User's message
        user_id: User ID for context (optional)
        conversation_history: List of previous messages (optional)
        db_session: Database session (optional)
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Always use chat completion with conversation history
    return getresponse_with_history(inputtext, conversation_history)

def getresponse_with_history(inputtext, conversation_history=None):
    """
    Get AI response using chat completion with conversation history.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Build conversation messages
    messages = [
        {
            "role": "system",
            "content": "You are an emotionally supportive AI psychologist. Provide compassionate, understanding responses that help users process their feelings and find clarity. CRITICAL: You must respond in exactly the same language that the user wrote their message in. If they write in English, respond in English. If they write in Spanish, respond in Spanish. If they write in Russian, respond in Russian. Never switch languages unless the user explicitly asks you to."
        }
    ]
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history:
            role = "user" if msg['type'] == 'user' else "assistant"
            messages.append({
                "role": role,
                "content": msg['message']
            })
    
    # Add current user message
    messages.append({
        "role": "user",
        "content": inputtext
    })
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        return answer
        
    except Exception as e:
        print(f"Error in chat completion: {e}")
        return "I'm sorry, I'm having trouble responding right now. Please try again."



def createlog(user_id=None, conversation_history=None):
    """
    Create a log entry based on conversation history.
    Now uses database instead of file-based approach.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Build conversation context for log generation
    messages = [
        {
            "role": "system",
            "content": "Ты — эмоционально поддерживающий ИИ, который ведёт краткий лог взаимодействия с пользователем. Ты должен составить краткий, но информативный лог, отражающий следующее:\n\n1. Основные трудности или переживания, с которыми обратился пользователь (например, тревога, одиночество, выгорание, утрата, неуверенность и т.д.).\n\n2. Какие шаги ты предпринял для оказания эмоциональной поддержки (например, выслушал, дал возможность выразить чувства, помог переосмыслить ситуацию, напомнил о ресурсе, порекомендовал обратиться к специалисту и т.д.).\n\n3. Возможный эффект взаимодействия на пользователя, если он был выражен или замечен (например, \"пользователь стал спокойнее\", \"выразил благодарность\", \"сказал, что почувствовал облегчение\" и т.д.).\n\nНе выдумывай информацию — лог должен быть основан только на реальном содержании диалога. Стиль лога — нейтрально-доброжелательный, без оценок, коротко и по делу. Не используй конкретные имена, просто 'пользователь'."
        }
    ]
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history:
            role = "user" if msg['type'] == 'user' else "assistant"
            messages.append({
                "role": role,
                "content": msg['message']
            })
    
    # Add log generation request
    messages.append({
        "role": "user",
        "content": "Составь краткий лог этого взаимодействия на основе диалога выше."
    })
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.3
        )
        
        log_entry = response.choices[0].message.content
        
        # Store log in database if user_id provided
        if user_id:
            from models import db, Chat
            log_chat = Chat(
                user_id=user_id,
                message=log_entry,
                message_type='log'
            )
            db.session.add(log_chat)
            db.session.commit()
        
        return log_entry
        
    except Exception as e:
        print(f"Error creating log: {e}")
        return "Не удалось создать лог взаимодействия."


if __name__ == "__main__":
    print('more - first AI psychologist in Azerbaijan')
    text=input("Enter text...")
    response=getresponse(inputtext=text)
    print(response)