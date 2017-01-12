import os
import json
import tempfile
from click import ClickException
from click.testing import CliRunner

from openag.db_names import FIRMWARE_MODULE
from openag.cli.firmware import init, run, run_module

EXAMPLE_HEADER = """
#ifndef TEST
#define TEST

#include "Arduino.h"
#include <std_msgs/Float32.h>

class Module {
  public:
    void begin();
    void update();
    bool get_output(std_msgs::Float32 &msg);
    void set_input(std_msgs::Float32 msg);
    uint8_t status_level;
    String status_msg;
    uint8_t status_code;
};

#endif """
EXAMPLE_SOURCE = """
#include "module.h"

void Module::begin() { }

void Module::update() { }

bool Module::get_output(std_msgs::Float32 &msg) {
    return true;
}

void Module::set_input(std_msgs::Float32 msg) { }
"""
EXAMPLE_MODULE_JSON = json.dumps({
    "_id": "module",
    "class_name": "Module",
    "header_file": "module.h",
    "inputs": {
        "input": {
            "type": "std_msgs/Float32",
        }
    },
    "outputs": {
        "output": {
            "type": "std_msgs/Float32",
        }
    }
})

EXAMPLE_LIBRARY_JSON = json.dumps({
    "name": "module",
    "frameworks": "arduino",
    "platforms": "*"
})

def test_run_no_modules():
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Run -- Should fail because the project is not initialized yet
        res = runner.invoke(run)
        assert res.exit_code, res.output

        # Init -- Should work
        res = runner.invoke(init)
        assert res.exit_code == 0, res.exception or res.output

        # Write an empty modules.json file
        with open("modules.json", "w+") as f:
            json.dump({ }, f)

        # Run -- Should work
        res = runner.invoke(run, ["-f", "modules.json"])
        assert res.exit_code == 0, res.exception or res.output

def test_run_no_modules_with_plugins():
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Init -- Should work
        res = runner.invoke(init)
        assert res.exit_code == 0, res.exception or res.output

        # Write an empty modules.json file
        with open("modules.json", "w+") as f:
            json.dump({ }, f)

        # Run with ROS plugin -- Should work
        res = runner.invoke(run, ["-p", "ros", "-f", "modules.json"])
        print res.output
        assert res.exit_code == 0, res.exception or res.output

        # Run with CSV pliugin -- Should work
        res = runner.invoke(run, ["-p", "csv", "-f", "modules.json"])
        assert res.exit_code == 0, res.exception or res.output

        # Run with both plugins -- Should work
        res = runner.invoke(
            run, ["-p", "ros", "-p", "csv", "-f", "modules.json"]
        )
        assert res.exit_code == 0, res.exception or res.output

def test_run_module():
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Write header file
        with open("module.h", "w+") as f:
            f.write(EXAMPLE_HEADER)
        # Write source file
        with open("module.cpp", "w+") as f:
            f.write(EXAMPLE_SOURCE)
        # Write module.json file
        with open("module.json", "w+") as f:
            f.write(EXAMPLE_MODULE_JSON)
        # Write library.json file
        with open("library.json", "w+") as f:
            f.write(EXAMPLE_LIBRARY_JSON)

        # Initialize the project
        res = runner.invoke(init)
        assert res.exit_code == 0, repr(res.exception) or res.output

        # Run with both plugins -- Should work
        res = runner.invoke(
            run_module, ["-p", "ros", "-p", "csv"]
        )
        assert res.exit_code == 0, repr(res.exception) or res.output

def test_run_single_module():
    runner = CliRunner()

    with runner.isolated_filesystem():
        res = runner.invoke(init)
        assert res.exit_code == 0, res.exception or res.output

        here = os.getcwd()
        lib_folder = os.path.join(here, "lib")
        module_folder = os.path.join(lib_folder, "module")
        os.mkdir(module_folder)
        with open(os.path.join(module_folder, "module.h"), "w+") as f:
            f.write(EXAMPLE_HEADER)
        with open(os.path.join(module_folder, "module.cpp"), "w+") as f:
            f.write(EXAMPLE_SOURCE)
        with open(os.path.join(module_folder, "module.json"), "w+") as f:
            f.write(EXAMPLE_MODULE_JSON)
        with open(os.path.join(module_folder, "library.json"), "w+") as f:
            f.write(EXAMPLE_LIBRARY_JSON)
        with open(os.path.join(here, "modules.json"), "w+") as f:
            json.dump({
                FIRMWARE_MODULE: [
                    {
                        "_id": "module",
                        "type": "module"
                    }
                ]
            }, f)

        res = runner.invoke(run, ["-f", "modules.json"])
        assert res.exit_code == 0, repr(res.exception) or res.output

        res = runner.invoke(run, [
            "-f", "modules.json", "-p", "csv"
        ])
        assert res.exit_code == 0, repr(res.exception) or res.output

        res = runner.invoke(run, [
            "-f", "modules.json", "-p", "ros"
        ])
        assert res.exit_code == 0, repr(res.exception) or res.output

def test_run_multiple_modules():
    runner = CliRunner()

    with runner.isolated_filesystem():
        res = runner.invoke(init)
        assert res.exit_code == 0, res.exception or res.output

        here = os.getcwd()
        lib_folder = os.path.join(here, "lib")
        module_folder = os.path.join(lib_folder, "module")
        os.mkdir(module_folder)
        with open(os.path.join(module_folder, "module.h"), "w+") as f:
            f.write(EXAMPLE_HEADER)
        with open(os.path.join(module_folder, "module.cpp"), "w+") as f:
            f.write(EXAMPLE_SOURCE)
        with open(os.path.join(module_folder, "module.json"), "w+") as f:
            f.write(EXAMPLE_MODULE_JSON)
        with open(os.path.join(module_folder, "library.json"), "w+") as f:
            f.write(EXAMPLE_LIBRARY_JSON)
        with open(os.path.join(here, "modules.json"), "w+") as f:
            json.dump({
                FIRMWARE_MODULE: [
                    {
                        "_id": "module_a",
                        "type": "module"
                    },
                    {
                        "_id": "module_b",
                        "type": "module"
                    }
                ]
            }, f)

        res = runner.invoke(run, ["-f", "modules.json"])
        assert res.exit_code == 0, repr(res.exception) or res.output

        res = runner.invoke(run, [
            "-f", "modules.json", "-p", "csv"
        ])
        assert res.exit_code == 0, repr(res.exception) or res.output

        res = runner.invoke(run, [
            "-f", "modules.json", "-p", "ros"
        ])
        assert res.exit_code == 0, repr(res.exception) or res.output

def test_csv_broken_output_type():
    runner = CliRunner()

    with runner.isolated_filesystem():
        res = runner.invoke(init)
        assert res.exit_code == 0, repr(res.exception) or res.output

        here = os.getcwd()
        lib_folder = os.path.join(here, "lib")
        module_folder = os.path.join(lib_folder, "module")
        os.mkdir(module_folder)
        with open(os.path.join(module_folder, "module.h"), "w+") as f:
            f.write("""
#ifndef TEST
#define TEST

#include "Arduino.h"
#include <std_msgs/UInt8MultiArray.h>

class Module {
  public:
    void begin();
    void update();
    bool get_output(std_msgs::UInt8MultiArray &msg);
    uint8_t status_level;
    String status_msg;
};
#endif
""")
        with open(os.path.join(module_folder, "module.cpp"), "w+") as f:
            f.write("""
#include "module.h"

void Module::begin() { }

void Module::update() { }

bool Module::get_output(std_msgs::UInt8MultiArray &msg) {
    return true;
}
""")
        with open(os.path.join(module_folder, "module.json"), "w+") as f:
            json.dump({
                "class_name": "Module",
                "header_file": "module.h",
                "outputs": {
                    "output": {
                        "type": "std_msgs/UInt8MultiArray"
                    }
                }
            }, f)
        with open(os.path.join(here, "modules.json"), "w+") as f:
            json.dump({
                FIRMWARE_MODULE: [
                    {
                        "_id": "module",
                        "type": "module"
                    }
                ]
            }, f)

        res = runner.invoke(run, ["-f", "modules.json", "-p", "csv"])
        assert isinstance(res.exception, RuntimeError), repr(res.exception)

def test_dependencies():
    runner = CliRunner()

    with runner.isolated_filesystem():
        with open("module.h", "w+") as f:
            f.write("""
#ifndef TEST
#define TEST

#include "Arduino.h"
#include "DallasTemperature.h"
#include <openag_module.h>

class MyModule : public Module {
  public:
    void begin();
    void update();
};
#endif
""")
        with open("module.cpp", "w+") as f:
            f.write("""
#include "module.h"

void MyModule::begin() { }
void MyModule::update() { }
""")
        with open("module.json", "w+") as f:
            json.dump({
                "header_file": "module.h",
                "class_name": "MyModule",
                "description": "My module",
                "dependencies": [
                    {
                        "type": "pio",
                        "id": 54
                    },
                    {
                        "type": "git",
                        "url": "https://github.com/OpenAgInitiative/openag_firmware_module.git"
                    }
                ]
            }, f)

        with open("library.json", "w+") as f:
            f.write(EXAMPLE_LIBRARY_JSON)

        res = runner.invoke(run_module, ["-p", "csv"])
        assert res.exit_code == 0, repr(res.exception) or res.output

def test_run_invalid_module_ids():
    runner = CliRunner()

    with runner.isolated_filesystem():
        res = runner.invoke(init)
        assert res.exit_code == 0, repr(res.exception) or res.output

        here = os.getcwd()
        lib_folder = os.path.join(here, "lib")
        module_folder = os.path.join(lib_folder, "module")
        os.mkdir(module_folder)
        with open(os.path.join(module_folder, "module.h"), "w+") as f:
            f.write(EXAMPLE_HEADER)
        with open(os.path.join(module_folder, "module.cpp"), "w+") as f:
            f.write(EXAMPLE_SOURCE)
        with open(os.path.join(module_folder, "module.json"), "w+") as f:
            f.write(EXAMPLE_MODULE_JSON)
        with open(os.path.join(module_folder, "library.json"), "w+") as f:
            f.write(EXAMPLE_LIBRARY_JSON)
        with open(os.path.join(here, "modules.json"), "w+") as f:
            json.dump({
                FIRMWARE_MODULE: [
                    {
                        "_id": "for",
                        "type": "module"
                    },
                    {
                        "_id": "123",
                        "type": "module"
                    }
                ]
            }, f)

        res = runner.invoke(run, ["-f", "modules.json"])
        assert res.exit_code == 0, repr(res.exception)

def test_preprocessor_flags():
    runner = CliRunner()

    with runner.isolated_filesystem():
        res = runner.invoke(init)
        assert res.exit_code == 0, repr(res.exception)

        here = os.getcwd()
        with open("module.h", "w+") as f:
            f.write("""
#ifndef TEST
#define TEST

#include <openag_module.h>

class MyModule : public Module {
  public:
    void begin();
    void update();
};

#endif
""")
        with open("module.cpp", "w+") as f:
            f.write("""
#include "module.h"

void MyModule::begin() { }

void MyModule::update() {
  #ifdef OPENAG_CATEGORY_CALIBRATION
  PlatformIO should complain about this line
  #endif
}
""")
        with open("module.json", "w+") as f:
            json.dump({
                "class_name": "MyModule",
                "header_file": "module.h",
                "dependencies": [
                    {
                        "type": "git",
                        "url": "https://github.com/OpenAgInitiative/openag_firmware_module.git"
                    }
                ]
            }, f)

        with open("library.json", "w+") as f:
            f.write(EXAMPLE_LIBRARY_JSON)

        res = runner.invoke(run_module)
        assert res.exit_code == 0, repr(res.exception)

        res = runner.invoke(run_module, ["-c", "calibration"])
        assert res.exit_code != 0, res.output
