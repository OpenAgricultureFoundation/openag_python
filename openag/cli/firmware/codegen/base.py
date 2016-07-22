__all__ = ["Plugin", "CodeGen"]

import itertools

class CodeWriter:
    """
    Provides a thin wrapper around a file object to make it easy to maintain
    consistent indentation when programmaticaly generating code.
    """
    def __init__(self, f):
        self.f = f
        self.indent_level = 0

    def writeln(self, data):
        self.f.write(" "*self.indent_level)
        self.f.write(data + "\n")

    def indent(self, levels=1):
        self.indent_level += 2*levels

    def deindent(self, levels=1):
        self.indent_level -= 2*levels
        if self.indent_level < 0:
            raise ValueError("Can't lower the indent level any further")

class Plugin:
    """
    Base class for plugins for the top-level CodeGen class that are responsible
    for generating a particular type of code.
    """
    def __init__(self, modules, module_types):
        self.modules = modules,
        self.module_types = module_types

    def dependencies(self):
        """
        Should return a set of all of the header files required for this plugin
        to function
        """
        return set()

    def write_declarations(self, f):
        """
        Should write to `CodeWriter` instance `f` statements that declare
        global objects required by this plugin
        """
        pass

    def setup_plugin(self, f):
        """
        Should write to `CodeWriter` instance `f` statements that set up any
        state required by this plugin
        """
        pass

    def _pre_setup_module(self, mod_name, f):
        """
        Should write to `CodeWriter` instance `f` statements to put right
        before the module given by `mod_name` is set up
        """
        pass

    def setup_module(self, mod_name, f):
        """
        Should write to `CodeWriter` instance `f` statements that set up any
        state required for the module given by `mod_name`
        """
        pass

    def _post_setup_module(self, mod_name, f):
        """
        Should write to `CodeWriter` instance `f` statements to put right after
        the module given by `mod_name` is set up
        """
        pass

    def update_plugin(self, f):
        """
        Should write to `CodeWriter` instance `f` statements that update any
        state used by this plugin
        """
        pass

    def _pre_update_module(self, mod_name, f):
        """
        Should write to `CodeWriter` instance `f` statements to put right
        before the module given by `mod_name` is updated
        """
        pass

    def update_module(self, mod_name, f):
        """
        Should write to `CodeWriter` instance `f` statements that update the
        module given by `mod_name`
        """
        pass

    def _post_update_module(self, mod_name, f):
        """
        Should write to `CodeWriter` instance `f` statements to put right after
        the module given by `mod_name` is updated
        """
        pass

    def _pre_on_output(self, mod_name, output_name, f):
        """
        Should write to `CodeWriter` instance `f` statements to put right
        before an output message from the module `mod_name` on the output
        `output_name` is processed
        """
        pass

    def on_output(self, mod_name, output_name, f):
        """
        Should write to `CodeWriter` instance `f` statements that handle an
        outputs message from the module `mod_name` on the output `output_name`
        """
        pass

    def _post_on_output(self, mod_name, output_name, f):
        """
        Should write to `CodeWriter` instance `f` statements to put right after
        an output message from the module `mod_name` on hte output
        `output_name` is processed
        """
        pass

class CodeGen(Plugin):
    """
    Class that handles generating code given information about available module
    types and a desired module configuration. Portions of the code that should
    be configurable are provided by plugins.

    `modules` should be a dictionary mapping module names to dictionaries
    validated by the `Module` schema. `module_types` should be a dictionary
    mapping module type names to dictionaries validated by the `ModuleType`
    schema. All other arguments passed in to the constructor will be
    interpretes as plugins. They should instances of subclasses of `Plugin`.
    """
    def __init__(self, modules, module_types, *plugins):
        self.modules = modules
        self.module_types = module_types
        self.plugins = (self, ) + plugins

    def write_to(self, f):
        """
        Generates code based on the given module configuration and writes it to
        the file object `f`.
        """
        f = CodeWriter(f)

        # Write all dependencies
        deps = set()
        for plugin in self.plugins:
            deps = deps.union(plugin.dependencies())
        for dep in deps:
            f.writeln("#include <{}>".format(dep))
        f.writeln("")

        # Write all declarations
        for plugin in self.plugins:
            plugin.write_declarations(f)
        f.writeln("")

        # Write the setup function
        f.writeln("void setup() {")
        f.indent()
        for plugin in self.plugins:
            plugin.setup_plugin(f)
        for mod_name in self.modules.keys():
            for plugin in self.plugins:
                plugin._pre_setup_module(mod_name, f)
            for plugin in self.plugins:
                plugin.setup_module(mod_name, f)
            for plugin in reversed(self.plugins):
                plugin._post_setup_module(mod_name, f)
        f.deindent()
        f.writeln("}")
        f.writeln("")

        # Write the loop function
        f.writeln("void loop() {")
        f.indent()
        for plugin in self.plugins:
            plugin.update_plugin(f)
        for mod_name, mod_info in self.modules.items():
            for plugin in self.plugins:
                plugin._pre_update_module(mod_name, f)
            for plugin in self.plugins:
                plugin.update_module(mod_name, f)
            for plugin in reversed(self.plugins):
                plugin._post_update_module(mod_name, f)
            mod_type = self.module_types[mod_info["type"]]
            for output_name in mod_type["outputs"]:
                for plugin in self.plugins:
                    plugin._pre_on_output(mod_name, output_name, f)
                for plugin in self.plugins:
                    plugin.on_output(mod_name, output_name, f)
                for plugin in reversed(self.plugins):
                    plugin._post_on_output(mod_name, output_name, f)

        f.deindent()
        f.writeln("}")

    def dependencies(self):
        res = set()
        for module_type in self.module_types.values():
            res.add(module_type["header_file"])
            inputs = module_type["inputs"].values()
            outputs = module_type["outputs"].values()
            for item_info in itertools.chain(inputs, outputs):
                res.add(item_info["type"] + ".h")
        return res

    def write_declarations(self, f):
        for module_name, module_info in self.modules.items():
            module_type = self.module_types[module_info["type"]]

            # Define the module itself
            args_str = ", ".join(
                repr(arg) if not isinstance(arg, bool) else repr(arg).lower()
                for arg in module_info["arguments"]
            )
            if args_str:
                args_str = "(" + args_str + ")"
            f.writeln("{cls_name} {obj_name}{args};".format(
                cls_name=module_type["class_name"], obj_name=module_name,
                args=args_str
            ))

            # Define callbacks for all inputs
            for input_name, input_info in module_type["inputs"].items():
                cls_name = "::".join(input_info["type"].split("/"))
                callback_name = "_".join([
                    module_name, input_name, "callback"
                ])
                f.writeln("void {callback_name}(const {cls_name} &msg) {{".format(
                    callback_name=callback_name, cls_name=cls_name
                ))
                f.writeln("  {module_name}.set_{input_name}(msg);".format(
                    module_name=module_name, input_name=input_name
                ))
                f.writeln("}")

            # Define messages for all outputs
            for output_name, output_info in module_type["outputs"].items():
                cls_name = "::".join(output_info["type"].split("/"))
                obj_name = "_".join([module_name, output_name, "msg"])
                f.writeln("{cls_name} {obj_name};".format(
                    cls_name=cls_name, obj_name=obj_name
                ))

    def setup_module(self, mod_name, f):
        f.writeln("{obj_name}.begin();".format(obj_name=mod_name))

    def update_module(self, mod_name, f):
        f.writeln("{obj_name}.update();".format(obj_name=mod_name))

    def _pre_on_output(self, mod_name, output_name, f):
        msg_name = "_".join([mod_name, output_name, "msg"])
        f.writeln("if ({mod_name}.get_{output_name}({msg_name})) {{".format(
            mod_name=mod_name, output_name=output_name, msg_name=msg_name
        ))
        f.indent()

    def _post_on_output(self, mod_name, output_name, f):
        f.deindent()
        f.writeln("}")
