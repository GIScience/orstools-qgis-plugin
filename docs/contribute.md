## Prerequisites

- IDE, e.g. PyCharm
- [Qt Creator](https://www1.qt.io/offline-installers/#section-11)

## Modifying GUI

Only modify the GUI over Qt Creator:

1. Open `gui/OSMtoolsDialogUI.ui` in Qt Creator
2. Modify to your needs. Name the widgets accordingly.
3. Save file.
4. Check preview: `pyuic5 gui/OSMtoolsDialogUI.ui -p`
4. Populate the `.py` file: `pyuic5 gui/OSMtoolsDialogUI.ui > gui/OSMtoolsDialogUI.py`

## Compile plugin

`pyrcc5 -o resources_rc.py resources.qrc`
