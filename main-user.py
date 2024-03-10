import sys
import socket
import os

# PyQt5相关库导入
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout, QPlainTextEdit, QMenuBar, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QTextCursor, QIcon, QColor, QKeySequence
from PyQt5.QtNetwork import QTcpSocket, QHostAddress, QAbstractSocket, QTcpServer
from PyQt5.QtCore import pyqtSignal, pyqtSlot

local_ip = socket.gethostbyname(socket.gethostname())

if local_ip == "127.0.0.1":
    noInternet_tip = QMessageBox.warning( "警告", "当前网络连接不可用，请检查网络连接！")


class ChatClient(QWidget):
    def __init__(self):
        super().__init__()
        self.socket = None
        self.username = None

        # 创建界面元素
        self.ip_label = QLabel("IP:")
        self.ip_edit = QLineEdit()
        self.port_label = QLabel("Port:")
        self.port_edit = QLineEdit("8888")
        self.connect_btn = QPushButton("连接")
        self.username_label = QLabel("用户名:")
        self.username_edit = QLineEdit()
        self.confirm_username_btn = QPushButton("确定")
        self.messages_display = QPlainTextEdit()
        self.input_edit = QTextEdit()
        self.send_btn = QPushButton("发送")
        self.send_btn.setEnabled(False)

        # 绑定事件处理函数
        self.connect_btn.clicked.connect(self.connect_to_server)
        self.input_edit.textChanged.connect(self.check_input)
        self.send_btn.clicked.connect(self.send_message)
        self.confirm_username_btn.clicked.connect(self.confirm_username)

        # 布局
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(self.ip_label)
        ip_layout.addWidget(self.ip_edit)
        ip_layout.addWidget(self.port_label)
        ip_layout.addWidget(self.port_edit)
        ip_layout.addWidget(self.connect_btn)

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

    def disconnect_from_server(self):
                if self.socket is not None:
                    self.socket.disconnectFromHost()
                    self.handle_disconnected()  # 直接调用断开连接的处理逻辑
    
    def connect_to_server(self):
        try:
            ip = QHostAddress(self.ip_edit.text())
            port = int(self.port_edit.text())
            self.socket = QTcpSocket(self)
            self.socket.readyRead.connect(self.receive_message)
            self.socket.disconnected.connect(self.handle_disconnected)
            self.socket.error.connect(self.handle_socket_error)
            self.socket.connectToHost(ip, port)
            self.send_btn.setEnabled(True)

            if self.socket.waitForConnected(1000):
                self.update_messages("已连接到服务器\n欲要发送消息请确定用户名\n\n")
                self.username_edit.setEnabled(True)
                self.confirm_username_btn.setEnabled(True)
                self.connect_btn.setEnabled(False)
                self.connect_btn.setText("断开连接")  # 修改连接按钮文本为“断开连接”
                self.connect_btn.clicked.disconnect()  # 断开原有点击事件连接
                self.connect_btn.clicked.connect(self.disconnect_from_server)  # 连接新的点击事件处理函数
                self.connect_btn.setEnabled(True)  # 在这里启用“断开连接”按钮

            else:
                self.handle_socket_error(self.socket.error())
            
            
        except ValueError as e:
            self.update_messages(f"输入错误: {str(e)}\n\n")

    @pyqtSlot(QAbstractSocket.SocketError)
    def handle_socket_error(self, error):
        self.update_messages(f"Socket错误: {self.socket.errorString()}\n\n")
        self.socket.close()
        self.socket = None

    def receive_message(self):
        try:
            message = self.socket.readAll().data().decode('utf-8')
            self.update_messages(message)
        except UnicodeDecodeError:
            self.update_messages("接收消息时出现编码错误\n\n")

    def send_message(self):
        try:
            message = self.input_edit.toPlainText()
            if not message:
                return
            formatted_message = f"{self.username}：{message}\n\n"
            self.socket.write(formatted_message.encode('utf-8'))

            self.update_messages(formatted_message)
            self.input_edit.clear()
            self.input_edit.setFocus()  # 将焦点重新设置到编辑框
            self.check_input()  # 检查输入框状态
        except Exception as e:
            print(f"发送消息时发生错误: {str(e)}")

    def handle_disconnected(self):
        self.update_messages("已与服务器断开连接\n\n")
        self.username_edit.setEnabled(False)
        self.confirm_username_btn.setEnabled(True)
        self.connect_btn.setText("连接")  # 更改按钮文本为“连接”
        self.connect_btn.clicked.disconnect()  # 断开当前点击事件处理函数
        self.connect_btn.clicked.connect(self.connect_to_server)  # 连接原有的点击事件处理函数
        self.socket = None
        
        msg_box = QMessageBox(QMessageBox.Warning, "双重提示", "您已断开连接！")
        msg_box.exec_()

    def update_messages(self, message):
        cursor = self.messages_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(message)

        # 设置文本颜色
        username_start = message.find(":") + 1
        username_end = message.find("：")
        if username_start > 0 and username_end > username_start:
            cursor.setPosition(cursor.position() - len(message) + username_start, QTextCursor.MoveAnchor)
            cursor.setPosition(cursor.position() + username_end - username_start, QTextCursor.KeepAnchor)
            color = QColor("blue")
            format_ = cursor.charFormat()
            format_.setForeground(color)
            cursor.setCharFormat(format_)

        # 滚动到底部
        self.messages_display.verticalScrollBar().setValue(self.messages_display.verticalScrollBar().maximum())

    def confirm_username(self):
        username = self.username_edit.text() + "[Users]"
        if username:
            self.username = username  # 在这里设置username属性
            self.username_edit.setReadOnly(True)
            self.confirm_username_btn.setEnabled(False)
            self.check_input()  # 调用check_input时，username已经初始化
            self.input_edit.setReadOnly(False)

    def check_input(self):
        if self.input_edit.toPlainText() and self.username:  # 现在这个条件判断就不会出错了
            self.send_btn.setEnabled(True)
        else:
            self.send_btn.setEnabled(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("聊天客户端")
        self.resize(600, 400)
        self.setWindowIcon(QIcon('ico02.ico'))

        self.chat_client = ChatClient()
        self.setCentralWidget(self.chat_client)
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
        # 更新消息到聊天客户端的显示区域而不是chat_room
        self.chat_client.update_messages(f"聊天记录已保存到当前目录：{filename}\n")

    def show_about_dialog(self):
        message = f"软件名称：聊天室客户端\n软件作者：XiaoZhao\nGithub开源地址：http://github.com/xiaozhao45"
        QMessageBox.about(self, "关于本软件", message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
