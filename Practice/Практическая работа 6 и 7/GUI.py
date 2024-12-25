import PySimpleGUI as sg
import modules_py.filework
import modules_py.compress_image
import modules_py.pdf_docx_func


def checkFormats(dirc):
    fl1 = 0
    fl2 = 0
    fl3 = 0

    for i in [*values.get(dirc)]:
        img_finder = ('.png', '.jpg', '.jpeg')

        if i.endswith(img_finder) and fl3 == 0:
            fl3 = 1

        if i.endswith('.pdf') and fl1 == 0:
            fl1 = 1

        if i.endswith('.docx') and fl2 == 0:
            fl2 = 1

    if fl1 + fl2 + fl3 == 1:

        if fl1:
            return 1
        
        elif fl2:
            return 2
        
        elif fl3:
            return 3
        
        else: 
            return 0
        
    else:
        return 0


def pdf2docx(choice, docs):

    try:
        modules_py.pdf_docx_func.pdf_to_docx(choice, docs)
        sg.popup('Успешно!')

    except:
        sg.popup('Ошибка!')


def docx2pdf(choice, docs):

    try:
        modules_py.pdf_docx_func.docx_to_pdf(choice, docs)
        sg.popup('Успешно!')

    except:
        sg.popup('Ошибка!')


def compressed_image(choice, images, compression):
    
    try:
        modules_py.cimgae.compress_img(choice, images, compression)
        if int(compression) not in range(1,101):
            raise Exception
        sg.popup('Успешно!')

    except:
        sg.popup('Ошибка!')


def deleteFiles(podstr, type):

    try:
        if modules_py.filework.find_files(podstr, type=type) != {}:
            modules_py.filework.delete_files(str(type), podstr)
            sg.popup('Успешно!')

        else:
            sg.popup('Файлы не найдены!')

    except:
        sg.popup('Ошибка!')


def create_delwin():
    sg.theme('light brown 11')

    del_layout = [
        [sg.Radio('Удалить все файлы начинающиеся на введенную подстроку', "dchoice")],
        [sg.Radio('Удалить все файлы оканчивающиеся на введенную подстроку', "dchoice")],
        [sg.Radio('Удалить все файлы содержащие введенную подстроку', "dchoice")],
        [sg.Radio('Удалить файлы по расширению', "dchoice")],
        [sg.Text('Подстрока'), sg.InputText(key='podstr')],
        [sg.Button('Продолжить'), sg.Button('Выйти')]
    ]

    return sg.Window('Окно удаления', del_layout, finalize=True, icon='icon.ico')


def create_selwin():
    sg.theme('light brown 11')

    sel_layout = [
        [sg.Radio('Выбрать все подходящие файлы', "schoice")],
        [sg.Radio('Выбрать только выделенные файлы', "schoice")],
        [sg.Text('Выберите степень сжатия (1-100, наиб.- наим.)', visible=False, key='comptxt'), sg.Spin(values=[i for i in range(1, 101)], visible=False, initial_value=1, key='compression')],
        [sg.Button('Продолжить'), sg.Button('Выйти')]
    ]

    return sg.Window('Окно выбора', sel_layout, finalize=True, icon='icon.ico')

# визуально разделительная строка

sg.theme('Light Brown 11')

layout_left = [
    [sg.Text(f"Рабочий каталог: "), sg.Text(modules_py.filework.return_curr_dir(), key='dirtext'), sg.Button('Выбрать каталог')],
    [sg.Listbox(values=[], select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED, enable_events=True, size=(60, 20), key='file_dir')],
    [sg.Button('Выход')]
]

layout_right = [
    [sg.Text('Выберите функцию')],
    [sg.Button('Преобразовать PDF в Docx', key='choice1', disabled=True)],
    [sg.Button('Преобразовать Docx в PDF', key='choice2', disabled=True)],
    [sg.Button('Произвести сжатие изображений', key='choice3', disabled=True)],
    [sg.Button('Удалить группу файлов', key='choice4')]
]

layout = [[sg.Column(layout_left), sg.VSeperator(), sg.Column(layout_right)]]


main_window, del_win, sel_win = sg.Window('Основное окно', layout, finalize=True, icon='icon.ico'), None, None
main_window['file_dir'].update(modules_py.filework.os.listdir())
flag = 0


while True:
    window, event, values = sg.read_all_windows()

    if window == main_window and event in (sg.WINDOW_CLOSED, 'Выход'):
        break

    elif window == main_window and event == 'Выбрать каталог':

        try:
            modules_py.filework.os.chdir(sg.popup_get_folder('Выберите папку', title='Выбор папки'))
            main_window['dirtext'].update(modules_py.filework.return_curr_dir())
            main_window['file_dir'].update('')
            main_window['file_dir'].update(modules_py.filework.os.listdir())

        except TypeError:
            pass

        except:
            sg.popup('Ошибка!')

    elif window == main_window and event == 'file_dir':
        sel_files = values.get('file_dir')
        main_window['choice1'].update(disabled=True)
        main_window['choice2'].update(disabled=True)
        main_window['choice3'].update(disabled=True)

        if checkFormats('file_dir') > 0:
            flag = checkFormats('file_dir')

            if flag == 1:
                main_window['choice1'].update(disabled=False)

            elif flag == 2:
                main_window['choice2'].update(disabled=False)

            elif flag == 3:
                main_window['choice3'].update(disabled=False)

    elif window == main_window and event == 'choice1':
        sel_win = create_selwin()

    elif window == main_window and event == 'choice2':
        sel_win = create_selwin()

    elif window == main_window and event == 'choice3':
        sel_win = create_selwin()
        sel_win['comptxt'].update(visible=True)
        sel_win['compression'].update(visible=True)

    elif window == main_window and event == 'choice4':
        del_win = create_delwin()

    elif window == del_win and event in (sg.WINDOW_CLOSED, 'Выйти'):
        del_win.close()

    elif window == del_win and event == 'Продолжить':

        if values[0]:
            deleteFiles(values['podstr'], 1)

        elif values[1]:
            deleteFiles(values['podstr'], 2)

        elif values[2]:
            deleteFiles(values['podstr'], 3)

        elif values[3]:
            deleteFiles(values['podstr'], 0)

        main_window['file_dir'].update(modules_py.filework.os.listdir())

    elif window == sel_win and event in (sg.WINDOW_CLOSED, 'Выйти'):
        sel_win.close()

    elif window == sel_win and event == 'Продолжить' and values[0] or values[1]:

        if flag == 1:

            if values[0]:
                pdf2docx('0', modules_py.filework.find_files('.pdf', type=0))

            else:
                pdf2docx('1', sel_files)

        elif flag == 2:

            if values[0]:
                docx2pdf('0', modules_py.filework.find_files('.docx', type=0))

            else:
                docx2pdf('1', sel_files)

        elif flag == 3:

            if values[0]:
                compressed_image('0', modules_py.filework.find_files('.jpg', '.jpeg', '.gif', '.png', type=0), values['compression'])

            else:
                compressed_image('1', sel_files, values['compression'])

        main_window['file_dir'].update(modules_py.filework.os.listdir())

main_window.close()
