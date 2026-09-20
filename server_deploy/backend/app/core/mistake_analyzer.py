from app.core.ai_client import ai_client
from app.schemas.mistake import MistakeUpdate
from app.crud import mistake as crud_mistake
from sqlalchemy.orm import Session

def analyze_mistake(db: Session, mistake_id: int):

    mistake = crud_mistake.get_mistake(db, mistake_id)
    if not mistake:
        return

    try:

        attachment_text = ""
        if mistake.image_url:
            file_path = mistake.image_url
            try:
                if file_path.lower().endswith(('.txt', '.md')):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        attachment_text = f.read()
                elif file_path.lower().endswith(('.doc', '.docx')):

                    try:
                        import docx2txt
                        attachment_text = docx2txt.process(file_path)
                    except ImportError:
                        print("未安装 docx2txt，无法解析 docx 文档")
            except Exception as e:
                try:
                    print(f"解析附件出错 {file_path}: {e}")
                except UnicodeEncodeError:
                    print(f"解析附件出错 {file_path}: {repr(e)}")

        base_content = mistake.raw_text if mistake.raw_text else ""
        content = base_content
        if attachment_text:
            content += f"\n\n【附件内容】:\n{attachment_text}"

        if not content.strip():
            content = "（该题目为文档附件且未提取到有效文字，请基于该科目通用易错知识点进行学习建议）"

        prompt = f"""
        请分析以下错题，给出解题思路、涉及的知识点以及学习建议。

        题目内容：
        {content}

        科目：{mistake.subject}
        """

        analysis = ai_client.get_answer(query=prompt, context="")

        crud_mistake.update_mistake(
            db, mistake, MistakeUpdate(ai_analysis=analysis)
        )
        print(f"错题 {mistake_id} 分析成功。")

    except Exception as e:
        print(f"分析错题出错 {mistake_id}: {e}")