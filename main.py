import sys
import sqlite3
import csv
import datetime as dt
from PIL import Image

from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtSql import QSqlTableModel, QSqlDatabase
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QLabel, QDialog, QTableView, \
    QLineEdit, QPushButton, QMessageBox

from sell import Sell
from add_on_warehouse import DialogWarehouseDisign
from add_product import ProductDialog
from worker import NewWorkerDialog
from Equi import EquiDialog

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
        e = None
        for el in wor:
            for pos in self.positions:
                if pos.id == el[3]:
                    p = pos
                    break
            for eqi in self.equipments:
                if eqi.id == el[-1]:
                    e = eqi.id
                    break
            self.workers.append(Worker(el[0], el[1], el[2], p.id, el[5], el[6], e))

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
    def __init__(self, id_worker, name, sec_name, posit, login, password, equipment_id):
        self.id = id_worker
        self.name = name  # Имя
        self.sec_name = sec_name  # Фамилия
        self.position_id = posit  # id Должности
        # Смотрим по должности, какой уровень доступа к системе он может иметь
        self.fines = []  # Штрафы(обнуляются каждый месяц)
        self.login = login
        self.password = str(password)
        self.equipment = equipment_id  # Необходимое оборудование для этого работника


# Класс профессии
class Position:
    def __init__(self, id_pos, name, access, salary):
        self.id = id_pos
        self.name = name  # название профессии
        self.access = access  # уровень доступа
        self.salary = salary  # Зарплата при данной прифессии
        # При первом уровне работник может продавать товар,
        # заполнять график уборок, проверять количество товара на складе и прочее


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
        if product not in self.products:  #
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


class NewWorker(NewWorkerDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.id = '-'

        self.fname = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Картинка (*.jpg);;')[0]
        self.pic = QPixmap(self.fname)
        self.image = QLabel(self)
        self.image.resize(300, 300)
        self.image.move(40, 50)
        self.image.setPixmap(self.pic)

    def quit(self):
        self.close()

    def add_new_worker(self):
        name = self.lineEdit.text()
        sec = self.lineEdit_2.text()
        pos = self.lineEdit_3.text()
        login = self.lineEdit_4.text()
        pas = self.lineEdit_5.text()
        eqi = self.lineEdit_6.text()
        pos_id = None
        for p in system.positions:
            if p.name == pos:
                pos_id = p.id
                break
        else:
            self.massege.setText('Такой должности у нас нет')
        for e in system.equipments:
            if e.thing == eqi:
                if not e.state:
                    self.id = cur.execute('SELECT max(id) FROM Worker').fetchall()
                    self.id = self.id[0][0] + 1
                    cur.execute(f'''INSERT INTO Worker VALUES ({self.id}, "{name}",
                                    '{sec}', '{pos_id}', 0, '{login}', '{pas}', {e.id});''')
                    cur.execute(f"""UPDATE Equipment
                                    SET state = True
                                    WHERE id = {e.id}""")
                    system.workers.append(Worker(self.id, name, sec, pos_id, login, pas, e.id))
                    self.massege.setText(f"Сотрудник {name} {sec} принят и готов к работе")
                    im = Image.open(self.fname)
                    im.save(f'Photos/{self.id}.jpg')
                    break
        else:
            self.massege.setText("Нет нужного оборудования для сотрудника")

    def load_photo(self):
        self.fname = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Картинка (*.jpg);;')[0]
        self.pic = QPixmap(self.fname)
        self.image.setPixmap(self.pic)
        im = Image.open(self.fname)
        im.save(f'Photos/{self.id}.jpg')


class SellProductDialog(Sell):
    def sell(self):
        q = int(self.spinBox.value())
        prod = None
        for el in system.warehouse.products.keys():
            if el.name == self.lineEdit.text():
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

    def quit(self):
        self.close()


class DialogWarehouse(DialogWarehouseDisign):
    def add(self):
        q = int(self.spinBox.value())
        for el in system.warehouse.products.keys():
            if el.name == self.lineEdit.text():
                prod = el
                system.warehouse.products[prod] += q
                self.label_2.setText(f'{prod.name} добавлены на склад в объеме {q} штук')
                cur.execute(f"""UPDATE Warehouse 
                                SET Count = {system.warehouse.products[prod]}
                                WHERE product = {prod.id}""")
                break
        else:
            self.label_2.setText('Такого товара раньше не было, обратитесь к товароведу '
                                 'или другому работнику с 2 уровнем доступа')

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


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        uic.loadUi('store.ui', self)
        self.setWindowTitle('Система для магазина')
        self.system_store.hide()
        self.log_in.clicked.connect(self.sign_in)
        self.log_out_button.clicked.connect(self.log_out)
        self.clean.clicked.connect(self.add_clean)
        self.plumber.clicked.connect(self.check_plumber)
        self.electricity.clicked.connect(self.electricity_check)
        self.sell.clicked.connect(self.sell_prod)
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
        self.new_prod.clicked.connect(self.new_product)
        self.inventory.clicked.connect(self.check_inventory)
        self.check_warehouse.clicked.connect(self.check_warehouse_report)
        self.worker.clicked.connect(self.add_new_worker)
        self.buy_equi.clicked.connect(self.buy_new_equi)
        self.list_workers.clicked.connect(self.return_worker_list)
        self.delete_worker.clicked.connect(self.delete_pers)
        # Зададим тип базы данных
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        # Укажем имя базы данных
        self.db.setDatabaseName('store_system.sqlite')
        # И откроем подключение
        self.db.open()

    def sign_in(self):
        try:
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
        except Equipment:
            self.label_3.setText('Неверные входные данные')

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
        a = SellProductDialog(self)
        a.exec_()
        self.new_report('работал у кассы')

    def add_on_warehouse_dialog(self):
        a = DialogWarehouse(self)
        a.exec_()
        self.new_report('разгружал товары на складе')

    def new_product(self):
        a = AddProduct(self)
        a.exec_()
        self.new_report('Закупил новые продукты. Теперь их можно закупать')

    def new_report(self, text):
        date = self.calendarWidget.selectedDate().toString("yyyy-MM-dd")
        time = dt.datetime.now().time().strftime("%H:%M")
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
        a = NewWorker(self)
        a.exec_()
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

    def closeEvent(self, event):
        con.commit()


if __name__ == '__main__':
    system = System()
    app = QApplication(sys.argv)
    ex = Window()
    ex.show()
    sys.exit(app.exec())
