# Tessier q-manager gui client

import logging
l = logging.getLogger()
l.setLevel(logging.WARNING)

import os
import sys
import time
import optparse
import this
adddir = os.path.join(os.getcwd(), 'source')
sys.path.insert(0, adddir)

# We should not overwrite the config file set up by client_shared.py
from lib import config
config = config.get_config()

from lib.network import object_sharer as objsh

from lib.misc import get_traceback
TB = get_traceback()()

from PySide import QtCore
from PySide import QtGui
from PySide import QtDeclarative

class ZenWrapper(QtCore.QObject):
    def __init__(self, zenItem):
        QtCore.QObject.__init__(self)
        self._zenItem = zenItem
        self._checked = False

    def _name(self):
        return self._zenItem

    def is_checked(self):
        return self._checked

    def toggle_checked(self):
        self._checked = not self._checked
        self.changed.emit()

    changed = QtCore.Signal()

    name = QtCore.Property(unicode, _name, notify=changed)
    checked = QtCore.Property(bool, is_checked, notify=changed)

class ZenListModel(QtCore.QAbstractListModel):
    def __init__(self, zenItems):
        QtCore.QAbstractListModel.__init__(self)
        self._zenItems = zenItems
        self.setRoleNames({0: 'zenItem'})

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._zenItems)

    def checked(self):
        return [x for x in self._zenItems if x.checked]

    def data(self, index, role):
        if index.isValid() and role == 0:
            return self._zenItems[index.row()]

class Controller(QtCore.QObject):
    @QtCore.Slot(QtCore.QObject, QtCore.QObject)
    def toggled(self, model, wrapper):
        global view, __doc__
        wrapper.toggle_checked()
        new_list = model.checked()
        print '='*20, 'New List', '='*20
        print '\n'.join(x.name for x in new_list)
        view.setWindowTitle('%s (%d)' % (__doc__, len(new_list)))

zenItems = [ZenWrapper(zenItem) for zenItem in \
        ''.join([this.d.get(c, c) for c in \
        this.s]).splitlines()[2:]]

controller = Controller()
zenItemList = ZenListModel(zenItems)

view = QtDeclarative.QDeclarativeView()
view.setWindowTitle(__doc__)
view.setResizeMode(QtDeclarative.QDeclarativeView.SizeRootObjectToView)

rc = view.rootContext()

rc.setContextProperty('controller', controller)
rc.setContextProperty('pythonListModel', zenItemList)

view.setSource(__file__.replace('.py', '.qml'))

def _close_client_cb(*args):

    app.exit()
    app.quit()
    sys.exit()

objsh.helper.register_event_callback('disconnected', _close_client_cb)

# Ignore CTRL-C
import signal
signal.signal(signal.SIGINT, signal.SIG_IGN)

view.show()
