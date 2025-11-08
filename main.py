import uvicorn
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from typing import Optional, Dict, List, Any
from factory import ChatbotFactory, DatabaseFactory, ChatbotType, DatabaseType

load_dotenv()

app = FastAPI(title="Spatial Mind")

sessions: Dict[str, dict] = {}


class DatabaseConfig(BaseModel):
    db_type: str = "postgresql"
    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: str


class TextChatRequest(BaseModel):
    session_id: str
    message: str


class VisionChatRequest(BaseModel):
    session_id: str
    message: str
    image: str


class ExecuteQueryRequest(BaseModel):
    session_id: str
    query: str


class ChatbotInitRequest(BaseModel):
    session_id: str
    database_config: DatabaseConfig
    chatbot_type: str = "gemini_text"


class ChatResponse(BaseModel):
    session_id: str
    response: str


class QueryExecutionResponse(BaseModel):
    session_id: str
    success: bool
    rows: List[List[Any]]
    column_names: List[str]
    row_count: int
    error: Optional[str] = None


class StatusResponse(BaseModel):
    status: str
    message: str


@app.get("/")
async def root():
    return {
        "message": "Spatial Mind Chatbot API",
        "endpoints": {
            "POST /initialize": "Initialize a chatbot session with database config",
            "POST /chat/text": "Send a message to the chatbot",
            "POST /chat/vision": "Send a message with an image to the chatbot",
            "POST /execute": "Execute a SQL query",
            "DELETE /session/{session_id}": "Close a session",
        },
    }


@app.post("/initialize", response_model=StatusResponse)
async def initialize_chatbot(request: ChatbotInitRequest):
    try:
        if request.session_id in sessions:
            raise HTTPException(
                status_code=400, detail=f"Session {request.session_id} already exists."
            )

        db_type_map = {"postgresql": DatabaseType.POSTGRESQL}
        chat_type_map = {
            "gemini_text": ChatbotType.GEMINI_TEXT,
            "gemini_vision": ChatbotType.GEMINI_VISION,
        }

        db_type = db_type_map.get(request.database_config.db_type.lower())
        if not db_type:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported database type: {request.database_config.db_type}",
            )

        chatbot_type = chat_type_map.get(request.chatbot_type.lower())
        if not chatbot_type:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported chatbot type: {request.chatbot_type}",
            )

        database = DatabaseFactory.get_database_connector(
            db_type=db_type,
            db_name=request.database_config.db_name,
            db_user=request.database_config.db_user,
            db_password=request.database_config.db_password,
            db_host=request.database_config.db_host,
            db_port=request.database_config.db_port,
        )

        database.connect()

        chatbot = ChatbotFactory.create_chatbot(
            chatbot_type=chatbot_type, database_connector=database
        )

        sessions[request.session_id] = {"database": database, "chatbot": chatbot}

        return StatusResponse(
            status="success",
            message=f"Session {request.session_id} initialized successfully.",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/text", response_model=ChatResponse)
async def text_chat(request: TextChatRequest):
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=404, detail=f"Session {request.session_id} not found."
        )

    try:
        chatbot = sessions[request.session_id]["chatbot"]
        response = chatbot.chat(request.message)

        if response is None:
            raise HTTPException(
                status_code=500,
                detail="Chatbot returned no response. Please check your API keys and try again.",
            )

        return ChatResponse(session_id=request.session_id, response=response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/vision", response_model=ChatResponse)
async def vision_chat(request: VisionChatRequest):
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=404, detail=f"Session {request.session_id} not found."
        )

    try:
        chatbot = sessions[request.session_id]["chatbot"]
        response = chatbot.chat({"query": request.message, "image": request.image})

        if response is None:
            raise HTTPException(
                status_code=500,
                detail="Chatbot returned no response. Please check your API keys and try again.",
            )

        return ChatResponse(session_id=request.session_id, response=response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute", response_model=QueryExecutionResponse)
async def execute_query(request: ExecuteQueryRequest):
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {request.session_id} not found. Please initialize first.",
        )

    try:
        database = sessions[request.session_id]["database"]

        rows = database.execute_query(request.query)

        column_names = (
            [desc[0] for desc in database.cursor.description]
            if database.cursor.description
            else []
        )

        rows_list = []
        for row in rows:
            row_list = []
            for item in row:
                if item is None:
                    row_list.append(None)
                else:
                    row_list.append(str(item))
            rows_list.append(row_list)

        return QueryExecutionResponse(
            session_id=request.session_id,
            success=True,
            rows=rows_list,
            column_names=column_names,
            row_count=len(rows_list),
            error=None,
        )

    except Exception as e:
        return QueryExecutionResponse(
            session_id=request.session_id,
            success=False,
            rows=[],
            column_names=[],
            row_count=0,
            error=str(e),
        )


@app.delete("/session/{session_id}", response_model=StatusResponse)
async def delete_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        database = sessions[session_id]["database"]
        database.close()
        del sessions[session_id]

        return StatusResponse(
            status="success", message=f"Session {session_id} closed successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", response_model=List[str])
async def list_sessions():
    return list(sessions.keys())


@app.delete("/sessions", response_model=StatusResponse)
async def delete_all_sessions():
    try:
        for session_id in list(sessions.keys()):
            database = sessions[session_id]["database"]
            database.close()
            del sessions[session_id]

        return StatusResponse(
            status="success", message="All sessions closed successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    for session_id in list(sessions.keys()):
        try:
            sessions[session_id]["database"].close()
        except:
            pass
    sessions.clear()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
