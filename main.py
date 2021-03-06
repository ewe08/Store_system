import sys
import sqlite3
import csv
import datetime as dt
from PIL import Image

from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtSql import QSqlTableModel, QSqlDatabase
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

from Dialogs.add_product import ProductDialog
from Dialogs.Equi import EquiDialog
from Dialogs.add_position import NewPosition

name_db = 'store_system.sqlite'

# Подключение к БД
con = sqlite3.connect(name_db)

# Создание курсора
cur = con.cursor()


# Задаем класс всей системы магазина
class System:
    def __init__(self):
        self.warehouse = Warehouse()  # Создаем склад
        self.equipments = []  # Оборудование магазина
        eq = cur.execute('''select * from Equipment''').fetchall()
        for el in eq:
            obj = Equipment(el[0], el[1], el[2])
            self.equipments.append(obj)
        self.positions = []  # Список должностей и уровней доступа к системе
        pos = cur.execute('''select * from Position''').fetchall()
        for el in pos:
            self.positions.append(Position(el[0], el[1], el[2], el[3]))
        self.workers = []  # Персонал магазина
        wor = cur.execute("""select * from Worker""").fetchall()
        p = None
        for el in wor:
            for pos in self.positions:
                if pos.id == el[3]:
                    p = pos
                    break
            self.workers.append(Worker(el[0], el[1], el[2], p.id, el[5], el[6]))

        self.access = None  # Уровень доступа текущего пользователя
        self.name = None  # Имя текущего пользователя
        self.sec_name = None  # фамилия
        self.id = None  # и ID пользователя

    def sign_in(self, login, password):
        for worker in self.workers:
            if worker.login == login and worker.password == password:
                self.id = worker.id
                for pos in self.positions:
                    if pos.id == worker.position_id:
                        self.access = pos.access  # Система получает уровень доступа сотрудника
                self.name = worker.name  # Его имя
                self.sec_name = worker.sec_name  # и фамилию
                return True
        return False

    def log_out(self):
        self.access = None
        self.name = None
        self.sec_name = None
        self.id = None


# класс сотрудника
class Worker:
    def __init__(self, id_worker, name, sec_name, posit, login, password):
        self.id = id_worker
        self.name = name  # Имя
        self.sec_name = sec_name  # Фамилия
        self.position_id = posit  # id Должности
        # Смотрим по должности, какой уровень доступа к системе он может иметь
        self.fines = []  # Штрафы(обнуляются каждый месяц)
        self.login = login
        self.password = str(password)


# Класс профессии
class Position:
    def __init__(self, id_pos, name, access, salary):
        self.id = id_pos
        self.name = name  # название профессии
        self.access = access  # уровень доступа
        self.salary = salary  # Зарплата при данной прифессии
        # При первом уровне работник может продавать товар,
        # заполнять график уборок, проверять количество товара на складе и прочее

    def __str__(self):
        return self.name


# Класс товара
class Product:
    def __init__(self, id_product, name, selling_price, purchase_price):
        self.id = id_product
        self.selling_price = float(selling_price)  # Цена продажи товара магазином
        self.purchase_price = float(purchase_price)  # Цена покупки товара магазином
        self.name = name  # Название товара
        self.delta = selling_price - purchase_price  # Прибыль от продажи

    def __str__(self):
        return self.name


# класс оборудования
class Equipment:
    def __init__(self, id_equipment, thing, price):
        self.id = id_equipment
        self.thing = thing  # Название оборудования
        self.price = price  # сколько оно стоило
        self.state = False  # Используется ли данное оборудование кем-то

    def __str__(self):
        return self.thing


# класс склада
class Warehouse:
    def __init__(self):
        self.products = {}  # Создание словаря в виде "Товар: его количество на складе"
        res = cur.execute('''select * from Warehouse''').fetchall()
        for el in res:
            a = cur.execute(f'''select * from Product
                                                where id = "{el[1]}"''').fetchall()
            self.products[Product(a[0][0], a[0][1], a[0][2], a[0][3])] = el[2]

    def add_product(self, product, quantity):  # добавдение товара и его количество
        if product in self.products:
            self.products[product] += int(quantity)
        else:
            self.products[product] = int(quantity)

    def check_product(self, product):  # Проверка на наличие товара
        if product not in self.products:  # возвращает истину если товар есть в базе данных
            return False
        return True

    def check_num(self, product, quantity):
        if self.products[product] - quantity < 0:  # Проверка, что нужное количество товара есть
            return False
        return True

    def del_product(self, product, quantity):
        if self.products[product] - quantity < 0:  # удаляет количество товара полностью
            self.products[product] = 0
        else:
            self.products[product] -= int(quantity)  # или часть


class NewWorker(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('Forms/worker.ui', self)
        self.id = '-'  # ID поумолчанию
        self.pic = QPixmap('Photos/netfoto.jpg')
        self.image = QLabel(self)
        self.image.move(40, 50)
        self.image.setPixmap(self.pic)  # загрузка фотографии
        self.load_comboBoxes()
        self.add.clicked.connect(self.add_new_worker)
        self.exit.clicked.connect(self.quit)
        self.photo.clicked.connect(self.load_photo)

    def quit(self):
        self.close()  # Закрытие окна

    def add_new_worker(self):
        name = self.lineEdit.text()
        sec = self.lineEdit_2.text()
        pos = self.comboBox.currentText()
        login = self.lineEdit_4.text()
        pas = self.lineEdit_5.text()
        pos_id = None
        for p in system.positions:  # Нахождение ID должности
            if p.name == pos:
                pos_id = p.id
                break

        self.id = cur.execute('SELECT max(id) FROM Worker').fetchall()
        self.id = self.id[0][0] + 1  # изменение ID текущего пользователя
        cur.execute(f'''INSERT INTO Worker VALUES ({self.id}, "{name}",
                        '{sec}', '{pos_id}', 0, '{login}', '{pas}')''')

        system.workers.append(Worker(self.id, name, sec, pos_id, login, pas))
        self.massege.setText(f"Сотрудник {name} {sec} принят и готов к работе")
        im = Image.open(self.fname)
        im.save(f'Photos/{self.id}.jpg')

    def load_photo(self):
        self.fname = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Картинка (*.jpg);;')[0]
        self.pic = QPixmap(self.fname).scaled(200, 200)
        self.image.setPixmap(self.pic)
        im = Image.open(self.fname)
        im.save(f'Photos/{self.id}.jpg')

    def load_comboBoxes(self):
        for pos in system.positions:
            self.comboBox.addItem(str(pos))


class SellProductDialog(QDialog):
    def __init__(self):
        super(SellProductDialog, self).__init__()
        uic.loadUi('Forms/sell.ui', self)
        self.setWindowTitle('Продажа товара')
        self.pushButton.clicked.connect(self.sell)
        self.pushButton_2.clicked.connect(self.close)
        self.load_combo()

    def sell(self):
        q = int(self.spinBox.value())
        if q == 0:
            self.massage.setText("Вы не указали количество товара")
        else:
            prod = None
            for el in system.warehouse.products.keys():
                if el.name == self.comboBox.currentText():
                    prod = el
            if system.warehouse.check_product(prod) or self.radioButton.isChecked():
                if system.warehouse.check_num(prod, q):
                    system.warehouse.del_product(prod, int(self.spinBox.value()))
                    self.massage.setText(f'Товар {prod.name} продан в количестве '
                                         f'{int(self.spinBox.value())} штук по цене '
                                         f'{prod.selling_price * q} рублей')
                    cur.execute(f'''UPDATE Warehouse
                                    SET Count = {system.warehouse.products[prod]}
                                    WHERE product = {prod.id}''')

                else:
                    self.massage.setText('Столько товара нет')
            else:
                self.massage.setText("Такого товара у нас нет")

    def load_combo(self):
        for el in system.warehouse.products.keys():
            self.comboBox.addItem(str(el))

    def quit(self):
        self.close()


class DialogWarehouse(QDialog):
    def __init__(self):
        super(DialogWarehouse, self).__init__()
        uic.loadUi('Forms/add_on_warehouse.ui', self)
        self.setWindowTitle('Разгрузка товара на склад')
        self.pushButton.clicked.connect(self.add)
        self.pushButton_2.clicked.connect(self.quit)
        self.load_combo()

    def add(self):
        q = int(self.spinBox.value())
        for el in system.warehouse.products.keys():
            if el.name == self.comboBox.currentText():
                prod = el
                system.warehouse.products[prod] += q
                self.label_2.setText(f'{prod.name} добавлены на склад в объеме {q} штук')
                cur.execute(f"""UPDATE Warehouse 
                                SET Count = {system.warehouse.products[prod]}
                                WHERE product = {prod.id}""")
                break

    def load_combo(self):
        for el in system.warehouse.products.keys():
            self.comboBox.addItem(str(el))

    def quit(self):
        self.close()


class AddProduct(ProductDialog):
    def quit(self):
        self.close()

    def add_product(self):
        name = self.lineEdit.text()
        buy = self.spinBox.value()
        sell = self.spinBox_2.value()
        if name != '' and buy > 0 and sell > 0:
            max_id = cur.execute('SELECT max(id) FROM Product').fetchall()
            obj = Product(max_id[0][0] + 1, name, sell, buy)
            system.warehouse.products[obj] = 0
            cur.execute(f'''INSERT INTO Product VALUES ({obj.id}, "{obj.name}",
                                                    {obj.selling_price}, {obj.purchase_price});''')
            max_id_ware = cur.execute('SELECT max(id) FROM Warehouse').fetchall()
            cur.execute(f"""INSERT INTO Warehouse VALUES({max_id_ware[0][0] + 1}, {obj.id}, 0)""")
            con.commit()
        else:
            self.label.setText('Ошибка')


class AddEquipment(EquiDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

    def quit(self):
        self.close()

    def add_equi(self):
        thing = self.thing.text()
        price = int(self.price.text())
        id_e = cur.execute('SELECT max(id) FROM Equipment').fetchall()
        id_e = id_e[0][0] + 1
        eq = Equipment(id, thing, price)
        system.equipments.append(eq)
        cur.execute(f"""INSERT INTO Equipment VALUES({id_e}, '{thing}', {price}, "False")""")


class AddNewPosition(NewPosition):
    def quit(self):
        self.close()

    def add_new_position(self):
        name = self.lineEdit.text()
        salary = self.lineEdit_2.text()
        if name != '' and salary != '':
            id_p = cur.execute('SELECT max(id) FROM Equipment').fetchall()
            id_p = id_p[0][0] + 1
            access = self.spinBox.value()
            pos = Position(id_p, name, access, salary)
            system.positions.append(pos)
            cur.execute(f'''INSERT INTO Position VALUES({id_p}, '{name}', {access}, {salary})''')
            self.message.setText('Должность успешно добавлена')
        else:
            self.message.setText('Произошла ошибка в вводе')


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        uic.loadUi('Forms/store.ui', self)
        self.setWindowTitle('Система для магазина')
        self.input = None
        self.system_store.hide()
        self.log_in.setShortcut(Qt.Key_Return)
        self.log_in.clicked.connect(self.sign_in)
        self.log_out_button.clicked.connect(self.log_out)
        self.clean.clicked.connect(self.add_clean)
        self.plumber.clicked.connect(self.check_plumber)
        self.electricity.clicked.connect(self.electricity_check)
        self.sell.clicked.connect(self.sell_prod)
        self.new_worker = NewWorker()

        self.add_on_warehouse.clicked.connect(self.add_on_warehouse_dialog)
        rep = cur.execute(f"""SELECT * FROM Reports""").fetchall()
        self.rep_id = 0
        pers = None
        for el in rep:
            for per in system.workers:
                if per.id == el[1]:
                    pers = per
            self.reports_2.insertItem(0, f'{el[2]} {el[3]} {pers.name} {pers.sec_name} {el[4]}')
        self.rep_id = rep[-1][0] + 1
        self.reports_2.sortItems()
        self.new_prod.clicked.connect(self.new_product)
        self.inventory.clicked.connect(self.check_inventory)
        self.check_warehouse.clicked.connect(self.check_warehouse_report)
        self.worker.clicked.connect(self.add_new_worker)
        self.buy_equi.clicked.connect(self.buy_new_equi)
        self.list_workers.clicked.connect(self.return_worker_list)
        self.new_position.clicked.connect(self.new_pos)
        self.delete_worker.clicked.connect(self.delete_pers)
        # Зададим тип базы данных
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        # Укажем имя базы данных
        self.db.setDatabaseName('store_system.sqlite')
        # И откроем подключение
        self.db.open()
        self.manual_check.stateChanged.connect(self.set_manual)
        self.manual = True
        self.calendarWidget.hide()
        self.timeEdit.hide()

    def set_manual(self):
        if self.manual:
            self.calendarWidget.show()
            self.timeEdit.show()
            self.manual = False
        else:
            self.manual = True
            self.calendarWidget.hide()
            self.timeEdit.hide()

    def sign_in(self):
        login = self.login.text()
        pas = self.password.text()
        if system.sign_in(login, pas):
            self.new_report('Вошел в систему')
            self.sing_in.hide()
            self.system_store.show()
            self.access3.hide()
            self.access2.hide()
            if system.access >= 3:
                self.access3.show()
            if system.access >= 2:
                self.access2.show()
        else:
            self.label_4.setText('Неверные входные данные')

    def log_out(self):
        self.new_report('Вышел из системы')
        system.log_out()
        self.system_store.hide()
        self.sing_in.show()
        self.login.setText('')
        self.password.setText('')
        self.label_4.setText('Войдите в систему')

    def add_clean(self):
        self.new_report('провел уборку')

    def check_plumber(self):
        self.new_report("провел сантехнические работы")

    def electricity_check(self):
        self.new_report('провел работы с электричеством')

    def sell_prod(self):
        self.sell = SellProductDialog()
        self.sell.show()
        self.new_report('работал у кассы')

    def add_on_warehouse_dialog(self):
        self.add_warehouse = DialogWarehouse()
        self.add_warehouse.show()
        self.new_report('разгружал товары на складе')

    def new_product(self):
        a = AddProduct(self)
        a.exec_()
        self.new_report('Закупил новые продукты. Теперь их можно закупать')

    def new_report(self, text):
        if self.manual:
            date = dt.datetime.now().date()
            time = dt.datetime.now().time().strftime("%H:%M")
        else:
            date = self.calendarWidget.selectedDate().toString("yyyy-MM-dd")
            time = self.timeEdit.time().toString("hh:mm")
        self.reports_2.addItem(
            f'{date} {time} {system.name} {system.sec_name} {text}'
        )
        cur.execute(f'''INSERT INTO Reports VALUES({self.rep_id},{system.id}, "{date}",
                                                  "{time}", "{text}")''')
        self.rep_id += 1
        con.commit()

    def check_inventory(self):
        w = open(
            f'Reports/inventory/{self.calendarWidget.selectedDate().toString("yyyy-MM-dd")}.txt',
            'w', encoding='utf8')
        for el in system.equipments:
            w.write(el.thing + '\n')
        w.close()
        self.new_report('провел инвентаризацию')

    def check_warehouse_report(self):
        header = ['Product', 'count']
        with open(
                f'Reports/Warehouse_reports/'
                f'{self.calendarWidget.selectedDate().toString("yyyy-MM-dd")}.csv', 'w',
                newline='\n') as csvfile:
            writer = csv.writer(
                csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([x for x in header])
            for prod in system.warehouse.products.keys():
                writer.writerow([prod.name, system.warehouse.products[prod]])

        self.new_report('провел переучет склада')

    def add_new_worker(self):
        self.new_worker.show()
        self.new_report('Рассмотрел новый персонал на работу')

    def buy_new_equi(self):
        a = AddEquipment(self)
        a.exec_()
        self.new_report('рассмотрел покупку нового оборудования')

    def return_worker_list(self):
        a = QDialog(self)

        # QTableView - виджет для отображения данных из базы
        view = QTableView(a)
        # Создадим объект QSqlTableModel,
        # зададим таблицу, с которой он будет работать,
        #  и выберем все данные
        model = QSqlTableModel(a, self.db)
        model.setTable('Worker')
        model.select()

        # Для отображения данных на виджете
        # свяжем его и нашу модель данных
        view.setModel(model)
        view.move(10, 10)
        view.resize(617, 315)
        a.exec_()

    def delete(self):
        try:
            id_pers = int(self.input.text())

            name = cur.execute(f"""Select Name From Worker
                                    Where id = {id_pers}""").fetchall()
            valid = QMessageBox.question(
                self, '', f"Действительно уволить {name}",
                QMessageBox.Yes, QMessageBox.No)
            # Если пользователь ответил утвердительно, удаляем элементы.
            # Не забываем зафиксировать изменения
            if valid == QMessageBox.Yes:
                cur.execute(f'''DELETE from Worker
                                where id = {id_pers}''')
            con.commit()
        except Equipment:
            pass

    def delete_pers(self):
        a = QDialog()
        a.label = QLabel(a)
        a.label.setText('Введите ID работника, которого хотите уволить:')
        a.label.move(5, 5)
        self.input = QLineEdit(a)
        self.input.move(5, 30)
        a.btn = QPushButton(a)
        a.btn.move(150, 30)
        a.btn.setText('Уволить')
        a.btn.clicked.connect(self.delete)
        # QTableView - виджет для отображения данных из базы
        view = QTableView(a)
        # Создадим объект QSqlTableModel,
        # зададим таблицу, с которой он будет работать,
        #  и выберем все данные
        model = QSqlTableModel(a, self.db)
        model.setTable('Worker')
        model.select()

        # Для отображения данных на виджете
        # свяжем его и нашу модель данных
        view.setModel(model)
        view.move(5, 70)
        view.resize(617, 315)

        a.exec_()

    def new_pos(self):
        a = AddNewPosition(self)
        a.exec_()
        self.new_report('Рассматривал новые должности')

    def closeEvent(self, event):
        con.commit()


if __name__ == '__main__':
    system = System()
    app = QApplication(sys.argv)
    ex = Window()
    ex.show()
    sys.exit(app.exec())
