from openai import OpenAI
from app.core.config import settings

class AIClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"

    def get_answer(self, query: str, context: str) -> str:

        system_prompt = f"""
        你是一个专业的学术助教。请根据以下参考资料回答用户的问题。

        参考资料：
        {context}

        要求：
        1. 如果资料中包含答案，请详细解释。
        2. 如果资料中没有相关信息，请诚实回答“资料中未找到相关信息”，并基于你的通用知识给出建议（需注明是通用建议）。
        3. 回答要条理清晰，适合学生阅读。
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"调用 DeepSeek API 出错: {e}")
            return "抱歉，AI 服务暂时不可用，请稍后再试。"

    def get_answer_stream(self, query: str, context: str):

        system_prompt = f"""
        你是一个专业的学术助教。请根据以下参考资料回答用户的问题。

        参考资料：
        {context}

        要求：
        1. 如果资料中包含答案，请详细解释。
        2. 如果资料中没有相关信息，请诚实回答“资料中未找到相关信息”，并基于你的通用知识给出建议（需注明是通用建议）。
        3. 回答要条理清晰，适合学生阅读。
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=1000,
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"调用 DeepSeek API 流式接口出错: {e}")
            yield "抱歉，AI 服务暂时不可用，请稍后再试。"

    def generate_plan(self, description: str) -> str:

        system_prompt = """
        你是一名资深的学业规划导师。请根据用户描述的学习方向，生成一份详细的长远学习计划。

        要求：
        1. 计划应包含阶段性目标（如：基础阶段、进阶阶段、冲刺阶段）。
        2. 每个阶段应有具体的学习内容和建议时长。
        3. 输出格式要求为 Markdown，结构清晰。
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": description}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"生成计划出错: {e}")
            return "抱歉，无法生成学习计划，请稍后再试。"

    def generate_daily_tasks(self, plan_content: str, day_offset: int = 0) -> list:

        import json
        system_prompt = f"""
        请根据以下长远学习计划，为用户生成第 {day_offset + 1} 天的学习任务列表。

        长远计划内容：
        {plan_content[:2000]}... (部分内容)

        要求：
        1. 生成 4-5 个具体的任务。
        2. 其中**必须**包含一个“AI出题”类型的任务（type="quiz"），生成 2-3 道基于当天学习重点的选择题。
        3. 其他任务类型可以是 "reading" (阅读/学习) 或 "practice" (练习)。
        4. 对于 type="quiz" 的任务，其 content 必须是一个 JSON 对象，包含 questions 数组。
        5. **严格**返回合法的 JSON 格式列表，不要包含 Markdown 代码块标记。

        JSON 格式示例：
        [
            { "title": "阅读第一章", "content": "学习基础概念...", "type": "reading"} ,
            { "title": "完成课后练习", "content": "习题 1-3", "type": "practice"} ,
            { "title": "今日测验", "content": { "questions": [{ "question": "什么是...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "因为..."} ]} , "type": "quiz"} 
        ]
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "请生成今日任务"}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            content = response.choices[0].message.content

            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"生成日常任务出错: {e}")

            return [
                {"title": "复习昨日内容", "content": "回顾昨天学习的知识点", "type": "reading"},
                {"title": "今日知识点学习", "content": "请根据长远计划自主学习", "type": "reading"},
                {"title": "今日小测", "content": {"questions": [{"question": "1+1=?", "options": ["1", "2", "3", "4"], "answer": "B", "explanation": "基础数学"}]}, "type": "quiz"}
            ]

    def extract_points(self, content: str) -> dict:

        import json
        system_prompt = """
        你是一个专业的学术助教。请阅读以下文档内容，提炼出核心知识点，并生成相关的练习题。

        要求：
        1. 提炼 3-5 个核心知识点。
        2. 生成 1-2 道选择题用于练习。
        3. **严格**返回合法的 JSON 格式，不要包含 Markdown 代码块标记。

        JSON 格式示例：
        {
            "points": ["知识点1...", "知识点2..."],
            "quiz": [
                {
                    "question": "问题描述...",
                    "options": ["选项A", "选项B", "选项C", "选项D"],
                    "answer": "A"
                }
            ]
        }
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"文档内容：\n{content[:3000]}..."} 
                ],
                temperature=0.5,
                max_tokens=1500
            )
            content = response.choices[0].message.content

            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"提取知识点出错: {e}")
            return {
                "points": ["无法提炼知识点，请稍后再试。"],
                "quiz": []
            }

ai_client = AIClient()