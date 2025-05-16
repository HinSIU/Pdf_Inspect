from openai import OpenAI
import re

api_key = '31e53dad-0f8f-46d3-b22f-637a3b27bc23'
api_base = 'https://ark.cn-beijing.volces.com/api/v3'
model = 'deepseek-v3-250324'
#model="deepseek-r1-250120", 
            
# api_key = 'a'
# api_base = 'http://localhost:11434/v1'
# model = 'deepseek-r1:14b'


def askAI(prompt):

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=api_base,
        )

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                # {"role": "user", "content": text}
            ],
            temperature=0
        )
        result = completion.choices[0].message.content

        return result

    except Exception as e:
        print(f"出错: {e}")
        return -1
    
def rm_think(text):
    """
    删除<think>标签的内容
    :param text: 输入文本
    """
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()