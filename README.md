# Spatial Mind

A system designed to automatically generate precise spatial SQL queries based on the user’s question and execute them within QGIS.

## Abstraction

Spatial Mind is an AI-powered application that converts natural language into spatial SQL queries that can be executed in QGIS. It enables students, teachers, spatial scientists, and researchers to perform spatial analysis quickly and easily.

## Introduction

Spatial analysis is a core component of modern geographic information systems, yet writing spatial SQL queries can be challenging for many users especially those without advanced technical backgrounds. Spatial Mind bridges this gap by transforming natural language questions into accurate spatial SQL queries that can be executed directly in QGIS.

By combining AI-driven language understanding with spatial database expertise, Spatial Mind makes complex analysis accessible to students, educators, researchers, and GIS professionals. Whether you want to filter features, calculate distances, analyze intersections, or perform advanced geospatial operations, the system simplifies the process and accelerates your workflow.

## Methodology

Spatial Mind follows a structured pipeline that transforms user questions into accurate spatial SQL queries. The system combines natural language understanding, schema awareness, and spatial reasoning to ensure reliable results.

### Natural Language Processing

The user submits a question in plain language. The system analyzes the intent, identifies spatial operations, and extracts relevant entities such as layers, attributes, geometry types, and conditions.

### Schema Interpretation

Spatial Mind loads the database schema, including table names, column details, and geometry fields. This ensures that the generated SQL matches the actual structure of the spatial database.

### Spatial Reasoning

The system interprets the user’s intent and maps it to appropriate spatial functions such as ```ST_Intersects```, ```ST_Distance```, ```ST_Buffer```, ```ST_Within```, and others used in PostGIS and QGIS.

### DE-9IM Model Integration
To ensure accurate interpretation of spatial relationships, Spatial Mind leverages the Dimensionally Extended Nine-Intersection Model (DE-9IM). This allows the system to distinguish between complex spatial relations such as intersects, touches, overlaps, crosses, and disjoint, and map them to precise PostGIS functions like ```ST_Relate```, ```ST_Touches```, ```ST_Overlaps```, and ```ST_Disjoint```.

### Query Generation

A single, valid SQL query is generated based on the extracted intent and schema context. The query is crafted to meet QGIS requirements and produce accurate results.

### Chat History Awareness

Spatial Mind maintains context across the conversation, allowing it to understand follow-up questions, refine previous queries, or build on earlier interactions. This continuity enables more natural and efficient spatial analysis workflows.

### Execution Within QGIS
The final SQL query can be executed directly in QGIS to produce the desired output new layers, filtered features, or computed spatial results.

## Results

Spatial Mind successfully translates natural language questions into precise spatial SQL queries that can be executed in QGIS. It can:

- Identify intersections and overlaps between layers

- Calculate distances and buffers around geographic features

- Perform containment and proximity analysis

- Handle complex queries using DE-9IM relationships

- Convert workflow diagrams or images into executable SQL queries, allowing users to visualize spatial analysis workflows and automatically generate the corresponding queries

Users including students, teachers, and researchers can now perform spatial analysis without manually writing SQL queries, significantly reducing errors and saving time. The chat history feature allows iterative analysis, enabling users to refine queries or ask follow-up questions naturally.

## Tech Stack
- Python
- LangChain
- QGIS
- FastAPI
- Ollama
- Postgres

## How to Run Locally
1. Clone the repository
   
```bash
git clone https://github.com/amjadAwad95/SpatialMind.git
cd SpatialMind
```

2. Create a virtual environment
   
```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
```

3. Create a ```.env``` file in the root folder
   
```file
GOOGLE_API_KEY = <YOUR API KEY FOR GOOGLE>
```

4. Install the dependencies
   
```bash
pip install -r requirements.txt
```

5. Run the app
   
```bash
uvicorn main:app --reload
```

The backend will start locally (default at ```http://127.0.0.1:8000```). Keep it running so the QGIS plugin can communicate with it.

6. Install the QGIS Plugin

    1. Open QGIS

    2. Go to Plugins → Manage and Install Plugins → Install from ZIP

    3. Click Browse, navigate to the plugin.zip file in the cloned repository, and click Install Plugin

7. Open and Use the Plugin

   1. Enable the plugin from Plugins → Installed

   2. Open the plugin panel (usually appears in the toolbar or under Plugins → Spatial Mind)

   3. Ensure the backend is running, then enter your queries or workflow images to generate spatial SQL queries in QGIS

## Conclusion

Spatial Mind demonstrates how AI can simplify complex spatial analysis tasks. By combining natural language processing, schema interpretation, DE-9IM spatial reasoning, workflow image interpretation, and conversational context, the system bridges the gap between GIS technology and non-expert users.

This approach empowers users to explore spatial data efficiently, enhances learning and research workflows, and provides a foundation for future improvements such as multi-database support, advanced geospatial analytics, and integration with other GIS platforms.
