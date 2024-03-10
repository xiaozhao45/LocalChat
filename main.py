import sys
import socket
import os

# PyQt5相关库导入
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout, QPlainTextEdit, QMenuBar, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QTextCursor, QIcon, QColor, QKeySequence
from PyQt5.QtNetwork import QTcpServer, QHostAddress, QTcpSocket
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

local_ip = socket.gethostbyname(socket.gethostname())

if local_ip == "127.0.0.1":
    noInternet_tip = QMessageBox.warning( "警告", "当前网络连接不可用，请检查网络连接！")


class ChatRoom(QWidget):
    def __init__(self):
        super().__init__()
        self.server = None
        self.username = None
        self.clients = []

        # 创建界面元素
        self.ip_label = QLabel("IP:")
        self.ip_edit = QLineEdit()
        self.port_label = QLabel("Port:")
        self.port_edit = QLineEdit()
        self.start_server_btn = QPushButton("开启服务器")
        self.username_label = QLabel("用户名:")
        self.username_edit = QLineEdit()
        self.confirm_username_btn = QPushButton("确定")
        self.messages_display = QPlainTextEdit()
        self.input_edit = QTextEdit()
        self.send_btn = QPushButton("发送")
        self.send_btn.setEnabled(False)

        # 绑定事件处理函数
        self.start_server_btn.clicked.connect(self.start_server)
        self.input_edit.textChanged.connect(self.check_input)
        self.send_btn.clicked.connect(self.send_message)
        self.confirm_username_btn.clicked.connect(self.confirm_username)

        # 布局
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(self.ip_label)
        ip_layout.addWidget(self.ip_edit)
        ip_layout.addWidget(self.port_label)
        ip_layout.addWidget(self.port_edit)
        ip_layout.addWidget(self.start_server_btn)

        username_layout = QHBoxLayout()
        username_layout.addWidget(self.username_label)
        username_layout.addWidget(self.username_edit)
        username_layout.addWidget(self.confirm_username_btn)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.send_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(ip_layout)
        main_layout.addLayout(username_layout)
        main_layout.addWidget(self.messages_display)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)

    def start_server(self):
        # 如果已经开启服务器，点击按钮则关闭服务器
        if self.server is not None:
            # 添加在关闭服务器时发送告别消息的逻辑
            goodbye_message = f"服务器创建者已经关闭服务器，有缘再会\n\n"
            self.update_clients(goodbye_message)
            for client in self.clients:
                client.write(goodbye_message.encode())

            
            self.server.close()
            self.server = None
            self.start_server_btn.setText("开启服务器")
            self.update_clients("服务器关闭\n\n")
            self.input_edit.setReadOnly(True)  # 关闭编辑功能
            return
        

        # 开启服务器
        port = int(self.port_edit.text())
        self.server = QTcpServer(self)
        self.server.listen(QHostAddress.Any, port)
        self.server.newConnection.connect(self.handle_new_connection)
        self.start_server_btn.setText("关闭服务器")
        self.update_clients(f"服务器开启，端口号：{port}\n\n")
        self.input_edit.setReadOnly(False)  # 开启编辑功能

    def handle_new_connection(self):
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(self.receive_message)
        self.clients.append(socket)
        self.update_clients("新客户端已连接\n\n")

    def receive_message(self):
        sender_socket = self.sender()
        message = sender_socket.readAll().data().decode()
        self.update_clients(message)

    def send_message(self):
        message = self.input_edit.toPlainText()
        formatted_message = f"{self.username}：{message}\n\n"

        for client in self.clients:
            client.write(formatted_message.encode())

        self.update_clients(formatted_message)
        self.input_edit.clear()
        self.input_edit.setFocus()  # 将焦点重新设置到编辑框
        self.check_input()  # 检查输入框状态

    def update_clients(self, message):
        cursor = self.messages_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(message)

        # 设置文本颜色
        username_start = message.find(":") + 1
        username_end = message.find("：")
        if username_start > 0 and username_end > 0:
            cursor.setPosition(cursor.position() - len(message) + username_start, QTextCursor.MoveAnchor)
            cursor.setPosition(cursor.position() + username_end - username_start, QTextCursor.KeepAnchor)
            color = QColor("blue")
            format_ = cursor.charFormat()
            format_.setForeground(color)
            cursor.setCharFormat(format_)

        # 滚动到底部
        self.messages_display.verticalScrollBar().setValue(self.messages_display.verticalScrollBar().maximum())

    def check_input(self):
        if self.input_edit.toPlainText() and self.username:
            self.send_btn.setEnabled(True)
        else:
            self.send_btn.setEnabled(False)

    def confirm_username(self):      
        username = self.username_edit.text() + "[Admin]"
        if username:
            self.username = username
            self.username_edit.setReadOnly(True)
            self.confirm_username_btn.setEnabled(False)
            self.check_input()
            self.input_edit.setReadOnly(False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("聊天服务器")
        self.resize(600, 400)
        self.setWindowIcon(QIcon('ico01.ico'))

        self.chat_room = ChatRoom()
        self.setCentralWidget(self.chat_room)

        self.chat_room = ChatRoom()
        self.setCentralWidget(self.chat_room)
                # 创建顶部菜单栏
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # 创建“文件”菜单及其动作
        file_menu = QMenu('文件', self)
        self.menu_bar.addMenu(file_menu)
        exit_action = QAction('退出', self, shortcut=QKeySequence.Quit)
        exit_action.triggered.connect(self.close_application)
        save_chat_action = QAction('保存聊天记录', self)
        save_chat_action.triggered.connect(self.save_chat_to_file)
        file_menu.addAction(exit_action)
        file_menu.addAction(save_chat_action)

        # 创建“编辑”菜单及其动作
        edit_menu = QMenu('编辑', self)
        self.menu_bar.addMenu(edit_menu)
        cut_action = QAction('剪切', self, shortcut=QKeySequence.Cut)
        copy_action = QAction('复制', self, shortcut=QKeySequence.Copy)
        paste_action = QAction('粘贴', self, shortcut=QKeySequence.Paste)
        cut_action.setEnabled(False)  # 确保在没有选中内容时，剪切不可用
        copy_action.setEnabled(False)  # 同理，复制也不可用
        self.chat_client = self.chat_room
        self.chat_client.input_edit.copyAvailable.connect(lambda c: cut_action.setEnabled(c))
        self.chat_client.input_edit.copyAvailable.connect(lambda c: copy_action.setEnabled(c))
        cut_action.triggered.connect(lambda: self.chat_client.input_edit.cut())
        copy_action.triggered.connect(lambda: self.chat_client.input_edit.copy())
        paste_action.triggered.connect(lambda: self.chat_client.input_edit.paste())
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)

        # 创建“关于”菜单及其动作
        about_menu = QMenu('关于', self)
        self.menu_bar.addMenu(about_menu)
        about_action = QAction('软件信息', self)
        about_action.triggered.connect(self.show_about_dialog)
        about_menu.addAction(about_action)

    def close_application(self):
        self.close()

    def update_messages(self, message: str):
        self.chat_room.update_clients(message)

    def save_chat_to_file(self):
        current_dir = os.getcwd()
        filename = "chat_log.txt"
        full_path = os.path.join(current_dir, filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            chat_history = self.chat_client.messages_display.toPlainText()
            f.write(chat_history)
        self.update_messages(f"聊天记录已保存到当前目录：{filename}\n")

    def show_about_dialog(self):
        message = f"软件名称：聊天室服务器\n软件作者：XiaoZhao\nGithub开源地址：http://github.com/xiaozhao45"
        QMessageBox.about(self, "关于本软件", message)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
