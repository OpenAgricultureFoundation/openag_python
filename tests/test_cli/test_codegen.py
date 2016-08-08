import json
import tempfile

from click.testing import CliRunner

from openag.cli.firmware import init, run, run_module

def test_basic_codegen():
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

def test_basic_plugins():
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

def test_codegen_simple_module():
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Write header file
        with open("module.h", "w+") as f:
            f.write("""
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

#endif
""")
        # Write source file
        with open("module.cpp", "w+") as f:
            f.write("""
#include "module.h"

void Module::begin() { }

void Module::update() { }

bool Module::get_output(std_msgs::Float32 &msg) {
    return true;
}

void Module::set_input(std_msgs::Float32 msg) { }
""")
        # Write module.json file
        with open("module.json", "w+") as f:
            json.dump({
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
            }, f)

        # Initialize the project
        res = runner.invoke(init)
        assert res.exit_code == 0, res.exception or res.output

        # Run with both plugins -- Should work
        res = runner.invoke(
            run_module, ["-p", "ros", "-p", "csv", "-f", "modules.json"]
        )
        assert res.exit_code == 0, res.exception or res.output
