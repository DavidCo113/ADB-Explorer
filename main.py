# ADB Explorer: An ADB-based utility to manage files on Android devices.
# Copyright (C) 2022 David Cole <davidco7777@protonmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from tkinter import *
from tkinter import ttk, messagebox, filedialog
from natsort import natsorted
import pathlib
import subprocess
import re
import os
import sys
import tempfile
import shutil
import webbrowser
import traceback
import json

# ensure the script is running in the proper directory
os.chdir(os.path.dirname(__file__))


# noinspection PyTypeChecker,PyGlobalUndefined
class ADBfm:

    def __init__(self):
        global garbage
        global icon
        global system
        global cut
        global hidden
        global adb
        cut = False
        garbage = []
        if sys.platform.startswith('linux'):
            system = 'linux'
        elif sys.platform.startswith('darwin'):
            system = 'darwin'
        elif sys.platform.startswith('win32'):
            system = 'win32'
        else:
            raise Exception(f'{sys.platform} not supported. ):')
        self.root = Tk()
        self.root.option_add('*tearOff', FALSE)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        try:
            icon = PhotoImage(file='assets/adb.png')
            self.root.iconphoto(False, icon)
            if not pathlib.Path('config.json').is_file():
                f = open('config.json', 'xt')
                self.adb_config(self.root, True)
                hidden = BooleanVar(value=False)
                f.write(json.dumps({'ADB_Path': adb, 'Show_Hidden': False}))
                f.close()
            else:
                f = open('config.json', 'rt')
                config_data = json.loads(f.read())
                f.close()
                hidden = BooleanVar(value=config_data['Show_Hidden'])
                adb = config_data['ADB_Path']
            self.choose_device()
        except Exception:
            messagebox.showerror('An exception has occurred:', traceback.format_exc())
            raise

    def adb_config(self, root, setup_mode):
        global adb_path
        global config_frame
        if setup_mode:
            root.title('Configure ADB')
            root.geometry('200x100')

            config_frame = Frame(root)
            config_frame.grid(sticky='nsew')
            config_frame.columnconfigure(0, weight=1)
            config_frame.rowconfigure(0, weight=1)

            adb_path = StringVar(value='adb')
            Entry(config_frame, textvariable=adb_path).grid(row=0, column=0, sticky='ew')
            folder = PhotoImage(file='assets/folder_open.png')
            Button(config_frame, image=folder, command=self.select_adb).grid(row=0, column=1)
            Button(config_frame, text='Save', command=lambda: self.save_adb(root)).grid(row=1, column=0)

            root.mainloop()
        else:
            win = Toplevel(root)
            win.title('Configure ADB')
            win.iconphoto(False, icon)

            config_frame = Frame(win)
            config_frame.grid(sticky='nsew')
            config_frame.columnconfigure(0, weight=1)
            config_frame.rowconfigure(0, weight=1)

            adb_path = StringVar(value='adb')
            Entry(config_frame, textvariable=adb_path).grid(row=0, column=0, sticky='ew')
            folder = PhotoImage(file='assets/folder_open.png')
            Button(config_frame, image=folder, command=self.select_adb).grid(row=0, column=1)
            Button(config_frame, text='Save', command=lambda: self.save_adb(root)).grid(row=1, column=0)

            win.protocol('WM_DELETE_WINDOW', lambda: self.dismiss(win))
            win.transient(root)
            win.wait_visibility()
            win.grab_set()
            win.wait_window()

    @staticmethod
    def select_adb():
        global adb_path
        if system == 'win32':
            filetypes = [('ADB', 'adb.exe'), ('All Files', '*')]
        else:
            filetypes = [('ADB', 'adb'), ('All Files', '*')]
        file = filedialog.askopenfilename(title='Select ADB', filetypes=filetypes)
        if file:
            adb_path.set(file)

    @staticmethod
    def save_adb(root):
        global adb
        global config_frame
        adb = adb_path.get()
        config_frame.destroy()
        root.quit()

    def choose_device(self):
        try:
            devices = None
            devices_friendly = None
            status = None
            devs_var = StringVar()

            def reload_devs():
                nonlocal devices
                nonlocal devices_friendly
                nonlocal status
                nonlocal devs_var
                devices = subprocess.check_output([adb, 'devices']).decode().split()[4:]
                devices_friendly = [f'{devices[i]}: {devices[i + 1]}'
                                    for i in range(0, len(devices) - 1, 2)]
                status = devices[1::2]
                devices = devices[::2]
                devs_var.set(value=devices_friendly)

            # find devices
            reload_devs()

            # configure root
            self.root.title('Pick device')
            self.root.geometry('200x250')

            # create the frame
            chooser_frame = Frame(self.root)
            chooser_frame.grid(sticky='nsew')
            chooser_frame.rowconfigure(0, weight=1)
            chooser_frame.rowconfigure(1, weight=1)
            chooser_frame.columnconfigure(0, weight=1)

            # create the menubar
            menubar = Menu(chooser_frame)
            self.root['menu'] = menubar
            menu_info = Menu(menubar)
            menubar.add_cascade(menu=menu_info, label='Help')

            # add menubar items
            menu_info.add_command(label='About...', command=lambda: self.about(self.root))

            # load assets
            refresh = PhotoImage(file='assets/refresh.png')

            # add the ribbon
            ribbon = Frame(chooser_frame)
            ribbon.grid(sticky='new', row=0, column=0)
            ribbon.columnconfigure(0, weight=1)

            # create the label, refresh button and listbox
            Label(ribbon, text='Select device:').grid(row=0, column=0)
            reload_button = Button(ribbon, image=refresh, command=reload_devs)
            reload_button.grid(sticky='e', row=0, column=1)
            devices_list = Listbox(chooser_frame, listvariable=devs_var, justify=CENTER)
            devices_list.grid(sticky='nsew', row=1, column=0)

            # create the button
            b = Button(chooser_frame, text='Connect',
                       command=lambda: self.connect(
                           devices_list.curselection(), self.root, devices, status, chooser_frame))
            b.grid(row=2, column=0)
            self.root.bind('<Return>', lambda e: b.invoke())

            try:
                self.root.mainloop()
            except KeyboardInterrupt:
                self.root.destroy()
        except Exception:
            messagebox.showerror('An exception has occurred:', traceback.format_exc())
            raise

    def connect(self, device, root, devices, status, chooser_frame):
        if device == ():
            messagebox.showinfo(message='No device selected!')
        else:
            chooser_frame.destroy()
            root.unbind('<Return>')
            if not status[device[0]] == 'device':
                subprocess.Popen([adb, '-s', devices[device[0]], 'reconnect', 'offline']).wait()
            self.file_manager(devices[device[0]], root)

    def file_manager(self, device, root):
        try:
            # set title and add frame
            root.title(f'ADB Explorer ({device})')
            root.geometry('600x300')
            main_frame = Frame(root)
            main_frame.grid(sticky='nsew')
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(1, weight=1)

            # create the menubar
            menubar = Menu(main_frame)
            root['menu'] = menubar
            menu_device = Menu(menubar)
            menu_view = Menu(menubar)
            menu_file = Menu(menubar)
            menu_info = Menu(menubar)
            menubar.add_cascade(menu=menu_device, label='Device')
            menubar.add_cascade(menu=menu_view, label='View')
            menubar.add_cascade(menu=menu_file, label='File')
            menubar.add_cascade(menu=menu_info, label='Help')

            # add menubar items
            menu_device.add_command(label='Reconnect',
                                    command=lambda: subprocess.Popen([adb, '-s', device, 'reconnect', 'device']).wait())
            menu_device.add_command(label='Change device', command=lambda: self.change_device(main_frame))
            menu_device.add_command(label='Root', command=lambda: subprocess.Popen([adb, '-s', device, 'root']).wait())
            menu_device.add_command(label='Unroot', command=lambda: subprocess.Popen(
                [adb, '-s', device, 'unroot']).wait())

            menu_view.add_checkbutton(label='Show hidden files', variable=hidden, onvalue=True, offvalue=False,
                                      command=lambda: self.reload(device))

            menu_file.add_command(label='Upload file...', command=lambda: self.push(device, root))
            menu_file.add_command(label='Upload dir...', command=lambda: self.push_dir(device, root))
            menu_file.add_command(label='Download...', command=lambda: self.pull(
                files.curselection(), device, root, False))
            menu_file.add_command(label='Download current dir...', command=lambda: self.pull_dir(device, root))
            menu_file.add_command(label='Copy', command=lambda: self.copy(files.curselection(), menu_file))
            menu_file.add_command(label='Cut', command=lambda: self.cut(files.curselection(), menu_file))
            menu_file.add_command(label='Paste', state=DISABLED, command=lambda: self.paste(device, menu_file))

            menu_info.add_command(label='About...', command=lambda: self.about(root))

            # create the right-click menu
            global menu_rmb
            menu_rmb = Menu(root)

            menu_rmb.add_command(label='Open', command=lambda: self.openf(files.curselection(), device, root, False))
            menu_rmb.add_command(label='Rename', command=lambda: self.rename_dialog(files.curselection(), root, device))
            menu_rmb.add_command(label='Download...', command=lambda: self.pull(
                files.curselection(), device, root, False))
            menu_rmb.add_command(label='Copy', command=lambda: self.copy(files.curselection(), menu_file))
            menu_rmb.add_command(label='Cut', command=lambda: self.cut(files.curselection(), menu_file))
            menu_rmb.add_command(label='Paste', state=DISABLED, command=lambda: self.paste(device, menu_file))
            menu_rmb.add_separator()
            menu_rmb.add_command(label='Delete', command=lambda: self.delete(files.curselection(), device))

            # load assets
            up_dir = PhotoImage(file='assets/subdirectory_arrow_left.png')
            upload = PhotoImage(file='assets/upload.png')
            refresh = PhotoImage(file='assets/refresh.png')
            arrow = PhotoImage(file='assets/arrow_forward.png')

            # add the ribbon
            global bar_dir
            ribbon = Frame(main_frame)
            ribbon.grid(sticky='new', row=0, column=0)
            ribbon.columnconfigure(2, weight=1)

            up_button = Button(ribbon, image=up_dir, command=lambda: self.up(device))
            up_button.grid(row=0, column=0)

            push_button = Button(ribbon, image=upload, command=lambda: self.push(device, root))
            push_button.grid(row=0, column=1)

            bar_dir = StringVar(value='/')
            browse_bar = Entry(ribbon, textvariable=bar_dir)
            browse_bar.bind('<Return>', lambda e: go_button.invoke())
            browse_bar.grid(sticky='ew', row=0, column=2)

            go_button = Button(ribbon, image=arrow, command=lambda: self.go_abs(device, root))
            go_button.grid(row=0, column=3)

            reload_button = Button(ribbon, image=refresh, command=lambda: self.reload(device))
            reload_button.grid(row=0, column=4)

            # create the file pane
            global open_dir
            global filesvar
            global fileslist
            open_dir = '/'
            fileslist = self.ls(open_dir, device)
            filesvar = StringVar(value=fileslist)
            files_frame = Frame(main_frame)
            files_frame.grid(sticky='nsew', row=1, column=0)
            files_frame.columnconfigure(0, weight=1)
            files_frame.rowconfigure(0, weight=1)
            files = Listbox(files_frame, listvariable=filesvar)
            files.bind('<Double-1>', lambda e: self.open_file(files.curselection(), device, root))
            files.bind('<Return>', lambda e: self.open_file(files.curselection(), device, root))
            files.bind('<Button-3>', self.popup_menu)
            files.grid(sticky='nsew', row=0, column=0)
            files_scroll = Scrollbar(files_frame)
            files_scroll.grid(sticky='nse', row=0, column=1)
            files.config(yscrollcommand=files_scroll.set)
            files_scroll.config(command=files.yview)

            try:
                root.mainloop()
            except KeyboardInterrupt:
                root.destroy()
        except Exception:
            messagebox.showerror('An exception has occurred:', traceback.format_exc())
            raise

    def change_device(self, main_frame):
        main_frame.destroy()
        self.choose_device()

    @staticmethod
    def is_ip(device):
        return bool(re.match('^[0-9.:]*$', device))

    @staticmethod
    def ls(ls_dir, device):
        try:
            if hidden.get():
                out = subprocess.check_output([adb, '-s', device, 'shell', 'ls', f'"{ls_dir}"', '-F', '-A'],
                                              stderr=subprocess.PIPE)
            else:
                out = subprocess.check_output([adb, '-s', device, 'shell', 'ls', f'"{ls_dir}"', '-F'],
                                              stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as ex:
            if ex.stderr.endswith(b'Permission denied\n'):
                messagebox.showerror('Permission denied', ex.stderr)
            else:
                messagebox.showerror('An exception has occurred:', ex.stderr)
            raise
        cont = out.decode().replace('\r', '').split('\n')[:-1]
        return natsorted(cont, key=lambda x: x.lower())

    def up(self, device):
        global open_dir
        open_dir = str(pathlib.PurePosixPath(open_dir).parent) + '/'
        if open_dir[1] == '/':
            open_dir = open_dir[1:]
        self.reload(device)

    def go(self, item, device, root):
        global open_dir
        prev_dir = open_dir
        open_dir = str(pathlib.PurePosixPath(open_dir, item))
        if len(open_dir) > 1 and open_dir[1] == '/':
            open_dir = open_dir[1:]
        status = self.get_file_status(open_dir, device)
        if status == 2:
            if len(open_dir) > 1:
                open_dir += '/'
            self.reload(device)
        elif status == 1:
            pull_from = pathlib.PurePosixPath(open_dir).parts[-1]
            open_dir = prev_dir
            self.pull(pull_from, device, root, True)
        else:
            print('Permission denied')
            open_dir = prev_dir

    @staticmethod
    def get_file_status(file, device):
        # return 0 if file does not exist, 1 if a file, 2 if a directory
        if subprocess.Popen([adb, '-s', device, 'shell', '[', '-f', f'"{file}"', ']']).wait() == 0:
            return 1
        elif subprocess.Popen([adb, '-s', device, 'shell', '[', '-d', f'"{file}"', ']']).wait() == 0:
            return 2
        else:
            return 0

    def rename_dialog(self, item, root, device):
        try:
            if fileslist[item[0]][-1] == '@' or fileslist[item[0]][-1] == '*' or fileslist[item[0]][-1] == '/':
                file = fileslist[item[0]][:-1]
            else:
                file = fileslist[item[0]]
            win = Toplevel(root)
            win.title('Rename')
            win.geometry('300x150')
            rename_icon = PhotoImage(file='assets/rename.png')
            win.iconphoto(False, rename_icon)
            win.columnconfigure(0, weight=1)
            win.rowconfigure(0, weight=1)
            rename_frame = ttk.Frame(win, padding=15)
            rename_frame.grid(sticky='nsew')
            rename_frame.columnconfigure(0, weight=1)
            rename_frame.rowconfigure(0, weight=1)
            rename_frame.rowconfigure(1, weight=1)

            rename_var = StringVar(value=file)
            rename_entry = Entry(rename_frame, textvariable=rename_var)
            rename_entry.grid(row=0, column=0, sticky='ew')
            button_frame = ttk.Frame(rename_frame, padding=15)
            button_frame.grid(row=1, column=0, sticky='sew')
            button_frame.columnconfigure(0, weight=1)
            button_frame.columnconfigure(1, weight=1)
            button_frame.rowconfigure(0, weight=1)
            Button(button_frame, text='Cancel', command=lambda: self.dismiss(win)).grid(row=0, column=0, sticky='nw')
            rename_button = Button(button_frame, text='Rename',
                                   command=lambda: self.rename(file, win, device, rename_var))
            rename_button.grid(row=0, column=1, sticky='ne')
            rename_entry.bind('<Return>', lambda e: rename_button.invoke())

            win.protocol('WM_DELETE_WINDOW', lambda: self.dismiss(win))
            win.transient(root)
            win.wait_visibility()
            win.grab_set()
            win.wait_window()
        except Exception:
            messagebox.showerror('An exception has occurred:', traceback.format_exc())
            raise

    def rename(self, file, win, device, rename_var):
        original = str(pathlib.PurePosixPath(open_dir, file))
        renamed = str(pathlib.PurePosixPath(open_dir, rename_var.get()))
        status = self.get_file_status(renamed, device)
        if status == 0:
            subprocess.Popen([adb, '-s', device, 'shell', 'mv', f'"{original}"', f'"{renamed}"']).wait()
            self.dismiss(win)
            self.reload(device)
        else:
            messagebox.showinfo(message='File already exists.')

    def reload(self, device):
        # reload the file pane
        global open_dir
        global bar_dir
        global filesvar
        global fileslist
        bar_dir.set(open_dir)
        try:
            fileslist = self.ls(open_dir, device)
            filesvar.set(fileslist)
        except subprocess.CalledProcessError:
            self.up(device)

    def push(self, device, root):
        # pushes a file
        global open_dir
        file = filedialog.askopenfilename(title='Push file')
        if file:
            root.title('Uploading...')
            try:
                subprocess.Popen([adb, '-s', device, 'push', file, open_dir]).wait()
                self.reload(device)
            finally:
                root.title(f'ADB Explorer ({device})')

    def push_dir(self, device, root):
        # pushes a directory
        global open_dir
        file = filedialog.askdirectory(title='Push file')
        if file:
            root.title('Uploading...')
            try:
                subprocess.Popen([adb, '-s', device, 'push', file, open_dir]).wait()
                self.reload(device)
            finally:
                root.title(f'ADB Explorer ({device})')

    def go_abs(self, device, root):
        # will navigate to an absolute path
        global open_dir
        global bar_dir
        prev_dir = open_dir
        open_dir = str(pathlib.PurePosixPath(bar_dir.get()))

        if len(open_dir) > 1 and open_dir[1] == '/':
            open_dir = open_dir[1:]
        status = self.get_file_status(open_dir, device)
        if status == 2:
            if len(open_dir) > 1:
                open_dir += '/'
            self.reload(device)
        elif status == 1:
            pull_from = pathlib.PurePosixPath(open_dir).parts[-1]
            open_dir = str(pathlib.PurePosixPath(open_dir).parent)
            self.openf(pull_from, device, root, True)
            open_dir = prev_dir
        else:
            print('File does not exist.')
            open_dir = prev_dir
            bar_dir.set(prev_dir)

    @staticmethod
    def pull(item, device, root, skip):
        # pulls the selected item
        try:
            if not skip:
                if fileslist[item[0]][-1] == '@' or fileslist[item[0]][-1] == '*':
                    from_file = fileslist[item[0]][:-1]
                else:
                    from_file = fileslist[item[0]]
            else:
                from_file = item
            file = filedialog.asksaveasfilename(title='Pull file', initialfile=from_file,
                                                filetypes=[('All Files', '*')])
            if file:
                root.title('Downloading...')
                try:
                    subprocess.Popen(
                        [adb, '-s', device, 'pull', str(pathlib.PurePosixPath(open_dir, from_file)), file]).wait()
                finally:
                    root.title(f'ADB Explorer ({device})')
        except Exception:
            messagebox.showerror('An exception has occurred:', traceback.format_exc())
            raise

    @staticmethod
    def pull_dir(device, root):
        # pulls the current directory
        global fileslist
        global open_dir
        dir_name = pathlib.PurePosixPath(open_dir).parts[-1]
        file = filedialog.asksaveasfilename(title='Pull file', initialfile=dir_name, filetypes=[('All Files', '*')])
        if file:
            root.title('Downloading...')
            try:
                subprocess.Popen([adb, '-s', device, 'pull', open_dir, file]).wait()
            finally:
                root.title(f'ADB Explorer ({device})')

    def delete(self, item, device):
        try:
            if fileslist[item[0]][-1] == '@' or fileslist[item[0]][-1] == '*':
                file = fileslist[item[0]][:-1]
            else:
                file = fileslist[item[0]]
            file = str(pathlib.PurePosixPath(open_dir, file))
            subprocess.check_output([adb, '-s', device, 'shell', 'rm', '-rf', f'"{file}"'], stderr=subprocess.PIPE)
            self.reload(device)
        except subprocess.CalledProcessError as ex:
            if ex.stderr.endswith(b'Permission denied\n'):
                messagebox.showerror('Permission denied', ex.stderr)
            else:
                messagebox.showerror('An exception has occurred:', ex.stderr)
            raise
        except Exception:
            messagebox.showerror('An exception has occurred:', traceback.format_exc())
            raise

    @staticmethod
    def popup_menu(event):
        global menu_rmb
        try:
            menu_rmb.tk_popup(event.x_root, event.y_root)
        finally:
            menu_rmb.grab_release()

    @staticmethod
    def copy(item, menu_file):
        try:
            global clipboard
            if fileslist[item[0]][-1] == '@' or fileslist[item[0]][-1] == '*':
                file = fileslist[item[0]][:-1]
            else:
                file = fileslist[item[0]]
            file = str(pathlib.PurePosixPath(open_dir, file))
            menu_file.entryconfig(6, state=NORMAL)
            menu_rmb.entryconfig(5, state=NORMAL)
            clipboard = file
        except Exception:
            messagebox.showerror('An exception has occurred:', traceback.format_exc())
            raise

    def paste(self, device, menu_file):
        global cut
        global menu_rmb
        if cut:
            cut = False
            menu_file.entryconfig(6, state=DISABLED)
            menu_rmb.entryconfig(5, state=DISABLED)
            subprocess.Popen([adb, '-s', device, 'shell', 'mv', f'"{clipboard}"', f'"{open_dir}"']).wait()
        else:
            subprocess.Popen([adb, '-s', device, 'shell', 'cp', f'"{clipboard}"', f'"{open_dir}"']).wait()
        self.reload(device)

    def openf(self, item, device, root, skip):
        try:
            global garbage
            if not skip:
                if fileslist[item[0]][-1] == '@' or fileslist[item[0]][-1] == '*':
                    file = fileslist[item[0]][:-1]
                else:
                    file = fileslist[item[0]]
            else:
                file = item
            root.title('Downloading...')
            tempdir = tempfile.mkdtemp()
            garbage.append(tempdir)
            subprocess.Popen([adb, '-s', device, 'pull', str(pathlib.PurePosixPath(open_dir, file)), tempdir]).wait()
            self.start_file(str(pathlib.Path(tempdir, pathlib.PurePosixPath(file).parts[-1])))
        except Exception:
            messagebox.showerror('An exception has occurred:', traceback.format_exc())
            raise
        finally:
            root.title(f'ADB Explorer ({device})')

    def open_file(self, item, device, root):
        # openf() item if file, if dir use go()
        global fileslist
        global open_dir
        try:
            if fileslist[item[0]][-1] == '@' or fileslist[item[0]][-1] == '*':
                file = fileslist[item[0]][:-1]
            else:
                file = fileslist[item[0]]
            file = str(pathlib.PurePosixPath(open_dir, file))
            status = self.get_file_status(file, device)
            if status == 1:
                self.openf(file, device, root, True)
            elif status == 2:
                self.go(file, device, root)
            else:
                print('Unable to open file')
        except IndexError:
            pass
        except Exception:
            messagebox.showerror('An exception has occurred:', traceback.format_exc())
            raise

    @staticmethod
    def dismiss(win):
        win.grab_release()
        win.destroy()

    def about(self, root):
        win = Toplevel(root)
        win.title('About')
        info = PhotoImage(file='assets/info.png')
        win.iconphoto(False, info)
        infoframe = ttk.Frame(win, padding=10)
        infoframe.pack()
        Label(infoframe, image=icon).grid(row=0, column=0)
        Label(infoframe, text='ADB Explorer', font=('TkDefaultFont', 25)).grid(row=0, column=1)
        Label(infoframe,
              text='An ADB-based utility to manage files on Android devices.\nCopyright (C) 2022 David Cole <'
                   'davidco7777@protonmail.com>\n\nThis program is free software: you can redistribute it and/or '
                   'modify\nit under the terms of the GNU General Public License as published by\nthe Free Software '
                   'Foundation, either version 3 of the License, or\n(at your option) any later version.\n\nThis '
                   'program is distributed in the hope that it will be useful,\nbut WITHOUT ANY WARRANTY; without '
                   'even the implied warranty of\nMERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\nGNU '
                   'General Public License for more details.\n\nYou should have received a copy of the GNU General '
                   'Public License\nalong with this program.  If not, see <https://www.gnu.org/licenses/>.').grid(
            row=1, column=1)
        Label(infoframe,
              text='Used modules:\ntkinter (GUI)\nnatsort (natural sorting)\npathlib (Working with paths)\nsubprocess '
                   '(Communicating with ADB and opening files)\nre (Detecting network-connected devices)\nos ('
                   'Starting files on win32 and changing directory)\nsys (Detecting platform)\ntempfile (Making '
                   'temporary directories)\nshutil (Garbage collection)\nwebbrowser (Opening the web browser if the '
                   'license file is not found)\ntraceback (Displaying exceptions)\njson (Saving/loading config)').grid(
            row=2, column=1)
        Label(infoframe, text='All used icons are part of Google\'s Material Icons collection,\n licensed under '
                              'the Apache License v2.0').grid(row=3, column=1)
        Button(infoframe, text='View License', command=self.get_license).grid(row=1, column=0)
        win.protocol('WM_DELETE_WINDOW', lambda: self.dismiss(win))
        win.transient(root)
        win.wait_visibility()
        win.grab_set()
        win.wait_window()

    def get_license(self):
        if pathlib.Path('LICENSE.md').is_file():
            self.start_file('LICENSE.md')
        else:
            webbrowser.open('https://www.gnu.org/licenses/#GPL', new=2)

    @staticmethod
    def start_file(file):
        global system
        if system == 'linux':
            subprocess.call(['xdg-open', file])
        elif system == 'darwin':
            subprocess.call(['open', file])
        elif system == 'win32':
            os.startfile(file)
        else:
            raise Exception(f'Unable to open files using {system}')

    def cut(self, item, menu_file):
        global cut
        cut = True
        self.copy(item, menu_file)


def finish():
    # remove files that have been opened with openf()
    for x in garbage:
        try:
            shutil.rmtree(x)
        except PermissionError:
            pass
    # save config
    f = open('config.json', 'wt')
    f.write(json.dumps({'ADB_Path': adb, 'Show_Hidden': hidden.get()}))
    f.close()


try:
    ADBfm()
finally:
    finish()
