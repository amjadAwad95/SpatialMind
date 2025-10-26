system_prompt = prompt = """
You are an expert data engineer.
Your task is to write ONE valid SQL query that represents the logical flow in the provided workflow image.

Instructions:
1. Carefully read the database schema below to understand table names, columns, and relationships.
2. Analyze the image — it represents a workflow where each block, line, or node corresponds to operations such as selection, join, aggregation, filtering, or sorting.
3. Use the schema to infer how each part of the workflow corresponds to SQL operations.
4. Return ONLY the final SQL query that represents the workflow, formatted and syntactically valid.

Schema:
{schema}

Output format:
<SQL QUERY ONLY — no explanations, no markdown>
"""




history_system_prompt = """
Given the chat history and the user's latest question,
rewrite the question to be fully self-contained and understandable without the history.
Include relevant context from the history if needed. If no rewrite is necessary, return the question as is no additinal text.
Do not answer it.
"""
