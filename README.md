# ORS Tools QGIS plugin

![Testing](https://github.com/Merydian/orstools-qgis-plugin/actions/workflows/test.yml/badge.svg)
![Ruff](https://github.com/Merydian/orstools-qgis-plugin/actions/workflows/ruff.yml/badge.svg)

![ORS Tools](https://user-images.githubusercontent.com/23240110/122937401-3ee72400-d372-11eb-8e3b-6c435d1dd964.png)

Set of tools for QGIS to use the [openrouteservice](https://openrouteservice.org) (ORS) API.

ORS Tools gives you easy access to the following API's:

- [Directions](https://openrouteservice.org/dev/#/api-docs/v2/directions/{profile}/geojson/post)
- [Isochrones](https://openrouteservice.org/dev/#/api-docs/v2/isochrones/{profile}/post)
- [Matrix](https://openrouteservice.org/dev/#/api-docs/v2/matrix/{profile}/post)
- [Traveling Salesman](https://openrouteservice.org/dev/#/api-docs/optimization/post)

The [wiki](https://github.com/GIScience/orstools-qgis-plugin/wiki/ORS-Tools-Help) offers a tutorial on usage.

In case of issues/bugs, please use the [issue tracker](https://github.com/GIScience/orstools-qgis-plugin/issues).

For general questions, please ask in our [forum](https://ask.openrouteservice.org/c/sdks/qgis).

See also:
- [Rate limits](https://openrouteservice.org/restrictions/)
- [ORS user dashboard](https://openrouteservice.org/dev/#/home)
- [API documentation](https://openrouteservice.org/dev/#/api-docs)
- ORS openrouteservice-py on [PyPi](https://pypi.python.org/pypi/openrouteservice)
- ORS Tools plugin in [QGIS repo](https://plugins.qgis.org/plugins/ORStools/)

## Functionalities

### General

Use QGIS to generate input for **routing**, **isochrones** and **matrix calculations** powered by ORS.

You'll have to create an openrouteservice account and get a free API key first: <https://openrouteservice.org/sign-up>.
After you have received your key, add it to the default `openrouteservice` provider via `Web` ► `ORS Tools` ►
`Provider Settings` or click the settings button in the ORS Tools dialog.

The plugin offers either a GUI in the `Web` menu and toolbar of QGIS to interactively use the ORS API
from the map canvas.

For batch operations you can find an `ORS Tools` folder in the Processing Toolbox.

### Customization

Additionally, you can register other ORS providers, e.g. if you're hosting a custom ORS backend.

Configuration takes place either from the Web menu entry *ORS Tools* ► *Provider settings*. Or from the *Config* button
in the GUI.

## Getting Started

### Requirements

QGIS version: **v3.4** or above

[ORS API key](https://openrouteservice.org/dev/#/signup)

### Installation

In the QGIS menu bar click `Plugins` ► `Manage and Install Plugins...`.

Then search for `openrouteservice` and install `ORS Tools`.

Alternatively, install the plugin manually:
  - [Download](https://github.com/GIScience/orstools-qgis-plugin/archive/main.zip) ZIP file from GitHub
  - Unzip folder contents and copy `ORStools` folder to:
    - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
    - Windows: `C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
    - Mac OS: `Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`

## Development Setup

### Requirements:
- QGIS-LTR (3.16)
  
  Recommended plugins:
  - [plugin reloader](https://plugins.qgis.org/plugins/plugin_reloader/)
  - [First Aid](https://plugins.qgis.org/plugins/firstaid/) (community PyCharm edition only)
- PyCharm or similar IDE

### Clone repository

On PyCharm startup create a new project with `Get From VHS` and paste the repository url
`https://github.com/GIScience/orstools-qgis-plugin`
    
or clone manually and open the folder with your IDE
```shell
# clone the repository
git clone https://github.com/GIScience/orstools-qgis-plugin.git
```

### Set up environment and python interpreter
Use the Python from your QGIS installation as interpreter in a new virtual environment
1. `PyCharm` ► `Preferences` ► `Project` ► `Python Interpreter`
1. click cogwheel and choose `Add...`
1. select `Virtualenv Environment`(default)
1. set env folder to e.g. `~/Workspaces/qgis` (this environment can be used for multiple QGIS plugins if needed)
1. set Base interpreter to the one QGIS uses (`QGIS` ► `Preferences` ► `System` ► `Current environment variables` ►
    `PYTHONHOME` + `bin/python3.8`)
    - (Mac) `/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3.8`
    - (Linux) might work with the system python (See [QGIS cookbook](https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/plugins/ide_debugging.html#debugging-with-pycharm-on-ubuntu-with-a-compiled-qgis))
    - (Windows) to be determined (Best also use the [cookbook](https://docs.qgis.org/3.16/en/docs/pyqgis_developer_cookbook/plugins/ide_debugging.html))
1. check `Inherit global site-packages` and if you want `Make available to all projects`
1. click `Ok`
1. in the overview of project interpreters, select the just created one (qgis) and click the last button showing
   interpreter paths
1. add the binary folder inside QGIS contents to the environment path, to expose cli commands like `pyuic5`,
  `pyrcc5`, `ogr2ogr` and more:
    - (Mac) `/Applications/QGIS-LTR.app/Contents/MacOS/bin`
    - (Linux) to be determined
    - (Windows) to be determined

### Link plugin to QGIS
To not copy around files all the time, create a symlink in the QGIS plugin folder to the ORStools folder of the
repository
```shell
ln -s ORStools <qgis_plugins_path>
```
where `<qgis_plugins_path>` is one of:
- Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/ORStools`
- Windows: `C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\ORStools`
- Mac OS: `Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/ORStools`

### CI
#### Testing
The repository tests on the QGis Versions *3.16*, *3.22* and the *latest* version. 
Until now, it's only possible to test one version at a time.

To do local test runs you can use a [conda installation](https://github.com/opengisch/qgis-conda-builder) of the QGis version you want to test.
You will also have to install *xvfb* to run the tests on involving an interface. 
Lastly, we need [*Pytest*](https://docs.pytest.org/en/8.0.x/) to run tests in general. 

To do the above run use these commands:
1. Install a version of anaconda, preferrably [*miniforge*](https://github.com/conda-forge/miniforge).

2. Create and prepare the environment.
```shell
# create environment
mamba create --name qgis_test
# activate envotonment
conda activate qgis_test
# install pip
mamba install qgis pip
```
3. Install QGis using mamba.
```shell
mamba install -c conda-forge qgis=[3.16, 3.22, latest] # choose one
```

4. Install *xvfb*
```shell
sudo apt-get update
sudo apt install xvfb
```

5. Install *Pytest* using pip in testing environment.
```shell
pip install -U pytest
```

To run the tests you will need an ORS-API key:
```shell
cd orstools-qgis-plugin
export ORS_API_KEY=[Your API key here] && xvfb-run pytest
```

### Debugging
In the **PyCharm community edition** you will have to use logging and printing to inspect elements.
The First Aid QGIS plugin can probably also be used additionally.

The **professional PyCharm edition** offers remote debugging with breakpoints which lets you inspect elements during runtime, and
step through the code execution.

To use the debugger create a new run configuration:
1. click the dropdown next to the run button
1. select `Edit configurations`
1. click `+` and select `Python Debug Server`
1. give the configuration a name and set the `Port` to `53100` and leave the `IDE host name` at `localhost`
1. copy the command to connect to the debug server (`2.`)
1. remember the version number of the `pydevd-pycharm` you will need (`1.`)
1. click `ok`
1. install the exact version package in the
   interpreter package list (`PyCharm` ► `Preferences` ► `Project` ► `Python Interpreter` ► `+`)
   
    or install from the terminal
   ```shell
   # replace the version with the one listed in the run configuration
   pip install pydevd-pycharm~=211.7142.13
    ```
1. create a live template to quickly insert break points (`PyCharm` ► `Preferences` ► `Editor` ► `Live Templates`)
    - collapse `Python` and click `+`
    - set abbreviation to e.g. `br` add description and set `Template text` to 
    ```shell
    import pydevd_pycharm
    pydevd_pycharm.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)
    ```
1. create a debug branch and commit that loads the pydev-pycharm code
    ```shell
    # create debug branch
    git checkout -b debug
    ```
    add in `ORStools/ORStoolsPlugin.py` before all imports and adjust path with your user and app location if PyCharm
   was not installed via JetBrains toolbox
    ```python
    DEBUG = True
    
    if DEBUG:
        import sys
        sys.path.append('/Users/{your_user}/Library/Application Support/JetBrains/Toolbox/apps/PyCharm-P/ch-0/211.7142.13/PyCharm.app/Contents/debug-eggs/pydevd-pycharm.egg')
        # add breakpoints like:
        import pydevd_pycharm
        pydevd_pycharm.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)
    ```
    avoid raising exceptions in `ORStools/gui/ORStoolsDialog.py` to not crash QGIS every time one is raised
    ```python
    # below other imports
    from ..ORStoolsPlugin import DEBUG
   
    # surround raise with if block around run_gui_control()
    if not DEBUG:
        raise
    ```
   commit changes
   ```shell
    git add . && git commit -m "Debug commit"
   ```
**Important**: When using the remote debugger of PyCharm you have to **disable the First Aid plugin**, as it interferes
with the remote debugger.

#### Workflow

To debug you now only need to `cherry-pick` the debug commit to the branch you are working on and place any changes
on top.
```shell
# this will cherry pick the last commit of the debug branch
git cherry-pick debug
```

Make sure the local `debug` branch is up to date with the `main` branch by rebasing regularly 
```shell
# you will be on debug branch afterwards
git rebase main debug
```

Before starting QGIS, you need to run the "QGIS debug" configuration you created.  
Afterwards you can open QGIS and press the plugin reloader button (configured to reload ORStools).
It should break at the breakpoint introduced in the debug commit.

In general, you can now use normal breakpoints of the IDE with [left click in the gutter](https://www.jetbrains.com/help/pycharm/using-breakpoints.html#set-line-breakpoint)
(or ctrl/cmd + F8).

If you are debugging the processing algorithms, which run in another thread, you will have to add another manual
breakpoint in e.g. `ORStools/proc/isochrones_layer_proc.py` by typing `br` (or
whatever you configured in your live template), pressing enter and **reload the plugin** in QGIS.

In short: Use IDE breakpoints if they work, if not use manual and IDE breakpoints afterwards.

Once you finalized your changes, remove the manual breakpoints again and drop the debug commit.

You can do this with one of the following
- pressing `alt/option + 9` and right-click the debug commit on your branch and choose `Drop Commit`
- `git stash && git reset --hard HEAD^ && git stash pop`
- commit your changes and `git rebase -i HEAD^^`, prepend the debug commit with a `d` and save

### Interface development

For designing the Dialog the Qt designer shipping with qgis is used. It has relevant classes such as
[QgsMapLayerComboBox](https://qgis.org/pyqgis/3.2/gui/Map/QgsMapLayerComboBox.html) already imported properly.

#### Mac
- use `/Applications/QGIS-LTR.app/Contents/MacOS/bin/designer` instead of
  `/Applications/QGIS-LTR.app/Contents/MacOS/Designer.app` (trying to get other Qt Designer
  or Qt Creator installations to use the correct QGIS classes was unsuccessful)
- if you want a shortcut in Applications do
    ```shell
    cd /Applications
    ln -s QGIS-LTR.app/Contents/MacOS/bin/designer "Qt Designer.app"
    ```

#### Windows
- should create you a shortcut to the Qt Designer with the installation

#### Linux
- [use `designer` command](https://github.com/GIScience/orstools-qgis-plugin/wiki/Developer-Information)

#### Workflow
Proceed similar for other `.ui` files:

1. open the `ORStools/gui/ORStoolsDialogUI.ui` file in the Designer and save your changes after editing.
1. convert the `.ui` file to `.py` file by using `pyuic5` (which should also be accessible as command from your terminal
   if PyCharm uses the [qgis env](#set-up-environment-and-python-interpreter) but using it as a module makes sure the
   correct one is used in case you have other PyQt installations on your machine)
   ```shell
   # make sure you are in the gui folder
   cd ORStools/gui
   # convert to .py and set correct import
   python -m PyQt5.uic.pyuic --import-from . -o ORStoolsDialogUI.py ORStoolsDialogUI.ui
   ```
1. in case you edit resources such as images you also need to convert the `resources.qrc` file
    ```shell
    # also within the gui folder
    python -m PyQt5.pyrcc_main -o resources_rc.py resources.qrc
    ```
1. if you edited or added new widgets you will have to change or include them in `ORStools/gui/directions_gui.py`
   as well

### Translation
Translation uses the QT Linguist for translating GUI and source code strings. All translation-related content resides in `ORStools/i18n`.
Translation is controlled by `ORStools/gui/translate.pro`, stating all UI-forms and sourcefiles that include strings to be translated.
To add a translation, add `orstools_<LANGUAGE_TAG>.ts` to the list of translation in this file.

#### Workflow
1. Generate the `.ts`-files (Translation Source) from `translate.pro` via
    ```shell
   pylupdate5 -noobsolete -verbose translate.pro
    ```
   Note that this will drop obsolete strings, skip `-noobsolete` if you want to keep them.
2. Inspect the changes this has on the existing `*.ts`-files. `pylupdate5` will remove translation comments and might restructure the translation.
3. Translate the `*.ts`-files using QT Linguist via
    ```shell
   linguist orstools_<LANGUAGE_TAG>.ts
    ```
4. Compile the `*.ts`-file to a `*.qm` Qt Translation file via
    ```shell
    lrelease orstools_<LANGUAGE_tag>.ts
    ```

## License

This project is published under the GPLv3 license, see [LICENSE.md](https://github.com/GIScience/orstools-qgis-plugin/blob/main/LICENSE.md) for details.

By using this plugin, you also agree to the [terms and conditions](https://openrouteservice.org/terms-of-service/) of
openrouteservice.

## Acknowledgements

This project was first started by [Nils Nolde](https://github.com/nilsnolde).
