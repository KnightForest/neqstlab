# main_window.py, main window for QT lab environment
# Reinier Heeres, <reinier@heeres.eu>, 2008
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk
import sys
from gettext import gettext as _L
import logging
import re
import os

import lib.gui as gui
from lib.gui import qtwindow, stopbutton, orderedbox
from lib.config import get_config, get_shared_config, get_read_only_config

import qtclient as qt

nouser_regex = re.compile('^[0-9]{8}[0-9]*$')

class MainWindow(qtwindow.QTWindow):

    _main_created = False

    def __init__(self):
        if MainWindow._main_created:
            logging.error('Error: Main window already created!')
            return
        MainWindow._main_created = True

        qtwindow.QTWindow.__init__(self, 'main', 'QT Lab', add_to_main=False)
        self.connect("delete-event", self._delete_event_cb)
        self.connect("destroy", self._destroy_cb)

        self.vbox = gtk.VBox()

        menu = [
            {'name': _L('File'), 'icon': '', 'submenu':
                [
                {'name': _L('Save'), 'icon': '', 'action': self._save_cb},
                {'name': _L('Exit'), 'icon': '', 'action': self._exit_cb}
                ]
            },
            {'name': _L('Help'), 'icon': '', 'submenu':
                [
                {'name': _L('About'), 'icon': ''}
                ]
            }
        ]
#        self.menu = gui.build_menu(menu)

        self._userlist = gtk.ListStore(str)
        self._populate_user_cb()
        self._userfield = gtk.ComboBoxEntry(self._userlist, 0)
        prevuser = get_shared_config().get('user')
        if prevuser == None:
        	prevuser = 'default'
        self._userfield.child.set_text(prevuser)
        if not self._user_in_cb(prevuser):
            self._add_user_cb_row(prevuser)
        self._userfield.connect('changed', self._user_changed)
        self._userfield.child.connect('activate', self._save_user)
        
        self._userlbl = gtk.Label('{:s}:'.format(_L('user')))
        self._userbtn = gtk.Button(_L('OK'))
        self._userbtn.set_sensitive(False)
        self._userbtn.connect('clicked', self._save_user)
        self._userhbox = gtk.HBox(spacing=2)
        self._userhbox.pack_start(self._userlbl, expand=False)
        self._userhbox.pack_start(self._userfield)
        self._userhbox.pack_start(self._userbtn, expand=False)
        
        self._liveplot_but = gtk.ToggleButton(_L('Live Plotting'))
        self._liveplot_but.set_active(qt.flow.get_live_plot())
        self._liveplot_but.connect('clicked', self._toggle_liveplot_cb)
        self._replot_but = gtk.Button(_L('Replot'))
        self._replot_but.connect('clicked', self._toggle_replot_cb)
        self._stop_but = stopbutton.StopButton()
        self._pause_but = stopbutton.PauseButton()

        vbox = gui.orderedbox.OrderedVBox()
        vbox.add(self._userhbox, 1, False)
        vbox.add(self._liveplot_but, 10, False)
        vbox.add(self._replot_but, 11, False)
        vbox.add(self._stop_but, 12, False)
        vbox.add(self._pause_but, 13, True)
        self._vbox = vbox
        self.add(self._vbox)

        self.show_all()

    def add_window(self, win):
        '''Add a button for window 'win' to the main window.'''

        title = win.get_title()

        button = gtk.ToggleButton(title)

        visible = qt.config.get('%s_show' % title, False)
        button.set_active(visible)

        # Connecting to clicked also triggers response on calling set_active()
        button.connect('released', self._toggle_visibility_cb, win)
        win.connect('show', self._visibility_changed_cb, button)
        win.connect('hide', self._visibility_changed_cb, button)

        try:
            orderid = win.ORDERID
        except:
            orderid = 1000
        self._vbox.add(button, orderid)
        button.show()

    def load_instruments(self):
        return

    def _checkbutton_cb(self, widget):
        if widget.get_active() == 0:
            qt.config['show_close_dialog'] = True
        else:
            qt.config['show_close_dialog'] = False

    def _delete_event_cb(self, widget, event, data=None):
        if not qt.config.get('show_close_dialog', True):
            return False

        label = gtk.Label("""
You are closing the QTLab GUI.

If you want to reopen it, run qt.flow.start_gui()
from the shell, or run the qtlabgui[.bat] script
in the QTLab folder.
""")
        label.set_line_wrap(True)

        checkbox = gtk.CheckButton("Do not show this message again.")
        checkbox.connect("toggled", self._checkbutton_cb)

        dialog = gtk.Dialog("Confirmation", None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))

        dialog.vbox.pack_start(label)
        dialog.vbox.pack_end(checkbox)
        dialog.vbox.show_all()
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_ACCEPT:
            return False
        else:
            return True

    def _destroy_cb(self, widget, data=None):
        logging.info('Closing GUI')
        qt.config.save(delay=0)
        try:
            gtk.main_quit()
        except:
            pass
        sys.exit()

    def _save_cb(self, widget):
        pass

    def _exit_cb(self, widget):
        pass

    def _toggle_visibility_cb(self, button, window):
        if (window.flags() & gtk.VISIBLE):
            window.hide()
        else:
            window.show()

    def _visibility_changed_cb(self, window, button):
        if window.flags() & gtk.VISIBLE:
            button.set_active(True)
        else:
            button.set_active(False)

    def _toggle_liveplot_cb(self, widget):
        qt.flow.toggle_live_plot()

    def _toggle_replot_cb(self, widget):
        qt.replot_all()
    
    def _user_changed(self, widget):
        self._userbtn.set_sensitive(True)
    
    def _save_user(self, widget):
        user = self._userfield.get_active_text()
        get_shared_config().set('user', user)
        self._userbtn.set_sensitive(False)
        if not self._user_in_cb(user):
            self._add_user_cb_row(user)
    
    def _user_in_cb(self, name):
        i = self._userlist.get_iter_first()
        while i is not None:
            if self._userlist.get_value(i, 0) == name:
                return True
            i = self._userlist.iter_next(i)
        return False
    
    def _add_user_cb_row(self, name):
        row_iter = self._userlist.append()
        self._userlist.set_value(row_iter, 0, name)
    
    def _populate_user_cb(self):
        '''Refresh the list of users who have measured before.'''
        self._userlist.clear()
        datadir = get_read_only_config('qtlab').get('datadir')
        if datadir[-1] != '/' and datadir[-1] != '\\':
            datadir += '/'
        if os.path.isdir(datadir):
           dirs = os.listdir(datadir)
           for name in dirs:
               if (re.match(nouser_regex, name) is None and
                       os.path.isdir(datadir + name)):
                   self._add_user_cb_row(name)
        else:
            logging.error('Couldn\'t open data dir %s'% datadir)


Window = MainWindow

