import os
import re
import json
import base64
import requests

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QAction,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QLineEdit,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QTabWidget,
    QWidget,
    QFileDialog,
    QComboBox,
)
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
)


class SQLQueryDialog(QDialog):
    def __init__(self, iface=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spatial Mind")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self.iface = iface
        self.text_session_id = None
        self.vision_session_id = None
        self.api_url = "http://localhost:8000"
        self.current_image_path = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Tab Widget with 3 tabs: Setup, Text Query, Image+Text Query
        self.tab_widget = QTabWidget()

        # Setup Tab
        self.setup_tab = self.create_setup_tab()
        self.tab_widget.addTab(self.setup_tab, "Setup")

        # Text Chat Tab
        self.text_tab = self.create_text_tab()
        self.tab_widget.addTab(self.text_tab, "Text Query")

        # Vision Chat Tab
        self.vision_tab = self.create_vision_tab()
        self.tab_widget.addTab(self.vision_tab, "Image + Text Query")

        layout.addWidget(self.tab_widget)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close_session_and_dialog)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def create_setup_tab(self):
        """Create setup configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # API Configuration
        api_group = QGroupBox("API Configuration")
        api_layout = QFormLayout()

        self.api_url_input = QLineEdit("http://localhost:8000")
        api_layout.addRow("API URL:", self.api_url_input)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # Database Configuration
        db_group = QGroupBox("Database Configuration")
        db_layout = QFormLayout()

        self.db_name_input = QLineEdit()
        self.db_user_input = QLineEdit()
        self.db_password_input = QLineEdit()
        self.db_password_input.setEchoMode(QLineEdit.Password)
        self.db_host_input = QLineEdit("localhost")
        self.db_port_input = QLineEdit("5432")

        db_layout.addRow("Database Name:", self.db_name_input)
        db_layout.addRow("User:", self.db_user_input)
        db_layout.addRow("Password:", self.db_password_input)
        db_layout.addRow("Host:", self.db_host_input)
        db_layout.addRow("Port:", self.db_port_input)

        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        # Model Configuration for Text
        text_model_group = QGroupBox("Text Query Model Configuration")
        text_model_layout = QFormLayout()

        # Chatbot type selection
        self.text_chatbot_type_combo = QComboBox()
        self.text_chatbot_type_combo.addItems(["gemini_text", "ollama_text"])
        text_model_layout.addRow("Chatbot Type:", self.text_chatbot_type_combo)

        # Model name input
        self.text_model_name_input = QLineEdit("gemini-2.5-pro")
        text_model_layout.addRow("Model Name:", self.text_model_name_input)

        text_model_group.setLayout(text_model_layout)
        layout.addWidget(text_model_group)

        # Model Configuration for Vision
        vision_model_group = QGroupBox("Vision Query Model Configuration")
        vision_model_layout = QFormLayout()

        # Chatbot type (fixed to gemini_vision for now)
        self.vision_chatbot_type_combo = QComboBox()
        self.vision_chatbot_type_combo.addItems(["gemini_vision"])
        vision_model_layout.addRow("Chatbot Type:", self.vision_chatbot_type_combo)

        # Model name input
        self.vision_model_name_input = QLineEdit("gemini-2.5-pro")
        vision_model_layout.addRow("Model Name:", self.vision_model_name_input)

        vision_model_group.setLayout(vision_model_layout)
        layout.addWidget(vision_model_group)

        # Add stretch to push everything to the top
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_text_tab(self):
        """Create text query tab with its own session"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Session status for text
        self.text_status_label = QLabel("Status: Not connected")
        layout.addWidget(self.text_status_label)

        # Initialize button for text session
        self.text_init_button = QPushButton("Initialize Text Session")
        self.text_init_button.clicked.connect(self.initialize_text_session)
        layout.addWidget(self.text_init_button)

        # Question input
        layout.addWidget(QLabel("Enter your question:"))
        self.text_question_input = QTextEdit()
        self.text_question_input.setPlaceholderText(
            "e.g., Show me all cities with population greater than 1 million"
        )
        self.text_question_input.setMaximumHeight(120)
        layout.addWidget(self.text_question_input)

        # Get SQL Query button
        self.text_query_button = QPushButton("Get SQL Query")
        self.text_query_button.clicked.connect(self.get_text_sql_query)
        self.text_query_button.setEnabled(False)
        layout.addWidget(self.text_query_button)

        # SQL Query display
        layout.addWidget(QLabel("Generated SQL Query:"))
        self.text_sql_display = QTextEdit()
        self.text_sql_display.setReadOnly(True)
        self.text_sql_display.setMaximumHeight(150)
        layout.addWidget(self.text_sql_display)

        # Execute button
        self.text_execute_button = QPushButton("Execute and Add to QGIS")
        self.text_execute_button.clicked.connect(
            lambda: self.execute_and_add_layer("text")
        )
        self.text_execute_button.setEnabled(False)
        layout.addWidget(self.text_execute_button)

        # Response display
        layout.addWidget(QLabel("Response:"))
        self.text_response_display = QTextEdit()
        self.text_response_display.setReadOnly(True)
        self.text_response_display.setMaximumHeight(100)
        layout.addWidget(self.text_response_display)

        tab.setLayout(layout)
        return tab

    def create_vision_tab(self):
        """Create vision query tab with its own session"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Session status for vision
        self.vision_status_label = QLabel("Status: Not connected")
        layout.addWidget(self.vision_status_label)

        # Initialize button for vision session
        self.vision_init_button = QPushButton("Initialize Vision Session")
        self.vision_init_button.clicked.connect(self.initialize_vision_session)
        layout.addWidget(self.vision_init_button)

        # Question input
        layout.addWidget(QLabel("Enter your question:"))
        self.vision_question_input = QTextEdit()
        self.vision_question_input.setPlaceholderText(
            "e.g., What do you see in this map? Find similar features."
        )
        self.vision_question_input.setMaximumHeight(120)
        layout.addWidget(self.vision_question_input)

        # Image selection
        image_layout = QHBoxLayout()
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("Select an image file...")
        self.image_path_input.setReadOnly(True)
        image_layout.addWidget(self.image_path_input)

        browse_button = QPushButton("Browse Image")
        browse_button.clicked.connect(self.browse_image)
        image_layout.addWidget(browse_button)

        layout.addLayout(image_layout)

        # Get SQL Query button
        self.vision_query_button = QPushButton("Get SQL Query with Image")
        self.vision_query_button.clicked.connect(self.get_vision_sql_query)
        self.vision_query_button.setEnabled(False)
        layout.addWidget(self.vision_query_button)

        # SQL Query display
        layout.addWidget(QLabel("Generated SQL Query:"))
        self.vision_sql_display = QTextEdit()
        self.vision_sql_display.setReadOnly(True)
        self.vision_sql_display.setMaximumHeight(150)
        layout.addWidget(self.vision_sql_display)

        # Execute button
        self.vision_execute_button = QPushButton("Execute and Add to QGIS")
        self.vision_execute_button.clicked.connect(
            lambda: self.execute_and_add_layer("vision")
        )
        self.vision_execute_button.setEnabled(False)
        layout.addWidget(self.vision_execute_button)

        # Response display
        layout.addWidget(QLabel("Response:"))
        self.vision_response_display = QTextEdit()
        self.vision_response_display.setReadOnly(True)
        self.vision_response_display.setMaximumHeight(100)
        layout.addWidget(self.vision_response_display)

        tab.setLayout(layout)
        return tab

    def browse_image(self):
        """Open file dialog to select image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.current_image_path = file_path
            self.image_path_input.setText(file_path)

    def image_to_base64(self, image_path):
        """Convert image to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                return encoded_string
        except Exception as e:
            raise Exception(f"Failed to encode image: {str(e)}")

    def initialize_text_session(self):
        """Initialize text chatbot session"""
        try:
            # Close existing text session if any
            if self.text_session_id:
                try:
                    requests.delete(
                        f"{self.api_url}/session/{self.text_session_id}", timeout=5
                    )
                    print(f"Closed existing text session: {self.text_session_id}")
                except:
                    pass

            self.api_url = self.api_url_input.text()

            # Generate new session ID
            import uuid

            self.text_session_id = str(uuid.uuid4())

            # Get model configuration from Setup tab
            chatbot_type = self.text_chatbot_type_combo.currentText()
            model_name = self.text_model_name_input.text()

            # Prepare request
            data = {
                "session_id": self.text_session_id,
                "database_config": {
                    "db_type": "postgresql",
                    "db_name": self.db_name_input.text(),
                    "db_user": self.db_user_input.text(),
                    "db_password": self.db_password_input.text(),
                    "db_host": self.db_host_input.text(),
                    "db_port": self.db_port_input.text(),
                },
                "chatbot_type": chatbot_type,
                "model_name": model_name,
            }

            print(f"Initializing text session: {self.text_session_id}")
            print(f"Using chatbot type: {chatbot_type}, model: {model_name}")

            # Send request
            response = requests.post(
                f"{self.api_url}/initialize", json=data, timeout=30
            )

            if response.status_code == 200:
                self.text_status_label.setText(
                    f"Status: Connected (Session: {self.text_session_id[:8]}...)"
                )
                self.text_status_label.setStyleSheet("color: green")
                self.text_query_button.setEnabled(True)
                self.text_init_button.setText("Reinitialize Text Session")

                QMessageBox.information(
                    self, "Success", "Text session initialized successfully!"
                )
            else:
                error_msg = response.json().get("detail", "Unknown error")
                QMessageBox.warning(
                    self, "Error", f"Failed to initialize text session: {error_msg}"
                )
                self.text_session_id = None

        except Exception as e:
            import traceback

            print(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")
            self.text_session_id = None

    def initialize_vision_session(self):
        """Initialize vision chatbot session"""
        try:
            # Close existing vision session if any
            if self.vision_session_id:
                try:
                    requests.delete(
                        f"{self.api_url}/session/{self.vision_session_id}", timeout=5
                    )
                    print(f"Closed existing vision session: {self.vision_session_id}")
                except:
                    pass

            self.api_url = self.api_url_input.text()

            # Generate new session ID
            import uuid

            self.vision_session_id = str(uuid.uuid4())

            # Get model configuration from Setup tab
            chatbot_type = self.vision_chatbot_type_combo.currentText()
            model_name = self.vision_model_name_input.text()

            # Prepare request
            data = {
                "session_id": self.vision_session_id,
                "database_config": {
                    "db_type": "postgresql",
                    "db_name": self.db_name_input.text(),
                    "db_user": self.db_user_input.text(),
                    "db_password": self.db_password_input.text(),
                    "db_host": self.db_host_input.text(),
                    "db_port": self.db_port_input.text(),
                },
                "chatbot_type": chatbot_type,
                "model_name": model_name,
            }

            print(f"Initializing vision session: {self.vision_session_id}")
            print(f"Using chatbot type: {chatbot_type}, model: {model_name}")

            # Send request
            response = requests.post(
                f"{self.api_url}/initialize", json=data, timeout=30
            )

            if response.status_code == 200:
                self.vision_status_label.setText(
                    f"Status: Connected (Session: {self.vision_session_id[:8]}...)"
                )
                self.vision_status_label.setStyleSheet("color: green")
                self.vision_query_button.setEnabled(True)
                self.vision_init_button.setText("Reinitialize Vision Session")

                QMessageBox.information(
                    self, "Success", "Vision session initialized successfully!"
                )
            else:
                error_msg = response.json().get("detail", "Unknown error")
                QMessageBox.warning(
                    self, "Error", f"Failed to initialize vision session: {error_msg}"
                )
                self.vision_session_id = None

        except Exception as e:
            import traceback

            print(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")
            self.vision_session_id = None

    def get_text_sql_query(self):
        """Send text question to chatbot and extract SQL query"""
        try:
            question = self.text_question_input.toPlainText().strip()
            if not question:
                QMessageBox.warning(self, "Warning", "Please enter a question")
                return

            if not self.text_session_id:
                QMessageBox.warning(
                    self, "Warning", "Please initialize text session first"
                )
                return

            print(f"Sending text query: {question}")

            # Send chat request to /chat/text endpoint
            data = {"session_id": self.text_session_id, "message": question}

            response = requests.post(f"{self.api_url}/chat/text", json=data, timeout=60)

            if response.status_code == 200:
                chatbot_response = response.json()["response"]
                self.text_response_display.setText(chatbot_response)

                # Extract SQL query from response
                sql_query = self.extract_sql_query(chatbot_response)

                if sql_query:
                    self.text_sql_display.setText(sql_query)
                    self.text_execute_button.setEnabled(True)
                    QMessageBox.information(
                        self, "Success", "SQL query generated successfully!"
                    )
                else:
                    QMessageBox.warning(
                        self, "Warning", "No SQL query found in response"
                    )
            else:
                error_msg = response.json().get("detail", "Unknown error")
                QMessageBox.warning(
                    self, "Error", f"Failed to get response: {error_msg}"
                )

        except Exception as e:
            import traceback

            print(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Request error: {str(e)}")

    def get_vision_sql_query(self):
        """Send vision question with image to chatbot and extract SQL query"""
        try:
            question = self.vision_question_input.toPlainText().strip()
            if not question:
                QMessageBox.warning(self, "Warning", "Please enter a question")
                return

            if not self.current_image_path:
                QMessageBox.warning(self, "Warning", "Please select an image")
                return

            if not self.vision_session_id:
                QMessageBox.warning(
                    self, "Warning", "Please initialize vision session first"
                )
                return

            print(f"Sending vision query: {question}")

            # Send chat request to /chat/vision endpoint
            data = {
                "session_id": self.vision_session_id,
                "message": question,
                "image": self.current_image_path,
            }

            response = requests.post(
                f"{self.api_url}/chat/vision", json=data, timeout=60
            )

            if response.status_code == 200:
                chatbot_response = response.json()["response"]
                self.vision_response_display.setText(chatbot_response)

                # Extract SQL query from response
                sql_query = self.extract_sql_query(chatbot_response)

                if sql_query:
                    self.vision_sql_display.setText(sql_query)
                    self.vision_execute_button.setEnabled(True)
                    QMessageBox.information(
                        self, "Success", "SQL query generated successfully!"
                    )
                else:
                    QMessageBox.warning(
                        self, "Warning", "No SQL query found in response"
                    )
            else:
                error_msg = response.json().get("detail", "Unknown error")
                QMessageBox.warning(
                    self, "Error", f"Failed to get response: {error_msg}"
                )

        except Exception as e:
            import traceback

            print(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Request error: {str(e)}")

    def extract_sql_query(self, response):
        """Extract SQL query from chatbot response"""
        # Look for ```sql ... ``` pattern
        sql_pattern = r"```sql\s*(.*?)\s*```"
        match = re.search(sql_pattern, response, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Fallback: look for SELECT statement
        select_pattern = r"(SELECT\s+.*?;)"
        match = re.search(select_pattern, response, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        return None

    def execute_and_add_layer(self, tab_type):
        """Execute SQL query via API and add results as QGIS layer"""
        try:
            # Get the correct session_id and sql_display based on tab
            if tab_type == "text":
                session_id = self.text_session_id
                sql_query = self.text_sql_display.toPlainText().strip()
            else:  # vision
                session_id = self.vision_session_id
                sql_query = self.vision_sql_display.toPlainText().strip()

            if not sql_query:
                QMessageBox.warning(self, "Warning", "No SQL query to execute")
                return

            if not session_id:
                QMessageBox.warning(self, "Warning", "Session not initialized")
                return

            # Send execute request to API
            data = {"session_id": session_id, "query": sql_query}

            response = requests.post(f"{self.api_url}/execute", json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()

                if not result["success"]:
                    QMessageBox.critical(
                        self, "Error", f"Query execution failed: {result['error']}"
                    )
                    return

                rows = result["rows"]
                column_names = result["column_names"]

                if not rows:
                    QMessageBox.information(self, "Info", "Query returned no results")
                    return

                # Check if there's a geometry column
                geom_col_index = self.find_geometry_column(column_names, rows[0])

                if geom_col_index is not None:
                    self.add_vector_layer(rows, column_names, geom_col_index)
                else:
                    self.add_attribute_table(rows, column_names)

                QMessageBox.information(
                    self, "Success", f"Added layer with {len(rows)} features!"
                )
            else:
                error_msg = response.json().get("detail", "Unknown error")
                QMessageBox.warning(
                    self, "Error", f"Failed to execute query: {error_msg}"
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Execution error: {str(e)}")

    def find_geometry_column(self, column_names, first_row):
        """Find geometry column in results"""
        geom_keywords = [
            "geom",
            "geometry",
            "the_geom",
            "wkb_geometry",
            "shape",
            "wkt_geometry",
        ]

        # First, check column names
        for i, col_name in enumerate(column_names):
            if col_name.lower() in geom_keywords:
                return i

        # Then check if any column contains geometry-like data
        for i in range(len(first_row)):
            if i < len(first_row) and first_row[i]:
                value_str = str(first_row[i])
                # Check if it looks like WKT geometry
                if any(
                    keyword in value_str.upper()[:50]  # Check first 50 chars
                    for keyword in [
                        "POINT(",
                        "LINESTRING(",
                        "POLYGON((",
                        "MULTIPOINT(",
                        "MULTILINESTRING(",
                        "MULTIPOLYGON(",
                    ]
                ):
                    return i

        return None

    def add_vector_layer(self, rows, column_names, geom_col_index):
        """Add results as vector layer with geometries"""
        try:
            # Debug: Show what we're working with
            print(f"Column names: {column_names}")
            print(f"Geometry column index: {geom_col_index}")
            print(f"First row sample: {rows[0] if rows else 'No rows'}")

            # Get first geometry to determine type and format
            first_geom_str = (
                str(rows[0][geom_col_index]) if rows and rows[0][geom_col_index] else ""
            )
            print(f"First geometry data: {first_geom_str[:100]}...")

            # Detect if it's WKB (hex string) or WKT (text)
            is_wkb = False
            if first_geom_str and all(
                c in "0123456789ABCDEFabcdef" for c in first_geom_str.replace(" ", "")
            ):
                is_wkb = True
                print("Detected WKB (binary) geometry format")
            else:
                print("Detected WKT (text) geometry format")

            # Parse first geometry to detect type
            if is_wkb:
                # Parse WKB to get type
                try:
                    wkb_bytes = bytes.fromhex(first_geom_str)
                    geom = QgsGeometry()
                    geom.fromWkb(wkb_bytes)

                    # Use wkbType() instead of type()
                    wkb_type = geom.wkbType()

                    # Check geometry type using QgsWkbTypes methods
                    if QgsWkbTypes.geometryType(wkb_type) == QgsWkbTypes.PointGeometry:
                        if QgsWkbTypes.isMultiType(wkb_type):
                            geom_type = "MultiPoint"
                        else:
                            geom_type = "Point"
                    elif QgsWkbTypes.geometryType(wkb_type) == QgsWkbTypes.LineGeometry:
                        if QgsWkbTypes.isMultiType(wkb_type):
                            geom_type = "MultiLineString"
                        else:
                            geom_type = "LineString"
                    elif (
                        QgsWkbTypes.geometryType(wkb_type)
                        == QgsWkbTypes.PolygonGeometry
                    ):
                        if QgsWkbTypes.isMultiType(wkb_type):
                            geom_type = "MultiPolygon"
                        else:
                            geom_type = "Polygon"
                    else:
                        geom_type = "Point"

                    print(f"WKB Type: {wkb_type}, Detected: {geom_type}")

                except Exception as e:
                    print("WKB parse error:", e)
                    geom_type = "Point"
            else:
                # Detect from WKT text
                upper_geom = first_geom_str.upper()
                if "MULTIPOLYGON" in upper_geom:
                    geom_type = "MultiPolygon"
                elif "POLYGON" in upper_geom:
                    geom_type = "Polygon"
                elif "MULTILINESTRING" in upper_geom:
                    geom_type = "MultiLineString"
                elif "LINESTRING" in upper_geom:
                    geom_type = "LineString"
                elif "MULTIPOINT" in upper_geom:
                    geom_type = "MultiPoint"
                else:
                    geom_type = "Point"

            print(f"Detected geometry type: {geom_type}")

            # Create layer
            uri = f"{geom_type}?crs=EPSG:4326"
            layer = QgsVectorLayer(uri, "Query Result", "memory")

            if not layer.isValid():
                print(f"Failed to create layer with Point type, trying Polygon")
                uri = "Polygon?crs=EPSG:4326"
                layer = QgsVectorLayer(uri, "Query Result", "memory")

            if not layer.isValid():
                error_msg = f"Failed to create memory layer with URI: {uri}"
                print(error_msg)
                QMessageBox.critical(
                    self, "Error", f"{error_msg}\n\nPlease check QGIS installation."
                )
                return

            print("Layer created successfully")
            provider = layer.dataProvider()

            # Add attribute fields (excluding geometry column)
            fields = []
            attr_indices = []
            for i, col_name in enumerate(column_names):
                if i != geom_col_index:
                    fields.append(QgsField(col_name, QVariant.String))
                    attr_indices.append(i)

            if not provider.addAttributes(fields):
                QMessageBox.critical(self, "Error", "Failed to add attributes to layer")
                return

            layer.updateFields()
            print(f"Added {len(fields)} attribute fields")

            # Add features
            features = []
            skipped = 0

            for row_idx, row in enumerate(rows):
                try:
                    feature = QgsFeature(layer.fields())

                    # Get geometry data
                    geom_data = (
                        str(row[geom_col_index]).strip()
                        if row[geom_col_index]
                        else None
                    )

                    if not geom_data:
                        skipped += 1
                        continue

                    # Parse geometry based on format
                    if is_wkb:
                        # Parse WKB (hex string)
                        try:
                            wkb_bytes = bytes.fromhex(geom_data)
                            geometry = QgsGeometry()
                            geometry.fromWkb(wkb_bytes)
                        except Exception as e:
                            print(f"Row {row_idx}: Failed to parse WKB: {str(e)}")
                            skipped += 1
                            continue
                    else:
                        # Parse WKT
                        geometry = QgsGeometry.fromWkt(geom_data)

                    if geometry.isNull():
                        print(f"Row {row_idx}: Invalid geometry")
                        skipped += 1
                        continue

                    if geometry.isEmpty():
                        print(f"Row {row_idx}: Empty geometry")
                        skipped += 1
                        continue

                    feature.setGeometry(geometry)

                    # Set attributes (only non-geometry columns)
                    attrs = []
                    for i in attr_indices:
                        val = row[i]
                        attrs.append(str(val) if val is not None else "")

                    feature.setAttributes(attrs)
                    features.append(feature)

                except Exception as e:
                    print(f"Row {row_idx}: Error processing - {str(e)}")
                    skipped += 1
                    continue

            print(f"Processed {len(features)} valid features, skipped {skipped}")

            if not features:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "No valid geometries found in the result set.",
                )
                return

            # Add features to layer
            if not provider.addFeatures(features):
                QMessageBox.critical(self, "Error", "Failed to add features to layer")
                return

            layer.updateExtents()
            print(f"Layer extent: {layer.extent().toString()}")

            # Add to project
            QgsProject.instance().addMapLayer(layer)
            print("Layer added to project")

            # Zoom to layer extent
            if self.iface:
                canvas = self.iface.mapCanvas()
                extent = layer.extent()
                extent.scale(1.1)  # Add 10% buffer
                canvas.setExtent(extent)
                canvas.refresh()
                print("Map canvas refreshed")

            msg = f"Added layer with {len(features)} features!"
            if skipped > 0:
                msg += f" ({skipped} features skipped)"

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            print(f"Error in add_vector_layer: {error_details}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to add vector layer:\n{str(e)}",
            )

    def add_attribute_table(self, rows, column_names):
        """Add results as attribute table (no geometry)"""
        try:
            layer = QgsVectorLayer("none", "Query Result (No Geometry)", "memory")

            if not layer.isValid():
                QMessageBox.critical(self, "Error", "Failed to create layer")
                return

            provider = layer.dataProvider()

            # Add fields
            fields = [QgsField(col_name, QVariant.String) for col_name in column_names]
            provider.addAttributes(fields)
            layer.updateFields()

            # Add features
            features = []
            for row in rows:
                feature = QgsFeature()
                attrs = [str(val) if val is not None else "" for val in row]
                feature.setAttributes(attrs)
                features.append(feature)

            provider.addFeatures(features)

            # Add to project
            QgsProject.instance().addMapLayer(layer)

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to add attribute table: {str(e)}"
            )

    def close_session_and_dialog(self):
        """Close both sessions and dialog"""
        # Close text session
        if self.text_session_id:
            try:
                requests.delete(
                    f"{self.api_url}/session/{self.text_session_id}", timeout=5
                )
                print(f"Closed text session: {self.text_session_id}")
            except:
                pass

        # Close vision session
        if self.vision_session_id:
            try:
                requests.delete(
                    f"{self.api_url}/session/{self.vision_session_id}", timeout=5
                )
                print(f"Closed vision session: {self.vision_session_id}")
            except:
                pass

        self.accept()


class SQLQueryPlugin:
    """QGIS Plugin Implementation"""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = "&SQL Query Plugin"
        self.toolbar = self.iface.addToolBar("SQL Query Plugin")
        self.toolbar.setObjectName("SQL Query Plugin")

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI"""
        plugin_dir = os.path.dirname(__file__)  # Plugin folder
        icon_path = os.path.join(plugin_dir, "icons", "icon.png")
        self.add_action(
            icon_path,
            text="Spatial Mind",
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

        self.action = QAction(QIcon(icon_path), "Spatial Mind", self.iface.mainWindow())
        self.action.setWhatsThis("Run Spatial Mind plugin")
        self.action.triggered.connect(self.run)

        self.iface.addToolBarIcon(self.action)

        self.iface.addPluginToMenu("&Spatial Mind", self.action)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI"""
        for action in self.actions:
            self.iface.removePluginMenu("&SQL Query Plugin", action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        """Run method that performs all the real work"""
        dialog = SQLQueryDialog(iface=self.iface)
        dialog.exec_()
