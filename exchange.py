from pywinauto.application import Application
from pywinauto import mouse, keyboard
import time
import psutil
import datetime
import os
from threading import Timer
from config import CONFIG

gExportSuccess = False;

def get_proc(process_name):
    p1 = psutil.pids()
    for pid in p1:
        try:
            if psutil.Process(pid).name() == process_name:
                print(psutil.Process(pid).name())
                return pid
        except Exception as e:
            print(e)
            kill_process('Exchanger')
    return 0;


def get_app():
    pid = get_proc(CONFIG.procName);
    if pid > 0:
        app = Application(backend='uia').connect(process=pid);
    else:
        app = Application(backend='uia').start(CONFIG.exchangerExe, timeout=10);
    return app;


# 判断文件列表中是否存在某个文件
def document_is_exist(window, name):
    element = window.descendants(control_type="ListItem", title=name)
    return len(element) != 0


# 判断是否有重命名弹窗
# 如果有弹窗，就把原有的文件覆盖
def controlwindow_is_exist(window):
    element = window.child_window(title="确认另存为", control_type="Window")
    if element.exists():
        win_control = window.child_window(title="确认另存为", control_type="Window")
        btn_yes = win_control.child_window(title="是(Y)", control_type="Button")
        btn_yes.click_input()

def check_error(app, title, timer):
    error_win = app.window(title=title);
    if error_win.exists(timeout=timer):
        error_win.Close.click_input()
        return True
    return False
def check_close_error(app):
    return check_error(app,"Exchanger Error", 1);

def check_close_error2(app):
    return check_error(app, "Internal error",1);

def check_close_display(app):
    return check_error(app,"Model displaying error", 1);

# 功能：导出ifc文件
# window是处理的窗口
# filename是转换之前的文件名字
# out_path是输出的路径
def export_ifc(app, window, filename, out_path):
    global gExportSuccess
    oldname = filename
    newname = oldname.split(".")[0]
    time.sleep(1)
    # 获取菜单中导出文件的按钮
    window.Export.click_input()
    if not gExportSuccess:
        window.IFC.click_input()

    stackview = window.child_window(class_name="QQuickStackView")
    stackview.Export.click_input()
    # 获取弹出的窗口
    win_brow = window.child_window(title="Please choose a file", control_type="Window")
    edit = win_brow.child_window(title="文件名:",  control_type="Edit")
    edit.set_edit_text(out_path + newname + '.ifc')
    time.sleep(2);
    window['保存(S)'].click_input();

    # 如果有弹窗就替换掉已经存在的转换后格式文件
    controlwindow_is_exist(win_brow)
    # 处理文件崩溃的情况：如果当前的窗口不存在，则文件进入了崩溃的状态，此时返回false
    if not window.exists():
        print("文件发生崩溃")
        return -1
    else:
        if check_close_error(app):
            return -1;

        # 添加对于文件导出成功与否的判断
        ret_name = out_path + newname + ".ifc";
        # exported = window.child_window(title="Export completed.", control_type="Edit")
        # exporting = window.child_window(title="Exporting...", control_type="Edit")
        gExportSuccess = True
        if window.child_window(title="Exporting...", control_type="Edit").exists(timeout=2):
            print('exporting')
            if window.child_window(title="Export completed.", control_type="Edit").exists(timeout=600):
                print('find exported')
                return ret_name
        if window.child_window(title="Export completed.", control_type="Edit").exists(timeout=2):
            print('find exported2')
            return ret_name

        return ret_name


def kill_process(name):
    # 获取当前所有应用的pids
    pids = psutil.pids()
    for pid in pids:
        # 根据pid 获取进程对象
        p = psutil.Process(pid)
        # 获取每个pid的应用对应的文件名字
        process_name = p.name()
        # print(process_name)
        # 判断形参是否是应用名字的子串来判断进程是否存在
        if name in process_name:
            # print("Process name is: %s, pid is: %s" % (process_name, pid))  # 1,33664
            try:
                # 如果存在，就删掉
                import subprocess
                subprocess.Popen("cmd.exe /k taskkill /F /T /PID %i" % pid, shell=True)
            except OSError:
                print('没有此进程!!!')


# 正常情况下发生转换框架函数
# 返回值：如果正常为0，不正常为-1
def autoexchange(in_path, filename, out_path):
    # 获取应用
    count = 2
    while count > 0:
        count = count - 1
        try:
            app = get_app()
        except Exception as e:
            print(e)
            kill_process('Exchanger')

    # 获取主窗口
    time.sleep(0.1)
    win_main = app.window(class_name='ExchangerGui_MainWindow_QMLTYPE_259')
    win_main.maximize()
    btn_browse = win_main.child_window(title="Browse", control_type="Button")
    if btn_browse.exists():
        # 点击浏览的按钮
        btn_browse.click_input()
        # 获取弹出的文件选择窗口
        win_brow = win_main.child_window(title="Please choose a file", control_type="Window")
        edit = win_main.child_window(title="文件名(N):", control_type="Edit")
        edit.set_edit_text(in_path + filename)
        time.sleep(0.1);
        win_main['打开O'].click_input();
        # 导入成功的判断
    else:
        # 如果没有，就通过侧栏的菜单选择import按钮后再浏览目标文件
        btn_import = win_main.child_window(title="Import", control_type="Button")
        btn_import.click_input()
        # 获取弹出菜单
        stackview = win_main.child_window(class_name="QQuickStackView")
        btn_browse = stackview.child_window(title="Browse", control_type="Button")
        btn_browse.click_input()
        # 获取弹出的文件选择窗口
        # win_brow = win_main.child_window(title="Please choose a file", control_type="Window")

        edit = win_main.child_window(title="文件名(N):", control_type="Edit")
        edit.set_edit_text(in_path + filename)
        time.sleep(0.1);
        win_main['打开O'].click_input();

        # 获取并点击下方的导入文件按钮
        btn_import1 = stackview.child_window(title="Import", control_type="Button")
        btn_import1.click_input()

    if check_close_error(app):
        check_close_error2(app)
        return -1;

    if check_close_display(app):
        return -1;
    # import_done = win_main.child_window(title="Import completed.", control_type="Edit")
    # importing = win_main.child_window(title="Importing...", control_type="Edit")
    # display_done = win_main.child_window(title="Display completed.", control_type="Edit")
    # displaying = win_main.child_window(title="Displaying...", control_type="Edit")
    if win_main.child_window(title="Importing...", control_type="Edit").exists(timeout=2):
        print('importing');
        if win_main.child_window(title="Displaying...", control_type="Edit").exists(timeout=600 * 3):
            print('try cancel 1');
            win_main.child_window(title="Cancel", control_type="Button").click_input()
    else:
        print('not importing');
        if win_main.child_window(title="Displaying...", control_type="Edit").exists(timeout=1):
            print('try cancel 2');
            win_main.child_window(title="Cancel", control_type="Button").click_input()

    if check_close_error(app):
        check_close_error2(app)
        return -1;

    print("文件导入成功！")
    new_file = export_ifc(app, win_main, filename, out_path)
    return new_file


# 包括异常处理
def myexchange(in_path, filename, out_path):
    # 如果出现异常就再执行一次
    try:
        # 成功转换
        result = autoexchange(in_path, filename, out_path)
        print("文件转换已经完成")
        if result == -1:
            # kill_process('Exchanger')
            time.sleep(2)
    except Exception as e:
        # if repr(e).split("\'")[1] == "timed out":
        #     print("程序崩溃")
        #     kill_process('Exchanger')
        # else:
        #     print(repr(e))
        print(repr(e))
        # kill_process('Exchanger')
    else:
        # kill_process('Exchanger')
        pass


# main函数中的内容是要出现在socket中的内容
# if __name__ == "__main__":
#     in_path = "C:\\Users\\aster\\Desktop\\分布式转码\\input"
#     filename = "kk35-7.step"
#     out_path = "C:\\Users\\aster\\Desktop\\分布式转码\\output"
#
#     myexchange(in_path, filename, out_path)
