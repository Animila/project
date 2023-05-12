# импорт библиотек для работы sql и pyqt
import sqlite3

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QDialog
from PyQt5 import uic

import sys
import os

# для конвертации файла в exe
app = QApplication([])


class RegisterModal(QMainWindow):
    """Окно регистрации"""

    def __init__(self):
        super().__init__()
        # загрузка дизайна
        path = resource_path(os.path.join('design', 'registerWindows.ui'))
        uic.loadUi(path, self)
        # оставить только "закрыть"
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        # подключанм кнопки
        self.goLogin.mousePressEvent = self.go_login
        self.registerBtn.clicked.connect(self.register)
        # подключаем БД
        self.connect = connect_db()

    def go_login(self, event):
        """Переход на окно авторизации"""
        self.hide()
        self.login = AuthModal()
        self.login.show()

    def register(self):
        """Логика регистрации"""
        login = self.registerUser.text()
        password = self.passwordUser.text()

        if not self.passwordUser.text():
            # если поле пароля пустое
            message("ошибка регистрации", "Введите пароль")
            return

        if self.check_old_account(login):
            # если login существует в БД - выводим сообщение, очищаем поле и выходим из функции
            message('Ошибка регистрации', 'Такой логин уже существует')
            self.registerUser.setText('')
            return

        # Если все в порядке - создаем пользователя
        self.create_account(login, password)

        # переходим в окно авторизации (none потому что костыль)
        self.go_login(event=None)

    def check_old_account(self, login):
        """Проверка существования такого же логина"""
        cmd = f"SELECT * FROM users WHERE nickname='{login}'"
        return get_answer_db(self.connect, cmd) != []

    def create_account(self, login, password):
        """Создаем профиль"""
        try:
            cmd = f"INSERT INTO users (nickname, password) VALUES ('{login}','{password}')"
            get_answer_db(self.connect, cmd)
            # сохраняем все действия в БД
            self.connect.commit()
        except sqlite3.Error as error:
            message("Ошибка регистрации", f"Ошибка: {error}")


class AuthModal(QMainWindow):
    """Окно авторизации"""

    def __init__(self):
        """Конструктор"""
        super().__init__()
        # установка дизайна
        path = resource_path(os.path.join('design', 'authWindows.ui'))
        uic.loadUi(path, self)
        # оставляем в окне только кнопку закрыть
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        # подключаем логику авторизации к кнопке
        self.loginBtn.clicked.connect(self.login)
        self.goRegister.mousePressEvent = self.go_register
        # соединяемся к БД
        self.connect = connect_db()

    def login(self):
        """Логика авторизации"""
        login = self.loginUser.text()
        password = self.passwordUser.text()

        if self.check_empty_account(login):
            # если login не существует в БД - выводим сообщение, очищаем поле и выходим из функции
            message('Ошибка авторизации', 'Такого аккаунта не существует')
            self.loginUser.setText('')
            return

        # если все ок, получаем профиль с помощью логина и пароля
        account = self.get_account(login, password)

        if not account:
            # если пароль неверный - повторяем прошлый шаг
            message('Ошибка авторизации', 'Неверный пароль')
            self.passwordUser.setText('')
            return

        # получаем id пользователя, передаем в другое окно и запускаем его
        self.start_app(account[0][0])

    def go_register(self, event):
        self.hide()
        self.reg = RegisterModal()
        self.reg.show()

    def register(self):
        """Логика регистрации"""
        login = self.loginUser.text()
        password = self.passwordUser.text()

        if self.check_empty_account(login):
            # если login не существует в БД - выводим сообщение, очищаем поле и выходим из функции
            message('Ошибка авторизации', 'Такого аккаунта не существует')
            self.loginUser.setText('')
            return

        # если все ок, получаем профиль с помощью логина и пароля
        account = self.get_account(login, password)

        if not account:
            # если пароль неверный - повторяем прошлый шаг
            message('Ошибка авторизации', 'Неверный пароль')
            self.passwordUser.setText('')
            return

        # получаем id пользователя, передаем в другое окно и запускаем его
        self.start_app(account[0][0])

    def check_empty_account(self, login):
        """Проверка пустого аккаунта"""
        cmd = f"SELECT * FROM users WHERE nickname='{login}'"
        return get_answer_db(self.connect, cmd) == []

    def get_account(self, login, password):
        """Получаем профиль"""
        cmd = f"SELECT * FROM users WHERE nickname='{login}' AND password='{password}'"
        return get_answer_db(self.connect, cmd)

    def start_app(self, user_id):
        """Запуск главного экрана"""
        # скрываем текущий экран
        self.hide()
        # создаем объект нового окна
        self.main = MainComputer(user_id)
        # показываем новый экран
        self.main.show()


class MainComputer(QMainWindow):
    """Главное окно"""

    def __init__(self, user_id):
        super().__init__()
        # установка дизайна
        path = resource_path(os.path.join('design', 'mainWindows.ui'))
        uic.loadUi(path, self)
        # оставляем в окне только кнопку закрыть
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        # подключаемся к БД
        self.connect = connect_db()
        # получаем id текущего пользователя
        self.user_id = user_id
        # загружаем и выводим все данные
        self.set_data()
        # привязываем все действий к кнопкам и действиям
        self.set_action()

    # Получение данных

    def get_price(self):
        """Расчёт итоговой суммы"""
        sumComp = 0
        # проходимся по списку новых компонентов,
        # и смотрим на "(0,1,2)" 2 элемент,
        # где указана цена
        for component in self.new_comp:
            sumComp += component[2]
        return sumComp

    def get_types_components(self):
        """Получить компоненты"""
        cmd = f"SELECT title FROM type_component"
        return get_answer_db(self.connect, cmd)

    def get_history(self, user_id):
        """Получить имена компьютеров из истории по пользователю"""
        cmd = f"SELECT name FROM history WHERE user_id={user_id}"
        return get_answer_db(self.connect, cmd)

    def get_components(self, type_id=None):
        """Получаем компоненты"""
        if type_id is None:
            # Если не указан тип, то загружается все данные
            cmd = "SELECT * FROM components"
        else:
            # иначе загружаем по типу
            cmd = f"SELECT * FROM components WHERE type={type_id}"
        return get_answer_db(self.connect, cmd)

    def get_last_number_computer(self):
        """Получаем номер последнего компьютера"""
        # при запросе сортируем результат по возрастанию number_pc
        cmd = "SELECT number_pc FROM computer ORDER BY number_pc"
        result = get_answer_db(self.connect, cmd)
        # если сейчас в истории нет ничего, то компьютер будет 0 (+1),
        # иначе - значение последнего элемента (самое большое значение)
        return 0 if not result else int(result[-1][0])

    # Вывод данных

    def set_action(self):
        """Все обработчики действий"""
        # при выборе чего-то в поле "типов компонентов"
        self.component_type.currentIndexChanged.connect(self.selected_type)
        # при нажатии на кнопку "добавить компонент"
        self.component_addBtn.clicked.connect(self.add_component)
        # при нажатии на кнопку "сохранить компьютер"
        self.pc_saveBtn.clicked.connect(self.add_history)
        # при нажатии на кнопку удалить компонент
        self.component_deleteBtn.clicked.connect(self.delete_component)
        # при нажатии на кнопку удалить историю
        self.history_deleteBtn.clicked.connect(self.delete_history)
        # при нажатии на кнопку загрузить историю
        self.history_loadBtn.clicked.connect(self.load_history)
        # кнопка выхода
        self.exitBtn.triggered.connect(self.exit_account)

    def set_data(self):
        """Загружаем и выводим все данные"""
        # выводим типы компонентов
        self.set_types_components()
        # сохраняем все компоненты
        self.components = self.get_components()
        # выводим все компоненты
        self.set_components()
        # выводим историю
        self.set_history()
        # создаем объект нового компьютера
        self.new_comp = []
        # объект списка для вывода нового компьютера
        self.view_components = []
        # для проверки на "изменение истории"
        self.old_comp = []
        # получаем данные пользователя
        self.get_user()

    def set_price(self):
        """Вывод итоговой суммы"""
        self.pc_sum.setText(f"Сумма: {self.get_price()} руб.")

    def set_history(self):
        """Выводим историю"""
        # очищаем список истории
        self.history_list.clear()
        # получаем историю и проходимся по ней, добавляя имена в список истории
        for comp in self.get_history(self.user_id):
            self.history_list.addItem(comp[0])

    def set_components(self, type_id=None):
        """Выводим компоненты"""
        for component in self.get_components(type_id):
            self.component_list.addItem(f"{component[2]} руб : {component[1]}")

    def set_types_components(self):
        """Установка типов компонентов"""
        # Получаем данные
        for type in self.get_types_components():
            # выводим данные в comboBox
            self.component_type.addItem(type[0])

    def get_user(self):
        cmd = f"SELECT * FROM users WHERE id={self.user_id}"
        user = get_answer_db(self.connect, cmd)
        self.user.setText(f"Пользователь: {user[0][1]}")

    # Обработчики

    def selected_type(self, type_id):
        """Обработка выбора типа"""
        # очищаем лист компонентов
        self.component_list.clear()
        # выводим список компонентов по ID
        self.set_components(type_id + 1)

    def set_new_component(self, components):
        """Выводим компоненты нового компьютера"""
        self.pc_components.clear()
        self.pc_components.addItems(components)
        self.set_price()

    def set_component_comp(self, item):
        """Логика добавления в новый компьютер"""
        # выбранный компонент
        current = None

        # проходимся по списку всех компонентов
        for component in self.components:
            # если имя текущего компонента является именем выбранного компонента,
            # то выбранный компонент - это текущий компонент
            if component[1].strip() == item.strip():
                current = component

        if not self.new_comp:
            # если это первый компонент в массиве нового компьютера,
            # то добавляем его в массив
            self.new_comp.append(current)
            self.view_components.append(f"{current[2]} : {current[1]}")
            # выводим его в список выбранных компонентов
            self.set_new_component(self.view_components)
            # выходим из функции
            return

        # если же это не первый компонент
        # создаем переменную проверки, что мы не добавляли ранее ТАКОЙ ЖЕ компонент
        no_is_comp = True
        # проходимся по всем компонентам НОВОГО компьютера
        for component in self.new_comp:
            # если оказалось, что мы УЖЕ ДОБАВИЛИ выбранный элемент
            # делаем false в переменной
            if component[1].strip() == current[1].strip():
                no_is_comp = False

        if no_is_comp:
            # если компонент новый,
            # то мы его добавляем, выводим на экран
            self.new_comp.append(current)
            self.view_components.append(f"{current[2]} : {current[1]}")
            self.set_new_component(self.view_components)
            # выводим его в список выбранных компонентов

    def add_component(self):
        """Добавляем новый компонент в компьютер"""
        # если ничего не выбрано - выйти из функции
        if not self.component_list.currentItem():
            return
        self.set_component_comp(self.component_list.currentItem().text().split(':')[1].strip())

    def add_history(self):
        """Сохраняем компьютер в истории"""
        # получаем последний номер компьютера в истории и делаем из него новый номер
        computer_number = self.get_last_number_computer() + 1

        # получаем имя и делаем проверку на существование имени
        name = self.pc_name.text()
        if not name:
            message("Ошибка", "Введите имя сборки")
            return

        # если мы редактируем ЗАГРУЖЕННЫЕ компьютеры
        if self.old_comp:
            try:
                # получаем id компьютера по имени
                cmd = f"SELECT pc_id FROM history WHERE name='{name}'"
                computer_id = get_answer_db(self.connect, cmd)[0][0]
                # удаляем все компоненты с id компьютера
                cmd = f"DELETE FROM computer WHERE number_pc={computer_id}"
                get_answer_db(self.connect, cmd)
                # создаем новые
                for component in self.new_comp:
                    cmd = f"INSERT INTO computer (number_pc, part_id) VALUES ({computer_id}, {component[0]})"
                    get_answer_db(self.connect, cmd)
                # сохраняем
                self.connect.commit()
            except sqlite3.Error as error:
                message("Ошибка", f"Ошибка: {error}")

            message("Успешно", "Загрузка завершена")
            # очистка экранов
            self.pc_components.clear()
            self.pc_name.setText('')
            # снова выводим историю
            self.set_history()
            return

        # делаем try для безопасности создания
        try:
            # проходимся по новым компьютерам и создаем новый компьютер
            for component in self.new_comp:
                cmd = f"INSERT INTO computer (number_pc, part_id) VALUES ({computer_number}, {component[0]})"
                get_answer_db(self.connect, cmd)

            # после этого мы создаем новую историю с именем компьютера
            cmd = f"INSERT INTO history (user_id, pc_id, name) VALUES ({self.user_id}, {computer_number}, '{name}')"
            get_answer_db(self.connect, cmd)
            # завершаем все операции и переносим все в БД
            self.connect.commit()

        except sqlite3.Error as error:
            # проверка на ошибки
            message("Ошибка сохранения", f"Ошибка: {error}")
            return

        message("Успешно", "Загрузка завершена")

        # очистка экранов
        self.pc_components.clear()
        self.pc_name.setText('')
        # снова выводим историю
        self.set_history()

    def delete_component(self):
        """Удаляем компонент из списка нового компьютера"""
        # если ничего не выбрано: выходим
        if not self.pc_components.currentItem():
            return

        # проходимся по списку
        # сравниваем каждый элемент с выбранным элементов по имени
        # Если это он, то удаляем из всех массивов найденный элемент
        # выводим получившийся массив
        for i in range(0, len(self.new_comp)):
            if self.new_comp[i-1][1].strip() == self.pc_components.currentItem().text().split(':')[1].strip():
                del self.new_comp[i-1]
                del self.view_components[i-1]
        self.set_new_component(self.view_components)

    def delete_history(self):
        """Удаляет компьютер из истории"""
        if not self.history_list.currentItem():
            return
        # получаем id выбранного компьютера по имени
        cmd = f"SELECT pc_id FROM history WHERE name='{self.history_list.currentItem().text()}'"
        result = get_answer_db(self.connect, cmd)[0][0]
        try:
            # пытаемся удалить сначала из таблицы компьютера, а потом из истории
            cmd = f"DELETE FROM computer WHERE number_pc={result}"
            get_answer_db(self.connect, cmd)
            cmd = f"DELETE FROM history WHERE pc_id={result}"
            get_answer_db(self.connect, cmd)
            self.connect.commit()
        except sqlite3.Error as error:
            message("Ошибка", f"Ошибка SQL: {error}")
        self.pc_components.clear()
        self.pc_name.setText('')
        self.set_history()

    def load_history(self):
        """Загружаем компоненты из истории"""
        if not self.history_list.currentItem():
            return
        # очищаем все массивы
        self.old_comp.clear()
        self.new_comp.clear()
        self.pc_components.clear()
        self.view_components.clear()
        # получаем id компонента компьютера (не самого компонента) и название
        cmd = f"SELECT computer.id, title " \
              f"FROM history " \
              f"INNER JOIN computer ON pc_id=number_pc " \
              f"INNER JOIN components ON part_id=components.id " \
              f"WHERE name='{self.history_list.currentItem().text()}'"
        # выводим данные
        for component in get_answer_db(self.connect, cmd):
            self.set_component_comp(component[1])
            self.old_comp.append(component[0])
        # ставим в поле имени компьютера текущее имя
        self.pc_name.setText(self.history_list.currentItem().text())

    def exit_account(self):
        """Обработка выхода из аккаунта"""
        # удаляем данные по id пользователя
        self.user_id = None
        # выполняяем переход
        self.hide()
        self.login = AuthModal()
        self.login.show()


def connect_db():
    # Подключаемся к БД
    try:
        # путь к файлу DB
        path = resource_path(os.path.join('files', 'app.db'))
        # возвращаем подключение
        return sqlite3.connect(path)
    except sqlite3.Error as error:
        message('Ошибка', f'Ошибка подключения к SQL\nОшибка: {error}')


def get_answer_db(connect, cmd):
    """Процесс получения данных"""
    # создание объекта запроса
    request = connect.cursor()
    # Выполнение запроса
    request.execute(cmd)
    # Получение результата запроса
    result = request.fetchall()
    # Вернуть результат
    return result


def resource_path(relative):
    """Для работы pyinstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)


def message(title, text):
    """Окно с сообщением (заголовок и сообщение)"""
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(QMessageBox.Warning)
    msg.exec_()


if __name__ == "__main__":
    # инициализация стартового экрана
    startApp = AuthModal()
    # открываем окно
    startApp.show()
    # для выхода из приложения
    sys.exit(app.exec_())
