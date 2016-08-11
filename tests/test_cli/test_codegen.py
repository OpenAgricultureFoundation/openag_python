import os
import json
import tempfile

from click.testing import CliRunner

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
EXAMPLE_JSON = json.dumps({
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
            f.write(EXAMPLE_JSON)

        # Initialize the project
        res = runner.invoke(init)
        assert res.exit_code == 0, res.exception or res.output

        # Run with both plugins -- Should work
        res = runner.invoke(
            run_module, ["-p", "ros", "-p", "csv", "-f", "modules.json"]
        )
        assert res.exit_code == 0, res.exception or res.output

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
            f.write(EXAMPLE_JSON)
        with open(os.path.join(here, "modules.json"), "w+") as f:
            json.dump({
                "module": {
                    "type": "module"
                }
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
            f.write(EXAMPLE_JSON)
        with open(os.path.join(here, "modules.json"), "w+") as f:
            json.dump({
                "module_a": {"type": "module"},
                "module_b": {"type": "module"}
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
