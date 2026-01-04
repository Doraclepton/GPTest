from tkinter import *
from tkinter import ttk
import webbrowser
import requests
from bs4 import BeautifulSoup
import re
import subprocess
import os

result_window = None

DANGEROUS_MODULES = {
    'os': 2, 'sys': 2, 'subprocess': 2, 'shutil': 2, 'platform': 2,
    'fileinput': 2, 'tempfile': 2, 'glob': 2, 'fnmatch': 2,
    'socket': 2, 'http': 2, 'urllib': 2, 'ftplib': 2, 'smtplib': 2,
    'poplib': 2, 'imaplib': 2, 'telnetlib': 2,
    'sqlite3': 2, 'pickle': 2, 'shelve': 2, 'marshal': 2,
    'ctypes': 2, 'winreg': 2, 'msvcrt': 2,
    'multiprocessing': 2, 'threading': 2,
    'builtins': 2, '__builtin__': 2, 'eval': 2, 'exec': 2, 'compile': 2
}

SAFE_MODULES = {
    'math': 1, 'random': 1, 'datetime': 1, 'time': 1, 'json': 1,
    'csv': 1, 're': 1, 'collections': 1, 'itertools': 1, 'functools': 1,
    'string': 1, 'array': 1, 'decimal': 1, 'fractions': 1, 'statistics': 1,
    'hashlib': 1, 'hmac': 1, 'secrets': 1, 'base64': 1, 'html': 1,
    'xml': 1, 'unicodedata': 1, 'textwrap': 1, 'difflib': 1
}


def search_module_info(module_name):
    try:
        search_query = f"{module_name} python documentation"

        url = f"https://www.google.com/search?q={search_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            search_results = soup.find_all('a', href=re.compile(r'^https://'))

            for result in search_results:
                href = result.get('href')
                if 'google.com' not in href and 'webcache' not in href:
                    match = re.search(r'q=(https?://[^&]+)', href)
                    if match:
                        return match.group(1)
                    else:
                        if href.startswith('/url?q='):
                            return href[7:].split('&')[0]
                        elif href.startswith('http'):
                            return href.split('&')[0]

        python_doc_url = f"https://docs.python.org/3/library/{module_name}.html"
        if requests.head(python_doc_url, timeout=5).status_code == 200:
            return python_doc_url

        pypi_url = f"https://pypi.org/project/{module_name}/"
        if requests.head(pypi_url, timeout=5).status_code == 200:
            return pypi_url

    except Exception as e:
        print(f"Ошибка при поиске информации о {module_name}: {e}")

    return f"https://www.google.com/search?q={module_name}+python+documentation"


def analyze_module_safety(module_name):
    if module_name in DANGEROUS_MODULES:
        return DANGEROUS_MODULES[module_name], "системный модуль"
    elif module_name in SAFE_MODULES:
        return SAFE_MODULES[module_name], "стандартный модуль"
    else:
        dangerous_keywords = ['sys', 'os', 'exec', 'eval', 'shell', 'file', 'net',
                              'socket', 'process', 'registry', 'win', 'linux']
        if any(keyword in module_name.lower() for keyword in dangerous_keywords):
            return 2, "потенциально системный"
        else:
            return 1, "неизвестный тип"


def open_url(event):
    widget = event.widget
    selection = widget.curselection()
    if selection:
        index = selection[0]
        url_text = widget.get(index)

        if ":" in url_text:
            url = url_text.split(":", 1)[1].strip()
        else:
            url = url_text

        webbrowser.open(url)


def close_result_window():
    global te

    report_window = Toplevel()
    report_window.title("GPTest - Полный отчет")
    report_window.geometry("900x700")
    report_window.resizable(False, False)
    report_window.iconbitmap("Sun.ico")

    class SmartPythonTranslator:
        def __init__(self, root):
            self.root = root
            self.root.title("GPTest - Полный отчет")
            self.root.geometry("900x700")

            self.explanation_cache = {}

            self.reliable_sources = [
                'python.su',
                'pythontutor.ru',
                'pythonworld.ru',
                'metanit.com/python',
                'proproprogs.ru/python',
                'younglinux.info/python',
                'all-python.ru'
            ]

            self.create_interface()

        def create_interface(self):
            title = Label(self.root, text="Python → Полное объяснение кода",
                          font=("Arial", 16, "bold"))
            title.pack(pady=10)

            input_frame = Frame(self.root)
            input_frame.pack(pady=10, padx=20, fill=X)

            Label(input_frame, text="Код Python:", font=("Arial", 11, "bold")).pack(anchor=W)

            self.code_input = Text(input_frame, height=8, font=("Consolas", 10), wrap=WORD)
            self.code_input.pack(fill=X, pady=5)

            self.code_input.insert("1.0", te)

            button_frame = Frame(input_frame)
            button_frame.pack(fill=X)

            self.translate_btn = Button(button_frame, text="🔍 Полное объяснение кода",
                                        command=self.start_translation,
                                        bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                        height=2)
            self.translate_btn.pack(pady=5, fill=X)

            self.loading_label = Label(button_frame, text="", fg="blue", font=("Arial", 10))
            self.loading_label.pack()

            result_frame = Frame(self.root)
            result_frame.pack(pady=10, padx=20, fill=BOTH, expand=True)

            Label(result_frame, text="📚 Полное объяснение кода:",
                  font=("Arial", 12, "bold")).pack(anchor=W)

            result_text_frame = Frame(result_frame)
            result_text_frame.pack(fill=BOTH, expand=True, pady=5)

            self.result_output = Text(result_text_frame, height=15, font=("Arial", 11),
                                      bg="#f8f9fa", wrap=WORD, padx=12, pady=12)
            scrollbar = Scrollbar(result_text_frame, orient=VERTICAL, command=self.result_output.yview)
            self.result_output.configure(yscrollcommand=scrollbar.set)

            self.result_output.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)

            self.status_label = Label(result_frame, text="", fg="gray", font=("Arial", 9))
            self.status_label.pack()

        def start_translation(self):
            code = self.code_input.get("1.0", END).strip()

            if not code:
                self.result_output.delete("1.0", END)
                self.result_output.insert("1.0", "❌ Введите код Python")
                return

            self.translate_btn.config(state=DISABLED, text="⏳ Анализируем код...")
            self.loading_label.config(text="Разбираем каждую команду...")
            self.result_output.delete("1.0", END)
            self.result_output.insert("1.0", "🔍 Анализируем код...\n\nПодробно разбираем каждую команду...")

            import threading
            thread = threading.Thread(target=self.analyze_code, args=(code,))
            thread.daemon = True
            thread.start()

        def analyze_code(self, code):
            try:
                clean_code = self.clean_code(code)

                lines = clean_code.split('\n')
                explanations = []

                for i, line in enumerate(lines, 1):
                    if line.strip():
                        line_explanation = self.analyze_line(line.strip(), i)
                        explanations.append(line_explanation)

                full_explanation = self.format_full_explanation(code, explanations)

                self.show_result(full_explanation)

            except Exception as e:
                self.show_result(f"❌ Ошибка анализа: {str(e)}\n\n💡 Попробуйте другой код")

            finally:
                self.root.after(0, self.reset_interface)

        def clean_code(self, code):
            lines = code.split('\n')
            cleaned_lines = []

            for line in lines:
                cleaned_line = line.strip()
                if cleaned_line:
                    cleaned_lines.append(cleaned_line)

            return '\n'.join(cleaned_lines)

        def analyze_line(self, line, line_number):
            explanation = f"Строка {line_number}: {line}\n"

            if re.match(r'^#', line):
                return explanation + "📝 Это комментарий - текст, который игнорируется Python\n"

            elif re.match(r'^print\(', line):
                return explanation + self.explain_print(line)

            elif re.match(r'^def\s+\w+', line):
                return explanation + self.explain_function_definition(line)

            elif re.match(r'^class\s+\w+', line):
                return explanation + self.explain_class_definition(line)

            elif re.match(r'^if\s+', line):
                return explanation + self.explain_if_statement(line)

            elif re.match(r'^elif\s+', line):
                return explanation + self.explain_elif_statement(line)

            elif re.match(r'^else:', line):
                return explanation + self.explain_else_statement(line)

            elif re.match(r'^for\s+', line):
                return explanation + self.explain_for_loop(line)

            elif re.match(r'^while\s+', line):
                return explanation + self.explain_while_loop(line)

            elif re.match(r'^\w+\s*=', line) and 'input(' in line:
                return explanation + self.explain_input(line)

            elif re.match(r'^\w+\s*=', line):
                return explanation + self.explain_assignment(line)

            elif re.match(r'^\w+\(', line) and not line.startswith('print'):
                return explanation + self.explain_function_call(line)

            elif re.match(r'^return\s+', line):
                return explanation + self.explain_return(line)

            elif re.match(r'^import\s+', line):
                return explanation + self.explain_import(line)

            elif re.match(r'^from\s+', line):
                return explanation + self.explain_from_import(line)

            elif re.match(r'^try:', line):
                return explanation + "🛡️ Начало блока обработки исключений\n"

            elif re.match(r'^except\s+', line):
                return explanation + "🔄 Обработка конкретного исключения\n"

            elif re.match(r'^finally:', line):
                return explanation + "⚡ Блок, который выполнится в любом случае\n"

            else:
                return explanation + self.explain_general_line(line)

        def explain_print(self, line):
            explanation = "🖨️ Функция print() - вывод данных на экран:\n"

            match = re.search(r'print\((.*)\)', line)
            if match:
                content = match.group(1)
                explanation += f"• Выводит: {content}\n"
                explanation += "• Может выводить текст, переменные, результаты вычислений\n"

            explanation += "• Автоматически добавляет перевод строки\n"
            return explanation

        def explain_function_definition(self, line):
            explanation = "🔧 Определение функции:\n"

            match = re.match(r'def\s+(\w+)\((.*)\):', line)
            if match:
                func_name = match.group(1)
                params = match.group(2)
                explanation += f"• Имя функции: {func_name}\n"
                explanation += f"• Параметры: {params if params else 'нет'}\n"
                explanation += "• Функция может быть вызвана позже по имени\n"
                explanation += "• Тело функции должно быть с отступом\n"

            return explanation

        def explain_class_definition(self, line):
            explanation = "🏗️ Определение класса:\n"

            match = re.match(r'class\s+(\w+)', line)
            if match:
                class_name = match.group(1)
                explanation += f"• Имя класса: {class_name}\n"
                explanation += "• Класс - шаблон для создания объектов\n"
                explanation += "• Содержит методы (функции) и атрибуты (данные)\n"

            return explanation

        def explain_if_statement(self, line):
            explanation = "❓ Условный оператор if:\n"

            match = re.match(r'if\s+(.*):', line)
            if match:
                condition = match.group(1)
                explanation += f"• Условие: {condition}\n"
                explanation += "• Блок кода выполнится, если условие истинно (True)\n"
                explanation += "• Тело условия должно быть с отступом\n"

            return explanation

        def explain_elif_statement(self, line):
            explanation = "🔀 Оператор elif (else if):\n"

            match = re.match(r'elif\s+(.*):', line)
            if match:
                condition = match.group(1)
                explanation += f"• Альтернативное условие: {condition}\n"
                explanation += "• Проверяется, если предыдущие условия ложны\n"
                explanation += "• Может быть несколько elif подряд\n"

            return explanation

        def explain_else_statement(self, line):
            explanation = "⚖️ Оператор else:\n"
            explanation += "• Выполняется, если все предыдущие условия ложны\n"
            explanation += "• Не требует условия\n"
            explanation += "• Должен быть последним в цепочке if-elif\n"
            return explanation

        def explain_for_loop(self, line):
            explanation = "🔄 Цикл for:\n"

            match = re.match(r'for\s+(\w+)\s+in\s+(.*):', line)
            if match:
                variable = match.group(1)
                sequence = match.group(2)
                explanation += f"• Переменная цикла: {variable}\n"
                explanation += f"• Последовательность: {sequence}\n"
                explanation += f"• Цикл выполнится для каждого элемента {sequence}\n"
                explanation += "• Тело цикла должно быть с отступом\n"

            return explanation

        def explain_while_loop(self, line):
            explanation = "⏳ Цикл while:\n"

            match = re.match(r'while\s+(.*):', line)
            if match:
                condition = match.group(1)
                explanation += f"• Условие продолжения: {condition}\n"
                explanation += "• Цикл выполняется, пока условие истинно\n"
                explanation += "• Важно обеспечить изменение условия\n"
                explanation += "• Тело цикла должно быть с отступом\n"

            return explanation

        def explain_input(self, line):
            explanation = "⌨️ Функция input() - ввод данных:\n"

            match = re.search(r'(\w+)\s*=\s*input\((.*)\)', line)
            if match:
                variable = match.group(1)
                prompt = match.group(2)
                explanation += f"• Сохраняет результат в переменную: {variable}\n"
                explanation += f"• Приглашение для пользователя: {prompt}\n"
                explanation += "• Возвращает введенные данные как строку\n"
                explanation += "• Программа ждет ввода пользователя\n"

            return explanation

        def explain_assignment(self, line):
            explanation = "💾 Присваивание значения переменной:\n"

            match = re.match(r'(\w+)\s*=\s*(.*)', line)
            if match:
                variable = match.group(1)
                value = match.group(2)
                explanation += f"• Переменная: {variable}\n"
                explanation += f"• Значение: {value}\n"
                explanation += "• Теперь можно использовать переменную в коде\n"

                if value.isdigit():
                    explanation += "• Тип: целое число (int)\n"
                elif re.match(r'^\d+\.\d+', value):
                    explanation += "• Тип: дробное число (float)\n"
                elif re.match(r'^[\'\"]', value):
                    explanation += "• Тип: строка (str)\n"
                elif value.startswith('[') and value.endswith(']'):
                    explanation += "• Тип: список (list)\n"
                elif value.startswith('{') and value.endswith('}'):
                    explanation += "• Тип: словарь (dict)\n"

            return explanation

        def explain_function_call(self, line):
            explanation = "📞 Вызов функции:\n"

            match = re.match(r'(\w+)\((.*)\)', line)
            if match:
                func_name = match.group(1)
                args = match.group(2)
                explanation += f"• Функция: {func_name}\n"
                explanation += f"• Аргументы: {args if args else 'нет'}\n"
                explanation += "• Выполняет код, определенный в функции\n"
                explanation += "• Может возвращать результат\n"

            return explanation

        def explain_return(self, line):
            explanation = "↩️ Оператор return:\n"

            match = re.match(r'return\s+(.*)', line)
            if match:
                value = match.group(1)
                explanation += f"• Возвращаемое значение: {value}\n"
                explanation += "• Завершает выполнение функции\n"
                explanation += "• Передает значение обратно в вызывающий код\n"

            return explanation

        def explain_import(self, line):
            explanation = "📦 Импорт модуля:\n"

            match = re.match(r'import\s+(.+)', line)
            if match:
                module = match.group(1)
                explanation += f"• Модуль: {module}\n"
                explanation += "• Добавляет функциональность из внешнего модуля\n"
                explanation += f"• Теперь можно использовать: {module}.функция()\n"

            return explanation

        def explain_from_import(self, line):
            explanation = "📥 Импорт конкретных функций:\n"

            match = re.match(r'from\s+(\w+)\s+import\s+(.+)', line)
            if match:
                module = match.group(1)
                imports = match.group(2)
                explanation += f"• Из модуля: {module}\n"
                explanation += f"• Импортирует: {imports}\n"
                explanation += f"• Теперь можно использовать напрямую: {imports.split(',')[0]}()\n"

            return explanation

        def explain_general_line(self, line):
            explanation = "📄 Строка кода Python:\n"

            if any(op in line for op in ['+', '-', '*', '/', '%', '**']):
                explanation += "• Содержит математические операции\n"

            if any(op in line for op in ['==', '!=', '>', '<', '>=', '<=']):
                explanation += "• Содержит операции сравнения\n"

            if any(op in line for op in ['and', 'or', 'not']):
                explanation += "• Содержит логические операции\n"

            explanation += "• Выполняет определенное действие или вычисление\n"
            return explanation

        def format_full_explanation(self, original_code, explanations):
            result = "=" * 70 + "\n"
            result += "📋 ПОЛНОЕ ОБЪЯСНЕНИЕ КОДА PYTHON\n"
            result += "=" * 70 + "\n\n"

            result += "💻 ИСХОДНЫЙ КОД:\n"
            result += "```python\n"
            result += original_code + "\n"
            result += "```\n\n"

            result += "📚 ПОДРОБНЫЙ РАЗБОР:\n"
            result += "-" * 50 + "\n\n"

            for i, explanation in enumerate(explanations, 1):
                result += f"{explanation}\n"
                if i < len(explanations):
                    result += "─" * 30 + "\n\n"

            result += "\n💡 СОВЕТЫ:\n"
            result += "• Внимательно следите за отступами (используйте 4 пробела)\n"
            result += "• Проверяйте правильность написания имен переменных и функций\n"
            result += "• Используйте комментарии для пояснения сложных моментов\n"

            return result

        def update_status(self, message):
            def update():
                self.status_label.config(text=message)

            self.root.after(0, update)

        def show_result(self, text):
            def update():
                self.result_output.delete("1.0", END)
                self.result_output.insert("1.0", text)
                char_count = len(text)
                self.status_label.config(text=f"✅ Анализ завершен! Символов: {char_count}")

            self.root.after(0, update)

        def reset_interface(self):
            def update():
                self.translate_btn.config(state=NORMAL, text="🔍 Полное объяснение кода")
                self.loading_label.config(text="")

            self.root.after(0, update)

    translator_instance = SmartPythonTranslator(report_window)

    translator_instance.start_translation()


def gene():
    global result_window, te

    selected_option = user.get()
    if selected_option == "Сканирование кода":
        te = text.get("1.0", END)

        if result_window is not None and result_window.winfo_exists():
            root = result_window
            for widget in root.winfo_children():
                widget.destroy()
        else:
            root = Tk()
            root.title("GPTest - Result")
            root.geometry("800x600")
            root.iconbitmap("Sun.ico")
            root.resizable(False, False)
            result_window = root

        f = Label(root, text="Обработка кода...", bg="black", fg="white")
        f.place(x=0, y=0, width=120, height=20)

        module_links = {}
        module_safety = {}

        if lea == "Python":
            all_imports = []
            lines = te.split('\n')
            security_level = 1

            for line in lines:
                line = line.strip()

                if line.startswith('import '):
                    modules = line[7:].strip().split(',')
                    for module in modules:
                        module = module.strip()
                        if module and not module.startswith('#'):
                            all_imports.append(module)
                            if module not in module_links:
                                module_links[module] = search_module_info(module)

                            safety_level, safety_desc = analyze_module_safety(module)
                            module_safety[module] = (safety_level, safety_desc)

                            if safety_level == 2:
                                security_level = 2

                elif line.startswith('from '):
                    if ' import ' in line:
                        module_part = line[5:].split(' import ')[0].strip()
                        if module_part and not module_part.startswith('#'):
                            all_imports.append(f"{module_part}")
                            if module_part not in module_links:
                                module_links[module_part] = search_module_info(module_part)

                            safety_level, safety_desc = analyze_module_safety(module_part)
                            module_safety[module_part] = (safety_level, safety_desc)

                            if safety_level == 2:
                                security_level = 2

                        parts = line.split(' import ')
                        if len(parts) == 2:
                            imported_items = parts[1].strip().split(',')
                            for item in imported_items:
                                item = item.strip()
                                if item and not item.startswith('#'):
                                    all_imports.append(item)
                                    if item not in module_links:
                                        module_links[item] = search_module_info(item)

                                    safety_level, safety_desc = analyze_module_safety(item)
                                    module_safety[item] = (safety_level, safety_desc)

                                    if safety_level == 2:
                                        security_level = 2

            if all_imports:
                a = ", ".join(all_imports)

                security_color = "green" if security_level == 1 else "orange"
                security_text = "Низкий риск (Уровень 1)" if security_level == 1 else "Повышенный риск (Уровень 2)"

                security_label = Label(root, text=f"Уровень риска: {security_text}",
                                       bg=security_color, fg="white", font=("Arial", 12, "bold"))
                security_label.place(x=10, y=30, width=780, height=30)

                modules_label = Label(root, text=f"Найдено модулей/библиотек: {len(all_imports)}", wraplength=780,
                                      justify=LEFT)
                modules_label.place(x=10, y=70, width=780, height=20)

                links_frame = Frame(root)
                links_frame.place(x=0, y=100, width=800, height=450)

                scrollbar = Scrollbar(links_frame)
                scrollbar.pack(side=RIGHT, fill=Y)

                links_listbox = Listbox(links_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
                links_listbox.pack(side=LEFT, fill=BOTH, expand=True)
                scrollbar.config(command=links_listbox.yview)

                high_risk_count = 0
                low_risk_count = 0
                unknown_count = 0

                for module in all_imports:
                    if module in module_safety:
                        safety_level, safety_desc = module_safety[module]

                        if safety_level == 2:
                            high_risk_count += 1
                            color_indicator = "🔴 Высокий риск"
                        elif safety_level == 1:
                            low_risk_count += 1
                            color_indicator = "🟢 Низкий риск"
                        else:
                            unknown_count += 1
                            color_indicator = "🟡 Неизвестный риск"

                        link_text = f"{color_indicator} | {module}: {module_links.get(module, 'Ссылка не найдена')}"
                        links_listbox.insert(END, link_text)
                    else:
                        links_listbox.insert(END,
                                             f"🟡 Неизвестный риск | {module}: {module_links.get(module, 'Ссылка не найдена')}")

                stats_text = f"Высокий риск: {high_risk_count} | Низкий риск: {low_risk_count} | Неизвестные: {unknown_count}"
                stats_label = Label(root, text=stats_text)
                stats_label.place(x=10, y=560, width=780, height=20)

                links_listbox.bind('<Double-Button-1>', open_url)

                instruction = Label(root, text="Дважды кликните на ссылку для открытия в браузере")
                instruction.place(x=0, y=580, width=800, height=20)
            else:
                security_label = Label(root, text="Уровень риска: Низкий (Уровень 1) - модули не найдены",
                                       bg="green", fg="white", font=("Arial", 12, "bold"))
                security_label.place(x=10, y=30, width=780, height=30)

                no_modules_label = Label(root, text="В коде не найдено импортируемых модулей")
                no_modules_label.place(x=10, y=70, width=780, height=20)

        close_button = Button(root, text="Полный отчёт", bg="red", fg="white",
                              font=("Arial", 10, "bold"), command=close_result_window)
        close_button.place(x=680, y=560, width=100, height=20)

        f.config(text="Анализ завершен")
        root.deiconify()
        root.lift()


lea = "Python"

w = Tk()
w.title("GPTest")
w.geometry("600x505")
w.resizable(False, False)
w.iconbitmap("Sun.ico")

def git():
    webbrowser.open('https://github.com/Doraclepton/GPTest')


def inetprit():
    global susi, users
    ses = "Python"
    root = Tk()
    root.title("Interpreter settings")
    root.geometry("400x200")
    root.iconbitmap("Sun.ico")
    root.resizable(False, False)
    a = Label(root, text=f"Выбранный интерпретатор: \n{ses}")
    a.place(x=0, y=0, width=160, height=30)
    aa = Label(root, text="Язык программирования:")
    aa.place(x=0, y=50, width=150, height=20)
    users = Entry(root, bg="black", fg="white", insertbackground='white')
    users.place(x=160, y=50, width=150, height=20)
    sus = Button(root, text="Начать операцию по смене языка интерпретатора", command=SUS)
    sus.place(x=0, y=110, width=300, height=20)
    susi = Label(root, text="")
    susi.place(x=0, y=180, width=400, height=20)


def SUS():
    user_input = users.get()

    if user_input == "Python":
        susi.config(text="Операция отменена: Нет изменений в языке")
    else:
        susi.config(text=f"Операция отменена: {user_input} отсутствует в списке языков")


text = Text(w)
text.place(x=0, y=20, width=600, height=380)

main_menu = Menu()
refere = Menu(tearoff=0)
refere.add_cascade(label="GitHub", command=git)
nas = Menu(tearoff=0)
nas.add_cascade(label="Интерпретатор", command=inetprit)

main_menu.add_cascade(label="Ресурсы", menu=refere)
main_menu.add_cascade(label="Настройки", menu=nas)

w.config(menu=main_menu)

v = Label(w, bg="black")
v.place(x=0, y=400, width=600, height=1)

gen = Button(w, text="Начать", bg="black", fg="green", command=gene)
gen.place(x=200, y=460, width=200, height=30)

vid = ["Сканирование кода"]

user = ttk.Combobox(w, values=vid)
user.place(x=0, y=410, width=150, height=20)
user.set("Сканирование кода")

example_code = '''import os
import tkinter
'''

text.insert("1.0", example_code)

w.mainloop()

