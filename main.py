from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
from factory import ChatbotFactory, DatabaseFactory, ChatbotType, DatabaseType
import os

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


class ChatRequest(BaseModel):
    session_id: str
    message: str


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
        "message": "Gemini Chatbot API",
        "endpoints": {
            "POST /initialize": "Initialize a chatbot session with database config",
            "POST /chat": "Send a message to the chatbot",
            "POST /execute": "Execute a SQL query",
            "DELETE /session/{session_id}": "Close a session",
            "GET /health": "Health check",
        },
    }


@app.post("/initialize", response_model=StatusResponse)
async def initialize_chatbot(request: ChatbotInitRequest):
    """
    Initialize a new chatbot session with custom database configuration.
    """
    try:
        if request.session_id in sessions:
            raise HTTPException(
                status_code=400, detail=f"Session {request.session_id} already exists"
            )

        db_type_map = {
            "postgresql": DatabaseType.POSTGRESQL,
        }

        chatbot_type_map = {
            "gemini_text": ChatbotType.GEMINI_TEXT,
        }

        db_type = db_type_map.get(request.database_config.db_type.lower())
        if not db_type:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported database type: {request.database_config.db_type}",
            )

        chatbot_type = chatbot_type_map.get(request.chatbot_type.lower())
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
            message=f"Session {request.session_id} initialized successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the chatbot in an existing session.
    """
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {request.session_id} not found. Please initialize first.",
        )

    try:
        chatbot = sessions[request.session_id]["chatbot"]
        response = chatbot.chat(request.message)

        if response is None:
            raise HTTPException(
                status_code=500,
                detail="Chatbot returned no response. Please check your API keys and try again.",
            )

        return ChatResponse(session_id=request.session_id, response=str(response))

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_detail = f"Error: {str(e)}\n\nTraceback: {traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute", response_model=QueryExecutionResponse)
async def execute_query(request: ExecuteQueryRequest):
    """
    Execute a SQL query through the database connector.
    """
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session {request.session_id} not found. Please initialize first.",
        )

    try:
        database = sessions[request.session_id]["database"]

        # Execute the query using the database connector
        rows = database.execute_query(request.query)

        # Get column names from cursor
        column_names = (
            [desc[0] for desc in database.cursor.description]
            if database.cursor.description
            else []
        )

        # Convert rows to list of lists (handle different data types)
        rows_list = []
        for row in rows:
            row_list = []
            for item in row:
                # Convert to string for JSON serialization if needed
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
async def close_session(session_id: str):
    """
    Close a chatbot session and cleanup database connection.
    """
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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_sessions": len(sessions)}


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup all sessions on shutdown.
    """
    for session_id in list(sessions.keys()):
        try:
            sessions[session_id]["database"].close()
        except:
            pass
    sessions.clear()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
