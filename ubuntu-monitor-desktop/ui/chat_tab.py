"""
Chat Tab — giao tiếp real-time qua TCP socket.

Cho phép tạo TCP server (QTcpServer) và client kết nối đến,
gửi/nhận tin nhắn text trực tiếp giữa các máy.

Sử dụng QtNetwork (QTcpServer, QTcpSocket) — event-driven,
tích hợp với vòng lặp sự kiện PyQt6, không cần thread riêng.

Nguyên lý kernel:
  - TCP socket: stream-oriented, connection-oriented protocol
  - struct sock trong include/net/sock.h chứa:
      sk_state, sk_rcvbuf, sk_sndbuf, sk_receive_queue, ...
  - TCP state machine: CLOSED → LISTEN → SYN_SENT → SYN_RECV → ESTABLISHED → ...
  - accept() tạo socket mới cho mỗi kết nối (fd mới)
"""

from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QGroupBox, QListWidget, QListWidgetItem,
    QSplitter, QStackedWidget, QButtonGroup, QRadioButton,
)
from PyQt6.QtNetwork import QTcpServer, QTcpSocket, QHostAddress

from . import styles


class ChatTab(QWidget):
    def __init__(self):
        super().__init__()
        self.server = None
        self.client_socket = None
        self.client_connections: dict[int, QTcpSocket] = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header with mode selector
        header = QHBoxLayout()
        title = QLabel("Socket Chat")
        title.setStyleSheet(styles.TITLE_STYLE)
        header.addWidget(title)
        header.addStretch()

        self.mode_group = QButtonGroup(self)
        self.server_radio = QRadioButton("Server")
        self.client_radio = QRadioButton("Client")
        self.server_radio.setChecked(True)
        for rb in (self.server_radio, self.client_radio):
            rb.setStyleSheet(f"color: {styles.COLORS['text']}; font-weight: bold; padding: 4px 8px;")
            self.mode_group.addButton(rb)
        self.server_radio.toggled.connect(self._on_mode_changed)
        header.addWidget(self.server_radio)
        header.addWidget(self.client_radio)
        layout.addLayout(header)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_server_panel())
        self.stack.addWidget(self._create_client_panel())
        layout.addWidget(self.stack, stretch=1)

    def _create_server_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Port:"))
        self.server_port = QLineEdit("8888")
        self.server_port.setStyleSheet(styles.INPUT_STYLE)
        self.server_port.setFixedWidth(100)
        ctrl.addWidget(self.server_port)

        self.start_btn = QPushButton("▶ Start Server")
        self.start_btn.setStyleSheet(styles.BTN_SUCCESS)
        self.start_btn.clicked.connect(self._start_server)
        ctrl.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setStyleSheet(styles.BTN_DANGER)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_server)
        ctrl.addWidget(self.stop_btn)

        self.server_status = QLabel("● Offline")
        self.server_status.setStyleSheet(f"color: {styles.COLORS['danger']}; font-weight: bold;")
        ctrl.addWidget(self.server_status)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Splitter: clients list + chat
        splitter = QSplitter(Qt.Orientation.Horizontal)

        clients_group = QGroupBox("Connected Clients")
        clients_group.setStyleSheet(f"QGroupBox {{ color: {styles.COLORS['text_secondary']}; font-size: 12px; font-weight: bold; border: 1px solid {styles.COLORS['border']}; border-radius: 6px; margin-top: 8px; padding: 12px; }}")
        cl = QVBoxLayout(clients_group)
        self.clients_list = QListWidget()
        self.clients_list.setStyleSheet(f"QListWidget {{ background: {styles.COLORS['bg']}; color: {styles.COLORS['text']}; border: none; font-size: 12px; }}")
        cl.addWidget(self.clients_list)
        splitter.addWidget(clients_group)

        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        self.server_display = QTextEdit()
        self.server_display.setReadOnly(True)
        self.server_display.setStyleSheet(styles.TERMINAL_STYLE)
        chat_layout.addWidget(self.server_display, stretch=1)

        inp = QHBoxLayout()
        self.server_input = QLineEdit()
        self.server_input.setStyleSheet(styles.INPUT_STYLE)
        self.server_input.setPlaceholderText("Type a message and press Enter...")
        self.server_input.returnPressed.connect(self._server_send)
        inp.addWidget(self.server_input, stretch=1)

        self.server_send_btn = QPushButton("Send")
        self.server_send_btn.setStyleSheet(styles.BTN_PRIMARY)
        self.server_send_btn.clicked.connect(self._server_send)
        inp.addWidget(self.server_send_btn)
        chat_layout.addLayout(inp)

        splitter.addWidget(chat_widget)
        splitter.setSizes([180, 600])
        layout.addWidget(splitter, stretch=1)

        return panel

    def _create_client_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Host:"))
        self.client_host = QLineEdit("127.0.0.1")
        self.client_host.setStyleSheet(styles.INPUT_STYLE)
        self.client_host.setFixedWidth(150)
        ctrl.addWidget(self.client_host)

        ctrl.addWidget(QLabel("Port:"))
        self.client_port = QLineEdit("8888")
        self.client_port.setStyleSheet(styles.INPUT_STYLE)
        self.client_port.setFixedWidth(100)
        ctrl.addWidget(self.client_port)

        self.connect_btn = QPushButton("▶ Connect")
        self.connect_btn.setStyleSheet(styles.BTN_SUCCESS)
        self.connect_btn.clicked.connect(self._connect)
        ctrl.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("⏹ Disconnect")
        self.disconnect_btn.setStyleSheet(styles.BTN_DANGER)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self._disconnect)
        ctrl.addWidget(self.disconnect_btn)

        self.client_status = QLabel("● Disconnected")
        self.client_status.setStyleSheet(f"color: {styles.COLORS['danger']}; font-weight: bold;")
        ctrl.addWidget(self.client_status)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.client_display = QTextEdit()
        self.client_display.setReadOnly(True)
        self.client_display.setStyleSheet(styles.TERMINAL_STYLE)
        layout.addWidget(self.client_display, stretch=1)

        inp = QHBoxLayout()
        self.client_input = QLineEdit()
        self.client_input.setStyleSheet(styles.INPUT_STYLE)
        self.client_input.setPlaceholderText("Type a message and press Enter...")
        self.client_input.returnPressed.connect(self._client_send)
        inp.addWidget(self.client_input, stretch=1)

        self.client_send_btn = QPushButton("Send")
        self.client_send_btn.setStyleSheet(styles.BTN_PRIMARY)
        self.client_send_btn.clicked.connect(self._client_send)
        inp.addWidget(self.client_send_btn)
        layout.addLayout(inp)

        return panel

    def _on_mode_changed(self):
        self.stack.setCurrentIndex(0 if self.server_radio.isChecked() else 1)

    # ── Server ──────────────────────────────────────────

    def _start_server(self):
        try:
            port = int(self.server_port.text())
        except ValueError:
            self._log_server("[Error] Invalid port number", styles.COLORS["danger"])
            return

        self.server = QTcpServer()
        self.server.newConnection.connect(self._on_new_connection)

        if self.server.listen(QHostAddress("0.0.0.0"), port):
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.server_port.setEnabled(False)
            self.server_status.setText(f"● Listening on port {port}")
            self.server_status.setStyleSheet(f"color: {styles.COLORS['success']}; font-weight: bold;")
            self._log_server(f"[Server] Listening on port {port}...", styles.COLORS["accent"])
        else:
            self._log_server(f"[Error] {self.server.errorString()}", styles.COLORS["danger"])

    def _stop_server(self):
        for sock in list(self.client_connections.values()):
            sock.disconnectFromHost()
        self.client_connections.clear()
        self.clients_list.clear()

        if self.server:
            self.server.close()
            self.server = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.server_port.setEnabled(True)
        self.server_status.setText("● Offline")
        self.server_status.setStyleSheet(f"color: {styles.COLORS['danger']}; font-weight: bold;")
        self._log_server("[Server] Stopped", styles.COLORS["text_muted"])

    def _on_new_connection(self):
        sock = self.server.nextPendingConnection()
        cid = id(sock)
        self.client_connections[cid] = sock

        peer = f"{sock.peerAddress().toString()}:{sock.peerPort()}"
        self.clients_list.addItem(QListWidgetItem(peer))

        sock.readyRead.connect(lambda c=cid: self._on_client_data(c))
        sock.disconnected.connect(lambda c=cid: self._on_client_disconnected(c))

        self._log_server(f"[+] Client connected: {peer}", styles.COLORS["success"])

    def _on_client_data(self, cid):
        sock = self.client_connections.get(cid)
        if not sock:
            return
        data = bytes(sock.readAll()).decode("utf-8")
        peer = f"{sock.peerAddress().toString()}:{sock.peerPort()}"
        for line in data.strip().split("\n"):
            if line:
                self._log_server(f"[{peer}] {line}", styles.COLORS["text"])

    def _on_client_disconnected(self, cid):
        sock = self.client_connections.pop(cid, None)
        if sock:
            self._log_server(f"[-] Client disconnected: {sock.peerAddress().toString()}:{sock.peerPort()}", styles.COLORS["warning"])

        self.clients_list.clear()
        for s in self.client_connections.values():
            self.clients_list.addItem(QListWidgetItem(f"{s.peerAddress().toString()}:{s.peerPort()}"))

    def _server_send(self):
        text = self.server_input.text().strip()
        if not text:
            return

        self._log_server(f"[Server] {text}", styles.COLORS["accent"])
        for sock in list(self.client_connections.values()):
            if sock.state() == QTcpSocket.SocketState.ConnectedState:
                sock.write(QByteArray(f"Server: {text}\n".encode("utf-8")))
        self.server_input.clear()

    def _log_server(self, msg, color):
        self.server_display.append(f'<span style="color:{color};">{msg}</span>')

    # ── Client ──────────────────────────────────────────

    def _connect(self):
        host = self.client_host.text().strip()
        try:
            port = int(self.client_port.text())
        except ValueError:
            self._log_client("[Error] Invalid port number", styles.COLORS["danger"])
            return

        self.client_socket = QTcpSocket()
        self.client_socket.connected.connect(self._on_connected)
        self.client_socket.disconnected.connect(self._on_disconnected)
        self.client_socket.readyRead.connect(self._on_server_data)
        self.client_socket.errorOccurred.connect(self._on_error)

        self.client_socket.connectToHost(host, port)

        self.connect_btn.setEnabled(False)
        self.client_host.setEnabled(False)
        self.client_port.setEnabled(False)
        self.client_status.setText("● Connecting...")
        self.client_status.setStyleSheet(f"color: {styles.COLORS['warning']}; font-weight: bold;")

    def _disconnect(self):
        if self.client_socket:
            self.client_socket.disconnectFromHost()
        self.disconnect_btn.setEnabled(False)
        self.connect_btn.setEnabled(True)
        self.client_host.setEnabled(True)
        self.client_port.setEnabled(True)
        self.client_status.setText("● Disconnected")
        self.client_status.setStyleSheet(f"color: {styles.COLORS['danger']}; font-weight: bold;")

    def _on_connected(self):
        self.disconnect_btn.setEnabled(True)
        self.client_status.setText("● Connected")
        self.client_status.setStyleSheet(f"color: {styles.COLORS['success']}; font-weight: bold;")
        self._log_client("[+] Connected to server", styles.COLORS["success"])

    def _on_disconnected(self):
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.client_host.setEnabled(True)
        self.client_port.setEnabled(True)
        self.client_status.setText("● Disconnected")
        self.client_status.setStyleSheet(f"color: {styles.COLORS['danger']}; font-weight: bold;")
        self._log_client("[-] Disconnected", styles.COLORS["warning"])
        self.client_socket = None

    def _on_error(self, error):
        self.connect_btn.setEnabled(True)
        self.client_host.setEnabled(True)
        self.client_port.setEnabled(True)
        self.client_status.setText("● Error")
        self.client_status.setStyleSheet(f"color: {styles.COLORS['danger']}; font-weight: bold;")
        self._log_client(f"[Error] {self.client_socket.errorString() if self.client_socket else 'Unknown'}", styles.COLORS["danger"])
        self.client_socket = None

    def _on_server_data(self):
        if not self.client_socket:
            return
        data = bytes(self.client_socket.readAll()).decode("utf-8")
        for line in data.strip().split("\n"):
            if line:
                self._log_client(line, styles.COLORS["text"])

    def _client_send(self):
        text = self.client_input.text().strip()
        if not text or not self.client_socket:
            return

        self._log_client(f"[Me] {text}", styles.COLORS["accent"])
        self.client_socket.write(QByteArray(f"{text}\n".encode("utf-8")))
        self.client_input.clear()

    def _log_client(self, msg, color):
        self.client_display.append(f'<span style="color:{color};">{msg}</span>')
